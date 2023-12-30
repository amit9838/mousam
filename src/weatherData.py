from datetime import datetime
from .backendWeather import Weather
from .backendAirPollution import AirPollution
from .Models import *

current_weather_data = None
hourly_forecast_data = None
daily_forecast_data = None
air_apllution_data = None

def fetch_current_weather():
    global current_weather_data
    # Get current weather data from api
    obj = Weather()
    current_weather_data = obj._get_current_weather()

    # create object of current weather data
    current_weather_data = CurrentWeather(current_weather_data)

    return current_weather_data

def fetch_hourly_forecast():
    global hourly_forecast_data
    # Get current weather data from api
    obj = Weather()
    hourly_forecast_data = obj._get_hourly_forecast()

    # create object of hourly forecast data
    hourly_forecast_data = HourlyWeather(hourly_forecast_data)
    set_uv_index()

    return hourly_forecast_data

def fetch_daily_forecast():
    global daily_forecast_data

    # Get current weather data from api
    obj = Weather()
    daily_forecast_data = obj._get_daily_forecast()

    # create object of daily forecast data
    daily_forecast_data = DailyWeather(daily_forecast_data)

    return daily_forecast_data

def fetch_current_air_pollution():
    global air_apllution_data
    obj = AirPollution()
    air_apllution_data = obj._get_current_air_pollution()
    if air_apllution_data is not None:
        air_apllution_data["level"] = classify_aqi(air_apllution_data["current"]["us_aqi"])
    return air_apllution_data


def classify_aqi(aqi_value):
    if aqi_value >= 0 and aqi_value <= 50:
        return "Good"
    elif aqi_value <= 100:
        return "Satisfactory"
    elif aqi_value <= 200:
        return "Moderate"
    elif aqi_value <= 300:
        return "Poor"
    elif aqi_value <= 400:
        return "Very Poor"
    elif aqi_value <= 500:
        return "Severe"
    else:
        return "Hazardous"
    
    
def set_uv_index():
    date_time = [d_t for d_t in hourly_forecast_data.time["data"] if int(datetime.fromtimestamp(d_t).strftime(r"%d")) == datetime.today().date().day]
    date_time = [d_t for d_t in date_time if int(datetime.fromtimestamp(d_t).strftime(r"%H")) == datetime.now().hour]
    date_time = date_time[0]
    
    uv_index = 0
    for i,item in enumerate(hourly_forecast_data.time["data"]):
        if item == date_time:
            uv_index = {"data": hourly_forecast_data.uv_index["data"][i]}
            
    current_weather_data.uv_index = uv_index
    return uv_index
