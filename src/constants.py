from gi.repository import Gio,GLib
from .backend_current_w import fetch_city_info

settings = Gio.Settings.new("io.github.amit9838.weather")

API_KEY = str(settings.get_value("personal-api-key"))

using_personal_api_key = settings.get_boolean("using-personal-api-key")

if using_personal_api_key and len(API_KEY)==34 and fetch_city_info(API_KEY[1:-1],'delhi'):
        API_KEY = API_KEY[1:-1]
        settings.set_value("using-personal-api-key",GLib.Variant("b",True))
        settings.set_value("isvalid-personal-api-key",GLib.Variant("b",True))
        print("Using personal api")

else:
        API_KEY = str(settings.get_value('api-key'))[1:-1]
        settings.set_value("using-personal-api-key",GLib.Variant("b",False))
        settings.set_value("isvalid-personal-api-key",GLib.Variant("b",False))
        print("Using Default api")



icons = {'01d':"weather-clear-symbolic",
         '02d':"weather-few-clouds-symbolic",
         '03d':"weather-few-clouds-symbolic",
         '04d':"weather-few-clouds-symbolic",
         '09d':"weather-showers-scattered-symbolic",
         '10d':"weather-showers-symbolic",
         '11d':"weather-storm-symbolic",
         '13d':"weather-snow-symbolic",
         '50d':"weather-fog-symbolic",

         '01n':"weather-clear-night-symbolic",
         '02n':"weather-few-clouds-night-symbolic",
         '03n':"weather-few-clouds-night-symbolic",
         '04n':"weather-few-clouds-night-symbolic",
         '09n':"weather-showers-scattered-symbolic",
         '10n':"weather-showers-symbolic",
         '11n':"weather-storm-symbolic",
         '13n':"weather-snow-symbolic",
         '50n':"weather-fog-symbolic",
         }

bg_css ={'01d':"clear_sky",
        '02d':"few_clouds",
        '03d':"overcast",
        '04d':"overcast",
        '09d':"showers_scattered",
        '10d':"showers_large",
        '11d':"storm",
        '13d':"snow",
        '50d':"fog",

        '01n':"clear_sky_night",
        '02n':"few_clouds_night",
        '03n':"overcast_night",
        '04n':"showers_scattered_night",
        '09n':"showers_large_night",
        '10n':"showers_large_night",
        '11n':"storm_night",
        '13n':"snow_night",
        '50n':"fog_night",
        }

# 01d: Clear sky (day)
# 01n: Clear sky (night)
# 02d: Few clouds (day)
# 02n: Few clouds (night)
# 03d: Scattered clouds (day)
# 03n: Scattered clouds (night)
# 04d: Broken clouds (day)
# 04n: Broken clouds (night)
# 09d: Shower rain (day)
# 09n: Shower rain (night)
# 10d: Rain (day)
# 10n: Rain (night)
# 11d: Thunderstorm (day)
# 11n: Thunderstorm (night)
# 13d: Snow (day)
# 13n: Snow (night)
# 50d: Mist (day)
# 50n: Mist (night)

