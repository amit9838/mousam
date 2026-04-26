import requests
from .CORE_Cache import cached
from .CORE_Helpers import TIMEOUT
from .configs import AIR_QUALITY_BASE_URL

# base_url moved to configs.py


class AirPollution:
    @staticmethod
    @cached()
    def current_air_pollution(latitude: float, longitude: float, **kwargs):
        url = AIR_QUALITY_BASE_URL + f"?latitude={latitude}&longitude={longitude}"
        if "hourly" in kwargs:
            hourly_fields = ",".join(kwargs.get("hourly"))
            url = url + f"&hourly={hourly_fields}"

        try:
            url = url + "&timeformat=unixtime" + "&past_days=3" + "&forecast_days=3"+ "&timezone=auto"
            response = requests.get(url, timeout=TIMEOUT)
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
            "carbon_dioxide",
            "nitrogen_dioxide",
            "sulphur_dioxide",
            "ozone",
            "dust",
            "ammonia",
            "methane",
            "alder_pollen",
            "birch_pollen",
            "grass_pollen",
            "mugwort_pollen",
            "olive_pollen",
            "ragweed_pollen",
        ]

        return self.current_air_pollution(lat, lon, hourly=hourly_args)
