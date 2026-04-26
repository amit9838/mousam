from gettext import gettext as _
from enum import IntEnum

# --- Application Info ---
APP_ID = "io.github.amit9838.mousam"

# --- Networking & Timeout ---
TIMEOUT = 15
INTERNET_CACHE_TTL = 120
DEFAULT_TIMEZONE = "UTC"

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