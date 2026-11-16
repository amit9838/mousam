"""Tests for the API's unit parameters and location formatting.

They pin down the current behaviour before the logic moves into GTK-free
modules (docs/architecture-plan.md, phase 2). The modules still import GTK,
requests and GSettings, so tests/stubs.py stands in for them.

Run: python3 tests/test_levels_and_formatting.py (also run by `meson test`).
"""

import os
import sys
import unittest
from datetime import datetime
from unittest import mock
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stubs  # noqa: E402

stubs.install()

from mousam import windowLocations  # noqa: E402
from mousam.API_Weather import unit_params  # noqa: E402
from mousam.windowLocations import LocationData  # noqa: E402


def fixed_clock():
    """Make windowLocations see 21:05 in Kolkata (15:35 UTC) as the time now."""
    fixed = datetime(2026, 1, 15, 21, 5, tzinfo=ZoneInfo("Asia/Kolkata"))

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed.astimezone(tz)

    return mock.patch.object(windowLocations, "datetime", FixedDatetime)


class SettingsTestCase(unittest.TestCase):
    def setUp(self):
        stubs.settings.reset()


class UnitParams(unittest.TestCase):
    def test_unit_params(self):
        self.assertEqual(unit_params("metric"), "")
        self.assertEqual(
            unit_params("imperial"), "&temperature_unit=fahrenheit&wind_speed_unit=mph"
        )


class LocationFormatting(SettingsTestCase):
    KOCHI = {
        "name": "Kochi",
        "region": "Ernakulam",
        "state": "Kerala",
        "country": "India",
        "latitude": 9.9312,
        "longitude": 76.2673,
        "timezone": "Asia/Kolkata",
    }

    def test_storage_round_trip(self):
        stored = LocationData.to_storage_string(self.KOCHI)
        self.assertEqual(LocationData.from_storage_string(stored), self.KOCHI)

    def test_bad_storage_string_is_empty(self):
        self.assertEqual(LocationData.from_storage_string("not json"), {})
        self.assertEqual(LocationData.from_storage_string(None), {})

    def test_display_name_skips_missing_parts(self):
        self.assertEqual(LocationData.format_display_name(self.KOCHI), "Kochi, Kerala, India")
        self.assertEqual(LocationData.format_display_name({"name": "Kochi"}), "Kochi")

    def test_place(self):
        self.assertEqual(LocationData.format_place(self.KOCHI), "Kerala, India")
        self.assertEqual(
            LocationData.format_place(self.KOCHI, with_region=True), "Ernakulam, Kerala, India"
        )

    def test_place_drops_state_and_region_named_like_the_city(self):
        delhi = {"name": "Delhi", "region": "Delhi", "state": "Delhi", "country": "India"}
        self.assertEqual(LocationData.format_place(delhi, with_region=True), "India")

    def test_place_and_coords(self):
        self.assertEqual(
            LocationData.format_place_and_coords(self.KOCHI),
            "Ernakulam, Kerala, India · 9.93, 76.27",
        )
        no_coords = {"name": "Kochi", "country": "India"}
        self.assertEqual(LocationData.format_place_and_coords(no_coords), "India")

    def test_coords_key(self):
        self.assertEqual(LocationData.get_coords_key(self.KOCHI), "9.9312,76.2673")

    def test_saved_coords(self):
        stubs.settings.added_cities = [LocationData.to_storage_string(self.KOCHI), "", "bad"]
        self.assertEqual(LocationData.saved_coords(), {"9.9312,76.2673"})

    def test_local_time_24h(self):
        with fixed_clock():
            self.assertEqual(LocationData.format_local_time(self.KOCHI), "21:05")

    def test_local_time_12h(self):
        stubs.settings.is_using_24h_clock = False
        with fixed_clock():
            self.assertEqual(LocationData.format_local_time(self.KOCHI), "9:05 PM")

    def test_local_time_without_a_known_timezone(self):
        with fixed_clock():
            self.assertEqual(LocationData.format_local_time({"name": "Kochi"}), "")
            self.assertEqual(LocationData.format_local_time({"timezone": "Not/A_Zone"}), "")

    def test_place_and_time(self):
        with fixed_clock():
            self.assertEqual(
                LocationData.format_place_and_time(self.KOCHI), "Kerala, India · 21:05"
            )


if __name__ == "__main__":
    unittest.main()
