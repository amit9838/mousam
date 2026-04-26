import json
import functools
import time
from threading import Lock
from collections import OrderedDict
from typing import Callable, Optional, Any
from .configs import DATA_CACHE_TTL, DATA_MAX_ENTRIES

# Constants moved to configs.py

class cached:
    """
    Decorator that caches a function's return value based on its arguments.
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
        data = {"args": list(args), "kwargs": kwargs}
        return json.dumps(data, sort_keys=True, default=str)

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = self.key_func(args, kwargs)
            with self.lock:
                if key in self.cache:
                    result, timestamp = self.cache[key]
                    if self.ttl is None or (time.time() - timestamp) < self.ttl:
                        self.cache.move_to_end(key)
                        self.hits += 1
                        return result
                    else:
                        del self.cache[key]
                        self.currsize -= 1

                result = func(*args, **kwargs)
                self.misses += 1
                
                # Only cache valid data (non-None results)
                if result is not None:
                    self.cache[key] = (result, time.time())
                    self.currsize += 1
                    if self.maxsize is not None and self.currsize > self.maxsize:
                        self.cache.popitem(last=False)
                        self.currsize -= 1
                return result

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
