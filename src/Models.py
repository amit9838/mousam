# Models for All weather data data



class CurrentWeather:
    total_instances = 0

    def __init__(self, data) -> None:
        # Dynamically create fields based on the data dictionary
        for field, values in data.get("current").items():
            setattr(
                self,
                field,
                {"unit": data.get("current_units").get(field), "data": values},
            )

        CurrentWeather.total_instances += 1

    def print_data(self):
        from pprint import pprint

        pprint(self.__dict__)

    def update_data(self, field, new_data):
        if hasattr(self, field):
            getattr(self, field)["data"] = new_data
        else:
            print(f"Field '{field}' not found in WeatherData.")


class HourlyWeather:
    total_instances = 0

    def __init__(self, data) -> None:
        # Dynamically create fields based on the data dictionary
        for field, values in data.get("hourly").items():
            setattr(
                self,
                field,
                {"unit": data.get("hourly_units").get(field), "data": values},
            )

        HourlyWeather.total_instances += 1

    def print_data(self):
        from pprint import pprint

        pprint(self.__dict__)

    def update_data(self, field, new_data):
        if hasattr(self, field):
            getattr(self, field)["data"] = new_data
        else:
            print(f"Field '{field}' not found in WeatherData.")


class DailyWeather:
    total_instances = 0

    def __init__(self, data) -> None:
        # Dynamically create fields based on the data dictionary
        for field, values in data.get("daily").items():
            setattr(
                self,
                field,
                {"unit": data.get("daily_units").get(field), "data": values},
            )

        DailyWeather.total_instances += 1

    def print_data(self):
        from pprint import pprint

        pprint(self.__dict__)

    def update_data(self, field, new_data):
        if hasattr(self, field):
            getattr(self, field)["data"] = new_data
        else:
            print(f"Field '{field}' not found in WeatherData.")


class Location:
    total_instances = 0

    def __init__(self, data) -> None:
        # Dynamically create fields based on the data dictionary
        for field, values in data.items():
            setattr(self,field,values)

        DailyWeather.total_instances += 1

    def print_data(self):
        from pprint import pprint

        pprint(self.__dict__)

    def update_data(self, field, new_data):
        if hasattr(self, field):
            getattr(self, field)["data"] = new_data
        else:
            print(f"Field '{field}' not found in WeatherData.")