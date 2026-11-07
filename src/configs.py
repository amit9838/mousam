from gettext import gettext as _

# --- Application Info ---
APP_ID = "io.github.amit9838.mousam"
VERSION = "2.0.2"

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

# Overview (the one-line summary under the current conditions)
OVERVIEW_FIRST_DELAY = 10  # seconds after the first data load, so start-up stays fast
OVERVIEW_REFRESH_DELAY = 2  # seconds after later refreshes, once the grid is rebuilt
OVERVIEW_HOURS = 12  # how far ahead the overview looks
RAIN_LIKELY_PROBABILITY = 50  # % chance from which an hour counts as rainy
# When the overview opens again by itself: BASE ÷ (1 + score), where the
# score adds up the priorities (÷ 100) of everything worth saying, so a busy
# forecast opens it more often. Kept between MIN and MAX minutes, then spread
# at random by ± SPREAD so it does not feel mechanical. MIN is also the
# shortest gap before something that just turned severe opens it again.
OVERVIEW_ANNOUNCE_BASE_MINUTES = 40
OVERVIEW_ANNOUNCE_MIN_MINUTES = 5
OVERVIEW_ANNOUNCE_MAX_MINUTES = 40
OVERVIEW_ANNOUNCE_SPREAD = 0.2

# Overview rules (CORE_OverviewRules.py). All thresholds are metric; rules
# convert imperial data before comparing.
OVERVIEW_DAY_MIN_HOURS = 3  # by day, look at least this far ahead, even near sunset
OVERVIEW_TOMORROW_FROM_HOUR = 18  # local hour from which tomorrow is worth a mention
OVERVIEW_RELATIVE_TOLERANCE = 300  # s a message saying "in N minutes" stays accurate
# Approximate times ("until about 6:40 AM") are rounded more the further
# ahead they are: (up to this many hours ahead, round to this many minutes).
# Beyond the last one, OVERVIEW_ROUND_FAR_MINUTES.
OVERVIEW_ROUNDING = [(3, 10), (5, 30)]
OVERVIEW_ROUND_FAR_MINUTES = 60
HEAVY_PRECIPITATION_MM = 7.6  # mm in an hour: heavy rain
HEAT_FEELS_LIKE_C = 40  # feels-like °C from which heat is a warning
COLD_FEELS_LIKE_C = -15  # feels-like °C from which cold is a warning
UNHEALTHY_US_AQI = 151  # US AQI from which air is unhealthy
VERY_HIGH_UV = 8
FOG_VISIBILITY_M = 1000
STRONG_WIND_KMH = 40  # matches "Strong" in classify_wind_speed_level
EXTREME_WIND_KMH = 60  # matches "Extreme": the wind insight becomes a warning
TEMPERATURE_SWING_C = 6  # change across the window worth a mention
TOMORROW_DIFFERENCE_C = 4  # tomorrow's high vs today's, worth a mention
SUNSET_SOON_MINUTES = 120
SUNRISE_SOON_MINUTES = 180

# Higher wins. Safety first, then changes, then calm facts.
OVERVIEW_PRIORITIES = {
    "storm": 100,
    "freezing": 95,
    "heavy_precipitation": 90,
    "extreme_feels": 85,
    "air_quality": 80,
    "uv": 75,
    "precipitation": 60,
    "wind": 55,
    "fog": 50,
    "temperature_swing": 40,
    "tomorrow": 30,
    "sun": 20,
    "calm": 0,
}

# How long a message stays open: a base time, plus extra for severe ones
# (seconds). Info 15 s, warning 22 s, error 30 s.
OVERVIEW_SHOW_BASE_SECONDS = 15
OVERVIEW_SHOW_EXTRA_SECONDS = {"info": 0, "warning": 7, "error": 15}
