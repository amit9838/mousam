"""Rules for the overview: each looks at the forecast and may offer an Insight.

Source of truth: docs/overview-rules.md. Change that file first, then this
one and the numbers in config.py to match.

Built by composition, with no GTK, so everything can be tested on made-up data:

- OverviewContext (context.py): the forecast as the rules see it.
- HourTest (hour_tests.py): a yes/no question about one hour (HasCode,
  AtLeast, Below, AnyOf), combined to describe what a rule looks for.
- Insight (insight.py): what a rule returns.
- Phrasing: the "now" and "later" message keys of a rule, rendered with the
  right valid_until. The wordings, several per message, are in
  core/overview/messages.py; the context's MessageBook picks one.
- Rule: one rule, `evaluate(ctx) -> Optional[Insight]`.
- RuleBook: the rules in use; `run(ctx)` returns every insight that applies
  and is still true, most important first, with the ones that happen together
  turned (TURNING_STORMY, TURNING_HEAVY), folded (FOLDS) or combined
  (COMBINATIONS) into one.
Which of those insights to show, and when the overview opens by itself, is
up to announce.py; the engine (state/overview_engine.py) runs the timers.
"""

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from gettext import pgettext as C_
from typing import Dict, List, Optional, Sequence

from ...config import (
    COLD_FEELS_LIKE_C,
    EXTREME_WIND_KMH,
    FOG_SUNRISE_MINUTES,
    FOG_VISIBILITY_M,
    HEAT_FEELS_LIKE_C,
    HEAVY_PRECIPITATION_MM,
    OVERVIEW_COMBINE_MINUTES,
    OVERVIEW_RELATIVE_TOLERANCE,
    OVERVIEW_TOMORROW_FROM_HOUR,
    RAIN_LIKELY_PROBABILITY,
    STRONG_WIND_KMH,
    SUN_ROUND_MINUTES,
    SUNRISE_SOON_MINUTES,
    SUNSET_SOON_MINUTES,
    TEMPERATURE_SWING_C,
    TOMORROW_DIFFERENCE_C,
    UNHEALTHY_US_AQI,
    VERY_HIGH_UV,
)
from ..log import get_logger
from .context import HOUR, MINUTE, OverviewContext, Units, hours_between, value_at
from .hour_tests import (
    FOG_CODES,
    FREEZING_CODES,
    HEAVY_RAIN_CODES,
    HEAVY_SNOW_CODES,
    IS_DRY,
    IS_SNOW,
    IS_WET,
    STORM_CODES,
    AnyOf,
    AtLeast,
    Below,
    HasCode,
    HourTest,
)
from .insight import LEVELS, Insight

logger = get_logger("overview")

# Symbolic icons shown before a message
ICON_STORM = "weather-storm-symbolic"
ICON_RAIN = "weather-showers-symbolic"
ICON_SNOW = "weather-snow-symbolic"
ICON_SUN = "weather-clear-symbolic"
ICON_WIND = "weather-windy-symbolic"
ICON_FOG = "weather-fog-symbolic"
ICON_SUNSET = "daytime-sunset-symbolic"
ICON_SUNRISE = "daytime-sunrise-symbolic"


def degrees(value: float) -> str:
    return "{0:.0f}°".format(value)


# =====================================================================
# Phrasing: a rule's "now" and "later" messages
# =====================================================================

@dataclass(frozen=True)
class Sentence:
    """A message as a rule said it: its key, the text, until when it is
    true, the hour or event it is about and when it happens (None for
    "now"), and what its placeholders were filled with."""

    key: str
    message: str
    valid_until: float
    about: Optional[float] = None
    when: Optional[float] = None
    values: Dict[str, object] = field(default_factory=dict)


@dataclass
class Phrasing:
    """Message keys: `now` for something in the current hour, `later` (its
    wordings have {time}) for an hour ahead. Both may have more placeholders,
    filled by `render`.

    "Now" is true until the next hour; "around {time}" until that time.
    """

    now: str
    later: str
    icon: Optional[str] = None

    def render(self, ctx: OverviewContext, i: int, **values) -> Sentence:
        """The sentence for hourly hour i."""
        return self.render_at(ctx, ctx.hourly.times[i], ctx.window.is_now(i), **values)

    def render_at(self, ctx: OverviewContext, ts: float, is_now: bool, **values) -> Sentence:
        """The sentence for the hour starting at `ts`, for data with its own
        timestamps (air quality)."""
        if is_now:
            message = ctx.messages.say(self.now, **values)
            return Sentence(self.now, message, ctx.clock.next_hour, values=values)
        message = ctx.messages.say(self.later, time=ctx.clock.approx_time(ts), **values)
        return Sentence(self.later, message, ts, ts, ts, values)


