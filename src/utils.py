import requests
import socket
import datetime
import time
import gi
from .config import settings

gi.require_version("Adw", "1")
from gi.repository import Adw

local_time_data = dict()
TIMEOUT = 5
GEONAMES_USERNAME = "mousam"


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
        requests.get(url, timeout=TIMEOUT)
        print("Internet connection confirmed through: ", url)
        return True
    except (requests.ConnectionError, requests.Timeout):
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


def create_toast(text, priority=0):
    toast = Adw.Toast.new(text)
    toast.set_priority(Adw.ToastPriority(priority))
    return toast


def get_cords():
    selected_city_ = settings.selected_city
    return [float(x) for x in selected_city_.split(",")]



def get_time_difference(target_latitude, target_longitude, force=False):
    global local_time_data
    
    cord_str = f"{target_latitude}_{target_longitude}"
    if force is False and local_time_data.get(cord_str) is not None:
        return local_time_data[cord_str]
    
    # Get timezone information from GeoNames
    url = f"http://api.geonames.org/timezoneJSON?lat={target_latitude}&lng={target_longitude}&username={GEONAMES_USERNAME}"
    response = requests.get(url)
    timezone_data = response.json()
    
    # Parse the time string from GeoNames
    time_str = timezone_data["time"]
    target_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    
    # Calculate difference in seconds
    epoch_diff = time.time() - target_time.timestamp()
    data = {"epoch_diff": epoch_diff, "target_time": target_time.timestamp()}
    local_time_data[cord_str] = data
    return data
