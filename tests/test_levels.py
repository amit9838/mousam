"""Tests for the level classifiers and unit conversions (src/CORE_Levels.py,
src/CORE_Units.py).

Plain Python, no GTK. Run: python3 tests/test_levels.py (also run by `meson test`).
"""

import os
import sys
import types
import unittest

# src/ is imported as the `mousam` package, as in the installed app
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
package = types.ModuleType("mousam")
package.__path__ = [SRC]
sys.modules.setdefault("mousam", package)

from mousam import CORE_Levels as levels  # noqa: E402
from mousam.CORE_Units import transform_visibility_data  # noqa: E402
from mousam.configs import HPA_TO_INHG  # noqa: E402


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
                self.assertEqual(levels.classify_aqi(aqi), word)

    def test_us_aqi_colour(self):
        cases = [(50, "success"), (51, "warning"), (150, "warning"), (151, "error"), (400, "error")]
        for aqi, css_class in cases:
            with self.subTest(aqi=aqi):
                self.assertEqual(levels.aqi_level_class(aqi), css_class)

    def test_us_aqi_advice_differs_per_band(self):
        advice = [levels.aqi_advice(aqi) for aqi in (50, 100, 150, 200, 300, 301)]
        self.assertEqual(len(set(advice)), 6)
        self.assertEqual(levels.aqi_advice(0), levels.aqi_advice(50))

    def test_eu_aqi_bands(self):
        cases = [
            (20, "Good"), (21, "Fair"), (40, "Fair"), (41, "Moderate"),
            (60, "Moderate"), (61, "Poor"), (80, "Poor"), (81, "Very Poor"),
            (100, "Very Poor"), (101, "Extremely Poor"),
        ]
        for aqi, word in cases:
            with self.subTest(aqi=aqi):
                self.assertEqual(levels.classify_eu_aqi(aqi), word)

    def test_pollutant_against_who_limits(self):
        # pm2_5: up to 15 good, up to 35 high, above that very high
        self.assertEqual(levels.classify_pollutant("pm2_5", 15), ("Good", "success"))
        self.assertEqual(levels.classify_pollutant("pm2_5", 16), ("High", "warning"))
        self.assertEqual(levels.classify_pollutant("pm2_5", 36), ("Very High", "error"))
        self.assertEqual(levels.classify_pollutant("pm2_5", 500), ("Very High", "error"))

    def test_unknown_pollutant_is_very_high(self):
        self.assertEqual(levels.classify_pollutant("unknown", 0), ("Very High", "error"))

    def test_pollen(self):
        cases = [
            (15, ("Low", "success")), (16, ("Moderate", "warning")),
            (90, ("Moderate", "warning")), (91, ("High", "error")),
            (500, ("High", "error")), (501, ("Very High", "error")),
        ]
        for value, level in cases:
            with self.subTest(value=value):
                self.assertEqual(levels.classify_pollen(value), level)

    def test_main_pollutant_is_furthest_above_its_limit(self):
        # pm2_5 at 30 is twice its limit (15); pm10 at 45 is just at its own
        values = {"pm2_5": 30, "pm10": 45, "ozone": None}
        self.assertEqual(levels.main_pollutant(values), "pm2_5")

    def test_main_pollutant_without_values(self):
        self.assertIsNone(levels.main_pollutant({}))
        self.assertIsNone(levels.main_pollutant({"pm2_5": None, "unknown": 5}))


class WeatherLevels(unittest.TestCase):
    def test_uv_index(self):
        cases = [
            (0, "Low"), (2, "Low"), (3, "Moderate"), (5, "Moderate"),
            (6, "High"), (7, "High"), (8, "Very High"), (10, "Very High"),
            (11, "Extreme"),
        ]
        for uv, word in cases:
            with self.subTest(uv=uv):
                self.assertEqual(levels.classify_uv_index(uv), word)

    def test_humidity(self):
        cases = [(49, "Low"), (50, "Moderate"), (80, "Moderate"), (81, "High")]
        for humidity, word in cases:
            with self.subTest(humidity=humidity):
                self.assertEqual(levels.classify_humidity_level(humidity), word)

    def test_wind_speed(self):
        cases = [
            (0, "Calm"), (1, "Calm"), (2, "Light"), (25, "Light"),
            (26, "Moderate"), (40, "Moderate"), (41, "Strong"), (60, "Strong"),
            (61, "Extreme"),
        ]
        for speed, word in cases:
            with self.subTest(speed=speed):
                self.assertEqual(levels.classify_wind_speed_level(speed), word)

    def test_pressure_metric(self):
        cases = [(999, "Low"), (1000, "Normal"), (1026, "Normal"), (1027, "High")]
        for pressure, word in cases:
            with self.subTest(pressure=pressure):
                self.assertEqual(levels.classify_presssure_level(pressure, "metric"), word)

    def test_pressure_imperial_uses_inhg(self):
        def level(hpa):
            return levels.classify_presssure_level(hpa * HPA_TO_INHG, "imperial")

        self.assertEqual(level(999), "Low")
        self.assertEqual(level(1013), "Normal")
        self.assertEqual(level(1030), "High")

    def test_rain_intensity(self):
        cases = [(0.1, 1), (2.5, 2), (7.6, 3), (49, 3), (50, 4)]
        for amount_mm, level in cases:
            with self.subTest(amount_mm=amount_mm):
                self.assertEqual(levels.classify_rain_intensity(amount_mm), level)

    def test_snow_intensity(self):
        cases = [(0.1, 1), (0.5, 2), (2.5, 3), (5, 4)]
        for amount_cm, level in cases:
            with self.subTest(amount_cm=amount_cm):
                self.assertEqual(levels.classify_snow_intensity(amount_cm), level)


class Units(unittest.TestCase):
    def test_visibility_metric_in_km(self):
        self.assertEqual(transform_visibility_data("m", 24000, "metric"), {"unit": "km", "data": 24.0})

    def test_visibility_imperial_in_miles(self):
        result = transform_visibility_data("m", 1609.34, "imperial")
        self.assertEqual(result["unit"], "miles")
        self.assertAlmostEqual(result["data"], 1.0)

    def test_visibility_in_other_units_is_kept(self):
        self.assertEqual(transform_visibility_data("ft", 500, "imperial"), {"unit": "ft", "data": 500})


if __name__ == "__main__":
    unittest.main()