def say(ctx: OverviewContext, key: str, valid_until: float, about: Optional[float] = None,
        happens_now: bool = False, **values) -> Sentence:
    """A sentence for one message key, for rules that don't use a Phrasing.
    It happens at `about` (None: now), unless `happens_now`: rain easing at
    4 PM is about 4 PM, but falling now."""
    when = None if happens_now else about
    return Sentence(key, ctx.messages.say(key, **values), valid_until, about, when, values)


# =====================================================================
# Rules
# =====================================================================

class Rule(ABC):
    """One rule. `evaluate` returns an Insight, or None when it has nothing
    to say. The plain-English description is in docs/overview-rules.md, the
    wordings in core/overview/messages.py."""

    def __init__(self, kind: str, level: str, topic: str, icon: Optional[str] = None):
        self.kind = kind
        self.level = level
        self.topic = topic
        self.icon = icon

    @abstractmethod
    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        """The insight for this forecast, or None."""

    def insight(self, sentence: Sentence, *, level: Optional[str] = None,
                icon: Optional[str] = None, heading: Optional[str] = None,
                topic: Optional[str] = None) -> Insight:
        return Insight(
            self.kind,
            sentence.message,
            sentence.valid_until,
            level or self.level,
            icon or self.icon,
            heading,
            topic=topic or self.topic,
            key=sentence.key,
            about=sentence.about,
            when=sentence.when,
            values=sentence.values,
        )


class FirstHourRule(Rule):
    """The first hour that passes `test`, said with `phrasing` (or
    `snow_phrasing`, on the snow topic, when that hour has a snow code)."""

    def __init__(self, kind: str, test: HourTest, phrasing: Phrasing, level: str, topic: str,
                 snow_phrasing: Optional[Phrasing] = None):
        super().__init__(kind, level, topic)
        self.test = test
        self.phrasing = phrasing
        self.snow_phrasing = snow_phrasing

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        i = ctx.first(self.test)
        if i is None:
            return None
        phrasing, topic = self.phrasing, self.topic
        if self.snow_phrasing is not None and IS_SNOW(ctx, i):
            phrasing, topic = self.snow_phrasing, "snow"
        return self.insight(phrasing.render(ctx, i), icon=phrasing.icon, topic=topic)


class StormRule(Rule):
    """The first hour with a thunderstorm code. Later, it says that hour's
    chance of rain: "likely" from RAIN_LIKELY_PROBABILITY, "possible" below
    it, and no chance when the data has none for that hour."""

    LIKELY = Phrasing("storm.now", "storm.likely")
    POSSIBLE = Phrasing("storm.now", "storm.possible")
    NO_CHANCE = Phrasing("storm.now", "storm.later")

    def __init__(self):
        super().__init__("storm", "extreme", "storm", ICON_STORM)
        self.test = HasCode(STORM_CODES)

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        i = ctx.first(self.test)
        if i is None:
            return None
        chance = value_at(ctx.hourly.precip_probability, i)
        if chance is None:
            return self.insight(self.NO_CHANCE.render(ctx, i))
        phrasing = self.LIKELY if chance >= RAIN_LIKELY_PROBABILITY else self.POSSIBLE
        return self.insight(phrasing.render(ctx, i, chance=round(chance)))


class ExtremeFeelsRule(Rule):
    """Feels like HEAT_FEELS_LIKE_C or more (checked first), or
    COLD_FEELS_LIKE_C or less: say how much, by when, and what to do."""

    HEAT = Phrasing("heat.now", "heat.later")
    COLD = Phrasing("cold.now", "cold.later")

    def __init__(self):
        super().__init__("extreme_feels", "high", "feels_like")

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        feels = ctx.hourly.feels_like
        hours = [i for i in ctx.window.hours if value_at(feels, i) is not None]
        if not hours:
            return None
        hottest = max(hours, key=lambda i: feels[i])
        coldest = min(hours, key=lambda i: feels[i])
        if ctx.units.celsius(feels[hottest]) >= HEAT_FEELS_LIKE_C:
            i, phrasing = hottest, self.HEAT
        elif ctx.units.celsius(feels[coldest]) <= COLD_FEELS_LIKE_C:
            i, phrasing = coldest, self.COLD
        else:
            return None
        return self.insight(phrasing.render(ctx, i, temp=degrees(feels[i])))


