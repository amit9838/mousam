"""The weather store: the selected city's data and its loading status.

Fetching runs on worker threads, and the results are handed to the main loop
before any property is set or any signal is emitted, so the UI never sees a
thread.
"""

import threading
import time
from typing import Callable, Dict, Iterable, List, Optional

from gi.repository import GLib, GObject

from ..services import open_meteo
from ..services import air_quality
from ..services.air_quality import fetch_air_quality
from ..services.settings import settings
from ..core.forecast_client import ForecastClient
from ..core.levels import (
    classify_humidity_level, classify_pressure_level, classify_uv_index, classify_wind_speed_level,
)
from ..core.forecast import nearest_hour_index
from ..core.units import transform_visibility_data
from ..core.models import CurrentWeather, HourlyWeather, DailyWeather, WeatherField, AirPollutionData
from ..services.selected_city import get_time_difference
from ..services.network import check_internet_connection
from ..core.locations import parse_coords_key
from ..core.log import get_logger
from ..config import CONNECT_TIMEOUT, TIMEOUT

logger = get_logger("data_manager")

# The values of WeatherStore.status
STATUS_IDLE = "idle"  # nothing fetched yet
STATUS_LOADING = "loading"  # a fetch is running; the data is cleared
STATUS_READY = "ready"  # the data of `location` is there
STATUS_OFFLINE = "offline"  # no connection; the data of the last fetch is kept
STATUS_ERROR = "error"  # the last fetch failed; `error` says why


