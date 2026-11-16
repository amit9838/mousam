"""Tests for saved-location storage and formatting (src/CORE_Locations.py).

Plain Python, no GTK. Run: python3 tests/test_locations.py (also run by `meson test`).
"""

import os
import sys
import types
import unittest
from datetime import datetime
from unittest import mock
from zoneinfo import ZoneInfo

# src/ is imported as the `mousam` package, as in the installed app
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
package = types.ModuleType("mousam")
package.__path__ = [SRC]
sys.modules.setdefault("mousam", package)

from mousam import CORE_Locations  # noqa: E402
from mousam.CORE_Locations import JsonProcessor, LocationData, find_selected_city  # noqa: E402


def fixed_clock():
    """Make CORE_Locations see 21:05 in Kolkata (15:35 UTC) as the time now."""
    fixed = datetime(2026, 1, 15, 21, 5, tzinfo=ZoneInfo("Asia/Kolkata"))

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed.astimezone(tz)

    return mock.patch.object(CORE_Locations, "datetime", FixedDatetime)


class LocationFormatting(unittest.TestCase):
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
        added_cities = [LocationData.to_storage_string(self.KOCHI), "", "bad"]
        self.assertEqual(LocationData.saved_coords(added_cities), {"9.9312,76.2673"})

    def test_local_time_24h(self):
        with fixed_clock():
            self.assertEqual(LocationData.format_local_time(self.KOCHI, True), "21:05")

    def test_local_time_12h(self):
        with fixed_clock():
            self.assertEqual(LocationData.format_local_time(self.KOCHI, False), "9:05 PM")

    def test_local_time_without_a_known_timezone(self):
        with fixed_clock():
            self.assertEqual(LocationData.format_local_time({"name": "Kochi"}, True), "")
            self.assertEqual(LocationData.format_local_time({"timezone": "Not/A_Zone"}, True), "")

    def test_place_and_time(self):
        with fixed_clock():
            self.assertEqual(
                LocationData.format_place_and_time(self.KOCHI, True), "Kerala, India · 21:05"
            )


class SelectedCity(unittest.TestCase):
    CITIES = [
        {"name": "Kochi", "latitude": 9.9312, "longitude": 76.2673},
        {"name": "Delhi", "latitude": 28.6, "longitude": 77.2},
    ]

    def test_found_by_its_coords_key(self):
        self.assertEqual(find_selected_city(self.CITIES, "28.6,77.2")["name"], "Delhi")

    def test_not_found(self):
        self.assertIsNone(find_selected_city(self.CITIES, "1.0,2.0"))
        self.assertIsNone(find_selected_city([], "28.6,77.2"))

    def test_json_list_round_trip(self):
        stored = JsonProcessor.json_list_to_str(self.CITIES)
        self.assertEqual(JsonProcessor.str_list_to_json(stored), self.CITIES)


if __name__ == "__main__":
    unittest.main()
