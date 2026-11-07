"""Rules for the overview: each looks at the forecast and may offer an Insight.

Source of truth: docs/overview-rules.md. Change that file first, then this
one and the numbers in configs.py to match.

Built by composition, with no GTK, so everything can be tested on made-up data:

- OverviewContext: the forecast as the rules see it, made of small parts
  (Clock, Units, HourlySeries, SunTimes, DailyOutlook, AirSeries) and the
  Window worked out from them.
- HourTest: a yes/no question about one hour (HasCode, AtLeast, Below,
  AnyOf), combined to describe what a rule looks for.
- Phrasing: the "now" and "later" message keys of a rule, rendered with the
  right valid_until. The wordings, several per message, are in
  CORE_OverviewMessages.py; the context's MessageBook picks one.
- Rule: one rule, `evaluate(ctx) -> Optional[Insight]`.
- RuleBook: the rules in use; `run(ctx)` returns every insight that applies
  and is still true, most important first.
- AnnouncePlanner: which of those insights to show, and when the overview
  opens by itself. The engine (CORE_Overview.py) runs the timers around it.
"""

import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from gettext import pgettext as C_
from typing import Callable, Dict, Iterable, List, Optional, Tuple
from zoneinfo import ZoneInfo

from .configs import (
    OVERVIEW_ANNOUNCE_BASE_MINUTES,
    OVERVIEW_ANNOUNCE_MAX_MINUTES,
    OVERVIEW_ANNOUNCE_MIN_MINUTES,
    OVERVIEW_ANNOUNCE_SPREAD,
    COLD_FEELS_LIKE_C,
    EXTREME_WIND_KMH,
    FOG_VISIBILITY_M,
    HEAT_FEELS_LIKE_C,
    HEAVY_PRECIPITATION_MM,
    OVERVIEW_DAY_MIN_HOURS,
    OVERVIEW_HOURS,
    OVERVIEW_PRIORITIES,
    OVERVIEW_RELATIVE_TOLERANCE,
    OVERVIEW_ROUND_FAR_MINUTES,
    OVERVIEW_ROUNDING,
    OVERVIEW_SHOW_BASE_SECONDS,
    OVERVIEW_SHOW_EXTRA_SECONDS,
    OVERVIEW_TOMORROW_FROM_HOUR,
    RAIN_LIKELY_PROBABILITY,
    STRONG_WIND_KMH,
    SUNRISE_SOON_MINUTES,
    SUNSET_SOON_MINUTES,
    TEMPERATURE_SWING_C,
    TOMORROW_DIFFERENCE_C,
    UNHEALTHY_US_AQI,
    VERY_HIGH_UV,
)
from .CORE_Logging import get_logger
from .CORE_OverviewMessages import MessageBook

logger = get_logger("overview")

HOUR = 3600
MINUTE = 60

# WMO weather codes
STORM_CODES = {95, 96, 99}
FREEZING_CODES = {56, 57, 66, 67}
SNOW_CODES = {71, 73, 75, 77, 85, 86}
HEAVY_RAIN_CODES = {65, 82}
HEAVY_SNOW_CODES = {75, 86}
FOG_CODES = {45, 48}


def hours_between(times: List[int], start: float, end: float) -> List[int]:
    """Indices of the hours that overlap [start, end): the current one first."""
    return [i for i, ts in enumerate(times) if ts + HOUR > start and ts < end]


def at(values: List, i: int):
    """values[i], or None when the list is short."""
    return values[i] if 0 <= i < len(values) else None


def degrees(value: float) -> str:
    return "{0:.0f}°".format(value)


# =====================================================================
# Insight
# =====================================================================

@dataclass
class Insight:
    """One thing worth saying about the coming hours."""

    kind: str  # a key of OVERVIEW_PRIORITIES
    message: str  # one whole translated sentence
    valid_until: float  # unix time from which the message is no longer true
    severity: str = "info"  # "info", "warning" or "error"
    icon: Optional[str] = None  # symbolic icon shown before the message
    heading: Optional[str] = None  # None: the window's heading (Today / Tonight)
    priority: int = field(init=False)
    show_seconds: int = field(init=False)  # how long the message stays open

    def __post_init__(self):
        self.priority = OVERVIEW_PRIORITIES[self.kind]
        self.show_seconds = OVERVIEW_SHOW_BASE_SECONDS + OVERVIEW_SHOW_EXTRA_SECONDS[self.severity]


