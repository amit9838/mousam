import requests
import socket
from datetime import datetime
import time
from gi.repository import Adw
from .config import settings

local_time_data = dict()
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
        print("Internet connection confirmed through: ", url)
        return True
    except (requests.ConnectionError, requests.Timeout) as exception:
        return False

# Check Internet connection using requests
def check_domoticz_url(url):
    try:
        request = requests.get(url, timeout=TIMEOUT)
        print("Domoticz connection confirmed through: ", url)
        return True
    except (requests.ConnectionError, requests.Timeout) as exception:
        return False


def check_internet_connection():
    result = False
    if (
        check_internet_socket()
        or check_internet_domain(domains["google"])
        or check_internet_domain(domains["wikipedia"])
        or check_internet_domain(domains["baidu"])
    ):
        if settings.is_using_domoticz_for_current_weather and check_domoticz_url("http://" + settings.domoticz_host + "/"):
            result = True
        else:
            result = True
    if not result:
        print("No internet!")
    return result


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

    # Get current time in the target location using timeapi.io
    url = f"https://timeapi.io/api/Time/current/coordinate?latitude={target_latitude}&longitude={target_longitude}"
    target_time_response = requests.get(url)
    target_time_data = target_time_response.json()
    target_current_time = target_time_data["dateTime"]
    target_time = datetime.strptime(target_current_time[:26], "%Y-%m-%dT%H:%M:%S.%f")

    epoch_diff = time.time() - target_time.timestamp()
    data = {"epoch_diff": epoch_diff, "target_time": target_time.timestamp()}
    local_time_data[cord_str] = data
    return data
