import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from gettext import gettext as _

# --- Locations ---
DEFAULT_ICON_LOC = "@icon_location@/share/icons/hicolor/scalable/default_icons/"
MATERIAL_ICON_LOC = "@icon_location@/share/icons/hicolor/scalable/material_icons/"

# --- Default Icons (mousam_icons) ---
icons_default = {
    "0": DEFAULT_ICON_LOC + "clear-day.svg",
    "1": DEFAULT_ICON_LOC + "overcast-day.svg",
    "2": DEFAULT_ICON_LOC + "overcast-day.svg",
    "3": DEFAULT_ICON_LOC + "overcast.svg",
    "51": DEFAULT_ICON_LOC + "partly-cloudy-day-drizzle.svg",
    "53": DEFAULT_ICON_LOC + "drizzle.svg",
    "55": DEFAULT_ICON_LOC + "overcast-drizzle.svg",
    "56": DEFAULT_ICON_LOC + "partly-cloudy-day-snow.svg",
    "57": DEFAULT_ICON_LOC + "overcast-snow.svg",
    "61": DEFAULT_ICON_LOC + "partly-cloudy-day-rain.svg",
    "63": DEFAULT_ICON_LOC + "rain.svg",
    "65": DEFAULT_ICON_LOC + "thunderstorms-rain.svg",
    "66": DEFAULT_ICON_LOC + "overcast-snow.svg",
    "67": DEFAULT_ICON_LOC + "thunderstorms-rain.svg",
    "45": DEFAULT_ICON_LOC + "fog.svg",
    "48": DEFAULT_ICON_LOC + "fog.svg",
    "71": DEFAULT_ICON_LOC + "partly-cloudy-day-snow.svg",
    "73": DEFAULT_ICON_LOC + "snow.svg",
    "75": DEFAULT_ICON_LOC + "snowflake.svg",
    "77": DEFAULT_ICON_LOC + "snowflake.svg",
    "80": DEFAULT_ICON_LOC + "overcast-day-rain.svg",
    "81": DEFAULT_ICON_LOC + "rain.svg",
    "82": DEFAULT_ICON_LOC + "thunderstorms-rain.svg",
    "85": DEFAULT_ICON_LOC + "snow.svg",
    "86": DEFAULT_ICON_LOC + "snowflake.svg",
    "95": DEFAULT_ICON_LOC + "thunderstorms-rain.svg",
    "96": DEFAULT_ICON_LOC + "thunderstorms-day-overcast-snow.svg",
    "99": DEFAULT_ICON_LOC + "snowflake.svg",

    "0n": DEFAULT_ICON_LOC + "clear-night.svg",
    "1n": DEFAULT_ICON_LOC + "overcast-night.svg",
    "2n": DEFAULT_ICON_LOC + "overcast-night.svg",
    "3n": DEFAULT_ICON_LOC + "overcast.svg",
    "51n": DEFAULT_ICON_LOC + "partly-cloudy-night-drizzle.svg",
    "53n": DEFAULT_ICON_LOC + "drizzle.svg",
    "55n": DEFAULT_ICON_LOC + "overcast-drizzle.svg",
    "56n": DEFAULT_ICON_LOC + "partly-cloudy-night-snow.svg",
    "57n": DEFAULT_ICON_LOC + "overcast-snow.svg",
    "61n": DEFAULT_ICON_LOC + "partly-cloudy-night-rain.svg",
    "63n": DEFAULT_ICON_LOC + "rain.svg",
    "65n": DEFAULT_ICON_LOC + "thunderstorms-rain.svg",
    "66n": DEFAULT_ICON_LOC + "overcast-snow.svg",
    "67n": DEFAULT_ICON_LOC + "thunderstorms-rain.svg",
    "45n": DEFAULT_ICON_LOC + "fog.svg",
    "48n": DEFAULT_ICON_LOC + "fog.svg",
    "71n": DEFAULT_ICON_LOC + "partly-cloudy-night-snow.svg",
    "73n": DEFAULT_ICON_LOC + "snow.svg",
    "75n": DEFAULT_ICON_LOC + "snowflake.svg",
    "77n": DEFAULT_ICON_LOC + "snowflake.svg",
    "80n": DEFAULT_ICON_LOC + "overcast-night-rain.svg",
    "81n": DEFAULT_ICON_LOC + "rain.svg",
    "82n": DEFAULT_ICON_LOC + "thunderstorms-rain.svg",
    "85n": DEFAULT_ICON_LOC + "snow.svg",
    "86n": DEFAULT_ICON_LOC + "snowflake.svg",
    "95n": DEFAULT_ICON_LOC + "thunderstorms-rain.svg",
    "96n": DEFAULT_ICON_LOC + "thunderstorms-night-overcast-snow.svg",
    "99n": DEFAULT_ICON_LOC + "snowflake.svg",
    "arrow": DEFAULT_ICON_LOC + "arrow.svg",
    "raindrop": DEFAULT_ICON_LOC + "raindrop.svg",
    "raindrops": DEFAULT_ICON_LOC + "raindrops.svg",
    "wind": DEFAULT_ICON_LOC + "wind.svg",
}

