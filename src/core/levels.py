"""Levels for weather and air-quality values: the words and colour classes
the cards show ("Moderate", "warning").

Plain functions with no GTK or settings, so they can be tested on their own.
"""

from gettext import gettext as _, pgettext as C_

from ..config import (
    HPA_TO_INHG, PRESSURE_LOW, PRESSURE_HIGH, RAIN_INTENSITY_FROM_MM, SNOW_INTENSITY_FROM_CM, THRESHOLDS,
)


def classify_aqi(aqi_value):
    if aqi_value <= 50: return _("Good")
    if aqi_value <= 100: return _("Moderate")
    if aqi_value <= 150: return _("Poor")
    if aqi_value <= 200: return _("Unhealthy")
    if aqi_value <= 300: return _("Severe")
    return _("Hazardous")


def aqi_level_class(aqi_value) -> str:
    """The colour class for a US AQI: good, raised, or unhealthy and worse."""
    if aqi_value <= 50:
        return "success"
    if aqi_value <= 150:
        return "warning"
    return "error"


def aqi_advice(aqi_value) -> str:
    """What to do at this US AQI, after the US EPA's advice for each band."""
    if aqi_value <= 50:
        return _("Air quality is good. A fine time to be outside.")
    if aqi_value <= 100:
        return _("Unusually sensitive people should cut back on long or intense outdoor activity.")
    if aqi_value <= 150:
        return _("Sensitive groups should cut back on long or intense outdoor activity.")
    if aqi_value <= 200:
        return _("Everyone should cut back on long or intense outdoor activity; sensitive groups should avoid it.")
    if aqi_value <= 300:
        return _("Everyone should avoid long or intense outdoor activity; sensitive groups should stay indoors.")
    return _("Everyone should avoid all outdoor activity.")


def classify_eu_aqi(aqi_value) -> str:
    """The European AQI's own level names."""
    if aqi_value <= 20:
        return C_("european aqi", "Good")
    if aqi_value <= 40:
        return C_("european aqi", "Fair")
    if aqi_value <= 60:
        return C_("european aqi", "Moderate")
    if aqi_value <= 80:
        return C_("european aqi", "Poor")
    if aqi_value <= 100:
        return C_("european aqi", "Very Poor")
    return C_("european aqi", "Extremely Poor")


def classify_pollutant(key: str, value) -> tuple:
    """A pollutant's level against the WHO guidelines: (word, colour class)."""
    level = "error"
    for threshold, css_class in THRESHOLDS.get(key, ()):
        if value <= threshold:
            level = css_class
            break
    words = {
        "success": C_("pollutant level", "Good"),
        "warning": C_("pollutant level", "High"),
        "error": C_("pollutant level", "Very High"),
    }
    return words[level], level


def classify_rain_intensity(amount_mm: float) -> int:
    """How heavy an hour's rain is: 1 light, 2 moderate, 3 heavy, 4 violent."""
    return 1 + sum(amount_mm >= limit for limit in RAIN_INTENSITY_FROM_MM)


def classify_snow_intensity(amount_cm: float) -> int:
    """How heavy an hour's snow is: 1 light, 2 moderate, 3 heavy, 4 very heavy."""
    return 1 + sum(amount_cm >= limit for limit in SNOW_INTENSITY_FROM_CM)


def classify_pollen(value) -> tuple:
    """A pollen count's level (grains/m³): (word, colour class)."""
    if value <= 15:
        return C_("pollen level", "Low"), "success"
    if value <= 90:
        return C_("pollen level", "Moderate"), "warning"
    if value <= 500:
        return C_("pollen level", "High"), "error"
    return C_("pollen level", "Very High"), "error"


def main_pollutant(values: dict):
    """The pollutant furthest above (or nearest to) its WHO limit, from
    {key: value}; None when there is none to compare."""
    ratios = {
        key: value / THRESHOLDS[key][0][0]
        for key, value in values.items()
        if value is not None and key in THRESHOLDS
    }
    return max(ratios, key=ratios.get) if ratios else None


def classify_uv_index(uv):
    if uv <= 2: return C_("uvindex", "Low")
    if uv <= 5: return C_("uvindex", "Moderate")
    if uv <= 7: return C_("uvindex", "High")
    if uv <= 10: return C_("uvindex", "Very High")
    return C_("uvindex", "Extreme")


def classify_humidity_level(h):
    if h < 50: return C_("humidity", "Low")
    if h <= 80: return C_("humidity", "Moderate")
    return C_("humidity", "High")


def classify_pressure_level(p, unit: str):
    """Sea-level pressure against PRESSURE_LOW and PRESSURE_HIGH, in hPa for
    "metric" and inHg for "imperial"."""
    low, high = PRESSURE_LOW, PRESSURE_HIGH
    if unit == "imperial":
        low, high = low * HPA_TO_INHG, high * HPA_TO_INHG
    if p < low: return C_("pressure", "Low")
    if p <= high: return C_("pressure", "Normal")
    return C_("pressure", "High")


def classify_wind_speed_level(w):
    if w <= 1: return _("Calm")
    if w <= 25: return _("Light")
    if w <= 40: return C_("wind", "Moderate")
    if w <= 60: return _("Strong")
    return C_("wind", "Extreme")


def compass_direction(degrees: float) -> str:
    """The nearest of the eight compass points for an angle (where the wind
    comes from): "North", "Northeast", …"""
    directions = [
        _("North"),
        _("Northeast"),
        _("East"),
        _("Southeast"),
        _("South"),
        _("Southwest"),
        _("West"),
        _("Northwest"),
    ]
    return directions[round(degrees % 360 / 45) % 8]
