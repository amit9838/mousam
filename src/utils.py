import gi
import datetime
import time
import json
import requests
import socket
import weakref
import functools
from threading import Lock
from collections import OrderedDict
from typing import Callable, Optional, Any


from typing import List, Optional
from zoneinfo import ZoneInfo  # Python 3.9+ internal library
from .config import settings

gi.require_version("Adw", "1")
from gi.repository import  Adw, GLib, Gio
from gettext import gettext as _

# ----------------------------------------------------------------------
# Cache for internet connection status
# ----------------------------------------------------------------------
INTERNET_CACHE_TTL = 120  # seconds
DATA_CACHE_TTL = 60
DATA_MAX_ENTRIES = 128
DEFAULT_TIMEZONE = "UTC"
_internet_cache = {"timestamp": 0.0, "status": False}

local_time_data = dict()
TIMEOUT = 5
GEONAMES_USERNAME = "mousam"

domains = {
    "google": "http://www.google.com",
    "wikipedia": "https://www.wikipedia.org/",
    "baidu": "https://www.baidu.com/",  # Specifically for china
}


def check_internet_connection(force: bool = False) -> bool:
    """
    Returns True if internet is reachable, otherwise False.
    Results are cached for INTERNET_CACHE_TTL seconds to avoid frequent checks.
    Use force=True to bypass cache and force a fresh check.
    """
    global _internet_cache
    now = time.time()

    if not force and (now - _internet_cache["timestamp"] < INTERNET_CACHE_TTL):
        return _internet_cache["status"]

    # Perform actual checks
    status = (
        check_internet_socket()
        or check_internet_domain(domains["google"])
        or check_internet_domain(domains["wikipedia"])
        or check_internet_domain(domains["baidu"])
    )

    _internet_cache = {"timestamp": now, "status": status}
    return status


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
            tz = city.get("timezone", DEFAULT_TIMEZONE)
            return tz if tz else DEFAULT_TIMEZONE

    return DEFAULT_TIMEZONE


def get_time_difference(timezone_str: str = "", force=False):
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
            "timezone": timezone_str,
        }

        local_time_data[timezone_str] = data
        return data

    except Exception as e:
        return {"error": f"Invalid timezone or library error: {str(e)}"}


class JsonProcessor:
    @staticmethod
    def str_list_to_json(data: List) -> List:
        return [json.loads(item) for item in data]

    @staticmethod
    def json_list_to_str(data: List) -> List:
        return [json.dumps(item) for item in data]


class cached:
    """
    Decorator that caches a function's return value based on its arguments.

    Features:
    - Time‑to‑live (ttl) – entries older than ttl seconds are considered stale.
    - LRU eviction when maxsize is exceeded.
    - Thread‑safe using a lock.
    - Customisable key function (default uses JSON with str fallback).
    - Cache introspection via wrapper.cache_info() and wrapper.cache_clear().

    Args:
        maxsize: Maximum number of entries to keep (None = unlimited).
        ttl: Time‑to‑live in seconds (None = never expire).
        key_func: Optional callable that takes (args, kwargs) and returns a hashable cache key.
                  If not provided, a default JSON‑based key is used.
    """

    def __init__(
        self,
        maxsize: Optional[int] = DATA_MAX_ENTRIES,
        ttl: Optional[float] = DATA_CACHE_TTL,
        key_func: Optional[Callable[[tuple, dict], Any]] = None,
    ):
        self.maxsize = maxsize
        self.ttl = ttl
        self.key_func = key_func or self._default_key
        self.cache = OrderedDict()  # key -> (result, timestamp)
        self.lock = Lock()
        self.hits = 0
        self.misses = 0
        self.currsize = 0

    @staticmethod
    def _default_key(args: tuple, kwargs: dict) -> str:
        """
        Default key generation: JSON dump of args and kwargs.
        - Sorts dictionary keys for consistency.
        - Uses `default=str` to convert non‑serialisable objects to strings
          (may cause collisions if two distinct objects stringify identically).
        """
        # Create a structure that contains both positional and keyword arguments
        data = {"args": list(args), "kwargs": kwargs}
        # Compact JSON with sorted keys for reproducibility
        return json.dumps(data, sort_keys=True, default=str)

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = self.key_func(args, kwargs)

            with self.lock:
                # Hit?
                if key in self.cache:
                    result, timestamp = self.cache[key]
                    # Check expiration
                    if self.ttl is None or (time.time() - timestamp) < self.ttl:
                        # Move to end to mark as most recently used (LRU)
                        self.cache.move_to_end(key)
                        self.hits += 1
                        return result
                    else:
                        # Stale entry – remove it
                        del self.cache[key]
                        self.currsize -= 1

                # Miss – compute result
                result = func(*args, **kwargs)
                self.misses += 1

                # Store in cache
                self.cache[key] = (result, time.time())
                self.currsize += 1

                # Enforce maxsize (LRU eviction)
                if self.maxsize is not None and self.currsize > self.maxsize:
                    # popitem(last=False) removes the first (oldest) item
                    self.cache.popitem(last=False)
                    self.currsize -= 1

                return result

        # Expose cache statistics and control methods
        def cache_info():
            with self.lock:
                return {
                    "hits": self.hits,
                    "misses": self.misses,
                    "currsize": self.currsize,
                    "maxsize": self.maxsize,
                    "ttl": self.ttl,
                }

        def cache_clear():
            with self.lock:
                self.cache.clear()
                self.hits = 0
                self.misses = 0
                self.currsize = 0

        wrapper.cache_info = cache_info
        wrapper.cache_clear = cache_clear
        return wrapper

