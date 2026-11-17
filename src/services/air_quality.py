"""Open-Meteo air-quality API: https://open-meteo.com/en/docs/air-quality-api

A plain function with the coordinates as arguments; it returns the JSON, or
None when the request fails.
"""

from typing import Optional

import requests

from ..core.cache import cached
from ..core.log import get_logger
from ..config import AIR_QUALITY_BASE_URL, REQUEST_TIMEOUT

logger = get_logger("API_AirPollution")

HOURLY_FIELDS = [
    "european_aqi",
    "us_aqi",
    "pm10",
    "pm2_5",
    "carbon_monoxide",
    "carbon_dioxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
    "dust",
    "ammonia",
    "methane",
    "alder_pollen",
    "birch_pollen",
    "grass_pollen",
    "mugwort_pollen",
    "olive_pollen",
    "ragweed_pollen",
]


@cached()
def fetch_air_quality(latitude: float, longitude: float) -> Optional[dict]:
    """Hourly air quality of one place, from three days back to three ahead."""
    url = (
        AIR_QUALITY_BASE_URL
        + f"?latitude={latitude}&longitude={longitude}"
        + f"&hourly={','.join(HOURLY_FIELDS)}"
        + "&timeformat=unixtime&past_days=3&forecast_days=3&timezone=auto"
    )
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch air pollution data: {e}")
        return None


def clear_cache(latitude: Optional[float] = None, longitude: Optional[float] = None) -> None:
    """Forget cached responses, so the next fetch goes to the network: all
    of them, or with a latitude and longitude only that place's."""
    place = () if latitude is None else (latitude, longitude)
    fetch_air_quality.cache_clear(*place)
