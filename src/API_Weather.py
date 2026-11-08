import requests
import datetime

from .settings import settings
from .CORE_Cache import cached
from .CORE_Helpers import TIMEOUT
from .configs import HPA_TO_INHG, OPEN_METEO_BASE_URL
from .CORE_Logging import get_logger

logger = get_logger("API_Weather")



def unit_params(unit: str) -> str:
    """URL parameters that ask Open-Meteo for the given measurement system."""
    if unit == "imperial":
        return "&temperature_unit=fahrenheit&wind_speed_unit=mph"
    return ""


class Weather:
    """
    See Documentation at: https://open-meteo.com/en/docs

    Every request takes the measurement system as ``unit``, so it is part of
    the cache key: switching units never returns data cached in the old ones.
    """

    # Current Weather =============================================
    @classmethod
    @cached()
    def current_weather(cls, latitude: float, longitude: float, unit: str = "metric", **kwargs):
        url = OPEN_METEO_BASE_URL + f"?latitude={latitude}&longitude={longitude}"

        # Check for kwargs keyword parameters
        if "current" in kwargs:
            current_fields = ",".join(kwargs.get("current"))
            url = url + f"&current={current_fields}" + unit_params(unit)

        try:
            url = url + "&timeformat=unixtime"
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()  # Raise an exception if the request was unsuccessful
            data = response.json()
            if unit == "imperial":
                inHg = data['current']['pressure_msl'] * HPA_TO_INHG
                data['current']['pressure_msl'] = inHg
                data['current_units']['pressure_msl'] = 'inHg'
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch current weather data: {e}")

    def _get_current_weather(self, lat, lon):
        current_args = [
            "temperature_2m",
            "relativehumidity_2m",
            "apparent_temperature",
            "is_day",
            "uv_index",
            "precipitation",
            "weathercode",
            "pressure_msl",
            "windspeed_10m",
            "winddirection_10m",
        ]
        return self.current_weather(lat, lon, unit=settings.unit, current=current_args)

    # Current Weather of several places ===========================
    @classmethod
    @cached()
    def current_for_locations(cls, latitudes: str, longitudes: str, unit: str = "metric"):
        """Current conditions of several places in one request, in the order given."""
        url = (
            OPEN_METEO_BASE_URL
            + f"?latitude={latitudes}&longitude={longitudes}"
            + "&current=temperature_2m,weathercode,is_day"
            + "&timeformat=unixtime"
            + unit_params(unit)
        )

        try:
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
            # A single place comes back as one object instead of a list
            return data if isinstance(data, list) else [data]
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch weather of saved locations: {e}")

    def _get_current_for_locations(self, coords: list):
        """Takes a list of "lat,lon" strings."""
        latitudes, longitudes = zip(*(item.split(",") for item in coords))
        return self.current_for_locations(
            ",".join(latitudes), ",".join(longitudes), unit=settings.unit
        )

    # Hourly Forecast ==============================================
    @classmethod
    @cached()
    def forecast_hourly(cls, latitude: float, longitude: float, unit: str = "metric", **kwargs):
        url = OPEN_METEO_BASE_URL + f"?latitude={latitude}&longitude={longitude}&timezone=auto"

        # Check for kwargs keyword parameters
        if "hourly" in kwargs:
            hourly_fields = ",".join(kwargs.get("hourly"))
            url = url + f"&hourly={hourly_fields}" + unit_params(unit)

        try:
            url = url + "&timeformat=unixtime"
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()  # Raise an exception if the request was unsuccessful
            data = response.json()
            if unit == "imperial":
                for i in range(len(data['hourly']['pressure_msl'])):
                    inHg = data['hourly']['pressure_msl'][i] * HPA_TO_INHG
                    data['hourly']['pressure_msl'][i] = inHg
                data['hourly_units']['pressure_msl'] = 'inHg'
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch data: {e}")

    def _get_hourly_forecast(self, lat, lon):
        hourly_args = [
            "temperature_2m",
            "relativehumidity_2m",
            "dewpoint_2m",
            "apparent_temperature",
            "weathercode",
            "precipitation",
            "precipitation_probability",
            "pressure_msl",
            "visibility",
            "windspeed_10m",
            "wind_direction_10m",
            "uv_index",
            "is_day",
        ]

        today = datetime.datetime.today().date()
        tomorrow = today + datetime.timedelta(days=1)
        return self.forecast_hourly(
            lat, lon, unit=settings.unit, hourly=hourly_args,
            start_date=today, end_date=tomorrow,
        )

    # Forecast daily ====================================================
    @classmethod
    @cached()
    def forecast_daily(cls, latitude: float, longitude: float, unit: str = "metric", **kwargs):
        url = OPEN_METEO_BASE_URL + f"?latitude={latitude}&longitude={longitude}"
        if "daily" in kwargs:
            hourly_fields = ",".join(kwargs.get("daily"))
            url = url + f"&daily={hourly_fields}"

        if "timezone" in kwargs:
            url = url + f"&timezone={kwargs.get('timezone')}"
        if "start_date" in kwargs:
            url = url + f"&start_date={kwargs.get('start_date')}"

        if "end_date" in kwargs:
            url = url + f"&end_date={kwargs.get('end_date')}" 

        try:
            url = url + "&timeformat=unixtime" + unit_params(unit)
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()  # Raise an exception if the request was unsuccessful
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch data: {e}")

    def _get_daily_forecast(self, lat, lon):
        daily_args = [
            "weathercode",
            "temperature_2m_max",
            "temperature_2m_min",
            "sunrise",
            "sunset",
            "uv_index_max",
            "precipitation_sum",
            "windspeed_10m_max",
            "precipitation_probability_max",
        ]

        return self.forecast_daily(
            lat, lon, unit=settings.unit, daily=daily_args, timezone="GMT"
        )
