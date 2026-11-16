"""What the weather data needs from the forecast API.

The API_Weather module is the real one; tests pass a fake with the same
functions (tests/fakes.py), so fetching can be tested without the network.
"""

from typing import List, Optional, Protocol, runtime_checkable


@runtime_checkable
class ForecastClient(Protocol):
    """The forecast API's fetch functions. Each returns the JSON, or None
    when the request fails."""

    def fetch_current(self, latitude: float, longitude: float, unit: str) -> Optional[dict]: ...

    def fetch_hourly(self, latitude: float, longitude: float, unit: str) -> Optional[dict]: ...

    def fetch_daily(self, latitude: float, longitude: float, unit: str) -> Optional[dict]: ...

    def fetch_many(self, coords: List[str], unit: str) -> Optional[list]: ...