# --- Material Icons (v3) ---
icons_material = {
    "0": MATERIAL_ICON_LOC + "clear_day.svg",
    "1": MATERIAL_ICON_LOC + "partly_cloudy_day.svg",
    "2": MATERIAL_ICON_LOC + "partly_cloudy_day.svg",
    "3": MATERIAL_ICON_LOC + "cloudy.svg",
    "51": MATERIAL_ICON_LOC + "drizzle.svg",
    "53": MATERIAL_ICON_LOC + "drizzle.svg",
    "55": MATERIAL_ICON_LOC + "drizzle.svg",
    "56": MATERIAL_ICON_LOC + "rain_with_snow.svg",
    "57": MATERIAL_ICON_LOC + "rain_with_snow.svg",
    "61": MATERIAL_ICON_LOC + "rain_with_cloudy.svg",
    "63": MATERIAL_ICON_LOC + "rain_showers.svg",
    "65": MATERIAL_ICON_LOC + "heavy_rain.svg",
    "66": MATERIAL_ICON_LOC + "rain_with_snow.svg",
    "67": MATERIAL_ICON_LOC + "rain_with_snow.svg",
    "45": MATERIAL_ICON_LOC + "haze_fog.svg",
    "48": MATERIAL_ICON_LOC + "haze_fog.svg",
    "71": MATERIAL_ICON_LOC + "snow_with_cloudy.svg",
    "73": MATERIAL_ICON_LOC + "flurries.svg",
    "75": MATERIAL_ICON_LOC + "heavy_snow.svg",
    "77": MATERIAL_ICON_LOC + "heavy_snow.svg",
    "80": MATERIAL_ICON_LOC + "rain_with_cloudy.svg",
    "81": MATERIAL_ICON_LOC + "rain_showers.svg",
    "82": MATERIAL_ICON_LOC + "heavy_rain.svg",
    "85": MATERIAL_ICON_LOC + "snow_with_cloudy.svg",
    "86": MATERIAL_ICON_LOC + "heavy_snow.svg",
    "95": MATERIAL_ICON_LOC + "thunderstorms_day.svg",
    "96": MATERIAL_ICON_LOC + "strong_thunderstorms.svg",
    "99": MATERIAL_ICON_LOC + "strong_thunderstorms.svg",

    "0n": MATERIAL_ICON_LOC + "clear_night.svg",
    "1n": MATERIAL_ICON_LOC + "partly_cloudy_night.svg",
    "2n": MATERIAL_ICON_LOC + "partly_cloudy_night.svg",
    "3n": MATERIAL_ICON_LOC + "cloudy.svg",
    "51n": MATERIAL_ICON_LOC + "drizzle.svg",
    "53n": MATERIAL_ICON_LOC + "drizzle.svg",
    "55n": MATERIAL_ICON_LOC + "drizzle.svg",
    "56n": MATERIAL_ICON_LOC + "rain_with_snow.svg",
    "57n": MATERIAL_ICON_LOC + "rain_with_snow.svg",
    "61n": MATERIAL_ICON_LOC + "rain_with_cloudy.svg",
    "63n": MATERIAL_ICON_LOC + "rain_showers.svg",
    "65n": MATERIAL_ICON_LOC + "heavy_rain.svg",
    "66n": MATERIAL_ICON_LOC + "rain_with_snow.svg",
    "67n": MATERIAL_ICON_LOC + "rain_with_snow.svg",
    "45n": MATERIAL_ICON_LOC + "haze_fog.svg",
    "48n": MATERIAL_ICON_LOC + "haze_fog.svg",
    "71n": MATERIAL_ICON_LOC + "snow_with_cloudy.svg",
    "73n": MATERIAL_ICON_LOC + "flurries.svg",
    "75n": MATERIAL_ICON_LOC + "heavy_snow.svg",
    "77n": MATERIAL_ICON_LOC + "heavy_snow.svg",
    "80n": MATERIAL_ICON_LOC + "rain_with_cloudy.svg",
    "81n": MATERIAL_ICON_LOC + "rain_showers.svg",
    "82n": MATERIAL_ICON_LOC + "heavy_rain.svg",
    "85n": MATERIAL_ICON_LOC + "snow_with_cloudy.svg",
    "86n": MATERIAL_ICON_LOC + "heavy_snow.svg",
    "95n": MATERIAL_ICON_LOC + "thunderstorms_night.svg",
    "96n": MATERIAL_ICON_LOC + "strong_thunderstorms.svg",
    "99n": MATERIAL_ICON_LOC + "strong_thunderstorms.svg",
    "arrow": MATERIAL_ICON_LOC + "arrow.svg",
    "raindrop": MATERIAL_ICON_LOC + "drizzle.svg",
    "raindrops": MATERIAL_ICON_LOC + "heavy_rain.svg",
    "wind": MATERIAL_ICON_LOC + "windy.svg",
}

