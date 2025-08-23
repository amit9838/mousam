import time
import gi

from .backendWeather import Weather
from .backendAirPollution import AirPollution
from .config import settings
from .constants import hpa_to_inhg
from .Models import CurrentWeather, HourlyWeather, DailyWeather
from .utils import get_cords
from gettext import gettext as _, pgettext as C_

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

current_weather_data = None
hourly_forecast_data = None
daily_forecast_data = None
air_apllution_data = None


def fetch_current_weather():
    global current_weather_data
    # Get current weather data from api
    obj = Weather()
    current_weather_data = obj._get_current_weather(*get_cords())

    # create object of current weather data
    current_weather_data = CurrentWeather(current_weather_data)

    # Add level strings for diffrent attributes
    current_weather_data.relativehumidity_2m["level_str"] = classify_humidity_level(
        current_weather_data.relativehumidity_2m.get("data")
    )
    current_weather_data.windspeed_10m["level_str"] = classify_wind_speed_level(
        current_weather_data.windspeed_10m.get("data")
    )
    current_weather_data.surface_pressure["level_str"] = classify_presssure_level(
        current_weather_data.surface_pressure.get("data")
    )

    return current_weather_data


def fetch_hourly_forecast():
    global hourly_forecast_data
    # Get current weather data from api
    obj = Weather()
    hourly_forecast_data = obj._get_hourly_forecast(*get_cords())
    hourly_forecast_time_list = hourly_forecast_data.get("hourly").get("time")

    nearest_current_time_idx = 0
    for i in range(len(hourly_forecast_time_list)):
        if (abs(time.time() - hourly_forecast_time_list[i]) // 60) < 30:
            nearest_current_time_idx = i
            break

    hourly_forecast_data = HourlyWeather(hourly_forecast_data)

    current_weather_data.uv_index = {
        "data": hourly_forecast_data.uv_index["data"][nearest_current_time_idx],
        "level_str": classify_uv_index(
            hourly_forecast_data.uv_index["data"][nearest_current_time_idx]
        ),
    }
    current_weather_data.dewpoint_2m = {
        "unit": hourly_forecast_data.dewpoint_2m["unit"],
        "data": hourly_forecast_data.dewpoint_2m["data"][nearest_current_time_idx],
    }
    current_weather_data.visibility = transform_visibility_data(
        hourly_forecast_data.visibility["unit"],
        hourly_forecast_data.visibility["data"][nearest_current_time_idx],
    )

    return hourly_forecast_data


def fetch_daily_forecast():
    global daily_forecast_data

    # Get current weather data from api
    obj = Weather()
    daily_forecast_data = obj._get_daily_forecast(*get_cords())

    # create object of daily forecast data
    daily_forecast_data = DailyWeather(daily_forecast_data)

    return daily_forecast_data


def fetch_current_air_pollution():
    global air_apllution_data
    obj = AirPollution()
    air_apllution_data = obj._get_current_air_pollution(*get_cords())
    return air_apllution_data


def classify_aqi(aqi_value):
    if aqi_value >= 0 and aqi_value <= 50:
        return _("Good")
    elif aqi_value <= 100:
        return _("Moderate")
    elif aqi_value <= 150:
        return _("Poor")
    elif aqi_value <= 200:
        return _("Unhealthy")
    elif aqi_value <= 300:
        return _("Severe")
    else:
        return _("Hazardous")


# ========= Classify diffrent attributes of current weather ==========


def classify_uv_index(uv_index):
    if uv_index <= 2:
        return C_("uvindex", "Low")
    elif uv_index <= 5:
        return C_("uvindex", "Moderate")
    elif uv_index <= 7:
        return C_("uvindex", "High")
    elif uv_index <= 10:
        return C_("uvindex", "Very High")
    else:
        return C_("uvindex", "Extreme")


def classify_humidity_level(uv_index):
    if uv_index < 50:
        return C_("humidity", "Low")
    elif uv_index <= 80:
        return C_("humidity", "Moderate")
    else:
        return C_("humidity", "High")


def classify_presssure_level(pressure):
    low = 940
    normal = 1010
    if settings.unit == "imperial":
        low *= hpa_to_inhg
        normal *= hpa_to_inhg
    if pressure < low:
        return C_("pressure", "Low")
    elif pressure <= normal:
        return C_("pressure", "Normal")
    else:
        return C_("pressure", "High")


def classify_wind_speed_level(wind_speed):
    if wind_speed <= 1:
        return _("Calm")
    elif wind_speed <= 25:
        return _("Light")
    elif wind_speed <= 40:
        return C_("wind", "Moderate")
    elif wind_speed <= 60:
        return _("Strong")
    else:
        return C_("wind", "Extreme")


def transform_visibility_data(unit, data):
    dist_unit = _("km")
    dist = data / 1000
    if settings.unit == "imperial":
        dist_unit = _("miles")
        dist = data / 1609.34

    if unit.lower() == "m":
        data = dist
        unit = dist_unit

    return {"unit": unit, "data": data}
