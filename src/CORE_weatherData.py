import time
import threading
from gi.repository import GObject
from .API_Weather import Weather
from .API_AirPollution import AirPollution
from .settings import settings
from .configs import HPA_TO_INHG, PRESSURE_LOW, PRESSURE_HIGH, THRESHOLDS
from .CORE_Models import CurrentWeather, HourlyWeather, DailyWeather, WeatherField, AirPollutionData
from .CORE_Helpers import get_cords
from .CORE_Logging import get_logger
from gettext import gettext as _, pgettext as C_

logger = get_logger("data_manager")

class WeatherDataManager(GObject.Object):
    """
    Centralized data manager for Mousam.
    Handles data storage, validation, and notification of updates.
    """
    
    __gsignals__ = {
        'data-updated': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    # Properties for data storage
    current_weather = GObject.Property(type=GObject.TYPE_PYOBJECT)
    hourly_forecast = GObject.Property(type=GObject.TYPE_PYOBJECT)
    daily_forecast = GObject.Property(type=GObject.TYPE_PYOBJECT)
    air_pollution = GObject.Property(type=GObject.TYPE_PYOBJECT)
    
    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()
        # Current weather of the saved locations, by their "lat,lon" key
        self.saved_locations_weather = {}

    @GObject.Property(type=bool, default=False)
    def is_ready(self):
        """Returns True if all essential data is loaded and valid."""
        with self._lock:
            return (self.current_weather is not None and 
                    self.hourly_forecast is not None and 
                    self.daily_forecast is not None and
                    self.air_pollution is not None)

    def clear(self):
        """Resets all data."""
        with self._lock:
            self.current_weather = None
            self.hourly_forecast = None
            self.daily_forecast = None
            self.air_pollution = None
        self.notify("is-ready")

    def update_current_weather(self):
        obj = Weather()
        logger.debug(f"Fetching current weather for cords: {get_cords()}")
        raw_data = obj._get_current_weather(*get_cords())
        if raw_data is None:
            logger.error("Failed to fetch current weather data from API")
            raise ValueError("Failed to fetch current weather data")

        data = CurrentWeather(raw_data)
        data.relativehumidity_2m.level_str = self.classify_humidity_level(data.relativehumidity_2m.data)
        data.windspeed_10m.level_str = self.classify_wind_speed_level(data.windspeed_10m.data)
        data.pressure_msl.level_str = self.classify_presssure_level(data.pressure_msl.data)
        
        with self._lock:
            self.current_weather = data
        self.emit("data-updated")
        self.notify("is-ready")
        return data

    def update_saved_locations_weather(self, coords: list) -> None:
        """Fetches every given "lat,lon" in one request; failed ones become None."""
        raw_data = Weather()._get_current_for_locations(coords) or []
        results = {key: CurrentWeather(raw) for key, raw in zip(coords, raw_data)}

        with self._lock:
            for key in coords:
                self.saved_locations_weather[key] = results.get(key)

    def update_hourly_forecast(self):
        obj = Weather()
        raw_data = obj._get_hourly_forecast(*get_cords())
        if raw_data is None:
            raise ValueError("Failed to fetch hourly forecast data")

        hourly_data = HourlyWeather(raw_data)
        time_list = raw_data.get("hourly").get("time")
        
        nearest_idx = 0
        now = time.time()
        for i, ts in enumerate(time_list):
            if abs(now - ts) < 1800:
                nearest_idx = i
                break

        # Update current weather with derived hourly fields
        with self._lock:
            if self.current_weather:
                self.current_weather.uv_index = WeatherField(
                    data=hourly_data.uv_index.data[nearest_idx],
                    level_str=self.classify_uv_index(hourly_data.uv_index.data[nearest_idx]),
                )
                self.current_weather.dewpoint_2m = WeatherField(
                    unit=hourly_data.dewpoint_2m.unit,
                    data=hourly_data.dewpoint_2m.data[nearest_idx],
                )
                vis_transformed = self.transform_visibility_data(
                    hourly_data.visibility.unit,
                    hourly_data.visibility.data[nearest_idx],
                )
                self.current_weather.visibility = WeatherField(
                    data=vis_transformed["data"],
                    unit=vis_transformed["unit"]
                )
            self.hourly_forecast = hourly_data
            
        self.emit("data-updated")
        self.notify("is-ready")
        return hourly_data

    def update_daily_forecast(self):
        obj = Weather()
        raw_data = obj._get_daily_forecast(*get_cords())
        if raw_data is None:
            raise ValueError("Failed to fetch daily forecast data")

        data = DailyWeather(raw_data)
        with self._lock:
            self.daily_forecast = data
        self.emit("data-updated")
        self.notify("is-ready")
        return data

    def update_air_pollution(self):
        obj = AirPollution()
        raw_data = obj._get_current_air_pollution(*get_cords())
        if raw_data is None:
            raise ValueError("Failed to fetch air pollution data")
        
        time_list = raw_data.get("hourly").get("time")
        nearest_idx = 0
        now = time.time()
        for i, ts in enumerate(time_list):
            if abs(now - ts) < 1800:
                nearest_idx = i
                break
                
        data = AirPollutionData(raw_data)
        data.current_us_aqi = data.us_aqi.data[nearest_idx]
        data.current_eu_aqi = data.european_aqi.data[nearest_idx]
        
        with self._lock:
            self.air_pollution = data
        self.emit("data-updated")
        self.notify("is-ready")
        logger.info("Air pollution data updated successfully")
        return data

    # Helper classification methods
    @staticmethod
    def classify_aqi(aqi_value):
        if aqi_value <= 50: return _("Good")
        if aqi_value <= 100: return _("Moderate")
        if aqi_value <= 150: return _("Poor")
        if aqi_value <= 200: return _("Unhealthy")
        if aqi_value <= 300: return _("Severe")
        return _("Hazardous")

    @staticmethod
    def aqi_level_class(aqi_value) -> str:
        """The colour class for a US AQI: good, raised, or unhealthy and worse."""
        if aqi_value <= 50:
            return "success"
        if aqi_value <= 150:
            return "warning"
        return "error"

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def classify_pollen(value) -> tuple:
        """A pollen count's level (grains/m³): (word, colour class)."""
        if value <= 15:
            return C_("pollen level", "Low"), "success"
        if value <= 90:
            return C_("pollen level", "Moderate"), "warning"
        if value <= 500:
            return C_("pollen level", "High"), "error"
        return C_("pollen level", "Very High"), "error"

    @staticmethod
    def main_pollutant(values: dict):
        """The pollutant furthest above (or nearest to) its WHO limit, from
        {key: value}; None when there is none to compare."""
        ratios = {
            key: value / THRESHOLDS[key][0][0]
            for key, value in values.items()
            if value is not None and key in THRESHOLDS
        }
        return max(ratios, key=ratios.get) if ratios else None

    @staticmethod
    def classify_uv_index(uv):
        if uv <= 2: return C_("uvindex", "Low")
        if uv <= 5: return C_("uvindex", "Moderate")
        if uv <= 7: return C_("uvindex", "High")
        if uv <= 10: return C_("uvindex", "Very High")
        return C_("uvindex", "Extreme")

    @staticmethod
    def classify_humidity_level(h):
        if h < 50: return C_("humidity", "Low")
        if h <= 80: return C_("humidity", "Moderate")
        return C_("humidity", "High")

    @staticmethod
    def classify_presssure_level(p):
        low, high = PRESSURE_LOW, PRESSURE_HIGH
        if settings.unit == "imperial":
            low, high = low * HPA_TO_INHG, high * HPA_TO_INHG
        if p < low: return C_("pressure", "Low")
        if p <= high: return C_("pressure", "Normal")
        return C_("pressure", "High")

    @staticmethod
    def classify_wind_speed_level(w):
        if w <= 1: return _("Calm")
        if w <= 25: return _("Light")
        if w <= 40: return C_("wind", "Moderate")
        if w <= 60: return _("Strong")
        return C_("wind", "Extreme")

    @staticmethod
    def transform_visibility_data(unit, data):
        dist_unit, dist = _("km"), data / 1000
        if settings.unit == "imperial":
            dist_unit, dist = _("miles"), data / 1609.34
        if unit.lower() == "m":
            data, unit = dist, dist_unit
        return {"unit": unit, "data": data}

# Singleton instance
weather_manager = WeatherDataManager()
