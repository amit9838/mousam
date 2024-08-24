import requests
import datetime

from .config import settings

extend_url = ""
base_url = "https://api.open-meteo.com/v1/forecast"


class Weather:
    """
    See Documentation at: https://open-meteo.com/en/docs
    """

    def __init__(self) -> None:
        global extend_url

        if settings.unit == "imperial":
            extend_url = "&temperature_unit=fahrenheit&wind_speed_unit=mph"
        else:
            extend_url = ""

    # Current Weather =============================================
    @classmethod
    def current_weather(cls,latitude: float, longitude: float, **kwargs):
        url = base_url + f"?latitude={latitude}&longitude={longitude}"

        # Check for kwargs keyword parameters
        if "current" in kwargs:
            current_fields = ",".join(kwargs.get("current"))
            url = url + f"&current={current_fields}" + extend_url

        try:
            url = url + "&timeformat=unixtime"
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception if the request was unsuccessful
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

    def _get_current_weather(self, lat, lon):
        current_args = [
            "temperature_2m",
            "relativehumidity_2m",
            "apparent_temperature",
            "is_day",
            "uv_index",
            "precipitation",
            "weathercode",
            "surface_pressure",
            "windspeed_10m",
            "winddirection_10m",
        ]
        return self.current_weather(lat, lon, current=current_args)

    # Hourly Forecast ==============================================
    @classmethod
    def forecast_hourly(cls,latitude: float, longitude: float, **kwargs):
        url = base_url + f"?latitude={latitude}&longitude={longitude}"

        # Check for kwargs keyword parameters
        if "hourly" in kwargs:
            hourly_fields = ",".join(kwargs.get("hourly"))
            url = url + f"&hourly={hourly_fields}" + extend_url

        try:
            url = url + "&timeformat=unixtime"
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception if the request was unsuccessful
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

    def _get_hourly_forecast(self, lat, lon):
        hourly_args = [
            "temperature_2m",
            "relativehumidity_2m",
            "dewpoint_2m",
            "apparent_temperature",
            "weathercode",
            "precipitation",
            "precipitation_probability",
            "surface_pressure",
            "visibility",
            "windspeed_10m",
            "wind_direction_10m",
            "uv_index",
            "is_day",
        ]

        today = datetime.datetime.today().date()
        tomorrow = today + datetime.timedelta(days=1)
        return self.forecast_hourly(
            lat, lon, hourly=hourly_args, start_date=today, end_date=tomorrow
        )

    # Forecast daily ====================================================
    @classmethod
    def forecast_daily(cls,latitude: float, longitude: float, **kwargs):
        url = base_url + f"?latitude={latitude}&longitude={longitude}"
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
            url = url + "&timeformat=unixtime" + extend_url
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception if the request was unsuccessful
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

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
        ]

        return self.forecast_daily(lat, lon, daily=daily_args, timezone="GMT")
