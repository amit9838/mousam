"""Tests for the overview rules and planner (src/core/overview/).

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

from mousam.core.overview.context import (  # noqa: E402
    AirSeries,
    Clock,
    DailyOutlook,
    HourlySeries,
    OverviewContext,
    SunTimes,
    Units,
)
from mousam.core.overview.hour_tests import AtLeast  # noqa: E402
from mousam.core.overview.insight import Insight  # noqa: E402
from mousam.core.overview.announce import NEWS, REMINDER, AnnounceMemory, decide, should_notify  # noqa: E402
from mousam.core.overview.rules import RuleBook, SunRule  # noqa: E402

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
    def assertSays(self, ctx, kind, valid_until, *parts, level=None, icon=None, topic=None):
        found = insights(ctx)
        self.assertIn(kind, found)
        insight = found[kind]
        self.assertEqual(insight.valid_until, valid_until)
        for part in parts:
            self.assertIn(part, insight.message)
        if level is not None:
            self.assertEqual(insight.level, level)
        if topic is not None:
            self.assertEqual(insight.topic, topic)
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
                        level="extreme", icon="weather-storm-symbolic", topic="storm")
        self.assertSays(context(codes={0: 95}), "storm", at_hour(1))

    def test_storm_after_the_window_is_silent(self):
        self.assertSilent(context(codes={8: 95}), "storm")

    def test_freezing(self):
        self.assertSays(context(codes={1: 66}), "freezing", at_hour(1), "11:00", level="high")

    def test_heavy_rain_and_snow(self):
        self.assertSays(context(precipitation={3: 8}), "heavy_precipitation", at_hour(3),
                        icon="weather-showers-symbolic", topic="rain")
        self.assertSays(context(codes={3: 75}), "heavy_precipitation", at_hour(3),
                        icon="weather-snow-symbolic", topic="snow")

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
                        "12:00", "70", icon="weather-showers-symbolic", level="medium", topic="rain")

    def test_snow_starts(self):
        self.assertSays(context(precip_probability={2: 70}, codes={2: 71}), "precipitation",
                        at_hour(2), icon="weather-snow-symbolic", topic="snow")

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
        self.assertSays(context(windspeed={2: 45}), "wind", at_hour(2), "45 km/h", level="medium")
        self.assertSays(context(windspeed={2: 65}), "wind", at_hour(2), level="high")
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
        self.assertIn("40 minutes", self.phrase(42.5).message)
        self.assertIn("45 minutes", self.phrase(42.6).message)

    def test_minutes_form_from_57_and_a_half(self):
        self.assertIn("55 minutes", self.phrase(57.5).message)
        self.assertIn("1 hour", self.phrase(57.6).message)

    def test_hours_round_halves_down(self):
        self.assertIn("1 hour", self.phrase(90).message)
        self.assertIn("2 hours", self.phrase(91).message)

    def test_hours_say_the_exact_time(self):
        self.assertIn("11:41", self.phrase(91).message)

    def test_nothing_in_the_last_two_and_a_half_minutes(self):
        self.assertIsNone(self.phrase(2.5))
        self.assertIsNotNone(self.phrase(2.6))

    def test_stays_true(self):
        for minutes in (3, 12, 42.5, 57.5, 57.6, 90, 91, 119):
            self.assertGreater(self.phrase(minutes).valid_until, NOW, minutes)


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
        # Every rule speaks; the wind (an hour after the storm) is combined into it
        each = {rule.kind for rule in RuleBook.default().rules if rule.evaluate(context(**self.BUSY))}
        self.assertEqual(
            each,
            {"storm", "freezing", "heavy_precipitation", "extreme_feels", "air_quality", "uv",
             "precipitation", "wind", "fog", "temperature_swing", "calm"},
        )
        found = insights(context(**self.BUSY))
        self.assertNotIn("wind", found)
        self.assertEqual(found["storm"].key, "storm_wind.later")

    def test_unknown_series_fails_at_once(self):
        with self.assertRaises(ValueError):
            AtLeast("wind_speed", 40)


class TestIdentity(unittest.TestCase):
    """Topics, levels and fingerprints: the same insight while time passes,
    another one when the forecast changes."""

    def one(self, kind, now=NOW, **forecast):
        return insights(context(now, **forecast))[kind]

    def test_topics_and_levels(self):
        ctx = context(**TestRuleBook.BUSY)
        busy = {rule.kind: rule.evaluate(ctx) for rule in RuleBook.default().rules}
        expected = {
            "storm": ("storm", "extreme"), "freezing": ("freezing", "high"),
            "heavy_precipitation": ("snow", "high"), "extreme_feels": ("feels_like", "high"),
            "air_quality": ("air", "high"), "uv": ("uv", "high"), "precipitation": ("rain", "medium"),
            "wind": ("wind", "high"), "fog": ("fog", "medium"),
            "temperature_swing": ("temperature", "low"), "calm": ("calm", "calm"),
        }
        for kind, (topic, level) in expected.items():
            self.assertEqual((busy[kind].topic, busy[kind].level), (topic, level), kind)

    def test_later_is_about_its_hour_and_now_about_nothing(self):
        self.assertEqual(self.one("storm", codes={2: 95}).about, at_hour(2))
        self.assertIsNone(self.one("storm", codes={0: 95}).about)
        self.assertEqual(self.one("storm", codes={2: 95}).key, "storm.later")

    def test_same_while_time_passes(self):
        rain = dict(precip_probability={3: 70})
        self.assertEqual(self.one("precipitation", **rain).fingerprint,
                         self.one("precipitation", NOW + 20 * MIN, **rain).fingerprint)
        sun = SunTimes(next_sunrise=NOW + 15 * H, next_sunset=NOW + 40 * MIN)
        first = insights(context(sun=sun))["sun"]
        later = insights(context(NOW + 10 * MIN, sun=sun))["sun"]
        self.assertNotEqual(first.message, later.message)  # 40, then 30 minutes
        self.assertEqual(first.fingerprint, later.fingerprint)

    def test_changes_with_the_forecast(self):
        def rain_at(hour):
            return self.one("precipitation", precip_probability={hour: 70}).fingerprint
        self.assertNotEqual(rain_at(2), rain_at(4))
        self.assertNotEqual(self.one("wind", windspeed={2: 45}).fingerprint,
                            self.one("wind", windspeed={2: 65}).fingerprint)  # medium, then high



class TestCombine(unittest.TestCase):
    """Two things at once: one sentence for a known pair, one folded into
    another, or each on its own (the next turn)."""

    def test_storm_and_wind_become_one_sentence(self):
        found = insights(context(codes={2: 95}, windspeed={2: 45}))
        self.assertNotIn("wind", found)
        storm = found["storm"]
        self.assertEqual(storm.key, "storm_wind.later")
        self.assertIn("45 km/h", storm.message)
        self.assertIn("12:00", storm.message)
        self.assertEqual((storm.level, storm.topics, len(storm.parts)), ("extreme", ("storm", "wind"), 2))

    def test_from_the_earlier_time_true_until_the_earlier_ends(self):
        storm = insights(context(codes={3: 95}, windspeed={2: 45}))["storm"]
        self.assertIn("12:00", storm.message)  # the wind's hour
        self.assertEqual(storm.valid_until, at_hour(2))

    def test_both_now(self):
        storm = insights(context(codes={0: 95}, windspeed={0: 45}))["storm"]
        self.assertEqual(storm.key, "storm_wind.now")
        self.assertEqual(storm.valid_until, at_hour(1))

    def test_not_combined_when_far_apart_or_one_now(self):
        for forecast in (dict(codes={1: 95}, windspeed={3: 45}), dict(codes={0: 95}, windspeed={2: 45})):
            found = insights(context(**forecast))
            self.assertEqual(found["storm"].key.split(".")[0], "storm", forecast)
            self.assertIn("wind", found, forecast)

    def test_each_insight_used_once(self):
        found = insights(context(codes={2: 95}, precipitation={2: 9}, windspeed={2: 45}))
        self.assertEqual(found["storm"].key, "storm_wind.later")
        self.assertEqual(found["heavy_precipitation"].key, "heavy_rain.later")  # the next turn

    def test_rain_is_folded_into_a_storm(self):
        found = insights(context(codes={2: 95}, precip_probability={2: 70}))
        self.assertNotIn("precipitation", found)
        storm = found["storm"]
        self.assertEqual(storm.key, "storm.later")
        self.assertEqual(len(storm.parts), 2)
        self.assertEqual(storm.covers, ("storm", "rain"))
        self.assertEqual(storm.topics, ("storm",))

    def test_rain_alone_stays_rain(self):
        self.assertEqual(insights(context(precip_probability={2: 70}))["precipitation"].key, "rain.start")

    def test_rain_and_wind(self):
        rain = insights(context(precip_probability={2: 70}, windspeed={2: 65}))["precipitation"]
        self.assertEqual((rain.key, rain.topic, rain.level), ("rain_wind.later", "rain", "high"))

    def test_snow_and_wind(self):
        snow = insights(context(precip_probability={2: 70}, codes={2: 71}, windspeed={2: 45}))["precipitation"]
        self.assertEqual((snow.key, snow.topic), ("snow_wind.later", "snow"))

    def test_rain_easing_now_and_wind_later_are_not_together(self):
        found = insights(context(precip_probability={0: 70, 1: 70}, windspeed={2: 45}))
        self.assertEqual(found["precipitation"].key, "rain.easing")
        self.assertIn("wind", found)

    def test_imperial_speed(self):
        storm = insights(context(imperial=True, codes={2: 95}, windspeed={2: 30}))["storm"]
        self.assertIn("30 mph", storm.message)


class TestAnnounce(unittest.TestCase):
    """decide(): news at once, reminders that wait longer, calm and low once."""

    def insight(self, kind: str, level: str = "medium", about=None, valid_hours: float = 24) -> Insight:
        return Insight(kind, kind, NOW + valid_hours * H, level, topic=kind, key=kind, about=about)

    def setUp(self):
        self.memory = AnnounceMemory()
        # Rain 5 hours away, so it is a different moment from the others
        self.rain = self.insight("precipitation", about=at_hour(5))
        self.wind = self.insight("wind", "high")
        self.calm = self.insight("calm", "calm")
        self.storm = self.insight("storm", "extreme")
        self.sun = self.insight("sun", "low")

    def decide(self, insights, at, showing=None):
        return decide(insights, self.memory, showing, at)

    def opened(self, insights, at, showing=None):
        """(kind, reason) of an opening, or (kind, None) for a silent update."""
        decision = self.decide(insights, at, showing)
        return (decision.insight.kind if decision.insight else None), decision.reason

    def test_nothing_to_say(self):
        decision = self.decide([], NOW)
        self.assertIsNone(decision.insight)
        self.assertIsNone(decision.wake_at)

    def test_first_run_opens_the_most_urgent_as_news(self):
        self.assertEqual(self.opened([self.rain, self.wind, self.calm], NOW), ("wind", NEWS))

    def test_unchanged_reminders_wait_longer_each_time(self):
        opened = [0]
        at = NOW
        self.decide([self.wind], at)
        for _ in range(5):
            at = self.decide([self.wind], at).wake_at
            self.assertEqual(self.opened([self.wind], at), ("wind", REMINDER))
            opened.append(round((at - NOW) / MIN))
        self.assertEqual(opened, [0, 60, 180, 420, 660, 900])  # high: 60, 120, 240, then 240

    def test_between_reminders_only_silent_updates(self):
        self.decide([self.wind], NOW)
        self.assertEqual(self.opened([self.wind], NOW + 30 * MIN, "wind"), ("wind", None))

    def test_changed_fingerprint_is_news_and_starts_over(self):
        at_4 = self.insight("precipitation", about=at_hour(4))
        at_7 = self.insight("precipitation", about=at_hour(7))
        self.decide([at_4], NOW)
        self.assertEqual(self.opened([at_7], NOW + 10 * MIN), ("precipitation", NEWS))
        self.assertEqual(self.memory.times_said(at_7), 1)

    def test_a_refresh_with_the_same_forecast_opens_nothing(self):
        self.decide([self.rain, self.wind], NOW)
        self.assertEqual(self.opened([self.rain, self.wind], NOW + 6 * MIN, "wind"),
                         ("precipitation", NEWS))  # rain was never said
        again = [self.insight("precipitation", about=at_hour(5)), self.insight("wind", "high")]  # rebuilt, equal
        self.assertEqual(self.opened(again, NOW + 12 * MIN, "precipitation"), ("precipitation", None))

    def test_news_waits_for_the_gap(self):
        self.decide([self.rain], NOW)
        busy = [self.storm, self.rain]
        decision = self.decide(busy, NOW + 2 * MIN, "precipitation")
        self.assertIsNone(decision.reason)
        self.assertEqual(decision.wake_at, NOW + 5 * MIN)
        self.assertEqual(self.opened(busy, NOW + 5 * MIN, "precipitation"), ("storm", NEWS))

    def test_news_before_reminders(self):
        self.decide([self.storm], NOW)
        later = NOW + 40 * MIN  # the storm's first reminder (30 min) is due too
        self.assertEqual(self.opened([self.storm, self.rain], later), ("precipitation", NEWS))
        self.assertEqual(self.opened([self.storm, self.rain], later + 5 * MIN), ("storm", REMINDER))

    def test_a_storm_that_comes_and_goes_counts_once(self):
        self.decide([self.storm], NOW)
        self.decide([self.rain], NOW + 10 * MIN)
        self.assertEqual(self.opened([self.storm, self.rain], NOW + 20 * MIN, "precipitation"),
                         ("precipitation", None))

    def test_forgotten_hours_after_it_was_last_true(self):
        self.decide([self.storm], NOW)
        self.decide([self.rain], NOW + 1 * H)
        self.decide([self.rain], NOW + 6 * H)  # the storm hasn't been true for 5 h
        self.assertTrue(self.memory.is_new(self.storm))

    def test_calm_and_low_are_said_once(self):
        self.assertEqual(self.opened([self.calm], NOW), ("calm", NEWS))
        self.assertEqual(self.opened([self.calm], NOW + 10 * H, "calm"), ("calm", None))
        self.decide([self.sun, self.calm], NOW + 11 * H)
        self.assertEqual(self.opened([self.sun, self.calm], NOW + 20 * H, "sun"), ("sun", None))

    def test_calm_after_the_rain_is_silent(self):
        self.decide([self.calm], NOW)
        self.decide([self.rain, self.calm], NOW + 10 * MIN)
        self.assertEqual(self.opened([self.calm], NOW + 3 * H), ("calm", None))

    def test_silent_updates_keep_the_shown_one(self):
        self.decide([self.rain, self.wind], NOW)
        self.decide([self.rain, self.wind], NOW + 6 * MIN)
        self.assertEqual(self.opened([self.rain, self.wind], NOW + 7 * MIN, "precipitation"),
                         ("precipitation", None))
        # The shown one stopped being true: the most important takes its place
        self.assertEqual(self.opened([self.wind], NOW + 8 * MIN, "precipitation"), ("wind", None))

    def test_wake_before_anything_stops_being_true(self):
        short = self.insight("fog", valid_hours=0.5)
        decision = self.decide([self.wind, short], NOW)
        self.assertLessEqual(decision.wake_at, short.valid_until)

    def test_topics_are_the_insights_taking_turns(self):
        self.assertEqual(self.decide([self.rain, self.calm], NOW).topics, {"precipitation"})
        self.assertEqual(self.decide([self.calm], NOW + 10 * MIN).topics, {"calm"})

    def test_clicking_counts_as_announcing(self):
        self.decide([self.wind], NOW)
        self.memory.note_said(self.wind, NOW + 50 * MIN)
        self.assertEqual(self.opened([self.wind], NOW + 70 * MIN), ("wind", None))  # due at 170

    def test_the_others_get_the_next_turn(self):
        decision = self.decide([self.storm, self.wind], NOW)
        self.assertEqual(decision.insight.kind, "storm")
        self.assertEqual([i.kind for i in decision.waiting], ["wind"])
        self.assertEqual(decision.wake_at, NOW + 5 * MIN)  # after the gap
        self.assertEqual(self.opened([self.storm, self.wind], decision.wake_at, "storm"), ("wind", NEWS))

    def combined(self, storm, wind):
        return Insight("storm", "both", NOW + 24 * H, "extreme", topic="storm", key="storm_wind.now",
                       parts=storm.parts + wind.parts, topics=("storm", "wind"))

    def test_a_combined_insight_counts_as_saying_each_part(self):
        both = self.combined(self.storm, self.wind)
        self.assertEqual(self.opened([both], NOW), ("storm", NEWS))
        # The wind drops: the storm alone is not news, and is due at its reminder
        self.assertEqual(self.opened([self.storm], NOW + 10 * MIN, "storm"), ("storm", None))
        self.assertEqual(self.memory.due_at(self.storm), NOW + 30 * MIN)

    def test_a_new_part_makes_it_news(self):
        self.decide([self.storm], NOW)
        both = self.combined(self.storm, self.wind)
        self.assertEqual(self.opened([both], NOW + 10 * MIN, "storm"), ("storm", NEWS))

    def test_topics_include_what_is_folded_in(self):
        folded = Insight("storm", "storm", NOW + H, "extreme", topic="storm", covers=("storm", "rain"))
        self.assertEqual(self.decide([folded], NOW).topics, {"storm", "rain"})

    def test_should_notify(self):
        self.assertTrue(should_notify(NEWS, self.rain))  # medium
        self.assertTrue(should_notify(NEWS, self.storm))
        self.assertFalse(should_notify(NEWS, self.sun))  # low
        self.assertFalse(should_notify(NEWS, self.calm))
        self.assertTrue(should_notify(REMINDER, self.storm))
        self.assertFalse(should_notify(REMINDER, self.wind))  # high
        self.assertFalse(should_notify(None, self.storm))

    def test_tomorrow_is_notified_as_news_only(self):
        tomorrow = self.insight("tomorrow", "low")
        self.assertTrue(should_notify(NEWS, tomorrow))
        self.assertFalse(should_notify(REMINDER, tomorrow))
        self.assertEqual(self.opened([tomorrow, self.calm], NOW), ("tomorrow", NEWS))
        self.assertEqual(self.opened([tomorrow, self.calm], NOW + 3 * H, "tomorrow"), ("tomorrow", None))


if __name__ == "__main__":
    unittest.main()