class WeatherStore(GObject.Object):
    """The one holder of the selected city's weather.

    Ask for data with refresh() and listen to notify::status (or
    notify::is-ready). A refresh while a fetch for the same city is running
    joins it: its result reaches every listener. A refresh for another city
    fetches that one once the running fetch ends, and the old result is
    dropped. Fields and signals change only on the main loop.
    """

    __gsignals__ = {
        "data-updated": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    status = GObject.Property(type=str, default=STATUS_IDLE)
    error = GObject.Property(type=str, default="")
    location = GObject.Property(type=str, default="")  # "lat,lon" the data belongs to

    current_weather = GObject.Property(type=GObject.TYPE_PYOBJECT)
    hourly_forecast = GObject.Property(type=GObject.TYPE_PYOBJECT)
    daily_forecast = GObject.Property(type=GObject.TYPE_PYOBJECT)
    air_pollution = GObject.Property(type=GObject.TYPE_PYOBJECT)

    def __init__(
        self,
        client: ForecastClient = open_meteo,
        fetch_air: Callable = fetch_air_quality,
        clear_air_cache: Callable = air_quality.clear_cache,
        settings=settings,
        is_online: Callable[..., bool] = check_internet_connection,
    ):
        super().__init__()
        self._client = client
        self._fetch_air = fetch_air
        self._clear_air_cache = clear_air_cache
        self._settings = settings
        self._is_online = is_online
        self._ready = False
        self._fetching = None  # The "lat,lon" being fetched, or None
        self._refetch = False  # Another city was asked for during the fetch
        # Current weather of the saved locations, by their "lat,lon" key
        self.saved_locations_weather: Dict[str, CurrentWeather] = {}

    @GObject.Property(type=bool, default=False)
    def is_ready(self):
        """True once a whole fetch has been published, until the next one starts."""
        return self._ready

    # ---------- Fetching ----------

    def refresh(self, check_online: bool = True, hard: bool = False) -> None:
        """Fetch the selected city's weather, unless a fetch is already
        running (then its result is the answer).

        With check_online, a missing connection ends it as STATUS_OFFLINE
        and keeps the data that is there. A hard refresh (Ctrl+Shift+R)
        first forgets the city's cached responses, so everything comes from
        the network; other cities keep theirs.
        """
        # Read on the main loop: the worker never touches settings
        coords = self._settings.selected_city
        unit = self._settings.unit
        if self._fetching is not None:
            if coords != self._fetching:
                self._refetch = True
            return
        self._fetching = coords
        threading.Thread(
            target=self._fetch_worker,
            args=(coords, unit, check_online, hard),
            name="fetch_all_worker",
            daemon=True,
        ).start()

    def _fetch_worker(self, coords: str, unit: str, check_online: bool, hard: bool) -> None:
        if check_online and not self._is_online(force=True):
            GLib.idle_add(self._finish, STATUS_OFFLINE, coords, None)
            return

        if hard:
            # Here, not on the main loop: the cache holds its lock while a
            # request runs, so forgetting could wait for one
            lat, lon = parse_coords_key(coords)
            logger.info(f"Hard refresh: forgetting cached data for {coords}")
            self._client.clear_cache(lat, lon)
            self._clear_air_cache(lat, lon)

        GLib.idle_add(self._start_loading)
        logger.info("Starting background fetch for all weather data")
        try:
            data = self._download(*parse_coords_key(coords), unit)
        except Exception as e:  # A worker's top level: report, never crash
            logger.error(f"Error fetching data: {e}")
            GLib.idle_add(self._finish, STATUS_ERROR, coords, str(e))
            return
        logger.info("All background fetch targets completed successfully")
        GLib.idle_add(self._finish, STATUS_READY, coords, data)

    def _download(self, lat: float, lon: float, unit: str) -> dict:
        """Every model of one city, or an exception saying what failed."""
        logger.debug(f"Fetching current weather for cords: {[lat, lon]}")
        current = _run_all(
            {"cwt": lambda: self._client.fetch_current(lat, lon, unit)},
            timeout_message="Current weather fetch timed out",
        )["cwt"]
        if current is None:
            logger.error("Failed to fetch current weather data from API")
            raise ValueError("Failed to fetch current weather data")

        logger.info("Current weather fetched successfully, starting forecasts and air pollution")
        raw = _run_all({
            "hft": lambda: self._client.fetch_hourly(lat, lon, unit),
            "dft": lambda: self._client.fetch_daily(lat, lon, unit),
            "apt": lambda: self._fetch_air(lat, lon),
            "local_time": lambda: get_time_difference("", True),
        }, optional=("apt",))
        if raw["hft"] is None:
            raise ValueError("Failed to fetch hourly forecast data")
        if raw["dft"] is None:
            raise ValueError("Failed to fetch daily forecast data")

        current_weather = build_current(current, unit)
        hourly = HourlyWeather(raw["hft"])
        add_hourly_fields(current_weather, hourly, raw["hft"]["hourly"]["time"], unit)
        return {
            "current_weather": current_weather,
            "hourly_forecast": hourly,
            "daily_forecast": DailyWeather(raw["dft"]),
            "air_pollution": build_air_pollution(raw["apt"]),
        }

    # ---------- On the main loop ----------

    def _start_loading(self) -> bool:
        self.current_weather = None
        self.hourly_forecast = None
        self.daily_forecast = None
        self.air_pollution = None
        self._ready = False
        self.status = STATUS_LOADING
        self.notify("is-ready")
        return GLib.SOURCE_REMOVE

    def _finish(self, status: str, coords: str, payload) -> bool:
        self._fetching = None
        if self._refetch:
            # The city changed during the fetch: its result is out of date
            self._refetch = False
            self.refresh()
            return GLib.SOURCE_REMOVE
        if status == STATUS_READY:
            for name, value in payload.items():
                setattr(self, name, value)
            self.location = coords
            self._ready = True
            self.emit("data-updated")
            self.notify("is-ready")
        elif status == STATUS_ERROR:
            self.error = payload
        self.status = status
        return GLib.SOURCE_REMOVE

    # ---------- Saved locations ----------

    def refresh_saved_locations(self, coords: List[str], on_done: Callable[[], None]) -> None:
        """Fetch the current weather of every given "lat,lon" in one request
        (failed ones become None), then call on_done on the main loop."""
        unit = self._settings.unit

        def worker():
            raw_data = self._client.fetch_many(coords, unit) or []
            results = {key: CurrentWeather(raw) for key, raw in zip(coords, raw_data)}
            GLib.idle_add(self._saved_locations_loaded, coords, results, on_done)

        threading.Thread(target=worker, name="saved_locations_worker", daemon=True).start()

    def _saved_locations_loaded(self, coords: List[str], results: dict, on_done) -> bool:
        for key in coords:
            self.saved_locations_weather[key] = results.get(key)
        on_done()
        return GLib.SOURCE_REMOVE


# ---------- Building the models (on the worker) ----------

def build_current(raw: dict, unit: str) -> CurrentWeather:
    """Current conditions with their levels."""
    data = CurrentWeather(raw)
    data.relativehumidity_2m.level_str = classify_humidity_level(data.relativehumidity_2m.data)
    data.windspeed_10m.level_str = classify_wind_speed_level(data.windspeed_10m.data)
    data.pressure_msl.level_str = classify_pressure_level(data.pressure_msl.data, unit)
    return data


def add_hourly_fields(current: CurrentWeather, hourly: HourlyWeather, times: list, unit: str) -> None:
    """Fill the current conditions the current API doesn't give (UV index,
    dew point, visibility) from this hour of the hourly forecast."""
    i = nearest_hour_index(times, time.time())
    current.uv_index = WeatherField(
        data=hourly.uv_index.data[i],
        level_str=classify_uv_index(hourly.uv_index.data[i]),
    )
    current.dewpoint_2m = WeatherField(
        unit=hourly.dewpoint_2m.unit,
        data=hourly.dewpoint_2m.data[i],
    )
    visibility = transform_visibility_data(hourly.visibility.unit, hourly.visibility.data[i], unit)
    current.visibility = WeatherField(data=visibility["data"], unit=visibility["unit"])


def build_air_pollution(raw: Optional[dict]) -> Optional[AirPollutionData]:
    """Air quality, with this hour's US and EU AQI; None without it.

    Air quality is optional: when it fails, the weather is still shown, and
    the air quality card says it isn't available.
    """
    if raw is None:
        logger.warning("Air quality isn't available; showing the weather without it")
        return None
    try:
        i = nearest_hour_index(raw["hourly"]["time"], time.time())
        data = AirPollutionData(raw)
        data.current_us_aqi = data.us_aqi.data[i]
        data.current_eu_aqi = data.european_aqi.data[i]
    except (KeyError, TypeError, ValueError, IndexError) as e:
        logger.warning(f"Air quality data unreadable, showing the weather without it: {e!r}")
        return None
    logger.info("Air pollution data updated successfully")
    return data


def _run_all(tasks: Dict[str, Callable], timeout_message: str = "",
             optional: Iterable[str] = ()) -> dict:
    """Run each task on its own thread and return {name: result}.

    Each gets CONNECT_TIMEOUT + TIMEOUT seconds, as long as its request may
    take to connect and answer; the first one still running after that, or
    the first error, is raised. An `optional` task that fails or runs out of
    time gives None instead.
    """
    results, errors = {}, []

    def run(name, task):
        try:
            logger.debug(f"Starting target: {name}")
            results[name] = task()
            logger.debug(f"Finished target: {name}")
        except Exception as e:  # Re-raised below, on the fetch worker
            logger.error(f"Error in target {name}: {e}")
            errors.append((name, e))

    threads = [
        threading.Thread(target=run, args=(name, task), name=name, daemon=True)
        for name, task in tasks.items()
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=CONNECT_TIMEOUT + TIMEOUT)
        if thread.is_alive():
            if thread.name in optional:
                logger.warning(f"{thread.name} fetch timed out; going on without it")
                continue
            raise TimeoutError(timeout_message or f"{thread.name} fetch timed out")
    required_errors = [e for name, e in errors if name not in optional]
    if required_errors:
        raise required_errors[0]
    # A copy, so an optional task that finishes late can't change it
    return {name: results.get(name) for name in tasks}


# The shared instance
weather_store = WeatherStore()
