import requests
from datetime import datetime, timedelta
from .units import get_measurement_type

def fetch_forecast(api_key,latitude, longitude, days=1):
    measurement_type = get_measurement_type()
    base_url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": api_key,
        "units": measurement_type,  # You can change the units to "imperial" for Fahrenheit
        "cnt": days * 8  # Each day has 8 forecast intervals (3-hour intervals)
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        forecast_data = response.json()
        return forecast_data


    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None
    

def extract_forecast_data(data,type='today'):
    data_n = None
    if type == 'today':
        date_today = datetime.now().date().day
        data_n = [x for x in data if datetime.fromtimestamp(x['dt']).date().day==date_today]

    elif type == 'tomorrow':
        date_tomorrow = datetime.now() + timedelta(days=1)
        date_tomorrow = date_tomorrow.date().day
        data_n = [x for x in data if datetime.fromtimestamp(x['dt']).date().day==date_tomorrow]

    return data_n