# --- Backward-compatible alias (defaults to default icons) ---
icons = icons_default


def get_icon_path(code: str, theme: str = "default") -> str:
    """Return the icon file path for a given WMO weather code and icon theme."""
    if theme == "material":
        icon_dict = icons_material
    else:
        icon_dict = icons_default

    return icon_dict.get(code, icon_dict.get("3", ""))


def get_icon_pixel_size(theme: str, base_size: int) -> int:
    """Return adjusted pixel size for the given icon theme.

    Material icons use a tighter 48×48 viewBox and have less internal whitespace,
    so they need to be rendered slightly smaller to visually match default icons.
    """
    if theme == "material":
        return int(base_size * 0.76)
    return base_size

def get_icon_margin(theme: str) -> int:
    """Return adjusted margin for the given icon theme.

    """
    if theme == "material":
        return 10
    return 0




def create_weather_icon(code: str, theme: str, pixel_size: int) -> Gtk.Image:
    """Create a Gtk.Image for a weather code, sized appropriately for the icon theme.

    Args:
        code: WMO weather code (e.g. "0", "61", "95n")
        theme: Icon theme name - "default" or "material"
        pixel_size: Base pixel size for the icon

    Returns:
        Gtk.Image widget with the correct icon and adjusted size
    """
    path = get_icon_path(code, theme)
    img = Gtk.Image.new_from_file(path)
    img.set_pixel_size(get_icon_pixel_size(theme, pixel_size))
    img.set_margin_top(get_icon_margin(theme))
    img.set_margin_bottom(get_icon_margin(theme))
    img.set_margin_start(get_icon_margin(theme))
    img.set_margin_end(get_icon_margin(theme))
    return img