class AirQualityRule(Rule):
    """US AQI reaching UNHEALTHY_US_AQI in the window: say now or from when."""

    PHRASING = Phrasing("air.now", "air.later")

    def __init__(self):
        super().__init__("air_quality", "high", "air")

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        hours = hours_between(ctx.air.times, ctx.now, ctx.window.end)
        j = next((j for j in hours if (value_at(ctx.air.us_aqi, j) or 0) >= UNHEALTHY_US_AQI), None)
        if j is None:
            return None
        return self.insight(self.PHRASING.render_at(ctx, ctx.air.times[j], j == hours[0]))


class UvRule(Rule):
    """UV index VERY_HIGH_UV or more: from when to when, or until when if it
    already is."""

    def __init__(self):
        super().__init__("uv", "high", "uv", ICON_SUN)
        self.test = AtLeast("uv", VERY_HIGH_UV)

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        hours = ctx.window.hours
        start = ctx.first(self.test)
        if start is None:
            return None
        # The last hour of that run of very high hours
        last = start
        for i in hours[hours.index(start) + 1:]:
            if not self.test(ctx, i):
                break
            last = i
        end_str = ctx.clock.approx_time(ctx.hourly.times[last] + HOUR)

        if ctx.window.is_now(start):
            return self.insight(say(ctx, "uv.now", ctx.clock.next_hour, time=end_str))
        start_ts = ctx.hourly.times[start]
        sentence = say(ctx, "uv.later", start_ts, start_ts,
                       start=ctx.clock.approx_time(start_ts), end=end_str)
        return self.insight(sentence)


class PrecipitationRule(Rule):
    """Rain or snow (a RAIN_LIKELY_PROBABILITY chance or more): easing at,
    lasting through, or starting at a time."""

    def __init__(self):
        super().__init__("precipitation", "medium", "rain")

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        window = ctx.window
        if not window.hours:
            return None
        first = window.hours[0]
        if IS_WET(ctx, first):
            return self._wet_now(ctx, IS_SNOW(ctx, first))

        start = ctx.first(IS_WET)
        if start is None:
            return None
        snow = IS_SNOW(ctx, start)
        ts = ctx.hourly.times[start]
        sentence = say(
            ctx,
            "snow.start" if snow else "rain.start",
            ts,
            ts,
            time=ctx.clock.approx_time(ts),
            chance=round(ctx.hourly.precip_probability[start]),
        )
        return self._insight(sentence, snow)

    def _wet_now(self, ctx: OverviewContext, snow: bool) -> Insight:
        dry = ctx.first(IS_DRY)
        if dry is None:
            sentence = say(
                ctx,
                "snow.through" if snow else "rain.through",
                ctx.clock.next_hour,
                time=ctx.clock.approx_time(ctx.window.end),
            )
            return self._insight(sentence, snow)

        ts = ctx.hourly.times[dry]
        sentence = say(ctx, "snow.easing" if snow else "rain.easing", ts, ts, happens_now=True,
                       time=ctx.clock.approx_time(ts))
        return self._insight(sentence, snow)

    def _insight(self, sentence: Sentence, snow: bool) -> Insight:
        if snow:
            return self.insight(sentence, icon=ICON_SNOW, topic="snow")
        return self.insight(sentence, icon=ICON_RAIN)


class WindRule(Rule):
    """Wind reaching STRONG_WIND_KMH: how fast and when; high from
    EXTREME_WIND_KMH."""

    PHRASING = Phrasing("wind.now", "wind.later")

    def __init__(self):
        super().__init__("wind", "medium", "wind", ICON_WIND)
        self.test = AtLeast("windspeed", STRONG_WIND_KMH, to_metric=Units.kmh)

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        i = ctx.first(self.test)
        if i is None:
            return None
        speed = ctx.hourly.windspeed[i]
        speed_str = "{0:.0f} {1}".format(speed, ctx.hourly.wind_unit)
        level = "high" if ctx.units.kmh(speed) >= EXTREME_WIND_KMH else "medium"
        return self.insight(self.PHRASING.render(ctx, i, speed=speed_str), level=level)


