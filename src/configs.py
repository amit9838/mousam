from gettext import gettext as _
from enum import IntEnum

# --- Application Info ---
APP_ID = "io.github.amit9838.mousam"

# --- Networking & Timeout ---
TIMEOUT = 15
INTERNET_CACHE_TTL = 120
DEFAULT_TIMEZONE = "UTC"

# Domain to check internet connectivity as fallback
DOMAINS = {
    "google": "http://www.google.com",
    "wikipedia": "https://www.wikipedia.org/",
    "baidu": "https://www.baidu.com/",
}

# --- API URLs ---
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_BASE_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
GEOCODING_BASE_URL = "https://geocoding-api.open-meteo.com/v1/search"

# --- Cache Settings ---
DATA_CACHE_TTL = 60
DATA_MAX_ENTRIES = 128

# --- Unit Conversion ---
HPA_TO_INHG = 0.02953

# --- Application Preferences ---
AUTO_REFRESH_OPTIONS = [
    (0, _("Off")),
    (1, _("Every 1 minute")),
    (15, _("Every 15 minutes")),
    (30, _("Every 30 minutes")),
    (60, _("Every hour")),
    (120, _("Every 2 hours")),
]


# Thresholds based on WHO Global Air Quality Guidelines 2021 (in µg/m³)
THRESHOLDS = {
    "pm2_5": [(15, "success"), (35, "warning"), (75, "error")],
    "pm10": [(45, "success"), (100, "warning"), (150, "error")],
    "carbon_monoxide": [(4000, "success"), (7000, "warning"), (10000, "error")],
    "carbon_dioxide": [(1000, "success"), (2000, "warning"), (5000, "error")],
    "nitrogen_dioxide": [(25, "success"), (50, "warning"), (120, "error")],
    "sulphur_dioxide": [(40, "success"), (50, "warning"), (125, "error")],
    "ozone": [(100, "success"), (120, "warning"), (160, "error")],
    "ammonia": [(100, "success"), (200, "warning"), (400, "error")],
    "methane": [(1900, "success"), (2500, "warning"), (5000, "error")],
    "dust": [(45, "success"), (100, "warning"), (150, "error")],
    "alder_pollen": [(15, "success"), (90, "warning"), (500, "error")],
    "birch_pollen": [(15, "success"), (90, "warning"), (500, "error")],
    "grass_pollen": [(15, "success"), (90, "warning"), (500, "error")],
    "mugwort_pollen": [(15, "success"), (90, "warning"), (500, "error")],
    "olive_pollen": [(15, "success"), (90, "warning"), (500, "error")],
    "ragweed_pollen": [(15, "success"), (90, "warning"), (500, "error")],
}
