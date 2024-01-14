import requests
from .Models import Location

def find_city(city, count=3):
    base_url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": city,
        "language": 'en',
        "format": "json", 
        "count": count
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        cities_res = response.json()
        cities = cities_res.get('results')
        # print(cities)
        cities_list = []
        if cities == None:
            return cities_list
        for city in cities:
            data = {
                "name": city.get('name'),
                "country": city.get('country'),
                "state": city.get('admin1'),
                "region": city.get('admin2'),
                "latitude": city.get('latitude'),
                "longitude": city.get('longitude')
            }

            cities_list.append(Location(data))
        return cities_list

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


# UI
# Name - state - Country
# Delhi, Delhi, India [name=state]
# Basti, Uttar Pradesh, India