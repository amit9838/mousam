import socket
import datetime
import time
import json
import gi
from .config import settings
import requests
from typing import List
from zoneinfo import ZoneInfo  # Python 3.9+ internal library


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


def get_timezone_from_selected_city():
    added_cities = JsonProcessor.str_list_to_json(settings.added_cities)
    for city in added_cities:
        if settings.selected_city == f"{city.get("latitude")},{city.get("longitude")}":
            return city.get("timezone","Asia/Kolkata")

def get_time_difference(timezone_str:str="", force=False):
    global local_time_data
    
    if not timezone_str:
        timezone_str = get_timezone_from_selected_city()

    # Use timezone name as the cache key
    if force is False and local_time_data.get(timezone_str) is not None:
        return local_time_data[timezone_str]
    
    try:
        # Get the current time in the target timezone using internal libraries
        target_tz = ZoneInfo(timezone_str)
        target_now = datetime.datetime.now(target_tz)
        
        # Calculate difference in seconds between local system clock and target timezone
        # we convert both to timestamps to get a clean epoch difference
        current_system_timestamp = time.time()
        target_timestamp = target_now.timestamp()
        
        epoch_diff = current_system_timestamp - target_timestamp
        
        data = {
            "epoch_diff": epoch_diff, 
            "target_time": target_timestamp,
            "timezone": timezone_str
        }
        
        local_time_data[timezone_str] = data
        return data

    except Exception as e:
        return {"error": f"Invalid timezone or library error: {str(e)}"}



class JsonProcessor():
    @staticmethod
    def str_list_to_json(data:List)->List:
        return [json.loads(item) for item in data]

    @staticmethod
    def json_list_to_str(data:List)->List:
        return [json.dumps(item) for item in data]