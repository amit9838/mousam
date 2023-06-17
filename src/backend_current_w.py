import requests

def fetch_weather(api_key, latitude, longitude):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": api_key,
        "units": "metric"  # You can change the units to "imperial" for Fahrenheit
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception if request was unsuccessful
        weather_data = response.json()
        return weather_data

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


# data = {'coord': {'lon': 77.3272, 'lat': 28.5706},
#         'weather': [{'id': 804, 'main': 'Clouds', 'description': 'overcast clouds', 'icon': '04n'}],
#         'base': 'stations',
#         'main': {'temp': 29.18, 'feels_like': 27.6, 'temp_min': 29.18, 'temp_max': 29.18, 'pressure': 1005, 'humidity': 20, 'sea_level': 1005, 'grnd_level': 982},'visibility': 10000,
#         'wind': {'speed': 2.68, 'deg': 341, 'gust': 4.59},
#         'clouds': {'all': 91},
#         'dt': 1685818745,
#         'sys': {'type': 1, 'id': 9165, 'country': 'IN', 'sunrise': 1685836384, 'sunset': 1685886305},
#         'timezone': 19800, 'id': 7279746, 'name': 'Noida', 'cod': 200}



def fetch_city_info(api_key, city):
    base_url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": city,
        "limit": 5,
        "appid": api_key
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

