"""Saved locations: how they are stored in the added-cities setting and how
their names and places are written.

Plain code with no GTK or settings: values from the settings are passed in.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class JsonProcessor:
    @staticmethod
    def str_list_to_json(data: List) -> List:
        return [json.loads(item) for item in data]

    @staticmethod
    def json_list_to_str(data: List) -> List:
        return [json.dumps(item) for item in data]


class LocationData:
    """Helper to handle serialization and formatting of city data."""

    @staticmethod
    def to_storage_string(city_dict: Dict) -> str:
        """Converts a city dictionary to a JSON string for settings."""
        return json.dumps(city_dict)

    @staticmethod
    def from_storage_string(json_str: str) -> Dict:
        """Converts a JSON string from settings back to a dictionary."""
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return {}

    @staticmethod
    def format_display_name(data: Dict) -> str:
        """Creates a clean 'City, State, Country' string."""
        parts = [data.get("name"), data.get("state"), data.get("country")]
        return ", ".join(filter(None, parts))

    @staticmethod
    def format_place(data: Dict, with_region: bool = False) -> str:
        """Creates the '[Region,] State, Country' line under a city's name."""
        name = data.get("name")
        # A state named like its city (Delhi, Delhi) adds nothing
        state = data.get("state") if data.get("state") != name else None
        region = data.get("region") if with_region else None
        if region in (name, state):
            region = None
        return ", ".join(filter(None, [region, state, data.get("country")]))

    @staticmethod
    def format_place_and_coords(data: Dict) -> str:
        """Creates the 'Region, State, Country · 9.93, 76.26' line of a search result."""
        place = LocationData.format_place(data, with_region=True)
        latitude, longitude = data.get("latitude"), data.get("longitude")
        coords = f"{latitude:.2f}, {longitude:.2f}" if None not in (latitude, longitude) else ""
        return " · ".join(filter(None, [place, coords]))

    @staticmethod
    def format_place_and_time(data: Dict, use_24h: bool) -> str:
        """Creates the 'State, Country · 9:14 PM' line of a saved city."""
        place = LocationData.format_place(data)
        return " · ".join(filter(None, [place, LocationData.format_local_time(data, use_24h)]))

    @staticmethod
    def format_local_time(data: Dict, use_24h: bool) -> str:
        """The city's current time, or an empty string if its timezone is unknown."""
        timezone = data.get("timezone")
        if not timezone:
            return ""
        try:
            now = datetime.now(ZoneInfo(timezone))
        except (ZoneInfoNotFoundError, ValueError, OSError):
            return ""
        return now.strftime("%H:%M" if use_24h else "%-I:%M %p")

    @staticmethod
    def get_coords_key(data: Dict) -> str:
        """Returns a unique coordinate string used for selection tracking."""
        return f"{data.get('latitude')},{data.get('longitude')}"

    @staticmethod
    def saved_coords(added_cities: List[str]) -> set:
        """The coordinate keys of every saved city, from the added-cities setting."""
        cities = [LocationData.from_storage_string(item) for item in added_cities if item]
        return {LocationData.get_coords_key(city) for city in cities if city}


def parse_coords_key(key: str) -> List[float]:
    """[latitude, longitude] from a "lat,lon" key (as get_coords_key writes it)."""
    return [float(x) for x in key.split(",")]


def find_selected_city(cities: List[Dict], selected_city: str) -> Optional[Dict]:
    """The city whose "lat,lon" key is `selected_city`, or None."""
    for city in cities:
        if LocationData.get_coords_key(city) == selected_city:
            return city
    return None
