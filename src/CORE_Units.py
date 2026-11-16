"""Unit conversions the API doesn't do for us.

Plain functions with no GTK or settings: the measurement system ("metric" or
"imperial") is passed in.
"""

from gettext import gettext as _


def transform_visibility_data(unit, data, system: str) -> dict:
    """A visibility in metres as km ("metric") or miles ("imperial"):
    {"unit": ..., "data": ...}. A value in any other unit is kept as it is."""
    dist_unit, dist = _("km"), data / 1000
    if system == "imperial":
        dist_unit, dist = _("miles"), data / 1609.34
    if unit.lower() == "m":
        data, unit = dist, dist_unit
    return {"unit": unit, "data": data}
