"""Tests for the Open-Meteo API modules (src/API_*.py) and the forecast
client seam (src/core/forecast_client.py).

Plain Python, no GTK and no network: a fake `requests` (tests/fakes.py)
records the URLs and answers with hand-built JSON.

Run: python3 tests/test_api.py (also run by `meson test`).
"""

import inspect
import os
import sys
import types
import unittest

TESTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TESTS)
from fakes import FakeForecastClient, FakeRequests, FakeResponse  # noqa: E402

# The API modules import requests: give them the fake, before they load
requests = FakeRequests()
sys.modules["requests"] = requests

# src/ is imported as the `mousam` package, as in the installed app
package = types.ModuleType("mousam")
package.__path__ = [os.path.join(TESTS, "..", "src")]
sys.modules.setdefault("mousam", package)

from mousam.services import air_quality, geocoding, open_meteo  # noqa: E402
from mousam.core.cache import cached  # noqa: E402
from mousam.core.forecast_client import ForecastClient  # noqa: E402
from mousam.config import HPA_TO_INHG, REQUEST_TIMEOUT  # noqa: E402


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        requests.reset()
        open_meteo.clear_cache()
        open_meteo.fetch_many.cache_clear()
        air_quality.clear_cache()
        geocoding.find_city.cache_clear()

    def url(self) -> str:
        self.assertEqual(len(requests.calls), 1)
        return requests.calls[0]["url"]


class CacheClear(unittest.TestCase):
    def test_forgets_every_call_for_the_place_and_keeps_the_rest(self):
        calls = []

        @cached()
        def fetch(latitude, longitude, unit):
            calls.append((latitude, longitude, unit))
            return unit

        for args in ((9.93, 76.27, "metric"), (9.93, 76.27, "imperial"), (28.6, 77.2, "metric")):
            fetch(*args)
        fetch.cache_clear(9.93, 76.27)
        for args in ((9.93, 76.27, "metric"), (9.93, 76.27, "imperial"), (28.6, 77.2, "metric")):
            fetch(*args)
        self.assertEqual(len(calls), 5)  # both units of the place again; the other cached
        self.assertEqual(fetch.cache_info()["currsize"], 3)

    def test_without_arguments_clears_everything(self):
        @cached()
        def fetch(latitude, longitude):
            return latitude

        fetch(9.93, 76.27)
        fetch(28.6, 77.2)
        fetch.cache_clear()
        self.assertEqual(fetch.cache_info()["currsize"], 0)


class UnitParams(unittest.TestCase):
    def test_metric_is_the_api_default(self):
        self.assertEqual(open_meteo.unit_params("metric"), "")

    def test_imperial(self):
        self.assertEqual(
            open_meteo.unit_params("imperial"), "&temperature_unit=fahrenheit&wind_speed_unit=mph"
        )


class Current(ApiTestCase):
    PAYLOAD = {"current": {"pressure_msl": 1000.0}, "current_units": {"pressure_msl": "hPa"}}

    def test_url(self):
        requests.response = FakeResponse(self.PAYLOAD)
        open_meteo.fetch_current(9.93, 76.27, "metric")
        url = self.url()
        self.assertIn("?latitude=9.93&longitude=76.27", url)
        self.assertIn("&current=" + ",".join(open_meteo.CURRENT_FIELDS), url)
        self.assertTrue(url.endswith("&timeformat=unixtime"))
        self.assertNotIn("fahrenheit", url)
        self.assertEqual(requests.calls[0]["timeout"], REQUEST_TIMEOUT)

    def test_imperial_pressure_in_inhg(self):
        requests.response = FakeResponse(
            {"current": {"pressure_msl": 1000.0}, "current_units": {"pressure_msl": "hPa"}}
        )
        data = open_meteo.fetch_current(9.93, 76.27, "imperial")
        self.assertIn("&temperature_unit=fahrenheit", self.url())
        self.assertAlmostEqual(data["current"]["pressure_msl"], 1000 * HPA_TO_INHG)
        self.assertEqual(data["current_units"]["pressure_msl"], "inHg")

    def test_failure_is_none(self):
        requests.error = FakeRequests.ConnectionError("offline")
        self.assertIsNone(open_meteo.fetch_current(9.93, 76.27, "metric"))

    def test_http_error_is_none(self):
        requests.response = FakeResponse(status=500)
        self.assertIsNone(open_meteo.fetch_current(9.93, 76.27, "metric"))

    def test_cached_per_unit(self):
        requests.response = FakeResponse(self.PAYLOAD)
        open_meteo.fetch_current(9.93, 76.27, "metric")
        open_meteo.fetch_current(9.93, 76.27, "metric")
        self.assertEqual(len(requests.calls), 1)
        requests.response = FakeResponse(
            {"current": {"pressure_msl": 1000.0}, "current_units": {"pressure_msl": "hPa"}}
        )
        open_meteo.fetch_current(9.93, 76.27, "imperial")
        self.assertEqual(len(requests.calls), 2)

    def test_clear_cache_of_one_place_goes_to_the_network_for_it_only(self):
        requests.response = FakeResponse(self.PAYLOAD)
        open_meteo.fetch_current(9.93, 76.27, "metric")
        open_meteo.fetch_current(28.6, 77.2, "metric")
        open_meteo.clear_cache(9.93, 76.27)
        open_meteo.fetch_current(9.93, 76.27, "metric")  # from the network
        open_meteo.fetch_current(28.6, 77.2, "metric")  # still cached
        self.assertEqual(len(requests.calls), 3)

    def test_clear_cache_goes_to_the_network_again(self):
        requests.response = FakeResponse(self.PAYLOAD)
        open_meteo.fetch_current(9.93, 76.27, "metric")
        open_meteo.clear_cache()
        open_meteo.fetch_current(9.93, 76.27, "metric")
        self.assertEqual(len(requests.calls), 2)


