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
  and is still true, most important first.
- AnnouncePlanner: which of those insights to show, and when the overview
  opens by itself. The engine (state/overview_engine.py) runs the timers around it.
"""

import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from gettext import pgettext as C_
from typing import Dict, List, Optional, Tuple

from ...config import (
    OVERVIEW_ANNOUNCE_BASE_MINUTES,
    OVERVIEW_ANNOUNCE_MAX_MINUTES,
    OVERVIEW_ANNOUNCE_MIN_MINUTES,
    OVERVIEW_ANNOUNCE_SPREAD,
    COLD_FEELS_LIKE_C,
    EXTREME_WIND_KMH,
    FOG_SUNRISE_MINUTES,
    FOG_VISIBILITY_M,
    HEAT_FEELS_LIKE_C,
    HEAVY_PRECIPITATION_MM,
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
from .insight import LEVEL_RANK, Insight

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
    true, and the hour or event it is about (None for "now")."""

    key: str
    message: str
    valid_until: float
    about: Optional[float] = None


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
            return Sentence(self.now, ctx.messages.say(self.now, **values), ctx.clock.next_hour)
        message = ctx.messages.say(self.later, time=ctx.clock.approx_time(ts), **values)
        return Sentence(self.later, message, ts, ts)


def say(ctx: OverviewContext, key: str, valid_until: float, about: Optional[float] = None,
        **values) -> Sentence:
    """A sentence for one message key, for rules that don't use a Phrasing."""
    return Sentence(key, ctx.messages.say(key, **values), valid_until, about)


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
        sentence = say(ctx, "snow.easing" if snow else "rain.easing", ts, ts,
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
            FirstHourRule(
                "storm",
                HasCode(STORM_CODES),
                Phrasing("storm.now", "storm.later", ICON_STORM),
                level="extreme",
                topic="storm",
            ),
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

    def run(self, ctx: OverviewContext) -> List[Insight]:
        """Every insight that applies and is still true, most important first.

        Ignore on fail: a rule that fails, on odd or missing data, simply
        offers nothing. It is logged (debug only) and the other rules still
        run, so one rule can never break the overview.
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
        return insights


# =====================================================================
# Announcing: which insight to show, and when to open
# =====================================================================


class AnnouncePlanner:
    """Decides which insight the overview shows and when it opens by itself.

    - **How often**: the score adds up the priorities (÷ 100) of everything
      worth saying. The next opening is OVERVIEW_ANNOUNCE_BASE_MINUTES ÷
      (1 + score), between the MIN and MAX minutes, spread at random. A busy
      forecast opens more often; as insights expire it calms down.
    - **What**: each opening shows the insight whose turn it is: never shown
      ones first (most important first), then the highest priority × minutes
      since it was last shown. Lower insights get their turn too. The first
      opening is an escalation (below), so it shows the most severe one.
    - **Escalation**: something more severe than before (a storm appears)
      opens at once, unless it was shown in the last MAX minutes (so one that
      comes and goes counts once). Within MIN minutes of the last opening it
      waits, and opens as soon as those minutes are up.
    - **Between openings** the shown insight's text is kept up to date
      silently; if it no longer applies, the most important one takes its
      place, silently.

    The memory (what was shown when, the next opening) belongs to one
    location: the engine keeps it across refreshes and calls `forget()` when
    the location changes or the overview is turned off.
    """

    def __init__(self):
        self.forget()

    def forget(self) -> None:
        self.last_shown: Dict[str, float] = {}  # kind -> when it was last shown
        self.next_announce = 0.0
        self.pending_rank = -1  # the highest level pending at the last run

    @staticmethod
    def worth_saying(insights: List[Insight]) -> List[Insight]:
        """The insights that take turns: calm only when there is nothing else."""
        return [i for i in insights if i.kind != "calm"] or insights[:1]

    @staticmethod
    def score(insights: List[Insight]) -> float:
        return sum(i.priority for i in insights) / 100

    @staticmethod
    def interval_minutes(score: float, spread: float) -> float:
        """Minutes to the next opening for a score; `spread` from -1 to 1
        moves it by up to OVERVIEW_ANNOUNCE_SPREAD."""
        minutes = OVERVIEW_ANNOUNCE_BASE_MINUTES / (1 + score)
        minutes *= 1 + spread * OVERVIEW_ANNOUNCE_SPREAD
        return min(max(minutes, OVERVIEW_ANNOUNCE_MIN_MINUTES), OVERVIEW_ANNOUNCE_MAX_MINUTES)

    def turn(self, insight: Insight, now: float) -> Tuple[int, float]:
        """How strongly `insight` wants the next opening: (1, priority) if
        never shown, else (0, priority × minutes since it was last shown)."""
        last = self.last_shown.get(insight.kind)
        if last is None:
            return (1, insight.priority)  # never shown: first, by priority
        return (0, insight.priority * (now - last) / 60)

    def turn_order(self, insights: List[Insight], now: float) -> List[Insight]:
        """The insights in the order they would get an opening at `now`."""
        # sorted() keeps ties in their order, so the first is whose_turn's
        return sorted(insights, key=lambda i: self.turn(i, now), reverse=True)

    def whose_turn(self, insights: List[Insight], now: float) -> Insight:
        return max(insights, key=lambda i: self.turn(i, now))

    def decide(self, insights: List[Insight], showing: Optional[str], now: float,
               rng: Optional[random.Random] = None) -> Tuple[Optional[Insight], bool]:
        """(the insight to show, whether to open the overview) for the
        insights true now, most important first. `showing` is the kind on
        screen, or None when it has expired: then another one takes its
        place silently, and the overview still waits for its next opening."""
        if not insights:
            return None, False
        pending = self.worth_saying(insights)
        top = max(pending, key=lambda i: (LEVEL_RANK[i.level], i.priority))
        rank = LEVEL_RANK[top.level]
        # pending_rank starts at -1, so the first opening is an escalation too
        escalated = rank > self.pending_rank

        # Escalation skips the wait, but only for something not shown lately
        # (a severe insight that comes and goes counts once), and never
        # straight after another opening: then it opens once the gap is over
        last_opening = max(self.last_shown.values(), default=-math.inf)
        gap_over = last_opening + OVERVIEW_ANNOUNCE_MIN_MINUTES * 60
        shown_lately = now - self.last_shown.get(top.kind, -math.inf) < OVERVIEW_ANNOUNCE_MAX_MINUTES * 60
        escalates = escalated and not shown_lately
        if escalates and now < gap_over:
            # Stays pending (rank not recorded) until the gap is over
            self.next_announce = min(self.next_announce, gap_over)
        else:
            self.pending_rank = rank

        if escalates and now >= gap_over:
            chosen = top
        elif now >= self.next_announce:
            # Its time has come
            chosen = self.whose_turn(pending, now)
        else:
            # Not time to open: keep the text up to date, silently
            same = next((i for i in insights if i.kind == showing), None)
            return same or pending[0], False

        self.last_shown[chosen.kind] = now
        minutes = self.interval_minutes(self.score(pending), (rng or random).uniform(-1, 1))
        self.next_announce = now + minutes * 60
        return chosen, True

    def note_shown(self, kind: str, now: float) -> None:
        """The user opened the overview on `kind`: that counts as its turn."""
        self.last_shown[kind] = now
