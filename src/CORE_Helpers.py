import json
import time
import socket
import requests
import datetime
from typing import List
from zoneinfo import ZoneInfo
from gi.repository import Adw
from .settings import settings
from gettext import gettext as _
from .configs import TIMEOUT, INTERNET_CACHE_TTL, DEFAULT_TIMEZONE, DOMAINS
from .CORE_Logging import get_logger

logger = get_logger("helpers")

_internet_cache = {"timestamp": 0.0, "status": False}
local_time_data = dict()

def check_internet_connection(force: bool = False) -> bool:
    global _internet_cache
    now = time.time()
    if not force and (now - _internet_cache["timestamp"] < INTERNET_CACHE_TTL):
        return _internet_cache["status"]
    status = (
        check_internet_socket()
        or check_internet_domain(DOMAINS["google"])
        or check_internet_domain(DOMAINS["wikipedia"])
        or check_internet_domain(DOMAINS["baidu"])
    )
    if not status:
        logger.error("Internet connection check failed - all domains/sockets unreachable")
    
    _internet_cache = {"timestamp": now, "status": status}
    return status

def check_internet_socket():
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=TIMEOUT)
        return True
    except OSError:
        return False

def check_internet_domain(url):
    try:
        requests.get(url, timeout=TIMEOUT)
        return True
    except (requests.ConnectionError, requests.Timeout):
        return False

def create_toast(text, priority=0):
    toast = Adw.Toast.new(text)
    toast.set_priority(Adw.ToastPriority(priority))
    return toast

def get_cords():
    selected_city_ = settings.selected_city
    return [float(x) for x in selected_city_.split(",")]

class JsonProcessor:
    @staticmethod
    def str_list_to_json(data: List) -> List:
        return [json.loads(item) for item in data]

    @staticmethod
    def json_list_to_str(data: List) -> List:
        return [json.dumps(item) for item in data]

def get_timezone_from_selected_city():
    added_cities = JsonProcessor.str_list_to_json(settings.added_cities)
    for city in added_cities:
        if settings.selected_city == f"{city.get('latitude')},{city.get('longitude')}":
            tz = city.get("timezone", DEFAULT_TIMEZONE)
            return tz if tz else DEFAULT_TIMEZONE
    return DEFAULT_TIMEZONE

def get_time_difference(timezone_str: str = "", force=False):
    global local_time_data
    if not timezone_str:
        timezone_str = get_timezone_from_selected_city()
    if force is False and local_time_data.get(timezone_str) is not None:
        return local_time_data[timezone_str]
    try:
        target_tz = ZoneInfo(timezone_str)
        target_now = datetime.datetime.now(target_tz)
        current_system_timestamp = time.time()
        target_timestamp = target_now.timestamp()
        epoch_diff = current_system_timestamp - target_timestamp
        data = {
            "epoch_diff": epoch_diff,
            "target_time": target_timestamp,
            "timezone": timezone_str,
        }
        local_time_data[timezone_str] = data
        return data
    except Exception as e:
        return {"error": f"Invalid timezone: {str(e)}"}

def get_selected_city_name():
    try:
        lat, lon = get_cords()
        added_cities = JsonProcessor.str_list_to_json(settings.added_cities)
        for city in added_cities:
            c_lat = float(city.get('latitude', 0))
            c_lon = float(city.get('longitude', 0))
            if abs(lat - c_lat) < 0.001 and abs(lon - c_lon) < 0.001:
                return city.get("name", _("Unknown City"))
    except:
        pass
    return _("Unknown City")
