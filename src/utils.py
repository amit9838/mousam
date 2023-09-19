import requests
from datetime import datetime, timedelta, timezone
from gi.repository import Adw,Gio

current_weather_data = None
air_pollution_data = None
forecast_weather_data = None

def get_weather_data():
    return current_weather_data,air_pollution_data,forecast_weather_data

def set_weather_data(current,air_pollution,forecast):
    global current_weather_data, air_pollution_data,forecast_weather_data
    current_weather_data = current
    air_pollution_data = air_pollution
    forecast_weather_data = forecast

def check_internet_connection():
    url = "http://www.google.com"
    timeout = 5  # Set the timeout value in seconds
    response_text = ""
    has_active_internet = False
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            has_active_internet = True
            return has_active_internet, response_text

    except requests.Timeout:
        response_text = _("Request timeout!")
        return has_active_internet, response_text
    except requests.RequestException as e:
        print(str(e))
        response_text = _("No internet connection!")
        has_active_internet = False
        return has_active_internet, response_text

def get_selected_city_coords():
    settings = Gio.Settings.new("io.github.amit9838.weather")
    selected_city = int(str(settings.get_value('selected-city')))
    added_cities = list(settings.get_value('added-cities'))
    city_loc = added_cities[selected_city].split(',')
    return city_loc[-2],city_loc[-1]  #latitude,longitude

def create_toast(text,priority=0):
    toast = Adw.Toast.new(text)
    toast.set_priority(Adw.ToastPriority(priority))
    return toast

def convert_to_local_time(timestamp, timezone_stamp):
    hour_offset_from_utc = (timezone_stamp)/3600
    return datetime.fromtimestamp(timestamp,tz=timezone.utc) + timedelta(hours=hour_offset_from_utc)

# converts wind degrees to direction 
def wind_dir(angle):
        directions = [
            _("N"), _("NNE"), _("NE"), _("ENE"), _("E"), _("ESE"), _("SE"), _("SSE"),
            _("S"), _("SSW"), _("SW"), _("WSW"), _("W"), _("WNW"), _("NW"), _("NNW"),
        ]
        index = round(angle / (360.0 / len(directions))) % len(directions)
        return directions[index]