class Forecasts(ApiTestCase):
    def test_hourly_url_and_imperial_pressure(self):
        requests.response = FakeResponse(
            {"hourly": {"pressure_msl": [1000.0, 1010.0]}, "hourly_units": {"pressure_msl": "hPa"}}
        )
        data = open_meteo.fetch_hourly(9.93, 76.27, "imperial")
        url = self.url()
        self.assertIn("?latitude=9.93&longitude=76.27&timezone=auto", url)
        self.assertIn("&hourly=" + ",".join(open_meteo.HOURLY_FIELDS), url)
        self.assertEqual(
            data["hourly"]["pressure_msl"], [1000 * HPA_TO_INHG, 1010 * HPA_TO_INHG]
        )
        self.assertEqual(data["hourly_units"]["pressure_msl"], "inHg")

    def test_daily_url_in_gmt(self):
        requests.response = FakeResponse({"daily": {}})
        open_meteo.fetch_daily(9.93, 76.27, "metric")
        url = self.url()
        self.assertIn("&daily=" + ",".join(open_meteo.DAILY_FIELDS), url)
        self.assertIn("&timezone=GMT", url)

    def test_many_places_in_one_request(self):
        requests.response = FakeResponse([{"a": 1}, {"b": 2}])
        data = open_meteo.fetch_many(["9.93,76.27", "28.6,77.2"], "metric")
        self.assertIn("?latitude=9.93,28.6&longitude=76.27,77.2", self.url())
        self.assertEqual(data, [{"a": 1}, {"b": 2}])

    def test_one_place_comes_back_as_a_list(self):
        requests.response = FakeResponse({"a": 1})
        self.assertEqual(open_meteo.fetch_many(["9.93,76.27"], "metric"), [{"a": 1}])


class AirQuality(ApiTestCase):
    def test_url(self):
        requests.response = FakeResponse({"hourly": {}})
        air_quality.fetch_air_quality(9.93, 76.27)
        url = self.url()
        self.assertIn("?latitude=9.93&longitude=76.27", url)
        self.assertIn("&hourly=" + ",".join(air_quality.HOURLY_FIELDS), url)
        self.assertIn("&past_days=3&forecast_days=3", url)

    def test_failure_is_none(self):
        requests.error = FakeRequests.Timeout("slow")
        self.assertIsNone(air_quality.fetch_air_quality(9.93, 76.27))


class FindCity(ApiTestCase):
    def test_results_are_mapped(self):
        requests.response = FakeResponse({"results": [{
            "name": "Kochi", "country": "India", "admin1": "Kerala", "admin2": "Ernakulam",
            "latitude": 9.93, "longitude": 76.27, "timezone": "Asia/Kolkata", "id": 1,
        }]})
        cities = geocoding.find_city("Kochi", 5)
        self.assertEqual(requests.calls[0]["params"]["count"], 5)
        self.assertEqual(cities, [{
            "name": "Kochi", "country": "India", "state": "Kerala", "region": "Ernakulam",
            "latitude": 9.93, "longitude": 76.27, "timezone": "Asia/Kolkata",
        }])

    def test_no_results_is_empty(self):
        requests.response = FakeResponse({})
        self.assertEqual(geocoding.find_city("Nowhere"), [])

    def test_failure_is_none(self):
        requests.error = FakeRequests.ConnectionError("offline")
        self.assertIsNone(geocoding.find_city("Kochi"))


class Client(unittest.TestCase):
    NAMES = ("fetch_current", "fetch_hourly", "fetch_daily", "fetch_many")

    def test_api_weather_is_a_forecast_client(self):
        self.assertIsInstance(open_meteo, ForecastClient)

    def test_fake_matches_the_real_functions(self):
        fake = FakeForecastClient()
        self.assertIsInstance(fake, ForecastClient)
        for name in self.NAMES:
            with self.subTest(name=name):
                real = list(inspect.signature(getattr(open_meteo, name)).parameters)
                faked = list(inspect.signature(getattr(fake, name)).parameters)
                self.assertEqual(faked, real)

    def test_fake_answers_and_records(self):
        fake = FakeForecastClient(fetch_current={"current": {}})
        self.assertEqual(fake.fetch_current(1, 2, "metric"), {"current": {}})
        self.assertIsNone(fake.fetch_daily(1, 2, "metric"))
        self.assertEqual(fake.calls, [("fetch_current", 1, 2, "metric"), ("fetch_daily", 1, 2, "metric")])


if __name__ == "__main__":
    unittest.main()
