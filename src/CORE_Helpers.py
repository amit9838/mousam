import time
from .settings import settings
from gettext import gettext as _
from .configs import DEFAULT_TIMEZONE
from .CORE_Locations import JsonProcessor, find_selected_city, parse_coords_key
from .CORE_Logging import get_logger
from .CORE_Timezones import time_difference

logger = get_logger("helpers")

local_time_data = dict()

def get_cords():
    return parse_coords_key(settings.selected_city)

def get_timezone_from_selected_city():
    added_cities = JsonProcessor.str_list_to_json(settings.added_cities)
    city = find_selected_city(added_cities, settings.selected_city)
    return (city or {}).get("timezone") or DEFAULT_TIMEZONE

def get_time_difference(timezone_str: str = "", force=False):
    global local_time_data
    if not timezone_str:
        timezone_str = get_timezone_from_selected_city()
    if force is False and local_time_data.get(timezone_str) is not None:
        return local_time_data[timezone_str]
    data = time_difference(timezone_str, time.time())
    if "error" not in data:
        local_time_data[timezone_str] = data
    return data

def get_selected_city_name():
    try:
        lat, lon = get_cords()
        added_cities = JsonProcessor.str_list_to_json(settings.added_cities)
        for city in added_cities:
            c_lat = float(city.get('latitude', 0))
            c_lon = float(city.get('longitude', 0))
            if abs(lat - c_lat) < 0.001 and abs(lon - c_lon) < 0.001:
                return city.get("name", _("Unknown City"))
    except (ValueError, TypeError, AttributeError) as e:
        # Malformed selected-city or added-cities value in GSettings
        logger.warning(f"Could not find the selected city's name: {e}")
    return _("Unknown City")
