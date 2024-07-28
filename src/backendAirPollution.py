import requests


base_url = "https://air-quality-api.open-meteo.com/v1/air-quality"


class AirPollution:
    @staticmethod
    def current_air_pollution(latitude: float, longitude: float, **kwargs):
        url = base_url + f"?latitude={latitude}&longitude={longitude}"
        if "hourly" in kwargs:
            hourly_fields = ",".join(kwargs.get("hourly"))
            url = url + f"&hourly={hourly_fields}"

        try:
            url = url + "&timeformat=unixtime" + "&forecast_days=1"
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception if the request was unsuccessful
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

    def _get_current_air_pollution(self, lat, lon):
        hourly_args = [
            "european_aqi",
            "us_aqi",
            "pm10",
            "pm2_5",
            "carbon_monoxide",
            "nitrogen_dioxide",
            "sulphur_dioxide",
            "ozone",
            "ammonia",
        ]

        return self.current_air_pollution(lat, lon, hourly=hourly_args)
