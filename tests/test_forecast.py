"""Tests for the forecast decisions (src/CORE_Forecast.py).

Plain Python, no GTK. Run: python3 tests/test_forecast.py (also run by `meson test`).
"""

import os
import sys
import types
import unittest
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

# src/ is imported as the `mousam` package, as in the installed app
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
package = types.ModuleType("mousam")
package.__path__ = [SRC]
sys.modules.setdefault("mousam", package)

from mousam.CORE_Forecast import (  # noqa: E402
    hourly_precipitation,
    is_snow_code,
    nearest_hour_index,
    rain_drop_count,
    today_high_low,
    today_sun_times,
)

H = 3600
NOON = datetime(2026, 1, 15, 12, tzinfo=timezone.utc).timestamp()


class NearestHour(unittest.TestCase):
    TIMES = [NOON - H, NOON, NOON + H]

    def test_hour_within_half_an_hour(self):
        self.assertEqual(nearest_hour_index(self.TIMES, NOON + 20 * 60), 1)
        self.assertEqual(nearest_hour_index(self.TIMES, NOON - 20 * 60), 1)

    def test_first_match_wins(self):
        # Exactly between two hours, neither is within half an hour
        self.assertEqual(nearest_hour_index(self.TIMES, NOON + 30 * 60), 0)

    def test_no_match_is_the_first_hour(self):
        self.assertEqual(nearest_hour_index(self.TIMES, NOON + 10 * H), 0)
        self.assertEqual(nearest_hour_index([], NOON), 0)


class Drops(unittest.TestCase):
    def test_drop_count(self):
        cases = [(10, 1), (49, 1), (50, 2), (79, 2), (80, 3), (89, 3), (90, 4), (100, 4)]
        for chance, count in cases:
            with self.subTest(chance=chance):
                self.assertEqual(rain_drop_count(chance), count)

    def test_snow_codes(self):
        for code in (71, "73", 75, 77, 85, "86"):
            with self.subTest(code=code):
                self.assertTrue(is_snow_code(code))
        for code in (0, "61", 95, None, "61n", ""):
            with self.subTest(code=code):
                self.assertFalse(is_snow_code(code))


class HourlyPrecipitation(unittest.TestCase):
    def test_dry_hour(self):
        self.assertIsNone(hourly_precipitation(0, 0))
        self.assertIsNone(hourly_precipitation(0.05, 0.05))

    def test_rain(self):
        self.assertEqual(hourly_precipitation(0, 2.0), ("rain", 2.0))

    def test_snow(self):
        self.assertEqual(hourly_precipitation(1.0, 0), ("snow", 1.0))

    def test_more_snow_water_than_rain_is_snow(self):
        # 1 cm of snow holds about 1.4 mm of water
        self.assertEqual(hourly_precipitation(1.0, 1.0), ("snow", 1.0))
        self.assertEqual(hourly_precipitation(1.0, 2.0), ("rain", 2.0))


class TodayHighLow(unittest.TestCase):
    MIDNIGHTS = [
        datetime(2026, 1, d, tzinfo=timezone.utc).timestamp() for d in (14, 15, 16)
    ]

    def test_today(self):
        result = today_high_low(self.MIDNIGHTS, [20, 25, 30], [5, 10, 15], date(2026, 1, 15))
        self.assertEqual(result, (25, 10))

    def test_missing_value(self):
        result = today_high_low(self.MIDNIGHTS, [20, None, 30], [5, 10, 15], date(2026, 1, 15))
        self.assertIsNone(result)

    def test_day_not_in_the_data(self):
        result = today_high_low(self.MIDNIGHTS, [20, 25, 30], [5, 10, 15], date(2026, 2, 1))
        self.assertIsNone(result)


class TodaySunTimes(unittest.TestCase):
    # Daily data: each day is its midnight in UTC
    MIDNIGHTS = [datetime(2026, 1, d, tzinfo=timezone.utc).timestamp() for d in (14, 15, 16)]
    SUNRISES = [114, 115, 116]
    SUNSETS = [214, 215, 216]

    def sun_times(self, zone, local_now):
        tz = ZoneInfo(zone)
        now = local_now.replace(tzinfo=tz).timestamp()
        return today_sun_times(self.MIDNIGHTS, self.SUNRISES, self.SUNSETS, tz, now)

    def test_east_of_utc(self):
        self.assertEqual(self.sun_times("Asia/Kolkata", datetime(2026, 1, 15, 12)), (115, 215))

    def test_utc(self):
        self.assertEqual(self.sun_times("UTC", datetime(2026, 1, 15, 12)), (115, 215))

    def test_day_not_in_the_data(self):
        self.assertEqual(self.sun_times("UTC", datetime(2026, 3, 1, 12)), (0, 0))


if __name__ == "__main__":
    unittest.main()