class AutoRefreshTimer:
    """
    Manages auto-refresh intervals using GLib timeouts.
    """
    def __init__(self, callback: Callable):
        self._timer_id = None
        self._callback = callback

    def setup(self):
        self.stop()
        interval = settings.auto_refresh_interval
        if interval > 0:
            self._timer_id = GLib.timeout_add_seconds(
                interval * 60, self._on_tick
            )

    def stop(self):
        if self._timer_id is not None:
            GLib.source_remove(self._timer_id)
            self._timer_id = None

    def _on_tick(self):
        self._callback()
        return GLib.SOURCE_CONTINUE



def safe_set_draw_func(drawing_area, obj, draw_method_name):
    """
    Sets a draw function on a Gtk.DrawingArea without creating a strong reference cycle.
    """
    # Keep obj alive in Python-space exactly as long as the drawing_area wrapper exists.
    # Python's cyclic GC will handle this perfectly once the drawing_area is removed from the UI.
    drawing_area._keep_alive_obj = obj
    
    weak_obj = weakref.ref(obj)
    def wrapper(area, cr, width, height, _user_data):
        target = weak_obj()
        if target:
            method = getattr(target, draw_method_name, None)
            if method:
                method(area, cr, width, height, _user_data)
    drawing_area.set_draw_func(wrapper, None)

def weak_connect(widget, signal_name, bound_method):
    """
    Connects a signal without creating a strong reference cycle.
    """
    weak_self = weakref.ref(bound_method.__self__)
    func_name = bound_method.__name__
    
    def wrapper(*args, **kwargs):
        target = weak_self()
        if target:
            method = getattr(target, func_name, None)
            if method:
                return method(*args, **kwargs)
                
    return widget.connect(signal_name, wrapper)


def get_selected_city_name():
    added_cities = JsonProcessor.str_list_to_json(settings.added_cities)
    for city in added_cities:
        if settings.selected_city == f"{city.get('latitude')},{city.get('longitude')}":
            return city.get("name", _("Unknown City"))
    return _("Unknown City")


def show_notification(app):
    if not app or not settings.show_notifications:
        return

    from .CORE_weatherData import current_weather_data as cw_data
    from .constants import condition as cond_map

    if not cw_data:
        return

    city_name = get_selected_city_name()
    
    # Get weather info
    temp = cw_data.temperature_2m.get("data")
    unit = cw_data.temperature_2m.get("unit")
    w_code = str(cw_data.weathercode.get("data"))
    
    cond_str = cond_map.get(w_code, _("Unknown"))
    
    notification = Gio.Notification.new(f"{city_name} • {temp}{unit}")
    notification.set_body(f"{cond_str}")
    
    app.send_notification("weather-update", notification)


def fetch_all_weather_data_async(on_success=None, on_error=None):
    """
    Fetches all weather data in a thread-safe manner, avoiding race conditions.
    Runs current_weather fetch sequentially before hourly/daily/pollution fetches.
    """
    import threading
    from .CORE_weatherData import (
        fetch_current_weather,
        fetch_hourly_forecast,
        fetch_daily_forecast,
        fetch_current_air_pollution
    )

    def _worker():
        try:
            # cwd : current_weather_data
            # cwt : current_weather_thread
            cwd = threading.Thread(target=fetch_current_weather, name="cwt")
            cwd.start()
            cwd.join()

            hfd = threading.Thread(target=fetch_hourly_forecast, name="hft")
            hfd.start()

            dfd = threading.Thread(target=fetch_daily_forecast, name="dft")
            dfd.start()

            apd = threading.Thread(target=fetch_current_air_pollution, name="apt")
            apd.start()

            local_time = threading.Thread(
                target=get_time_difference, args=("", True), name="local_time"
            )
            local_time.start()

            hfd.join()
            dfd.join()
            apd.join()
            local_time.join()
            
            if on_success:
                GLib.idle_add(on_success)
        except Exception as e:
            print(f"Error fetching data: {e}")
            if on_error:
                GLib.idle_add(on_error, str(e))

    if not any(t.name == "fetch_all_worker" for t in threading.enumerate()):
        threading.Thread(target=_worker, name="fetch_all_worker", daemon=True).start()