class FogRule(Rule):
    """Visibility under FOG_VISIBILITY_M or a fog code: now, around sunrise,
    or when."""

    PHRASING = Phrasing("fog.now", "fog.later")

    def __init__(self):
        super().__init__("fog", "medium", "fog", ICON_FOG)
        self.test = AnyOf(Below("visibility", FOG_VISIBILITY_M), HasCode(FOG_CODES))

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        i = ctx.first(self.test)
        if i is None:
            return None
        ts = ctx.hourly.times[i]
        sunrise = ctx.sun.next_sunrise
        if not ctx.window.is_now(i) and sunrise is not None and abs(ts - sunrise) <= FOG_SUNRISE_MINUTES * MINUTE:
            return self.insight(say(ctx, "fog.sunrise", ts, ts))
        return self.insight(self.PHRASING.render(ctx, i))


class TemperatureSwingRule(Rule):
    """A rise or drop of TEMPERATURE_SWING_C or more from now (the bigger
    change wins): say the temperature and when."""

    def __init__(self):
        super().__init__("temperature_swing", "low", "temperature")

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        temps = ctx.hourly.temperature
        hours = [i for i in ctx.window.hours if value_at(temps, i) is not None]
        if len(hours) < 2:
            return None
        celsius = ctx.units.celsius
        now_c = celsius(temps[hours[0]])
        warmest = max(hours, key=lambda i: temps[i])
        coldest = min(hours, key=lambda i: temps[i])
        rise = celsius(temps[warmest]) - now_c
        drop = now_c - celsius(temps[coldest])

        if max(rise, drop) < TEMPERATURE_SWING_C:
            return None
        i, key = (warmest, "temperature.warming") if rise >= drop else (coldest, "temperature.cooling")
        ts = ctx.hourly.times[i]
        return self.insight(say(ctx, key, ts, ts, temp=degrees(temps[i]), time=ctx.clock.approx_time(ts)))


class TomorrowRule(Rule):
    """From OVERVIEW_TOMORROW_FROM_HOUR: rain likely tomorrow, or a high
    TOMORROW_DIFFERENCE_C warmer or cooler than today's. True until midnight."""

    def __init__(self):
        super().__init__("tomorrow", "low", "tomorrow")

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        if ctx.clock.local().hour < OVERVIEW_TOMORROW_FROM_HOUR:
            return None
        daily = ctx.daily
        # After midnight, "tomorrow" is another day
        valid_until = ctx.clock.next_midnight
        heading = C_("overview heading", "Tomorrow")

        if (daily.tomorrow_rain_chance or 0) >= RAIN_LIKELY_PROBABILITY:
            sentence = say(ctx, "tomorrow.rain", valid_until, chance=round(daily.tomorrow_rain_chance))
            return self.insight(sentence, icon=ICON_RAIN, heading=heading)

        if daily.today_high is None or daily.tomorrow_high is None:
            return None
        difference = ctx.units.celsius(daily.tomorrow_high) - ctx.units.celsius(daily.today_high)
        if difference >= TOMORROW_DIFFERENCE_C:
            key = "tomorrow.warmer"
        elif difference <= -TOMORROW_DIFFERENCE_C:
            key = "tomorrow.cooler"
        else:
            return None
        sentence = say(ctx, key, valid_until, temp=degrees(daily.tomorrow_high))
        return self.insight(sentence, heading=heading)


