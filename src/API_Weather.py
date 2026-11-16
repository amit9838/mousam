"""Open-Meteo forecast API: https://open-meteo.com/en/docs

Plain functions: every input is an argument (coordinates, the measurement
system as ``unit``), and each returns the JSON, or None when the request
fails. ``unit`` is part of the cache key, so switching units never returns
data cached in the old ones.
"""

from typing import List, Optional

import requests

from .core.cache import cached
from .core.log import get_logger
from .config import HPA_TO_INHG, OPEN_METEO_BASE_URL, TIMEOUT

logger = get_logger("API_Weather")

CURRENT_FIELDS = [
    "temperature_2m",
    "relativehumidity_2m",
    "apparent_temperature",
    "is_day",
    "uv_index",
    "precipitation",
    "weathercode",
    "pressure_msl",
    "windspeed_10m",
    "winddirection_10m",
]

HOURLY_FIELDS = [
    "temperature_2m",
    "relativehumidity_2m",
    "dewpoint_2m",
    "apparent_temperature",
    "weathercode",
    "precipitation",
    "precipitation_probability",
    "rain",
    "showers",
    "snowfall",
    "pressure_msl",
    "visibility",
    "windspeed_10m",
    "wind_direction_10m",
    "uv_index",
    "is_day",
]

DAILY_FIELDS = [
    "weathercode",
    "temperature_2m_max",
    "temperature_2m_min",
    "sunrise",
    "sunset",
    "uv_index_max",
    "precipitation_sum",
    "windspeed_10m_max",
    "precipitation_probability_max",
]


def unit_params(unit: str) -> str:
    """URL parameters that ask Open-Meteo for the given measurement system."""
    if unit == "imperial":
        return "&temperature_unit=fahrenheit&wind_speed_unit=mph"
    return ""


def _get_json(url: str, what: str):
    """The JSON at url, or None (logged) when the request fails."""
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {what}: {e}")
        return None


@cached()
def fetch_current(latitude: float, longitude: float, unit: str) -> Optional[dict]:
    """Current conditions of one place."""
    url = (
        OPEN_METEO_BASE_URL
        + f"?latitude={latitude}&longitude={longitude}"
        + f"&current={','.join(CURRENT_FIELDS)}"
        + unit_params(unit)
        + "&timeformat=unixtime"
    )
    data = _get_json(url, "current weather data")
    if data is not None and unit == "imperial":
        # Open-Meteo has no pressure unit parameter
        data["current"]["pressure_msl"] = data["current"]["pressure_msl"] * HPA_TO_INHG
        data["current_units"]["pressure_msl"] = "inHg"
    return data


@cached()
def fetch_many(coords: List[str], unit: str) -> Optional[list]:
    """Current conditions of several "lat,lon" places in one request, in the
    order given."""
    latitudes, longitudes = zip(*(item.split(",") for item in coords))
    url = (
        OPEN_METEO_BASE_URL
        + f"?latitude={','.join(latitudes)}&longitude={','.join(longitudes)}"
        + "&current=temperature_2m,weathercode,is_day"
        + "&timeformat=unixtime"
        + unit_params(unit)
    )
    data = _get_json(url, "weather of saved locations")
    if data is None:
        return None
    # A single place comes back as one object instead of a list
    return data if isinstance(data, list) else [data]


@cached()
def fetch_hourly(latitude: float, longitude: float, unit: str) -> Optional[dict]:
    """The hourly forecast of one place, in its own time zone."""
    url = (
        OPEN_METEO_BASE_URL
        + f"?latitude={latitude}&longitude={longitude}&timezone=auto"
        + f"&hourly={','.join(HOURLY_FIELDS)}"
        + unit_params(unit)
        + "&timeformat=unixtime"
    )
    data = _get_json(url, "hourly forecast")
    if data is not None and unit == "imperial":
        data["hourly"]["pressure_msl"] = [
            value * HPA_TO_INHG for value in data["hourly"]["pressure_msl"]
        ]
        data["hourly_units"]["pressure_msl"] = "inHg"
    return data


@cached()
def fetch_daily(latitude: float, longitude: float, unit: str) -> Optional[dict]:
    """The daily forecast of one place, with days in GMT."""
    url = (
        OPEN_METEO_BASE_URL
        + f"?latitude={latitude}&longitude={longitude}"
        + f"&daily={','.join(DAILY_FIELDS)}"
        + "&timezone=GMT"
        + "&timeformat=unixtime"
        + unit_params(unit)
    )
    return _get_json(url, "daily forecast")


def clear_cache() -> None:
    """Forget the selected city's cached responses, so the next fetch goes
    to the network. fetch_many (the Locations list) keeps its cache."""
    fetch_current.cache_clear()
    fetch_hourly.cache_clear()
    fetch_daily.cache_clear()
