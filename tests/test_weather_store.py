"""Tests for the weather store (src/state/weather_store.py).

The store is a GObject that hands its results to the GLib main loop, so
these tests need PyGObject (GLib and GObject only: no display). The network,
the online check and the settings are fakes (tests/fakes.py).

Run: python3 tests/test_weather_store.py (also run by `meson test`).
"""

import os
import sys
import threading
import time
import types
import unittest

import gi

gi.require_version("GLib", "2.0")
from gi.repository import GLib  # noqa: E402

TESTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TESTS)
from fakes import FakeForecastClient, FakeRequests, FakeSettings, settings_module  # noqa: E402

# src/ is imported as the `mousam` package, as in the installed app. The API
# modules import requests, and the real settings need the installed schema.
sys.modules["requests"] = FakeRequests()
package = types.ModuleType("mousam")
package.__path__ = [os.path.join(TESTS, "..", "src")]
sys.modules.setdefault("mousam", package)
sys.modules["mousam.services.settings"] = settings_module(FakeSettings())

from mousam.state import weather_store as store_module  # noqa: E402
from mousam.state.weather_store import WeatherStore, _run_all  # noqa: E402


def current_json(pressure=1013):
    return {
        "current": {
            "temperature_2m": 21, "relativehumidity_2m": 85, "windspeed_10m": 30,
            "pressure_msl": pressure, "weathercode": 61, "is_day": 1,
        },
        "current_units": {"temperature_2m": "°C"},
    }


def hourly_json():
    now = time.time()
    return {
        "hourly": {
            "time": [now - 3600, now], "uv_index": [1, 6],
            "dewpoint_2m": [9, 10], "visibility": [20000, 24000],
        },
        "hourly_units": {"dewpoint_2m": "°C", "visibility": "m"},
    }


def air_json():
    return {"hourly": {"time": [time.time()], "us_aqi": [42], "european_aqi": [18]}}


def full_client():
    return FakeForecastClient(
        fetch_current=current_json(), fetch_hourly=hourly_json(), fetch_daily={"daily": {"time": []}},
    )


class StoreTestCase(unittest.TestCase):
    def make_store(self, client=None, air=None, online=True, **settings):
        self.client = client or full_client()
        self.air_calls = []
        self.settings = FakeSettings(**settings)

        def fetch_air(lat, lon):
            self.air_calls.append((lat, lon))
            return air_json() if air is None else air

        self.store = WeatherStore(
            client=self.client,
            fetch_air=fetch_air,
            settings=self.settings,
            is_online=lambda force=False: online,
        )
        self.statuses = []
        self.store.connect("notify::status", lambda store, _p: self.statuses.append(store.status))
        self.ready_changes = []
        self.store.connect("notify::is-ready", lambda store, _p: self.ready_changes.append(store.is_ready))
        self.updates = []
        self.store.connect("data-updated", lambda _store: self.updates.append(True))
        return self.store

    def run_until(self, done, timeout=5):
        """Run the main loop until done() is true."""
        context = GLib.MainContext.default()
        end = time.monotonic() + timeout
        while not done():
            if time.monotonic() > end:
                self.fail(f"Timed out; statuses so far: {self.statuses}")
            context.iteration(False)
            time.sleep(0.002)

    def refresh_and_wait(self, **kwargs):
        count = len(self.statuses)
        self.store.refresh(**kwargs)
        self.run_until(lambda: len(self.statuses) > count and self.statuses[-1] != "loading")