class SunRule(Rule):
    """Sunset within SUNSET_SOON_MINUTES by day, or sunrise within
    SUNRISE_SOON_MINUTES at night: say how soon, never more than
    OVERVIEW_RELATIVE_TOLERANCE off."""

    def __init__(self):
        super().__init__("sun", "low", "sun")

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        sun = ctx.sun
        if sun.is_day:
            event, soon, sunset = sun.next_sunset, SUNSET_SOON_MINUTES, True
            icon = ICON_SUNSET
        else:
            event, soon, sunset = sun.next_sunrise, SUNRISE_SOON_MINUTES, False
            icon = ICON_SUNRISE
        if event is None or event - ctx.now > soon * MINUTE:
            return None
        sentence = self.phrase(ctx, event, sunset)
        if sentence is None:
            return None
        return self.insight(sentence, icon=icon)

    @staticmethod
    def phrase(ctx: OverviewContext, event: float, sunset: bool) -> Optional[Sentence]:
        """The sentence for "The sun sets in …" (about the event), or None.

        Under an hour: minutes to the nearest SUN_ROUND_MINUTES (halves
        down), true while no more than the tolerance off. Longer: "about N
        hours" (nearest hour, halves down) with the exact time, true while N
        is the nearest hour. In the last half step (2½ minutes) there is
        nothing accurate to say.
        """
        name = "sunset" if sunset else "sunrise"
        minutes = (event - ctx.now) / MINUTE
        step = SUN_ROUND_MINUTES
        last_half_step = step / 2 * MINUTE  # where the smallest count, `step`, stops being right
        n = math.ceil(minutes / step - 0.5) * step
        if n <= 0:
            return None
        if n < 60:
            key = f"{name}.minutes"
            valid_until = min(event - n * MINUTE + OVERVIEW_RELATIVE_TOLERANCE, event - last_half_step)
            return Sentence(key, ctx.messages.say_count(key, n), valid_until, event)

        n = math.ceil(minutes / 60 - 0.5)
        # Until n - ½ hours are left; from 57½ minutes (an hour less half a
        # step) the minutes form takes over
        key = f"{name}.hours"
        valid_until = event - max((n - 0.5) * HOUR, HOUR - last_half_step)
        message = ctx.messages.say_count(key, n, time=ctx.clock.time(event))
        return Sentence(key, message, valid_until, event)


class CalmRule(Rule):
    """Always applies: the fallback when nothing else is worth saying."""

    def __init__(self):
        super().__init__("calm", "calm", "calm")

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        end = ctx.window.end
        return self.insight(say(ctx, "calm", end, time=ctx.clock.approx_time(end)))


# =====================================================================
# Several things at once: combine, or fold
# =====================================================================

@dataclass(frozen=True)
class Combination:
    """Two insights that become one sentence, `key` + ".now" or ".later".
    `first` is the more important: it gives the rule, topic and icon."""

    first: str
    second: str
    key: str


@dataclass(frozen=True)
class Fold:
    """`kept` already says `folded`: the folded one isn't shown."""

    kept: str
    folded: str


@dataclass(frozen=True)
class Turning:
    """Rain (`light`) and something `later` in the same wet spell (heavy
    rain, a storm): one sentence, `key` + the rain message's form
    (".easing", ".through" or ".start"). `time_name` is the placeholder for
    the later one's time; None when the sentence doesn't say it."""

    light: str
    later: str
    key: str
    time_name: Optional[str] = None


# Tried in this order, each insight used once (docs/overview-rules.md,
# "Several things at once"): turning stormy, folds, turning heavy, the pairs
TURNING_STORMY = (
    Turning("rain", "storm", "rain_stormy"),
)
FOLDS = (
    Fold("storm", "rain"),
    Fold("storm", "snow"),
    Fold("heavy_rain", "rain"),
    Fold("heavy_snow", "snow"),
)
TURNING_HEAVY = (
    Turning("rain", "heavy_rain", "rain_heavier", time_name="heavy_time"),
    Turning("snow", "heavy_snow", "snow_heavier", time_name="heavy_time"),
)
COMBINATIONS = (
    Combination("storm", "wind", "storm_wind"),
    Combination("storm", "heavy_rain", "storm_heavy_rain"),
    Combination("heavy_rain", "wind", "heavy_rain_wind"),
    Combination("heavy_snow", "wind", "heavy_snow_wind"),
    Combination("rain", "wind", "rain_wind"),
    Combination("snow", "wind", "snow_wind"),
)


def what(insight: Insight) -> str:
    """The name an insight has in FOLDS and COMBINATIONS ("heavy_rain")."""
    if insight.kind == "heavy_precipitation":
        return f"heavy_{insight.topic}"
    if insight.kind == "precipitation":
        return insight.topic
    return insight.kind


def not_together(a: Insight, b: Insight) -> Optional[str]:
    """Why `a` and `b` don't happen together, or None when they do: both now,
    or both later and within OVERVIEW_COMBINE_MINUTES."""
    if (a.when is None) != (b.when is None):
        return "one now, one later"
    if a.when is None:
        return None
    apart_minutes = abs(a.when - b.when) / MINUTE
    if apart_minutes > OVERVIEW_COMBINE_MINUTES:
        return f"{apart_minutes:.0f} min apart"
    return None


