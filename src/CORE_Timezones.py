"""Time-zone helpers for a city, by its time-zone name.

Plain functions with no GTK or settings: the zone name and the time are
passed in.
"""

import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def time_difference(timezone_str: str, now: float) -> dict:
    """The city's time at `now`, as get_time_difference reports it:
    {"epoch_diff", "target_time", "timezone"}, or {"error": ...} for an
    unknown zone."""
    try:
        target_tz = ZoneInfo(timezone_str)
    except (ZoneInfoNotFoundError, ValueError, TypeError) as e:
        return {"error": f"Invalid timezone: {str(e)}"}
    target_timestamp = datetime.datetime.fromtimestamp(now, target_tz).timestamp()
    return {
        "epoch_diff": now - target_timestamp,
        "target_time": target_timestamp,
        "timezone": timezone_str,
    }
