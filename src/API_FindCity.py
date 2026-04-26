import requests
from typing import List
from requests.exceptions import RequestException
from .CORE_Cache import cached
from .configs import GEOCODING_BASE_URL, TIMEOUT
from .CORE_Logging import get_logger

# Configure logging at the module level
logger = get_logger("API_FindCity")

# GEO_BASE_URL moved to configs.py


@cached(5)
def find_city(city: str, count: int = 3) -> List[dict]:
    """
    Fetches city location data from the Open-Meteo Geocoding API.

    Args:
        city: The name of the city to search for.
        count: The maximum number of results to return.

    Returns:
        A list of Location model instances.
    """
    params = {"name": city, "language": "en", "format": "json", "count": count}

    try:
        # Use a timeout to prevent the thread from hanging indefinitely
        response = requests.get(GEOCODING_BASE_URL, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", [])

        # If no results are found, return early
        if not results:
            return []

        # List comprehension is more Pythonic and efficient for small datasets
        return [
            {
                "name": item.get("name"),
                "country": item.get("country"),
                "state": item.get("admin1"),
                "region": item.get("admin2"),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "timezone": item.get("timezone"),
            }
            for item in results
        ]

    except RequestException as e:
        # Log the error with context instead of printing
        logger.error(f"Failed to fetch city data for '{city}': {e}")
        return []
