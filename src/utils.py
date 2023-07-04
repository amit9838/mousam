import requests
from gi.repository import Adw,Gio

current_weather_data = None
forecast_weather_data = None

def get_weather_data():
    return current_weather_data,forecast_weather_data

def set_weather_data(current,forecast):
    global current_weather_data, forecast_weather_data
    current_weather_data = current
    forecast_weather_data = forecast

def check_internet_connection():
    url = "http://www.google.com"
    timeout = 10  # Set the timeout value in seconds
    response_text = ""
    has_active_internet = False
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            has_active_internet = True
            return has_active_internet, response_text

    except requests.RequestException as e:
        print(str(e))
        response_text = _("No internet connection!")
        has_active_internet = False
        return has_active_internet, response_text
    except requests.Timeout:
        response_text = _("Request timeout!")
        return has_active_internet, response_text

def get_selected_city_cord():
    settings = Gio.Settings.new("io.github.amit9838.weather")
    selected_city = int(str(settings.get_value('selected-city')))
    added_cities = list(settings.get_value('added-cities'))
    city_loc = added_cities[selected_city]
    city_loc = city_loc.split(',')
    latitude = (city_loc[-2])
    longitude = (city_loc[-1])
    return latitude,longitude

def create_toast(text,priority=0):
        toast = Adw.Toast.new(text)
        toast.set_priority(Adw.ToastPriority(priority))
        return toast