# =====================================================================
# The context, and the parts it is made of
# =====================================================================

@dataclass
class Clock:
    """Now, and how times are written: the city's time zone, 12 or 24 h."""

    now: float
    tz: Optional[ZoneInfo] = None
    use_24h: bool = False

    def local(self, ts: Optional[float] = None) -> datetime:
        return datetime.fromtimestamp(self.now if ts is None else ts, tz=self.tz)

    def time(self, ts: float) -> str:
        return self.local(ts).strftime("%H:%M" if self.use_24h else "%-I:%M %p")

    def approx_time(self, ts: float) -> str:
        """A rounded time ("6:40 AM", "06:40") for every predicted time: a
        forecast is never minute-exact. Messages always hedge it ("about",
        "around", "by around"). Only sunrise and sunset use `time()`.

        The further ahead, the rounder (OVERVIEW_ROUNDING): to 10 minutes up
        to 3 hours ahead, to 30 minutes up to 5 hours, to the hour beyond.
        """
        hours_ahead = (ts - self.now) / HOUR
        step = next(
            (minutes for limit, minutes in OVERVIEW_ROUNDING if hours_ahead <= limit),
            OVERVIEW_ROUND_FAR_MINUTES,
        )
        # Round in local time: some time zones are half an hour off UTC
        local = self.local(ts).replace(second=0, microsecond=0)
        minutes = local.hour * 60 + local.minute
        rounded = math.floor(minutes / step + 0.5) * step
        rounded_dt = local.replace(hour=0, minute=0) + timedelta(minutes=rounded)
        return rounded_dt.strftime("%H:%M" if self.use_24h else "%-I:%M %p")

    @property
    def next_hour(self) -> float:
        return (int(self.now) // HOUR + 1) * HOUR

    @property
    def next_midnight(self) -> float:
        tomorrow = self.local().date() + timedelta(days=1)
        return datetime.combine(tomorrow, datetime.min.time(), tzinfo=self.tz).timestamp()


@dataclass
class Units:
    """Data comes in the user's units; thresholds are metric."""

    imperial: bool = False

    def celsius(self, value: float) -> float:
        return (value - 32) * 5 / 9 if self.imperial else value

    def kmh(self, value: float) -> float:
        return value * 1.609344 if self.imperial else value


@dataclass
class HourlySeries:
    """The hourly forecast: lists that share `times`, in the user's units.
    Precipitation (mm) and visibility (m) are metric in both systems."""

    times: List[int]
    codes: List[Optional[int]] = field(default_factory=list)
    temperature: List[Optional[float]] = field(default_factory=list)
    feels_like: List[Optional[float]] = field(default_factory=list)
    precip_probability: List[Optional[float]] = field(default_factory=list)
    precipitation: List[Optional[float]] = field(default_factory=list)
    windspeed: List[Optional[float]] = field(default_factory=list)
    visibility: List[Optional[float]] = field(default_factory=list)
    uv: List[Optional[float]] = field(default_factory=list)
    wind_unit: str = ""

    def value(self, series: str, i: int):
        """One hour's value of a series, or None when it is missing."""
        return at(getattr(self, series), i)


@dataclass
class SunTimes:
    """The next sunrise and sunset after now (None in polar day or night)."""

    next_sunrise: Optional[int] = None
    next_sunset: Optional[int] = None

    @property
    def is_day(self) -> bool:
        """Day when the next sunset comes before the next sunrise."""
        if self.next_sunset is None:
            return False
        return self.next_sunrise is None or self.next_sunset < self.next_sunrise


@dataclass
class DailyOutlook:
    """Today's and tomorrow's daily values, in the user's units."""

    today_high: Optional[float] = None
    tomorrow_high: Optional[float] = None
    tomorrow_rain_chance: Optional[float] = None


@dataclass
class AirSeries:
    """Hourly US AQI, with its own timestamps."""

    times: List[int] = field(default_factory=list)
    us_aqi: List[Optional[float]] = field(default_factory=list)


class Window:
    """The hours the rules look at, following the part of the day.

    By day: now until sunset, but at least OVERVIEW_DAY_MIN_HOURS ahead.
    At night: now until the next sunrise. With no sunrise or sunset: the next
    OVERVIEW_HOURS. The current hour comes first.
    """

    def __init__(self, hourly: HourlySeries, clock: Clock, sun: SunTimes):
        self.is_day = sun.is_day
        if self.is_day:
            self.end = max(sun.next_sunset, clock.now + OVERVIEW_DAY_MIN_HOURS * HOUR)
        elif sun.next_sunrise is not None:
            self.end = sun.next_sunrise
        else:
            self.end = clock.now + OVERVIEW_HOURS * HOUR
        self.hours = hours_between(hourly.times, clock.now, self.end)

    @property
    def heading(self) -> str:
        if self.is_day:
            return C_("overview heading", "Today")
        return C_("overview heading", "Tonight")

    def first(self, test: Callable[[int], bool]) -> Optional[int]:
        """The first hour that passes `test`."""
        return next((i for i in self.hours if test(i)), None)

    def is_now(self, i: int) -> bool:
        return bool(self.hours) and i == self.hours[0]


@dataclass
class OverviewContext:
    """The forecast as the rules see it."""

    clock: Clock
    units: Units
    hourly: HourlySeries
    sun: SunTimes = field(default_factory=SunTimes)
    daily: DailyOutlook = field(default_factory=DailyOutlook)
    air: AirSeries = field(default_factory=AirSeries)
    messages: MessageBook = field(default_factory=MessageBook)
    window: Window = field(init=False)

    def __post_init__(self):
        self.window = Window(self.hourly, self.clock, self.sun)

    @property
    def now(self) -> float:
        return self.clock.now

    @classmethod
    def from_models(cls, hourly, daily, air, now: float, tz: Optional[ZoneInfo],
                    imperial: bool, use_24h: bool, seed: int = 0) -> "OverviewContext":
        """Build the context from HourlyWeather, DailyWeather and
        AirPollutionData (daily and air may be None). `seed` picks the
        wordings (see MessageBook)."""
        clock = Clock(now, tz, use_24h)
        today = clock.local().date()
        tomorrow = today + timedelta(days=1)
        wind = getattr(hourly, "windspeed_10m", None)
        sunrises = [ts for ts in _series(daily, "sunrise") if ts and ts > now]
        sunsets = [ts for ts in _series(daily, "sunset") if ts and ts > now]

        return cls(
            clock=clock,
            units=Units(imperial),
            hourly=HourlySeries(
                times=_series(hourly, "time"),
                codes=_series(hourly, "weathercode"),
                temperature=_series(hourly, "temperature_2m"),
                feels_like=_series(hourly, "apparent_temperature"),
                precip_probability=_series(hourly, "precipitation_probability"),
                precipitation=_series(hourly, "precipitation"),
                windspeed=_series(hourly, "windspeed_10m"),
                visibility=_series(hourly, "visibility"),
                uv=_series(hourly, "uv_index"),
                wind_unit=wind.unit if wind is not None else "",
            ),
            sun=SunTimes(
                next_sunrise=min(sunrises) if sunrises else None,
                next_sunset=min(sunsets) if sunsets else None,
            ),
            daily=DailyOutlook(
                today_high=_daily_value(daily, "temperature_2m_max", today),
                tomorrow_high=_daily_value(daily, "temperature_2m_max", tomorrow),
                tomorrow_rain_chance=_daily_value(daily, "precipitation_probability_max", tomorrow),
            ),
            air=AirSeries(times=_series(air, "time"), us_aqi=_series(air, "us_aqi")),
            messages=MessageBook(seed),
        )


def _series(model, name: str) -> list:
    """A model field's data as a list, or [] when it is missing."""
    weather_field = getattr(model, name, None) if model is not None else None
    if weather_field is None or weather_field.data is None:
        return []
    return list(weather_field.data)


def _daily_value(daily, name: str, day) -> Optional[float]:
    """A daily value for a date. Daily data is requested in GMT, so each
    day's timestamp is its midnight in UTC: compare UTC dates."""
    for i, ts in enumerate(_series(daily, "time")):
        if datetime.fromtimestamp(ts, tz=timezone.utc).date() == day:
            return at(_series(daily, name), i)
    return None


# =====================================================================
# Hour tests: yes/no questions about one hour, combined by composition
# =====================================================================

class HourTest(ABC):
    @abstractmethod
    def __call__(self, ctx: OverviewContext, i: int) -> bool:
        """Does hour i pass?"""


class HasCode(HourTest):
    """The hour's weather code is one of `codes`."""

    def __init__(self, codes: Iterable[int]):
        self.codes = set(codes)

    def __call__(self, ctx: OverviewContext, i: int) -> bool:
        return ctx.hourly.value("codes", i) in self.codes


class AtLeast(HourTest):
    """The hour's value of `series` is `threshold` or more. `to_metric`
    (Units.celsius, Units.kmh) converts imperial data first."""

    def __init__(self, series: str, threshold: float,
                 to_metric: Optional[Callable[[Units, float], float]] = None):
        self.series = series
        self.threshold = threshold
        self.to_metric = to_metric

    def metric_value(self, ctx: OverviewContext, i: int) -> Optional[float]:
        value = ctx.hourly.value(self.series, i)
        if value is None or self.to_metric is None:
            return value
        return self.to_metric(ctx.units, value)

    def __call__(self, ctx: OverviewContext, i: int) -> bool:
        value = self.metric_value(ctx, i)
        return value is not None and value >= self.threshold


class Below(AtLeast):
    """The hour's value of `series` is under `threshold`."""

    def __call__(self, ctx: OverviewContext, i: int) -> bool:
        value = self.metric_value(ctx, i)
        return value is not None and value < self.threshold


class AnyOf(HourTest):
    """At least one of `tests` passes."""

    def __init__(self, *tests: HourTest):
        self.tests = tests

    def __call__(self, ctx: OverviewContext, i: int) -> bool:
        return any(test(ctx, i) for test in self.tests)


IS_SNOW = HasCode(SNOW_CODES)
IS_WET = AtLeast("precip_probability", RAIN_LIKELY_PROBABILITY)


# =====================================================================
# Phrasing: a rule's "now" and "later" messages
# =====================================================================

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

    def render(self, ctx: OverviewContext, i: int, **values) -> Tuple[str, float]:
        if ctx.window.is_now(i):
            return ctx.messages.say(self.now, **values), ctx.clock.next_hour
        ts = ctx.hourly.times[i]
        return ctx.messages.say(self.later, time=ctx.clock.approx_time(ts), **values), ts


# =====================================================================
# Rules
# =====================================================================

class Rule(ABC):
    """One rule. `evaluate` returns an Insight, or None when it has nothing
    to say. The plain-English description is in docs/overview-rules.md, the
    wordings in CORE_OverviewMessages.py."""

    def __init__(self, kind: str, severity: str = "info", icon: Optional[str] = None):
        self.kind = kind
        self.severity = severity
        self.icon = icon

    @abstractmethod
    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        """The insight for this forecast, or None."""

    def insight(self, message: str, valid_until: float, *, severity: Optional[str] = None,
                icon: Optional[str] = None, heading: Optional[str] = None) -> Insight:
        return Insight(
            self.kind,
            message,
            valid_until,
            severity or self.severity,
            icon or self.icon,
            heading,
        )


class FirstHourRule(Rule):
    """The first hour that passes `test`, said with `phrasing` (or
    `snow_phrasing` when that hour has a snow code)."""

    def __init__(self, kind: str, test: HourTest, phrasing: Phrasing, severity: str = "info",
                 snow_phrasing: Optional[Phrasing] = None):
        super().__init__(kind, severity)
        self.test = test
        self.phrasing = phrasing
        self.snow_phrasing = snow_phrasing

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        i = ctx.window.first(lambda i: self.test(ctx, i))
        if i is None:
            return None
        phrasing = self.phrasing
        if self.snow_phrasing is not None and IS_SNOW(ctx, i):
            phrasing = self.snow_phrasing
        message, valid_until = phrasing.render(ctx, i)
        return self.insight(message, valid_until, icon=phrasing.icon)


class ExtremeFeelsRule(Rule):
    """Feels like HEAT_FEELS_LIKE_C or more (checked first), or
    COLD_FEELS_LIKE_C or less: say how much, by when, and what to do."""

    HEAT = Phrasing("heat.now", "heat.later")
    COLD = Phrasing("cold.now", "cold.later")

    def __init__(self):
        super().__init__("extreme_feels", "warning")

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        feels = ctx.hourly.feels_like
        hours = [i for i in ctx.window.hours if at(feels, i) is not None]
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
        message, valid_until = phrasing.render(ctx, i, temp=degrees(feels[i]))
        return self.insight(message, valid_until)


class AirQualityRule(Rule):
    """US AQI reaching UNHEALTHY_US_AQI in the window: say now or from when."""

    def __init__(self):
        super().__init__("air_quality", "warning")

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        hours = hours_between(ctx.air.times, ctx.now, ctx.window.end)
        j = next((j for j in hours if (at(ctx.air.us_aqi, j) or 0) >= UNHEALTHY_US_AQI), None)
        if j is None:
            return None
        if j == hours[0]:
            return self.insight(ctx.messages.say("air.now"), ctx.clock.next_hour)
        ts = ctx.air.times[j]
        return self.insight(ctx.messages.say("air.later", time=ctx.clock.approx_time(ts)), ts)


class UvRule(Rule):
    """UV index VERY_HIGH_UV or more: from when to when, or until when if it
    already is."""

    def __init__(self):
        super().__init__("uv", "warning", "weather-clear-symbolic")
        self.test = AtLeast("uv", VERY_HIGH_UV)

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        hours = ctx.window.hours
        start = ctx.window.first(lambda i: self.test(ctx, i))
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
            return self.insight(ctx.messages.say("uv.now", time=end_str), ctx.clock.next_hour)
        start_ts = ctx.hourly.times[start]
        message = ctx.messages.say("uv.later", start=ctx.clock.approx_time(start_ts), end=end_str)
        return self.insight(message, start_ts)


class PrecipitationRule(Rule):
    """Rain or snow (a RAIN_LIKELY_PROBABILITY chance or more): easing at,
    lasting through, or starting at a time."""

    RAIN_ICON = "weather-showers-symbolic"
    SNOW_ICON = "weather-snow-symbolic"

    def __init__(self):
        super().__init__("precipitation")

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        window = ctx.window
        if not window.hours:
            return None
        first = window.hours[0]
        if IS_WET(ctx, first):
            return self._wet_now(ctx, IS_SNOW(ctx, first))

        start = window.first(lambda i: IS_WET(ctx, i))
        if start is None:
            return None
        snow = IS_SNOW(ctx, start)
        ts = ctx.hourly.times[start]
        message = ctx.messages.say(
            "snow.start" if snow else "rain.start",
            time=ctx.clock.approx_time(ts),
            chance=round(ctx.hourly.precip_probability[start]),
        )
        return self.insight(message, ts, icon=self.SNOW_ICON if snow else self.RAIN_ICON)

    def _wet_now(self, ctx: OverviewContext, snow: bool) -> Insight:
        icon = self.SNOW_ICON if snow else self.RAIN_ICON
        dry = ctx.window.first(lambda i: not IS_WET(ctx, i))
        if dry is None:
            message = ctx.messages.say(
                "snow.through" if snow else "rain.through",
                time=ctx.clock.approx_time(ctx.window.end),
            )
            return self.insight(message, ctx.clock.next_hour, icon=icon)

        ts = ctx.hourly.times[dry]
        message = ctx.messages.say(
            "snow.easing" if snow else "rain.easing", time=ctx.clock.approx_time(ts)
        )
        return self.insight(message, ts, icon=icon)


class WindRule(Rule):
    """Wind reaching STRONG_WIND_KMH: how fast and when; a warning from
    EXTREME_WIND_KMH."""

    PHRASING = Phrasing("wind.now", "wind.later")

    def __init__(self):
        super().__init__("wind", icon="weather-windy-symbolic")
        self.test = AtLeast("windspeed", STRONG_WIND_KMH, to_metric=Units.kmh)

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        i = ctx.window.first(lambda i: self.test(ctx, i))
        if i is None:
            return None
        speed = ctx.hourly.windspeed[i]
        speed_str = "{0:.0f} {1}".format(speed, ctx.hourly.wind_unit)
        message, valid_until = self.PHRASING.render(ctx, i, speed=speed_str)
        severity = "warning" if ctx.units.kmh(speed) >= EXTREME_WIND_KMH else "info"
        return self.insight(message, valid_until, severity=severity)


class FogRule(Rule):
    """Visibility under FOG_VISIBILITY_M or a fog code: now, around sunrise,
    or when."""

    PHRASING = Phrasing("fog.now", "fog.later")

    def __init__(self):
        super().__init__("fog", icon="weather-fog-symbolic")
        self.test = AnyOf(Below("visibility", FOG_VISIBILITY_M), HasCode(FOG_CODES))

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        i = ctx.window.first(lambda i: self.test(ctx, i))
        if i is None:
            return None
        ts = ctx.hourly.times[i]
        sunrise = ctx.sun.next_sunrise
        if not ctx.window.is_now(i) and sunrise is not None and abs(ts - sunrise) <= HOUR:
            return self.insight(ctx.messages.say("fog.sunrise"), ts)
        return self.insight(*self.PHRASING.render(ctx, i))


class TemperatureSwingRule(Rule):
    """A rise or drop of TEMPERATURE_SWING_C or more from now (the bigger
    change wins): say the temperature and when."""

    def __init__(self):
        super().__init__("temperature_swing")

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        temps = ctx.hourly.temperature
        hours = [i for i in ctx.window.hours if at(temps, i) is not None]
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
        message = ctx.messages.say(key, temp=degrees(temps[i]), time=ctx.clock.approx_time(ts))
        return self.insight(message, ts)


class TomorrowRule(Rule):
    """From OVERVIEW_TOMORROW_FROM_HOUR: rain likely tomorrow, or a high
    TOMORROW_DIFFERENCE_C warmer or cooler than today's. True until midnight."""

    def __init__(self):
        super().__init__("tomorrow")

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        if ctx.clock.local().hour < OVERVIEW_TOMORROW_FROM_HOUR:
            return None
        daily = ctx.daily
        # After midnight, "tomorrow" is another day
        valid_until = ctx.clock.next_midnight
        heading = C_("overview heading", "Tomorrow")

        if (daily.tomorrow_rain_chance or 0) >= RAIN_LIKELY_PROBABILITY:
            message = ctx.messages.say("tomorrow.rain", chance=round(daily.tomorrow_rain_chance))
            return self.insight(message, valid_until, icon=PrecipitationRule.RAIN_ICON, heading=heading)

        if daily.today_high is None or daily.tomorrow_high is None:
            return None
        difference = ctx.units.celsius(daily.tomorrow_high) - ctx.units.celsius(daily.today_high)
        if difference >= TOMORROW_DIFFERENCE_C:
            key = "tomorrow.warmer"
        elif difference <= -TOMORROW_DIFFERENCE_C:
            key = "tomorrow.cooler"
        else:
            return None
        message = ctx.messages.say(key, temp=degrees(daily.tomorrow_high))
        return self.insight(message, valid_until, heading=heading)


class SunRule(Rule):
    """Sunset within SUNSET_SOON_MINUTES by day, or sunrise within
    SUNRISE_SOON_MINUTES at night: say how soon, never more than
    OVERVIEW_RELATIVE_TOLERANCE off."""

    def __init__(self):
        super().__init__("sun")

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        sun = ctx.sun
        if sun.is_day:
            event, soon, sunset = sun.next_sunset, SUNSET_SOON_MINUTES, True
            icon = "daytime-sunset-symbolic"
        else:
            event, soon, sunset = sun.next_sunrise, SUNRISE_SOON_MINUTES, False
            icon = "daytime-sunrise-symbolic"
        if event is None or event - ctx.now > soon * MINUTE:
            return None
        result = self.phrase(ctx, event, sunset)
        if result is None:
            return None
        return self.insight(*result, icon=icon)

    @staticmethod
    def phrase(ctx: OverviewContext, event: float, sunset: bool) -> Optional[Tuple[str, float]]:
        """(message, valid_until) for "The sun sets in …", or None.

        Under an hour: minutes to the nearest 5 (halves down), true while no
        more than the tolerance off. Longer: "about N hours" (nearest hour,
        halves down) with the exact time, true while N is the nearest hour.
        In the last 2½ minutes there is nothing accurate to say.
        """
        name = "sunset" if sunset else "sunrise"
        minutes = (event - ctx.now) / MINUTE
        n = math.ceil(minutes / 5 - 0.5) * 5
        if n <= 0:
            return None
        if n < 60:
            valid_until = min(
                event - n * MINUTE + OVERVIEW_RELATIVE_TOLERANCE, event - 2.5 * MINUTE
            )
            return ctx.messages.say_count(f"{name}.minutes", n), valid_until

        n = math.ceil(minutes / 60 - 0.5)
        # Until n - ½ hours are left; from 57½ minutes the minutes form takes over
        valid_until = event - max((n - 0.5) * HOUR, 57.5 * MINUTE)
        return ctx.messages.say_count(f"{name}.hours", n, time=ctx.clock.time(event)), valid_until


class CalmRule(Rule):
    """Always applies: the fallback when nothing else is worth saying."""

    def __init__(self):
        super().__init__("calm")

    def evaluate(self, ctx: OverviewContext) -> Optional[Insight]:
        end = ctx.window.end
        return self.insight(ctx.messages.say("calm", time=ctx.clock.approx_time(end)), end)


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
                Phrasing("storm.now", "storm.later", "weather-storm-symbolic"),
                severity="error",
            ),
            FirstHourRule(
                "freezing",
                HasCode(FREEZING_CODES),
                Phrasing("freezing.now", "freezing.later", "weather-showers-symbolic"),
                severity="warning",
            ),
            FirstHourRule(
                "heavy_precipitation",
                AnyOf(
                    HasCode(HEAVY_RAIN_CODES | HEAVY_SNOW_CODES),
                    AtLeast("precipitation", HEAVY_PRECIPITATION_MM),
                ),
                Phrasing("heavy_rain.now", "heavy_rain.later", "weather-showers-symbolic"),
                severity="warning",
                snow_phrasing=Phrasing("heavy_snow.now", "heavy_snow.later", "weather-snow-symbolic"),
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

SEVERITY_RANK = {"info": 0, "warning": 1, "error": 2}


class AnnouncePlanner:
    """Decides which insight the overview shows and when it opens by itself.

    - **How often**: the score adds up the priorities (÷ 100) of everything
      worth saying. The next opening is OVERVIEW_ANNOUNCE_BASE_MINUTES ÷
      (1 + score), between the MIN and MAX minutes, spread at random. A busy
      forecast opens more often; as insights expire it calms down.
    - **What**: each opening shows the insight whose turn it is: never shown
      ones first (most important first), then the highest priority × minutes
      since it was last shown. Lower insights get their turn too.
    - **Escalation**: something more severe than before (a storm appears)
      opens at once, unless it was shown in the last MAX minutes (so one that
      comes and goes counts once), and never within MIN minutes of the last
      opening.
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
        self.pending_rank = -1  # the highest severity pending at the last run

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

    def whose_turn(self, insights: List[Insight], now: float) -> Insight:
        def turn(insight: Insight):
            last = self.last_shown.get(insight.kind)
            if last is None:
                return (1, insight.priority)  # never shown: first, by priority
            return (0, insight.priority * (now - last) / 60)
        return max(insights, key=turn)

    def decide(self, insights: List[Insight], showing: Optional[str], now: float,
               rng: random.Random = random) -> Tuple[Optional[Insight], bool]:
        """(the insight to show, whether to open the overview) for the
        insights true now, most important first. `showing` is the kind on
        screen, or None when it has expired: then another one takes its
        place silently, and the overview still waits for its next opening."""
        if not insights:
            return None, False
        pending = self.worth_saying(insights)
        top = max(pending, key=lambda i: (SEVERITY_RANK[i.severity], i.priority))
        rank = SEVERITY_RANK[top.severity]
        escalated = rank > self.pending_rank
        self.pending_rank = rank

        # Escalation skips the wait, but only for something not shown lately
        # (a severe insight that comes and goes counts once), and never
        # straight after another opening
        last_opening = max(self.last_shown.values(), default=-math.inf)
        top_last = self.last_shown.get(top.kind, -math.inf)
        if (
            escalated
            and now - last_opening >= OVERVIEW_ANNOUNCE_MIN_MINUTES * 60
            and now - top_last >= OVERVIEW_ANNOUNCE_MAX_MINUTES * 60
        ):
            chosen = top
        elif not self.last_shown or now >= self.next_announce:
            # The first opening, or its time has come
            chosen = self.whose_turn(pending, now)
        else:
            # Not time to open: keep the text up to date, silently
            same = next((i for i in insights if i.kind == showing), None)
            return same or pending[0], False

        self.last_shown[chosen.kind] = now
        minutes = self.interval_minutes(self.score(pending), rng.uniform(-1, 1))
        self.next_announce = now + minutes * 60
        return chosen, True

    def note_shown(self, kind: str, now: float) -> None:
        """The user opened the overview on `kind`: that counts as its turn."""
        self.last_shown[kind] = now
