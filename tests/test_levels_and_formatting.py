"""Tests for today's level classifiers, unit helpers and location formatting.

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
from mousam.CORE_weatherData import WeatherDataManager  # noqa: E402
from mousam.configs import HPA_TO_INHG  # noqa: E402
from mousam.windowLocations import LocationData  # noqa: E402

W = WeatherDataManager


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


class AirQualityLevels(unittest.TestCase):
    def test_us_aqi_bands(self):
        cases = [
            (0, "Good"), (50, "Good"),
            (51, "Moderate"), (100, "Moderate"),
            (101, "Poor"), (150, "Poor"),
            (151, "Unhealthy"), (200, "Unhealthy"),
            (201, "Severe"), (300, "Severe"),
            (301, "Hazardous"),
        ]
        for aqi, word in cases:
            with self.subTest(aqi=aqi):
                self.assertEqual(W.classify_aqi(aqi), word)

    def test_us_aqi_colour(self):
        cases = [(50, "success"), (51, "warning"), (150, "warning"), (151, "error"), (400, "error")]
        for aqi, css_class in cases:
            with self.subTest(aqi=aqi):
                self.assertEqual(W.aqi_level_class(aqi), css_class)

    def test_us_aqi_advice_differs_per_band(self):
        advice = [W.aqi_advice(aqi) for aqi in (50, 100, 150, 200, 300, 301)]
        self.assertEqual(len(set(advice)), 6)
        self.assertEqual(W.aqi_advice(0), W.aqi_advice(50))

    def test_eu_aqi_bands(self):
        cases = [
            (20, "Good"), (21, "Fair"), (40, "Fair"), (41, "Moderate"),
            (60, "Moderate"), (61, "Poor"), (80, "Poor"), (81, "Very Poor"),
            (100, "Very Poor"), (101, "Extremely Poor"),
        ]
        for aqi, word in cases:
            with self.subTest(aqi=aqi):
                self.assertEqual(W.classify_eu_aqi(aqi), word)

    def test_pollutant_against_who_limits(self):
        # pm2_5: up to 15 good, up to 35 high, above that very high
        self.assertEqual(W.classify_pollutant("pm2_5", 15), ("Good", "success"))
        self.assertEqual(W.classify_pollutant("pm2_5", 16), ("High", "warning"))
        self.assertEqual(W.classify_pollutant("pm2_5", 36), ("Very High", "error"))
        self.assertEqual(W.classify_pollutant("pm2_5", 500), ("Very High", "error"))

    def test_unknown_pollutant_is_very_high(self):
        self.assertEqual(W.classify_pollutant("unknown", 0), ("Very High", "error"))

    def test_pollen(self):
        cases = [
            (15, ("Low", "success")), (16, ("Moderate", "warning")),
            (90, ("Moderate", "warning")), (91, ("High", "error")),
            (500, ("High", "error")), (501, ("Very High", "error")),
        ]
        for value, level in cases:
            with self.subTest(value=value):
                self.assertEqual(W.classify_pollen(value), level)

    def test_main_pollutant_is_furthest_above_its_limit(self):
        # pm2_5 at 30 is twice its limit (15); pm10 at 45 is just at its own
        values = {"pm2_5": 30, "pm10": 45, "ozone": None}
        self.assertEqual(W.main_pollutant(values), "pm2_5")

    def test_main_pollutant_without_values(self):
        self.assertIsNone(W.main_pollutant({}))
        self.assertIsNone(W.main_pollutant({"pm2_5": None, "unknown": 5}))


class WeatherLevels(SettingsTestCase):
    def test_uv_index(self):
        cases = [
            (0, "Low"), (2, "Low"), (3, "Moderate"), (5, "Moderate"),
            (6, "High"), (7, "High"), (8, "Very High"), (10, "Very High"),
            (11, "Extreme"),
        ]
        for uv, word in cases:
            with self.subTest(uv=uv):
                self.assertEqual(W.classify_uv_index(uv), word)

    def test_humidity(self):
        cases = [(49, "Low"), (50, "Moderate"), (80, "Moderate"), (81, "High")]
        for humidity, word in cases:
            with self.subTest(humidity=humidity):
                self.assertEqual(W.classify_humidity_level(humidity), word)

    def test_wind_speed(self):
        cases = [
            (0, "Calm"), (1, "Calm"), (2, "Light"), (25, "Light"),
            (26, "Moderate"), (40, "Moderate"), (41, "Strong"), (60, "Strong"),
            (61, "Extreme"),
        ]
        for speed, word in cases:
            with self.subTest(speed=speed):
                self.assertEqual(W.classify_wind_speed_level(speed), word)

    def test_pressure_metric(self):
        cases = [(999, "Low"), (1000, "Normal"), (1026, "Normal"), (1027, "High")]
        for pressure, word in cases:
            with self.subTest(pressure=pressure):
                self.assertEqual(W.classify_presssure_level(pressure), word)

    def test_pressure_imperial_uses_inhg(self):
        stubs.settings.unit = "imperial"
        self.assertEqual(W.classify_presssure_level(999 * HPA_TO_INHG), "Low")
        self.assertEqual(W.classify_presssure_level(1013 * HPA_TO_INHG), "Normal")
        self.assertEqual(W.classify_presssure_level(1030 * HPA_TO_INHG), "High")

    def test_rain_intensity(self):
        cases = [(0.1, 1), (2.5, 2), (7.6, 3), (49, 3), (50, 4)]
        for amount_mm, level in cases:
            with self.subTest(amount_mm=amount_mm):
                self.assertEqual(W.classify_rain_intensity(amount_mm), level)

    def test_snow_intensity(self):
        cases = [(0.1, 1), (0.5, 2), (2.5, 3), (5, 4)]
        for amount_cm, level in cases:
            with self.subTest(amount_cm=amount_cm):
                self.assertEqual(W.classify_snow_intensity(amount_cm), level)


class Units(SettingsTestCase):
    def test_visibility_metric_in_km(self):
        self.assertEqual(W.transform_visibility_data("m", 24000), {"unit": "km", "data": 24.0})

    def test_visibility_imperial_in_miles(self):
        stubs.settings.unit = "imperial"
        result = W.transform_visibility_data("m", 1609.34)
        self.assertEqual(result["unit"], "miles")
        self.assertAlmostEqual(result["data"], 1.0)

    def test_visibility_in_other_units_is_kept(self):
        self.assertEqual(W.transform_visibility_data("ft", 500), {"unit": "ft", "data": 500})

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
