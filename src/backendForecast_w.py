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
    date_today = datetime.now().date().day

    if type == 'today':
        data_n = [x for x in data if datetime.fromtimestamp(x['dt']).date().day==date_today]

    elif type == 'tomorrow':
        date_tomorrow = datetime.now() + timedelta(days=1)
        date_tomorrow = date_tomorrow.date().day
        data_n = [x for x in data if datetime.fromtimestamp(x['dt']).date().day==date_tomorrow]

    elif type == "five_d":
        # print("five d")
        data_forecast = []
        dt = data[0]['dt']
        temp_avg = {'sum':0,'cnt':0}
        temp_min = 10000
        temp_max = -10000
        pop_max = -5
        pressure_max = -5
        main_icon = {}
        main_condition = {}
        wind_s = -10000
        for i in data:
            if datetime.fromtimestamp(i['dt']).date().day != date_today:
                date_today = datetime.fromtimestamp(i['dt']).date().day
                if  len(main_icon) == 0:
                    main_icon['04d'] = 1
                main_cnd = max(main_condition, key=main_condition.get)
                main_cnd = main_cnd if len(main_cnd)<18 else main_cnd[0:16]+"..."
                data_n = {
                    'dt' : dt,
                    'main':{
                        'temp' : round(temp_avg['sum']/temp_avg['cnt'],3),
                        'temp_min' : temp_min,
                        'temp_max' : temp_max,
                        'pressure_max' : pressure_max,
                    },
                    'pop' : pop_max,
                    'weather':[
                        {
                        'main':main_cnd,
                        'icon':max(main_icon, key=main_icon.get),
                        }],
                    'wind':{
                        "speed":wind_s
                    }
                }
                # print(main_icon)
                data_forecast.append(data_n)
                temp_avg = {'sum':0,'cnt':0}
                temp_min = 10000
                temp_max = -10000
                pop_max = -5
                pressure_max = -5
                main_icon.clear()
                main_condition.clear()
                wind_s = -10000

            else:
                dt = i['dt']
                temp_avg['sum'] += i['main']['temp']    
                temp_avg['cnt'] += 1
                wind_s = max(i['wind']['speed'],wind_s)
                temp_min = min(temp_min,i['main']['temp_min'])
                temp_max = max(temp_max,i['main']['temp_max'])
                pressure_max = max(pressure_max,i['main']['pressure'])
                pop_max = max(pop_max,i['pop'])

                if i['weather'][0]['icon'][2]!='n':
                    if i['weather'][0]['icon'] in main_icon:
                        main_icon[i['weather'][0]['icon']] += 1
                    else:
                        main_icon[i['weather'][0]['icon']] = 1

                if i['weather'][0]['description'] in main_condition:
                    main_condition[i['weather'][0]['description']] +=1
                else:
                    main_condition[i['weather'][0]['description']] =1

        data_n = data_forecast
    return data_n
