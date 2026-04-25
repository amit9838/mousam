from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict

@dataclass
class WeatherField:
    """Represents a single weather metric with data, unit, and optional level description."""
    data: Any
    unit: str = ""
    level_str: str = ""

    def get(self, key, default=None):
        """Backward compatibility for dict-like access."""
        if key == "data": return self.data
        if key == "unit": return self.unit
        if key == "level_str": return self.level_str
        return default

    def __getitem__(self, key):
        return self.get(key)

class CurrentWeather:
    """Model for current weather data with explicit fields for better IDE suggestions."""
    time: WeatherField
    temperature_2m: WeatherField
    relativehumidity_2m: WeatherField
    apparent_temperature: WeatherField
    is_day: WeatherField
    precipitation: WeatherField
    weathercode: WeatherField
    surface_pressure: WeatherField
    windspeed_10m: WeatherField
    winddirection_10m: WeatherField
    
    # Optional/Derived fields
    uv_index: Optional[WeatherField] = None
    dewpoint_2m: Optional[WeatherField] = None
    visibility: Optional[WeatherField] = None

    def __init__(self, data: Dict[str, Any]):
        current = data.get("current", {})
        units = data.get("current_units", {})
        for k, v in current.items():
            setattr(self, k, WeatherField(data=v, unit=units.get(k, "")))

class HourlyWeather:
    """Model for hourly forecast data."""
    time: WeatherField
    temperature_2m: WeatherField
    relativehumidity_2m: WeatherField
    dewpoint_2m: WeatherField
    apparent_temperature: WeatherField
    weathercode: WeatherField
    precipitation: WeatherField
    precipitation_probability: WeatherField
    surface_pressure: WeatherField
    visibility: WeatherField
    windspeed_10m: WeatherField
    wind_direction_10m: WeatherField
    uv_index: WeatherField
    is_day: WeatherField

    def __init__(self, data: Dict[str, Any]):
        hourly = data.get("hourly", {})
        units = data.get("hourly_units", {})
        for k, v in hourly.items():
            setattr(self, k, WeatherField(data=v, unit=units.get(k, "")))

class DailyWeather:
    """Model for daily forecast data."""
    time: WeatherField
    weathercode: WeatherField
    temperature_2m_max: WeatherField
    temperature_2m_min: WeatherField
    sunrise: WeatherField
    sunset: WeatherField
    uv_index_max: WeatherField
    precipitation_sum: WeatherField
    windspeed_10m_max: WeatherField

    def __init__(self, data: Dict[str, Any]):
        daily = data.get("daily", {})
        units = data.get("daily_units", {})
        for k, v in daily.items():
            setattr(self, k, WeatherField(data=v, unit=units.get(k, "")))

@dataclass
class Location:
    """Model for location search results."""
    id: int
    name: str
    latitude: float
    longitude: float
    elevation: Optional[float] = None
    feature_code: Optional[str] = None
    country_code: Optional[str] = None
    admin1_id: Optional[int] = None
    timezone: Optional[str] = None
    population: Optional[int] = None
    country_id: Optional[int] = None
    country: Optional[str] = None
    admin1: Optional[str] = None

    def __init__(self, data: Dict[str, Any]):
        for k, v in data.items():
            setattr(self, k, v)

@dataclass
class AirPollutionData:
    """Model for air pollution data."""
    time: WeatherField
    european_aqi: WeatherField
    us_aqi: WeatherField
    pm10: WeatherField
    pm2_5: WeatherField
    carbon_monoxide: WeatherField
    carbon_dioxide: WeatherField
    nitrogen_dioxide: WeatherField
    sulphur_dioxide: WeatherField
    ozone: WeatherField
    dust: WeatherField
    ammonia: WeatherField
    methane: WeatherField
    alder_pollen: WeatherField
    birch_pollen: WeatherField
    grass_pollen: WeatherField
    mugwort_pollen: WeatherField
    olive_pollen: WeatherField
    ragweed_pollen: WeatherField
    
    # Derived fields added by manager
    current_us_aqi: Optional[int] = None
    current_eu_aqi: Optional[int] = None

    def __init__(self, data: Dict[str, Any]):
        hourly = data.get("hourly", {})
        units = data.get("hourly_units", {})
        for k, v in hourly.items():
            setattr(self, k, WeatherField(data=v, unit=units.get(k, "")))
