import requests
import socket
import json
from datetime import datetime, timedelta, timezone
import time
from gi.repository import Adw, Gio

current_weather_data = None
air_pollution_data = None
forecast_weather_data = None
epoch_offset = None


TIMEOUT = 5
domains = {
    "google": "http://www.google.com",
    "wikipedia": "https://www.wikipedia.org/",
    "baidu": "https://www.baidu.com/",  # Specifically for china
}

# Check internet connection using socket connecton
def check_internet_socket():
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=TIMEOUT)  # 53 is the DNS port
        print("Internet connection confirmed through socket connection")
        return True
    except OSError:
        return False


# Check Internet connection using requests
def check_internet_domain(url):
    try:
        request = requests.get(url, timeout=TIMEOUT)
        print("Internet connection confirmed through: ",url)
        return True
    except (requests.ConnectionError, requests.Timeout) as exception:
        return False


def check_internet_connection():
    if (
        check_internet_socket()
        or check_internet_domain(domains["google"])
        or check_internet_domain(domains["wikipedia"])
        or check_internet_domain(domains["baidu"]) 
    ):
        return True
    
    print("No internet!")
    return False


def get_selected_city_coords():
    settings = Gio.Settings.new("io.github.amit9838.mousam")
    selected_city = int(str(settings.get_value("selected-city")))
    added_cities = list(settings.get_value("added-cities"))
    city_loc = added_cities[selected_city].split(",")
    return city_loc[-2], city_loc[-1]  # latitude,longitude


def create_toast(text, priority=0):
    toast = Adw.Toast.new(text)
    toast.set_priority(Adw.ToastPriority(priority))
    return toast


def convert_to_local_time(timestamp, timezone_stamp):
    hour_offset_from_utc = (timezone_stamp) / 3600
    return datetime.fromtimestamp(timestamp, tz=timezone.utc) + timedelta(
        hours=hour_offset_from_utc
    )


def get_cords():
    settings = Gio.Settings(schema_id="io.github.amit9838.mousam")
    selected_city_ = settings.get_string("selected-city")
    return [float(x) for x in selected_city_.split(",")]


def get_my_tz_offset_from_utc():
    try:
        offset = datetime.utcnow() - datetime.now()
        # Convert the offset to seconds
        offset_seconds = int(offset.total_seconds())

        return offset_seconds
    except Exception as e:
        return f"Error: {str(e)}"


def get_tz_offset_by_cord(lat, lon):
    global epoch_offset

    if epoch_offset is None:
        url = f"https://api.geotimezone.com/public/timezone?latitude={lat}&longitude={lon}"

        res = requests.get(url)
        if res.status_code != 200:
            return 0

        res = json.loads(res.text)
        if res.get("offset") is None:
            return 0

        offset_arr = res.get("offset")[3:].split(":")
        offset_arr = [int(x) for x in offset_arr]
        epoch_hr = abs(offset_arr[0]) * 3600
        epoch_s = 0

        if len(offset_arr) > 1:
            epoch_s = offset_arr[1] * 60

        epoch_offset = epoch_hr + epoch_s
        if offset_arr[0] < 0:
            epoch_offset *= -1

    return epoch_offset


def get_local_time():
    return time.time() + get_my_tz_offset_from_utc() + get_tz_offset_by_cord(*get_cords())
