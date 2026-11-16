"""Decisions about forecast data: which hour is now, how many rain drops a
chance gets, whether a code is snow, today's high and low.

Plain functions with no GTK or settings, so they can be tested on their own.
"""

from datetime import date, datetime, timezone, tzinfo
from typing import Optional

from ..config import (
    RAIN_MIN_AMOUNT_MM, RAIN_MORE_DROPS_FROM, SNOW_MIN_AMOUNT_CM, SNOW_WATER_MM_PER_CM,
    SNOW_WEATHER_CODES,
)


def nearest_hour_index(times: list, now: float) -> int:
    """The index of the hour that is now: the first timestamp within half an
    hour of `now`, or 0 when there is none."""
    for i, ts in enumerate(times):
        if abs(now - ts) < 1800:
            return i
    return 0


def rain_drop_count(rain_chance: float) -> int:
    """How many drops to show: one, then one more from each RAIN_MORE_DROPS_FROM."""
    return 1 + sum(rain_chance >= chance for chance in RAIN_MORE_DROPS_FROM)


def is_snow_code(weather_code) -> bool:
    """Whether a WMO weather code is snow."""
    try:
        return int(weather_code) in SNOW_WEATHER_CODES
    except (TypeError, ValueError):
        return False


def hourly_precipitation(snow_cm: float, rain_mm: float) -> Optional[tuple]:
    """What an hour shows: ("snow", cm) or ("rain", mm), whichever there is
    more of (comparing the snow's water), or None for a dry hour."""
    if snow_cm >= SNOW_MIN_AMOUNT_CM and snow_cm * SNOW_WATER_MM_PER_CM >= rain_mm:
        return "snow", snow_cm
    if rain_mm >= RAIN_MIN_AMOUNT_MM:
        return "rain", rain_mm
    return None


def today_high_low(times: list, highs: list, lows: list, today: date) -> Optional[tuple]:
    """Today's (max, min) from daily data, or None.

    Daily data is requested in GMT, so each day's timestamp is its midnight
    in UTC: compare its UTC date with the city's `today`.
    """
    for i, ts in enumerate(times):
        if datetime.fromtimestamp(ts, tz=timezone.utc).date() == today:
            high, low = highs[i], lows[i]
            if high is None or low is None:
                return None
            return high, low
    return None


def today_sun_times(times: list, sunrises: list, sunsets: list, tz: tzinfo, now: float) -> tuple:
    """Today's (sunrise, sunset) timestamps from daily data, or (0, 0).

    Today is the day it is at `now` in `tz`, the city's time zone. Daily
    data is requested in GMT, so each day's timestamp is its midnight in
    UTC: compare its UTC date, as today_high_low does.
    """
    today = datetime.fromtimestamp(now, tz).date()
    for i, ts in enumerate(times):
        if datetime.fromtimestamp(ts, tz=timezone.utc).date() == today:
            return sunrises[i], sunsets[i]
    return 0, 0