class Ready(StoreTestCase):
    def test_a_fetch_publishes_once(self):
        store = self.make_store()
        self.refresh_and_wait()
        self.assertEqual(self.statuses, ["loading", "ready"])
        self.assertEqual(self.ready_changes, [False, True])
        self.assertEqual(self.updates, [True])
        self.assertTrue(store.is_ready)
        self.assertEqual(store.location, "9.93,76.27")

    def test_requests_use_the_settings(self):
        self.make_store(selected_city="28.6,77.2", unit="imperial")
        self.refresh_and_wait()
        self.assertIn(("fetch_current", 28.6, 77.2, "imperial"), self.client.calls)
        self.assertEqual(self.air_calls, [(28.6, 77.2)])

    def test_models_and_levels(self):
        store = self.make_store()
        self.refresh_and_wait()
        current = store.current_weather
        self.assertEqual(current.temperature_2m.data, 21)
        self.assertEqual(current.relativehumidity_2m.level_str, "High")
        self.assertEqual(current.windspeed_10m.level_str, "Moderate")
        self.assertEqual(current.pressure_msl.level_str, "Normal")
        # From this hour of the hourly forecast
        self.assertEqual(current.uv_index.data, 6)
        self.assertEqual(current.uv_index.level_str, "High")
        self.assertEqual(current.dewpoint_2m.data, 10)
        self.assertEqual((current.visibility.data, current.visibility.unit), (24.0, "km"))
        self.assertEqual(store.air_pollution.current_us_aqi, 42)
        self.assertEqual(store.air_pollution.current_eu_aqi, 18)

    def test_imperial_levels(self):
        client = full_client()
        client.responses["fetch_current"] = current_json(pressure=29.0)  # inHg, below 1000 hPa
        store = self.make_store(client=client, unit="imperial")
        self.refresh_and_wait()
        self.assertEqual(store.current_weather.pressure_msl.level_str, "Low")
        self.assertEqual(store.current_weather.visibility.unit, "miles")


class Offline(StoreTestCase):
    def test_offline_fetches_nothing(self):
        store = self.make_store(online=False)
        self.refresh_and_wait()
        self.assertEqual(self.statuses, ["offline"])
        self.assertEqual(self.client.calls, [])
        self.assertFalse(store.is_ready)

    def test_offline_keeps_the_data(self):
        store = self.make_store()
        self.refresh_and_wait()
        store._is_online = lambda force=False: False
        self.refresh_and_wait()
        self.assertEqual(self.statuses, ["loading", "ready", "offline"])
        self.assertTrue(store.is_ready)
        self.assertIsNotNone(store.current_weather)

    def test_the_check_can_be_skipped(self):
        self.make_store(online=False)
        self.refresh_and_wait(check_online=False)
        self.assertEqual(self.statuses, ["loading", "ready"])


class Errors(StoreTestCase):
    def test_failed_current_weather(self):
        client = full_client()
        client.responses["fetch_current"] = None
        store = self.make_store(client=client)
        self.refresh_and_wait()
        self.assertEqual(self.statuses, ["loading", "error"])
        self.assertEqual(store.error, "Failed to fetch current weather data")
        self.assertFalse(store.is_ready)
        self.assertEqual([call[0] for call in client.calls], ["fetch_current"])

    def test_failed_forecast(self):
        client = full_client()
        client.responses["fetch_daily"] = None
        store = self.make_store(client=client)
        self.refresh_and_wait()
        self.assertEqual(store.status, "error")
        self.assertEqual(store.error, "Failed to fetch daily forecast data")
        self.assertIsNone(store.current_weather)
        self.assertEqual(self.updates, [])

    def test_failed_air_quality_still_shows_the_weather(self):
        store = self.make_store(air={})
        store._fetch_air = lambda lat, lon: None
        self.refresh_and_wait()
        self.assertEqual(store.status, "ready")
        self.assertIsNone(store.air_pollution)
        self.assertEqual(store.current_weather.temperature_2m.data, 21)

    def test_unreadable_air_quality_still_shows_the_weather(self):
        store = self.make_store(air={"hourly": {}})
        self.refresh_and_wait()
        self.assertEqual(store.status, "ready")
        self.assertIsNone(store.air_pollution)

    def test_exception_in_the_client(self):
        client = full_client()
        client.responses["fetch_hourly"] = RuntimeError("boom")
        store = self.make_store(client=client)
        self.refresh_and_wait()
        self.assertEqual((store.status, store.error), ("error", "boom"))

    def test_a_later_fetch_recovers(self):
        client = full_client()
        client.responses["fetch_current"] = None
        store = self.make_store(client=client)
        self.refresh_and_wait()
        client.responses["fetch_current"] = current_json()
        self.refresh_and_wait()
        self.assertEqual(self.statuses, ["loading", "error", "loading", "ready"])
        self.assertTrue(store.is_ready)