def combine(insights: Sequence[Insight], ctx: OverviewContext,
            log_steps: bool = True) -> List[Insight]:
    """`insights` with the ones that happen together turned (TURNING_STORMY,
    TURNING_HEAVY), folded (FOLDS) and combined (COMBINATIONS) into one;
    everything else as it is. Each step is logged (debug) unless `log_steps`
    is off."""
    result = list(insights)

    def note(message: str) -> None:
        if log_steps:
            logger.debug(message)

    combined_ones = []  # each insight is combined once: these are out of the running

    def find(name: str) -> Optional[Insight]:
        return next((i for i in result if what(i) == name and not _is_in(i, combined_ones)), None)

    def turn(turnings: Sequence[Turning], how: str) -> None:
        for turning in turnings:
            light, later = find(turning.light), find(turning.later)
            if light is None or later is None:
                continue
            why = not_in_the_same_spell(light, later, ctx)
            if why:
                note(f"Overview not turning {how}: {later.kind} with {light.kind} ({light.key}): {why}")
                continue
            turned = _turned(light, later, turning, ctx)
            note(f"Overview turning {how}: {light.kind} ({light.key}) + {later.kind} "
                 f"({_hh_mm(ctx, later.when)}) -> {turned.key}")
            result[result.index(later)] = turned
            result.remove(light)
            combined_ones.append(turned)

    # First, so a rain that leads a storm isn't folded into it
    turn(TURNING_STORMY, "stormy")

    for fold in FOLDS:
        kept, folded = find(fold.kept), find(fold.folded)
        if kept is None or folded is None:
            continue
        why = not_together(kept, folded)
        if why:
            note(f"Overview not folded: {folded.kind} into {kept.kind}: {why}")
            continue
        note(f"Overview folded: {folded.kind} ({folded.key}) into {kept.kind}")
        result.remove(folded)
        result[result.index(kept)] = replace(
            kept, parts=kept.parts + folded.parts, covers=kept.covers + folded.covers
        )

    turn(TURNING_HEAVY, "heavy")

    for combination in COMBINATIONS:
        first, second = find(combination.first), find(combination.second)
        if first is None or second is None:
            continue
        why = not_together(first, second)
        if why:
            note(f"Overview not combined: {first.kind} + {second.kind}: {why}")
            continue
        combined = _combined(first, second, combination.key, ctx)
        note(f"Overview combined: {first.kind} + {second.kind} -> {combined.key}")
        result[result.index(first)] = combined
        result.remove(second)
        combined_ones.append(combined)
    return result


def not_in_the_same_spell(light: Insight, later: Insight, ctx: OverviewContext) -> Optional[str]:
    """Why `later` (heavy rain, a storm) is not part of the rain that is
    falling (or starting), or None when it is: it comes after the rain
    starts and before its first dry hour."""
    form = light.key.split(".")[-1]
    if form not in ("easing", "through", "start"):
        return f"no sentence for {light.key}"
    if later.when is None:
        return "it is now"
    starts = light.when if light.when is not None else ctx.now
    if later.when <= starts:
        return "it comes with or before the rain"
    if form == "easing":
        ends = light.about
    elif form == "through":
        ends = ctx.window.end
    else:
        ends = _wet_until(ctx, starts)
    if later.when >= ends:
        return f"it comes after the rain eases ({_hh_mm(ctx, ends)})"
    return None


def _wet_until(ctx: OverviewContext, starts: float) -> float:
    """The first dry hour after `starts`, or the window's end."""
    return next(
        (ctx.hourly.times[i] for i in ctx.window.hours
         if ctx.hourly.times[i] > starts and IS_DRY(ctx, i)),
        ctx.window.end,
    )


def _turned(light: Insight, later: Insight, turning: Turning, ctx: OverviewContext) -> Insight:
    """One insight for rain turning heavy or stormy: the later one's rule,
    level and topic, the rain's times, true until the later one's hour (or
    the rain's end, if sooner), counting as both.

    A part is about the hour the sentence says. Without the later one's time
    in it, the later one's parts are about the rain's hour, so a storm moving
    within the spell isn't news: the sentence stays the same.
    """
    key = f"{turning.key}.{light.key.split('.')[-1]}"
    values = dict(light.values)
    later_parts = later.parts
    if turning.time_name:
        values[turning.time_name] = ctx.clock.approx_time(later.when)
    else:
        later_parts = tuple((kind, key, level, light.about) for kind, _key, level, _about in later.parts)
    return Insight(
        later.kind,
        ctx.messages.say(key, **values),
        min(light.valid_until, later.valid_until),
        later.level,
        later.icon,
        later.heading,
        topic=later.topic,
        key=key,
        about=light.about,
        when=light.when,
        values=values,
        parts=light.parts + later_parts,
        topics=later.topics + tuple(t for t in light.topics if t not in later.topics),
        covers=light.covers + later.covers,
    )


