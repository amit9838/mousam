"""Whether the internet can be reached: a socket to a public DNS server,
then a few well-known sites. The answer is cached for INTERNET_CACHE_TTL
seconds unless asked with force.
"""

import time
import socket
import requests
from .configs import TIMEOUT, INTERNET_CACHE_TTL, DOMAINS
from .CORE_Logging import get_logger

logger = get_logger("network")

_internet_cache = {"timestamp": 0.0, "status": False}

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
