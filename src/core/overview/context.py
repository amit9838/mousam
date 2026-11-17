"""The forecast as the overview rules see it.

OverviewContext is made of small parts (Clock, Units, HourlySeries,
SunTimes, DailyOutlook, AirSeries) and the Window worked out from them.
It has no GTK, so tests build it by hand from made-up data.
"""

import math
from dataclasses import dataclass, field, fields
from datetime import datetime, timedelta, timezone
from gettext import pgettext as C_
from typing import TYPE_CHECKING, Any, Callable, List, Optional
from zoneinfo import ZoneInfo

from ...config import (
    OVERVIEW_DAY_MIN_HOURS,
    OVERVIEW_HOURS,
    OVERVIEW_ROUND_FAR_MINUTES,
    OVERVIEW_ROUNDING,
)
from .messages import MessageBook

if TYPE_CHECKING:
    from .hour_tests import HourTest

HOUR = 3600
MINUTE = 60


def hours_between(times: List[int], start: float, end: float) -> List[int]:
    """Indices of the hours that overlap [start, end): the current one first."""
    return [i for i, ts in enumerate(times) if ts + HOUR > start and ts < end]


def value_at(values: list, i: int) -> Optional[Any]:
    """values[i], or None when the list is short."""
    return values[i] if 0 <= i < len(values) else None


@dataclass
class Clock:
    """Now, and how times are written: the city's time zone, 12 or 24 h."""

    now: float
    tz: Optional[ZoneInfo] = None
    use_24h: bool = False

    def local(self, ts: Optional[float] = None) -> datetime:
        return datetime.fromtimestamp(self.now if ts is None else ts, tz=self.tz)

    def _format(self, dt: datetime) -> str:
        return dt.strftime("%H:%M" if self.use_24h else "%-I:%M %p")

    def time(self, ts: float) -> str:
        """The exact time ("6:12 PM", "18:12")."""
        return self._format(self.local(ts))

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
        return self._format(local.replace(hour=0, minute=0) + timedelta(minutes=rounded))

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

    @classmethod
    def has_series(cls, series: str) -> bool:
        return series in {f.name for f in fields(cls)}

    def value(self, series: str, i: int) -> Optional[Any]:
        """One hour's value of a series, or None when it is missing. Read
        hours this way; index a list directly only for an hour a test has
        just passed (so its value is there)."""
        return value_at(getattr(self, series), i)

    def hour_near(self, ts: float) -> Optional[int]:
        """The hour nearest `ts` (at exactly half past, the later one), or
        None when no hour starts within half an hour of it."""
        if not self.times:
            return None
        i = min(range(len(self.times)), key=lambda k: (abs(self.times[k] - ts), -self.times[k]))
        return i if abs(self.times[i] - ts) <= HOUR / 2 else None


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

    def first(self, test: "HourTest") -> Optional[int]:
        """The first hour of the window that passes `test`."""
        return self.window.first(lambda i: test(self, i))

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
            return value_at(_series(daily, name), i)
    return None