# --- Background CSS ---
bg_css = {
    "0": "bg-weather-clear-sky",
    "1": "bg-weather-few-clouds",
    "2": "bg-weather-few-clouds",
    "3": "bg-weather-overcast",
    "51": "bg-weather-showers-scattered",
    "53": "bg-weather-showers-scattered",
    "55": "bg-weather-showers-scattered",
    "56": "bg-weather-snow",
    "57": "bg-weather-snow",
    "61": "bg-weather-showers-scattered",
    "63": "bg-weather-showers-large",
    "65": "bg-weather-showers-large",
    "66": "bg-weather-snow",
    "67": "bg-weather-showers-large",
    "45": "bg-weather-fog",
    "48": "bg-weather-fog",
    "71": "bg-weather-snow",
    "73": "bg-weather-snow",
    "75": "bg-weather-snow",
    "77": "bg-weather-snow",
    "80": "bg-weather-showers-large",
    "81": "bg-weather-showers-large",
    "82": "bg-weather-showers-large",
    "85": "bg-weather-snow",
    "86": "bg-weather-snow",
    "95": "bg-weather-storm",
    "96": "bg-weather-storm",
    "99": "bg-weather-snow",

    "0n": "bg-weather-clear-sky-night",
    "1n": "bg-weather-few-clouds-night",
    "2n": "bg-weather-few-clouds-night",
    "3n": "bg-weather-overcast-night",
    "51n": "bg-weather-showers-scattered-night",
    "53n": "bg-weather-showers-scattered-night",
    "55n": "bg-weather-showers-scattered-night",
    "56n": "bg-weather-snow-night",
    "57n": "bg-weather-snow-night",
    "61n": "bg-weather-showers-scattered-night",
    "63n": "bg-weather-showers-large-night",
    "65n": "bg-weather-showers-large-night",
    "66n": "bg-weather-snow-night",
    "67n": "bg-weather-showers-large-night",
    "45n": "bg-weather-fog-night",
    "48n": "bg-weather-fog-night",
    "71n": "bg-weather-snow-night",
    "73n": "bg-weather-snow-night",
    "75n": "bg-weather-snow-night",
    "77n": "bg-weather-snow-night",
    "80n": "bg-weather-showers-large-night",
    "81n": "bg-weather-showers-large-night",
    "82n": "bg-weather-showers-large-night",
    "85n": "bg-weather-snow-night",
    "86n": "bg-weather-snow-night",
    "95n": "bg-weather-storm-night",
    "96n": "bg-weather-storm-night",
    "99n": "bg-weather-snow-night",
}

# --- Weather Conditions ---
condition = {
    "0": _("Clear sky"),
    "1": _("Few Clouds"),
    "2": _("Partly Cloudy"),
    "3": _("Overcast"),
    "45": _("Fog"),
    "48": _("Mist"),
    "51": _("Light Drizzle"),
    "53": _("Moderate Drizzle"),
    "55": _("Heavy Intensity Drizzle"),
    "56": _("Light Freezing Drizzle"),
    "57": _("Heavy Freezing Drizzle"),
    "61": _("Light Rain"),
    "63": _("Moderate Rain"),
    "65": _("Heavy Rain"),
    "66": _("Light Freezing Rain"),
    "67": _("Heavy Freezing Rain"),
    "71": _("Light Snow Fall"),
    "73": _("Moderate Snow Fall"),
    "75": _("Heavy Snow Fall"),
    "77": _("Snow grains"),
    "80": _("Light Rain Showers"),
    "81": _("Moderate Rain Showers"),
    "82": _("Heavy Rain Showers"),
    "85": _("Light Snow Showers"),
    "86": _("Heavy Snow Showers "),
    "95": _("Thunderstorm"),
    "96": _("Thunderstorm with Hail"),
}