class RunAll(unittest.TestCase):
    """_run_all: required tasks fail the fetch, optional ones become None."""

    def test_an_optional_error_is_none(self):
        def broken():
            raise ValueError("no air today")
        results = _run_all({"hft": lambda: 1, "apt": broken}, optional=("apt",))
        self.assertEqual(results, {"hft": 1, "apt": None})

    def test_a_required_error_is_raised(self):
        def broken():
            raise ValueError("no forecast")
        with self.assertRaises(ValueError):
            _run_all({"hft": broken, "apt": lambda: 2}, optional=("apt",))

    def test_an_optional_timeout_is_none(self):
        saved = store_module.CONNECT_TIMEOUT, store_module.TIMEOUT
        store_module.CONNECT_TIMEOUT, store_module.TIMEOUT = 0, 0.05
        release = threading.Event()
        try:
            results = _run_all({"hft": lambda: 1, "apt": release.wait}, optional=("apt",))
        finally:
            release.set()
            store_module.CONNECT_TIMEOUT, store_module.TIMEOUT = saved
        self.assertEqual(results, {"hft": 1, "apt": None})

    def test_a_required_timeout_is_raised(self):
        saved = store_module.CONNECT_TIMEOUT, store_module.TIMEOUT
        store_module.CONNECT_TIMEOUT, store_module.TIMEOUT = 0, 0.05
        release = threading.Event()
        try:
            with self.assertRaises(TimeoutError):
                _run_all({"hft": release.wait})
        finally:
            release.set()
            store_module.CONNECT_TIMEOUT, store_module.TIMEOUT = saved


class Joining(StoreTestCase):
    def test_a_refresh_during_a_fetch_joins_it(self):
        store = self.make_store()
        self.client.gate = threading.Event()
        store.refresh()
        self.run_until(lambda: self.statuses == ["loading"])
        store.refresh()
        store.refresh()
        self.client.gate.set()
        self.run_until(lambda: self.statuses[-1] == "ready")
        self.assertEqual([c[0] for c in self.client.calls].count("fetch_current"), 1)
        self.assertEqual(self.updates, [True])

    def test_another_city_during_a_fetch_fetches_it_after(self):
        store = self.make_store()
        self.client.gate = threading.Event()
        store.refresh()
        self.run_until(lambda: self.statuses == ["loading"])
        self.settings.selected_city = "28.6,77.2"
        store.refresh()
        self.client.gate.set()
        self.run_until(lambda: self.statuses[-1] == "ready")
        currents = [c[1:3] for c in self.client.calls if c[0] == "fetch_current"]
        self.assertEqual(currents, [(9.93, 76.27), (28.6, 77.2)])
        # The first city's data is never shown
        self.assertEqual(store.location, "28.6,77.2")
        self.assertEqual(self.updates, [True])
        self.assertEqual(self.ready_changes.count(True), 1)

    def test_a_refresh_after_a_fetch_fetches_again(self):
        self.make_store()
        self.refresh_and_wait()
        self.refresh_and_wait()
        self.assertEqual([c[0] for c in self.client.calls].count("fetch_current"), 2)


class SavedLocations(StoreTestCase):
    def test_weather_by_coords(self):
        client = FakeForecastClient(fetch_many=[current_json()])
        store = self.make_store(client=client)
        done = []
        store.refresh_saved_locations(["9.93,76.27", "28.6,77.2"], lambda: done.append(True))
        self.run_until(lambda: done)
        self.assertEqual(store.saved_locations_weather["9.93,76.27"].temperature_2m.data, 21)
        # One answer for two places: the other has none
        self.assertIsNone(store.saved_locations_weather["28.6,77.2"])

    def test_failed_request(self):
        store = self.make_store(client=FakeForecastClient())
        done = []
        store.refresh_saved_locations(["9.93,76.27"], lambda: done.append(True))
        self.run_until(lambda: done)
        self.assertIsNone(store.saved_locations_weather["9.93,76.27"])


if __name__ == "__main__":
    unittest.main()
