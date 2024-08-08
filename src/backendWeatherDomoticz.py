import time
import json
import urllib.request as urllib2
from .config import settings


class WeatherDomoticz:
   def __init__(self):
        self.mWeatherJson = None
        self.mDomoticzSettingsRestApi = "/json.htm?type=settings"
        self.mDomoticzWeatherRestApi = "/json.htm?type=devices&filter=weather&used=true"
        self.mHostname = settings.domoticz_host
        self.mHardwareName = settings.domoticz_weather_hwtype
   
           
   def ReadDomoticzLocation(self):
        domUrl = "http://" + self.mHostname + self.mDomoticzSettingsRestApi
        request = urllib2.Request(domUrl)
        response = urllib2.urlopen(request)
        domJson = json.loads(response.read())
        lat = domJson['Location']['Latitude']
        lon = domJson['Location']['Longitude']
        return float(lat), float(lon)

   def IsLocationNearDomoticz(self, lat, lon):
        domLat, domLon = self.ReadDomoticzLocation()
        diffLat = abs(domLat - lat)
        diffLon = abs(domLon - lon)
        if diffLat < 0.05 and diffLon < 0.05:
            return True
        return False        
           
   def ReadDomoticzWeather(self):
        # Get the current weather items from domoticz
        domUrl = "http://" + self.mHostname + self.mDomoticzWeatherRestApi
        request = urllib2.Request(domUrl)
        response = urllib2.urlopen(request)
        return json.loads(response.read())

   def _get_current_weather(self):
        # Get location
        lat, lon = self.ReadDomoticzLocation()
        # Retreive all weather items from Domoticz
        tsStart = time.time()
        self.mWeatherJson = self.ReadDomoticzWeather()
        tsEnd = time.time()
        cwGenerationTime = tsEnd - tsStart
        # Get current time determine if it is day or night
        sunrise = self.mWeatherJson['Sunrise'].split(':')
        sunriseNr = 60 * int(sunrise[0]) + int(sunrise[1])
        sunset = self.mWeatherJson['Sunset'].split(':')
        sunsetNr = 60 * int(sunset[0]) + int(sunset[1])
        curtime = self.mWeatherJson['ServerTime'].split(' ')[1].split(':')
        curtimeNr = 60 * int(curtime[0]) + int(curtime[1])
        isDay = sunriseNr < curtimeNr < sunsetNr
        # Filter weather item according 'domoticz-weather-hwtype' setting
        output_dict = [x for x in self.mWeatherJson['result'] if x['HardwareName'] == self.mHardwareName]
        # Seperate different weather items        
        temp = [x for x in output_dict if x["Type"] == "Temp + Humidity + Baro"]
        wind = [x for x in output_dict if x["Type"] == "Wind"]
        rain = [x for x in output_dict if x["Type"] == "Rain"]
        uv = [x for x in output_dict if x["Type"] == "UV"]
        # Get all current weather conditions
        cwTemp = float(temp[0]['Temp'])
        cwHum = float(temp[0]['Humidity'])
        cwApp = wind[0]["Chill"]
        cwUV = float(uv[0]['UVI'])
        cwPreci = float(rain[0]['Rain'])
        cwPressure = float(temp[0]['Barometer'])
        cwWindSpeed = float(wind[0]["Speed"]) * 3.6
        # Get rid of more then 2 decimals in float
        cwWindSpeed = float(int(cwWindSpeed*100)/100)
        cwWindDir = wind[0]['Direction']
        cwIsDay = 0
        if isDay:
          cwIsDay = 1
        cwTime = int(self.mWeatherJson["ActTime"])
        cwWeatherCode = int(temp[0]['Forecast'])
        # Create current weather dict
        current_weather = {
            'latitude': lat,
            'longitude': lon,
            'generationtime_ms': cwGenerationTime,
            'utc_offset_seconds': 0,
            "timezone": "GMT",
            "timezone_abbreviation": "GMT",
            "elevation": 15.0,
            "current_units": {
                "time": "unixtime",
                "interval": "seconds",
                "temperature_2m": "°C",
                "relativehumidity_2m": "%",
                "apparent_temperature": "°C",
                "is_day": "",
                "uv_index": "",
                "precipitation": "mm",
                "weathercode": "wmo code",
                "surface_pressure": "hPa",
                "windspeed_10m": "km/h",
                "winddirection_10m": "°"
            },
            "current": {
                "time": cwTime,
                "interval": 300,
                "temperature_2m": cwTemp,
                "relativehumidity_2m": cwHum,
                "apparent_temperature": cwApp,
                "is_day": cwIsDay,
                "uv_index": cwUV,
                "precipitation": cwPreci,
                "weathercode": cwWeatherCode,
                "surface_pressure": cwPressure,
                "windspeed_10m": cwWindSpeed,
                "winddirection_10m": cwWindDir
            }
        }
        
        return current_weather

