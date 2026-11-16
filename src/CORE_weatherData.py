import time
import threading
from gi.repository import GLib, GObject
from .API_Weather import Weather
from .API_AirPollution import AirPollution
from .settings import settings
from .CORE_Levels import (
    classify_humidity_level, classify_presssure_level, classify_uv_index, classify_wind_speed_level,
)
from .CORE_Forecast import nearest_hour_index
from .CORE_Units import transform_visibility_data
from .CORE_Models import CurrentWeather, HourlyWeather, DailyWeather, WeatherField, AirPollutionData
from .CORE_Helpers import get_cords
from .CORE_Logging import get_logger

logger = get_logger("data_manager")

class WeatherDataManager(GObject.Object):
    """
    Centralized data manager for Mousam.
    Handles data storage, validation, and notification of updates.

    The update_* methods run on the fetch worker threads and only store
    data. The signals (data-updated, notify::is-ready) are emitted on the
    main loop, once when a fetch starts (clear) and once when it is done
    (publish), so handlers may touch GTK directly.
    """
    
    __gsignals__ = {
        'data-updated': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    # Properties for data storage
    current_weather = GObject.Property(type=GObject.TYPE_PYOBJECT)
    hourly_forecast = GObject.Property(type=GObject.TYPE_PYOBJECT)
    daily_forecast = GObject.Property(type=GObject.TYPE_PYOBJECT)
    air_pollution = GObject.Property(type=GObject.TYPE_PYOBJECT)
    
    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()
        # Turns true only on the main loop, when a finished fetch is
        # announced, so is-ready is never true before its handlers run
        self._ready = False
        # Current weather of the saved locations, by their "lat,lon" key
        self.saved_locations_weather = {}

    @GObject.Property(type=bool, default=False)
    def is_ready(self):
        """True once a whole fetch has been published, until the next one starts."""
        with self._lock:
            return self._ready

    def _has_all_data(self) -> bool:
        return (self.current_weather is not None and
                self.hourly_forecast is not None and
                self.daily_forecast is not None and
                self.air_pollution is not None)

    def clear(self):
        """Resets all data at the start of a fetch (called from its worker)."""
        with self._lock:
            self._ready = False
            self.current_weather = None
            self.hourly_forecast = None
            self.daily_forecast = None
            self.air_pollution = None
        GLib.idle_add(self._announce, False)

    def publish(self):
        """Announces a finished fetch (called from its worker after every update_*)."""
        GLib.idle_add(self._announce, True)

    def _announce(self, finished: bool) -> bool:
        """Emits the change on the main loop, once per clear or publish."""
        with self._lock:
            # A fetch that started after publish() has cleared the data again
            self._ready = finished and self._has_all_data()
            ready = self._ready
        if ready:
            self.emit("data-updated")
        self.notify("is-ready")
        return GLib.SOURCE_REMOVE

    def update_current_weather(self):
        obj = Weather()
        logger.debug(f"Fetching current weather for cords: {get_cords()}")
        raw_data = obj._get_current_weather(*get_cords())
        if raw_data is None:
            logger.error("Failed to fetch current weather data from API")
            raise ValueError("Failed to fetch current weather data")

        data = CurrentWeather(raw_data)
        data.relativehumidity_2m.level_str = classify_humidity_level(data.relativehumidity_2m.data)
        data.windspeed_10m.level_str = classify_wind_speed_level(data.windspeed_10m.data)
        data.pressure_msl.level_str = classify_presssure_level(data.pressure_msl.data, settings.unit)
        
        with self._lock:
            self.current_weather = data
        return data

    def update_saved_locations_weather(self, coords: list) -> None:
        """Fetches every given "lat,lon" in one request; failed ones become None."""
        raw_data = Weather()._get_current_for_locations(coords) or []
        results = {key: CurrentWeather(raw) for key, raw in zip(coords, raw_data)}

        with self._lock:
            for key in coords:
                self.saved_locations_weather[key] = results.get(key)

    def update_hourly_forecast(self):
        obj = Weather()
        raw_data = obj._get_hourly_forecast(*get_cords())
        if raw_data is None:
            raise ValueError("Failed to fetch hourly forecast data")

        hourly_data = HourlyWeather(raw_data)
        time_list = raw_data.get("hourly").get("time")
        nearest_idx = nearest_hour_index(time_list, time.time())

        # Update current weather with derived hourly fields
        with self._lock:
            if self.current_weather:
                self.current_weather.uv_index = WeatherField(
                    data=hourly_data.uv_index.data[nearest_idx],
                    level_str=classify_uv_index(hourly_data.uv_index.data[nearest_idx]),
                )
                self.current_weather.dewpoint_2m = WeatherField(
                    unit=hourly_data.dewpoint_2m.unit,
                    data=hourly_data.dewpoint_2m.data[nearest_idx],
                )
                vis_transformed = transform_visibility_data(
                    hourly_data.visibility.unit,
                    hourly_data.visibility.data[nearest_idx],
                    settings.unit,
                )
                self.current_weather.visibility = WeatherField(
                    data=vis_transformed["data"],
                    unit=vis_transformed["unit"]
                )
            self.hourly_forecast = hourly_data
            
        return hourly_data

    def update_daily_forecast(self):
        obj = Weather()
        raw_data = obj._get_daily_forecast(*get_cords())
        if raw_data is None:
            raise ValueError("Failed to fetch daily forecast data")

        data = DailyWeather(raw_data)
        with self._lock:
            self.daily_forecast = data
        return data

    def update_air_pollution(self):
        obj = AirPollution()
        raw_data = obj._get_current_air_pollution(*get_cords())
        if raw_data is None:
            raise ValueError("Failed to fetch air pollution data")
        
        time_list = raw_data.get("hourly").get("time")
        nearest_idx = nearest_hour_index(time_list, time.time())
                
        data = AirPollutionData(raw_data)
        data.current_us_aqi = data.us_aqi.data[nearest_idx]
        data.current_eu_aqi = data.european_aqi.data[nearest_idx]
        
        with self._lock:
            self.air_pollution = data
        logger.info("Air pollution data updated successfully")
        return data

# Singleton instance
weather_manager = WeatherDataManager()