def _hh_mm(ctx: OverviewContext, ts: Optional[float]) -> str:
    """A time for the debug log, in the city's time zone."""
    return "now" if ts is None else ctx.clock.local(ts).strftime("%H:%M")


def _is_in(insight: Insight, insights: Sequence[Insight]) -> bool:
    """Whether this very insight object is in `insights` (equal ones don't count)."""
    return any(insight is other for other in insights)


def _combined(first: Insight, second: Insight, key: str, ctx: OverviewContext) -> Insight:
    """One insight saying both: from the earlier time, true until either
    stops being true, at the higher level, and counting as both."""
    whens = [i.when for i in (first, second) if i.when is not None]
    when = min(whens) if whens else None
    values = {**second.values, **first.values}
    if when is None:
        key, message = f"{key}.now", ctx.messages.say(f"{key}.now", **values)
    else:
        values["time"] = ctx.clock.approx_time(when)
        key, message = f"{key}.later", ctx.messages.say(f"{key}.later", **values)
    return Insight(
        first.kind,
        message,
        min(first.valid_until, second.valid_until),
        max(first.level, second.level, key=LEVELS.index),
        first.icon,
        first.heading,
        topic=first.topic,
        key=key,
        about=when,
        when=when,
        values=values,
        parts=first.parts + second.parts,
        topics=first.topics + second.topics,
        covers=first.covers + second.covers,
    )


# =====================================================================
# The rule book
# =====================================================================

class RuleBook:
    """The rules in use, in the order of docs/overview-rules.md."""

    def __init__(self, rules: List[Rule]):
        self.rules = rules

    @classmethod
    def default(cls) -> "RuleBook":
        """Every rule."""
        return cls([
            StormRule(),
            FirstHourRule(
                "freezing",
                HasCode(FREEZING_CODES),
                Phrasing("freezing.now", "freezing.later", ICON_RAIN),
                level="high",
                topic="freezing",
            ),
            FirstHourRule(
                "heavy_precipitation",
                AnyOf(
                    HasCode(HEAVY_RAIN_CODES | HEAVY_SNOW_CODES),
                    AtLeast("precipitation", HEAVY_PRECIPITATION_MM),
                ),
                Phrasing("heavy_rain.now", "heavy_rain.later", ICON_RAIN),
                level="high",
                topic="rain",
                snow_phrasing=Phrasing("heavy_snow.now", "heavy_snow.later", ICON_SNOW),
            ),
            ExtremeFeelsRule(),
            AirQualityRule(),
            UvRule(),
            PrecipitationRule(),
            WindRule(),
            FogRule(),
            TemperatureSwingRule(),
            TomorrowRule(),
            SunRule(),
            CalmRule(),
        ])

    def run(self, ctx: OverviewContext, log_steps: bool = True) -> List[Insight]:
        """Every insight that applies and is still true, most important first.

        Ignore on fail: a rule that fails, on odd or missing data, simply
        offers nothing. It is logged (debug only) and the other rules still
        run, so one rule can never break the overview.

        `log_steps` off: the folds and pairs aren't logged, for the engine's
        second run that only draws a fresh wording.
        """
        insights = []
        for rule in self.rules:
            try:
                insight = rule.evaluate(ctx)
            except Exception as e:  # noqa: BLE001 - ignore on fail, see above
                logger.debug(f"Overview rule {rule.kind} skipped: {e!r}")
                continue
            if insight is not None and insight.valid_until > ctx.now:
                insights.append(insight)
        insights.sort(key=lambda insight: insight.priority, reverse=True)
        try:
            return combine(insights, ctx, log_steps)
        except Exception as e:  # noqa: BLE001 - ignore on fail: each insight on its own
            logger.debug(f"Overview combining skipped: {e!r}")
            return insights
