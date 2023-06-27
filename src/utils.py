current_weather_data = None
forecast_weather_data = None

def get_weather_data():
    return current_weather_data,forecast_weather_data

def set_weather_data(current,forecast):
    global current_weather_data, forecast_weather_data
    current_weather_data = current
    forecast_weather_data = forecast