"""Hour tests: yes/no questions about one forecast hour, combined by
composition to describe what a rule looks for."""

from abc import ABC, abstractmethod
from typing import Callable, Iterable, Optional

from ...config import RAIN_LIKELY_PROBABILITY
from .context import HourlySeries, OverviewContext, Units

# WMO weather codes
STORM_CODES = {95, 96, 99}
FREEZING_CODES = {56, 57, 66, 67}
SNOW_CODES = {71, 73, 75, 77, 85, 86}
HEAVY_RAIN_CODES = {65, 82}
HEAVY_SNOW_CODES = {75, 86}
FOG_CODES = {45, 48}


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
        if not HourlySeries.has_series(series):
            raise ValueError(f"HourlySeries has no series {series!r}")
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
IS_DRY = Below("precip_probability", RAIN_LIKELY_PROBABILITY)  # an hour with no data is neither
