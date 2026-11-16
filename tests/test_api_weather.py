"""Tests for the forecast API's URL helpers (src/API_Weather.py).

API_Weather still imports requests, GSettings and (through CORE_Helpers) GTK,
so tests/stubs.py stands in for them until the API layer takes every input as
an argument (docs/architecture-plan.md, phase 3).

Run: python3 tests/test_api_weather.py (also run by `meson test`).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stubs  # noqa: E402

stubs.install()

from mousam.API_Weather import unit_params  # noqa: E402


class UnitParams(unittest.TestCase):
    def test_metric_is_the_api_default(self):
        self.assertEqual(unit_params("metric"), "")

    def test_imperial(self):
        self.assertEqual(
            unit_params("imperial"), "&temperature_unit=fahrenheit&wind_speed_unit=mph"
        )


if __name__ == "__main__":
    unittest.main()
