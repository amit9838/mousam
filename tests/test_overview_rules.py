"""Tests for the overview rules and planner (src/core/overview/rules.py).

Plain Python, no GTK: each test builds a forecast by hand, as
docs/overview-rules.md describes, and checks what the rules say.

Run: python3 tests/test_overview_rules.py (also run by `meson test`).
"""

import os
import sys
import types
import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# src/ is imported as the `mousam` package, as in the installed app
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
package = types.ModuleType("mousam")
package.__path__ = [SRC]
sys.modules.setdefault("mousam", package)

from mousam.core.overview.rules import (  # noqa: E402
    AirSeries,
    AnnouncePlanner,
    AtLeast,
    Clock,
    DailyOutlook,
    HourlySeries,
    Insight,
    OverviewContext,
    RuleBook,
    SunRule,
    SunTimes,
    Units,
)

UTC = timezone.utc
H = 3600
MIN = 60
HOURS = 30  # hours of data, from the hour before now

# 15 January 2026, 10:10 UTC: the current hour is 10:00
NOW = datetime(2026, 1, 15, 10, 10, tzinfo=UTC).timestamp()


def at_hour(offset: int, now: float = NOW) -> float:
    """The start of the hour `offset` hours after the current one."""
    return (int(now) // H + offset) * H


def series(default, overrides=None, now: float = NOW) -> list:
    """HOURS values, the first one for the hour before now; `overrides` maps
    an offset from the current hour (0 = now) to a value."""
    values = [default] * HOURS
    for offset, value in (overrides or {}).items():
        values[offset + 1] = value
    return values


def context(now: float = NOW, imperial: bool = False, sun: SunTimes = None,
            daily: DailyOutlook = None, aqi: dict = None, tz=UTC, **overrides) -> OverviewContext:
    """A calm forecast, by day with sunset in 5 hours, changed by `overrides`
    (series name -> {offset: value})."""
    defaults = {
        "codes": 3,
        "temperature": 59 if imperial else 15,
        "feels_like": 59 if imperial else 15,
        "precip_probability": 0,
        "precipitation": 0,
        "windspeed": 10,
        "visibility": 20000,
        "uv": 2,
    }
    values = {name: series(default, overrides.pop(name, None), now) for name, default in defaults.items()}
    assert not overrides, f"unknown series {list(overrides)}"
    times = [at_hour(k - 1, now) for k in range(HOURS)]
    return OverviewContext(
        clock=Clock(now, tz, use_24h=True),
        units=Units(imperial),
        hourly=HourlySeries(times=times, wind_unit="mph" if imperial else "km/h", **values),
        sun=sun or SunTimes(next_sunrise=now + 20 * H, next_sunset=now + 5 * H),
        daily=daily or DailyOutlook(),
        air=AirSeries(times=times, us_aqi=series(20, aqi, now)),
    )


def insights(ctx: OverviewContext) -> dict:
    """kind -> insight, for every insight that applies."""
    return {insight.kind: insight for insight in RuleBook.default().run(ctx)}


class TestRules(unittest.TestCase):
    def assertSays(self, ctx, kind, valid_until, *parts, severity=None, icon=None):
        found = insights(ctx)
        self.assertIn(kind, found)
        insight = found[kind]
        self.assertEqual(insight.valid_until, valid_until)
        for part in parts:
            self.assertIn(part, insight.message)
        if severity is not None:
            self.assertEqual(insight.severity, severity)
        if icon is not None:
            self.assertEqual(insight.icon, icon)
        return insight

    def assertSilent(self, ctx, kind):
        self.assertNotIn(kind, insights(ctx))

    def test_calm_forecast(self):
        found = insights(context())
        self.assertEqual(list(found), ["calm"])
        self.assertEqual(found["calm"].valid_until, NOW + 5 * H)  # the window's end

    def test_storm(self):
        self.assertSays(context(codes={2: 95}), "storm", at_hour(2), "12:00",
                        severity="error", icon="weather-storm-symbolic")
        self.assertSays(context(codes={0: 95}), "storm", at_hour(1))

    def test_storm_after_the_window_is_silent(self):
        self.assertSilent(context(codes={8: 95}), "storm")

    def test_freezing(self):
        self.assertSays(context(codes={1: 66}), "freezing", at_hour(1), "11:00", severity="warning")

    def test_heavy_rain_and_snow(self):
        self.assertSays(context(precipitation={3: 8}), "heavy_precipitation", at_hour(3),
                        icon="weather-showers-symbolic")
        self.assertSays(context(codes={3: 75}), "heavy_precipitation", at_hour(3),
                        icon="weather-snow-symbolic")

    def test_extreme_feels(self):
        self.assertSays(context(feels_like={2: 41}), "extreme_feels", at_hour(2), "41°", "12:00")
        self.assertSays(context(feels_like={0: -20}), "extreme_feels", at_hour(1), "-20°")
        self.assertSilent(context(feels_like={2: 39}), "extreme_feels")

    def test_extreme_feels_imperial(self):
        self.assertSays(context(imperial=True, feels_like={2: 106}), "extreme_feels", at_hour(2), "106°")
        self.assertSilent(context(imperial=True, feels_like={2: 100}), "extreme_feels")

    def test_air_quality(self):
        self.assertSays(context(aqi={2: 160}), "air_quality", at_hour(2), "12:00")
        self.assertSays(context(aqi={0: 160}), "air_quality", at_hour(1))
        self.assertSilent(context(aqi={2: 140}), "air_quality")

    def test_uv(self):
        self.assertSays(context(uv={1: 8, 2: 9, 3: 5}), "uv", at_hour(1), "11:00", "13:00")
        self.assertSays(context(uv={0: 9, 1: 9}), "uv", at_hour(1), "12:00")

    def test_rain_starts(self):
        self.assertSays(context(precip_probability={2: 70}), "precipitation", at_hour(2),
                        "12:00", "70", icon="weather-showers-symbolic")

    def test_snow_starts(self):
        self.assertSays(context(precip_probability={2: 70}, codes={2: 71}), "precipitation",
                        at_hour(2), icon="weather-snow-symbolic")

    def test_rain_easing(self):
        self.assertSays(context(precip_probability={0: 70, 1: 70, 2: 70}), "precipitation",
                        at_hour(3), "13:00")

    def test_rain_through_the_window(self):
        wet = {k: 70 for k in range(-1, HOURS - 1)}
        self.assertSays(context(precip_probability=wet), "precipitation", at_hour(1), "15:00")

    def test_an_hour_with_no_data_is_not_dry(self):
        wet = {k: 70 for k in range(-1, HOURS - 1)}
        wet[1] = None
        self.assertSays(context(precip_probability=wet), "precipitation", at_hour(1), "15:00")

    def test_wind(self):
        self.assertSays(context(windspeed={2: 45}), "wind", at_hour(2), "45 km/h", severity="info")
        self.assertSays(context(windspeed={2: 65}), "wind", at_hour(2), severity="warning")
        self.assertSilent(context(windspeed={2: 35}), "wind")

    def test_wind_imperial(self):
        self.assertSays(context(imperial=True, windspeed={2: 30}), "wind", at_hour(2), "30 mph")
        self.assertSilent(context(imperial=True, windspeed={2: 20}), "wind")

    def test_fog(self):
        self.assertSays(context(visibility={2: 500}), "fog", at_hour(2), "12:00")
        self.assertSays(context(codes={0: 45}), "fog", at_hour(1))

    def test_fog_around_sunrise(self):
        night = SunTimes(next_sunrise=NOW + 3 * H, next_sunset=NOW + 15 * H)
        fog = self.assertSays(context(sun=night, visibility={3: 500}), "fog", at_hour(3))
        self.assertNotIn("13:00", fog.message)

    def test_temperature_swing(self):
        self.assertSays(context(temperature={3: 22}), "temperature_swing", at_hour(3), "22°", "13:00")
        self.assertSays(context(temperature={4: 8}), "temperature_swing", at_hour(4), "8°")
        self.assertSilent(context(temperature={3: 20}), "temperature_swing")

    def test_temperature_swing_imperial(self):
        self.assertSays(context(imperial=True, temperature={3: 72}), "temperature_swing", at_hour(3))
        self.assertSilent(context(imperial=True, temperature={3: 68}), "temperature_swing")

    def test_tomorrow(self):
        evening = datetime(2026, 1, 15, 19, 10, tzinfo=UTC).timestamp()
        midnight = datetime(2026, 1, 16, tzinfo=UTC).timestamp()
        night = SunTimes(next_sunrise=evening + 11 * H, next_sunset=evening + 23 * H)

        warmer = DailyOutlook(today_high=20, tomorrow_high=25, tomorrow_rain_chance=10)
        insight = self.assertSays(context(evening, sun=night, daily=warmer), "tomorrow", midnight, "25°")
        self.assertEqual(insight.heading, "Tomorrow")

        rain = DailyOutlook(today_high=20, tomorrow_high=21, tomorrow_rain_chance=60)
        self.assertSays(context(evening, sun=night, daily=rain), "tomorrow", midnight, "60",
                        icon="weather-showers-symbolic")

        same = DailyOutlook(today_high=20, tomorrow_high=22, tomorrow_rain_chance=10)
        self.assertSilent(context(evening, sun=night, daily=same), "tomorrow")

    def test_tomorrow_only_in_the_evening(self):
        warmer = DailyOutlook(today_high=20, tomorrow_high=25)
        self.assertSilent(context(daily=warmer), "tomorrow")

    def test_sunset_soon(self):
        sun = SunTimes(next_sunrise=NOW + 15 * H, next_sunset=NOW + 40 * MIN)
        insight = self.assertSays(context(sun=sun), "sun", NOW + 5 * MIN, "40",
                                  icon="daytime-sunset-symbolic")
        self.assertEqual(insight.heading, None)

    def test_sunrise_too_far(self):
        night = SunTimes(next_sunrise=NOW + 4 * H, next_sunset=NOW + 15 * H)
        self.assertSilent(context(sun=night), "sun")


class TestSunPhrase(unittest.TestCase):
    def phrase(self, minutes: float):
        ctx = context()
        return SunRule.phrase(ctx, NOW + minutes * MIN, sunset=True)

    def test_minutes_round_to_5_halves_down(self):
        self.assertIn("40 minutes", self.phrase(42.5)[0])
        self.assertIn("45 minutes", self.phrase(42.6)[0])

    def test_minutes_form_from_57_and_a_half(self):
        self.assertIn("55 minutes", self.phrase(57.5)[0])
        self.assertIn("1 hour", self.phrase(57.6)[0])

    def test_hours_round_halves_down(self):
        self.assertIn("1 hour", self.phrase(90)[0])
        self.assertIn("2 hours", self.phrase(91)[0])

    def test_hours_say_the_exact_time(self):
        self.assertIn("11:41", self.phrase(91)[0])

    def test_nothing_in_the_last_two_and_a_half_minutes(self):
        self.assertIsNone(self.phrase(2.5))
        self.assertIsNotNone(self.phrase(2.6))

    def test_stays_true(self):
        for minutes in (3, 12, 42.5, 57.5, 57.6, 90, 91, 119):
            message, valid_until = self.phrase(minutes)
            self.assertGreater(valid_until, NOW, minutes)


class TestClock(unittest.TestCase):
    def test_rounding_steps(self):
        clock = Clock(NOW - 10 * MIN, UTC, use_24h=True)  # 10:00
        cases = [
            (11 * H + 4 * MIN, "11:00"), (11 * H + 6 * MIN, "11:10"),  # up to 3 h: 10 minutes
            (14 * H + 14 * MIN, "14:00"), (14 * H + 16 * MIN, "14:30"),  # 3 to 5 h: 30 minutes
            (16 * H + 29 * MIN, "16:00"), (16 * H + 31 * MIN, "17:00"),  # beyond: the hour
        ]
        midnight = at_hour(-10)
        for seconds, expected in cases:
            self.assertEqual(clock.approx_time(midnight + seconds), expected)

    def test_rounding_past_midnight(self):
        clock = Clock(datetime(2026, 1, 15, 22, 0, tzinfo=UTC).timestamp(), UTC, use_24h=True)
        self.assertEqual(clock.approx_time(datetime(2026, 1, 15, 23, 56, tzinfo=UTC).timestamp()), "00:00")

    def test_rounds_in_local_time(self):
        # 16:50 UTC is 22:20 in India (UTC+5:30): to the hour, 22:00, not 22:30
        clock = Clock(datetime(2026, 1, 15, 10, 0, tzinfo=UTC).timestamp(), ZoneInfo("Asia/Kolkata"), True)
        self.assertEqual(clock.approx_time(datetime(2026, 1, 15, 16, 50, tzinfo=UTC).timestamp()), "22:00")

    def test_12_hour_clock(self):
        clock = Clock(NOW, UTC, use_24h=False)
        self.assertEqual(clock.time(datetime(2026, 1, 15, 13, 5, tzinfo=UTC).timestamp()), "1:05 PM")

    def test_next_hour_and_midnight(self):
        clock = Clock(NOW, UTC)
        self.assertEqual(clock.next_hour, at_hour(1))
        self.assertEqual(clock.next_midnight, datetime(2026, 1, 16, tzinfo=UTC).timestamp())


class TestRuleBook(unittest.TestCase):
    BUSY = dict(
        codes={1: 95, 2: 66, 3: 75}, precipitation={3: 9}, feels_like={2: 41},
        aqi={2: 160}, uv={1: 9}, precip_probability={0: 70, 1: 70}, windspeed={2: 70},
        visibility={2: 300}, temperature={4: 25},
    )

    def contexts(self):
        empty = OverviewContext(Clock(NOW, UTC), Units(), HourlySeries(times=[]))
        sunset = SunTimes(next_sunrise=NOW + 15 * H, next_sunset=NOW + 30 * MIN)
        return [context(), context(**self.BUSY), context(sun=sunset, **self.BUSY),
                context(imperial=True), empty]

    def test_no_rule_raises(self):
        # run() ignores a rule that fails, which would hide a broken rule:
        # call each one directly
        for ctx in self.contexts():
            for rule in RuleBook.default().rules:
                rule.evaluate(ctx)

    def test_every_insight_is_true_and_sorted(self):
        for ctx in self.contexts():
            found = RuleBook.default().run(ctx)
            self.assertTrue(found)  # calm always speaks
            self.assertTrue(all(insight.valid_until > NOW for insight in found))
            priorities = [insight.priority for insight in found]
            self.assertEqual(priorities, sorted(priorities, reverse=True))

    def test_busy_forecast(self):
        self.assertEqual(
            set(insights(context(**self.BUSY))),
            {"storm", "freezing", "heavy_precipitation", "extreme_feels", "air_quality", "uv",
             "precipitation", "wind", "fog", "temperature_swing", "calm"},
        )

    def test_unknown_series_fails_at_once(self):
        with self.assertRaises(ValueError):
            AtLeast("wind_speed", 40)


class NoSpread:
    """An rng that always lands in the middle: no random spread."""

    @staticmethod
    def uniform(a, b):
        return 0


class TestPlanner(unittest.TestCase):
    def insight(self, kind: str, severity: str = "info") -> Insight:
        return Insight(kind, kind, NOW + 10 * H, severity)

    def setUp(self):
        self.planner = AnnouncePlanner()
        self.rain = self.insight("precipitation")
        self.wind = self.insight("wind")
        self.calm = self.insight("calm")
        self.storm = self.insight("storm", "error")

    def decide(self, insights, at, showing=None):
        chosen, opened = self.planner.decide(insights, showing, at, NoSpread)
        return (chosen.kind if chosen else None), opened

    def test_interval(self):
        interval = AnnouncePlanner.interval_minutes
        self.assertEqual(interval(0, 0), 40)
        self.assertEqual(interval(0.6, 0), 25)
        self.assertEqual(interval(1.0, 0), 20)
        self.assertEqual(interval(10, 0), 5)
        self.assertEqual(interval(0, 1), 40)  # kept under the maximum

    def test_nothing_to_say(self):
        self.assertEqual(self.decide([], NOW), (None, False))

    def test_calm_only_when_alone(self):
        self.assertEqual(self.decide([self.calm], NOW), ("calm", True))
        self.assertEqual(AnnouncePlanner.worth_saying([self.rain, self.calm]), [self.rain])

    def test_first_opening_shows_the_most_severe(self):
        windy = self.insight("wind", "warning")
        self.assertEqual(self.decide([self.rain, windy, self.calm], NOW), ("wind", True))

    def test_turns(self):
        both = [self.rain, self.wind, self.calm]
        self.assertEqual(self.decide(both, NOW), ("precipitation", True))
        next_opening = self.planner.next_announce
        self.assertAlmostEqual(next_opening, NOW + 40 / 2.15 * 60)  # score 1.15
        # Between openings: the shown one, silently
        self.assertEqual(self.decide(both, NOW + MIN, "precipitation"), ("precipitation", False))
        # The shown one expired: the most important takes its place, silently
        self.assertEqual(self.decide([self.wind, self.calm], NOW + MIN, None), ("wind", False))
        # The next opening: the one never shown
        self.assertEqual(self.decide(both, next_opening), ("wind", True))
        # Then the highest priority × time since shown
        self.assertEqual(self.decide(both, self.planner.next_announce), ("precipitation", True))

    def test_escalation_opens_at_once(self):
        self.decide([self.rain], NOW)
        self.assertEqual(self.decide([self.storm, self.rain], NOW + 10 * MIN), ("storm", True))

    def test_escalation_waits_for_the_gap(self):
        self.decide([self.rain], NOW)
        busy = [self.storm, self.rain]
        self.assertEqual(self.decide(busy, NOW + 2 * MIN, "precipitation"), ("precipitation", False))
        self.assertEqual(self.planner.next_announce, NOW + 5 * MIN)
        self.assertEqual(self.decide(busy, NOW + 4 * MIN, "precipitation"), ("precipitation", False))
        self.assertEqual(self.decide(busy, NOW + 5 * MIN, "precipitation"), ("storm", True))

    def test_severe_that_comes_and_goes_counts_once(self):
        self.assertEqual(self.decide([self.storm], NOW), ("storm", True))  # next opening in 20 min
        self.assertEqual(self.decide([self.rain], NOW + 10 * MIN, None), ("precipitation", False))
        self.assertEqual(self.decide([self.storm, self.rain], NOW + 15 * MIN, "precipitation"),
                         ("precipitation", False))

    def test_note_shown_counts_as_a_turn(self):
        both = [self.rain, self.wind]
        self.decide(both, NOW)
        self.planner.note_shown("wind", NOW + MIN)
        self.assertEqual(self.decide(both, self.planner.next_announce), ("precipitation", True))

    def test_forget(self):
        self.decide([self.storm], NOW)
        self.planner.forget()
        self.assertEqual(self.decide([self.rain], NOW + MIN), ("precipitation", True))


if __name__ == "__main__":
    unittest.main()
