import socket
import datetime
import time
import json
import gi
from .config import settings
import requests
from typing import List, Optional
from zoneinfo import ZoneInfo  # Python 3.9+ internal library
import functools
from collections import OrderedDict
from threading import Lock
from typing import Callable, Optional, Any, Union

gi.require_version("Adw", "1")
from gi.repository import Adw

# ----------------------------------------------------------------------
# Cache for internet connection status
# ----------------------------------------------------------------------
INTERNET_CACHE_TTL = 120  # seconds
DATA_CACHE_TTL = 30
DATA_MAX_ENTRIES = 128
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
            return city.get("timezone", "Asia/Kolkata")


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
