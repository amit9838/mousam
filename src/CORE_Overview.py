"""Overview engine: decides what the overview says, and when.

What to say comes from the rules (CORE_OverviewRules.py, described in
docs/overview-rules.md): the engine runs the rule book and takes the most
important insight.

When:

- Lazy: nothing is worked out while the app starts. The first run is
  OVERVIEW_FIRST_DELAY seconds after the first data load, later ones
  OVERVIEW_REFRESH_DELAY seconds after each refresh.
- Always true: the rules run again before the current insight stops being
  true (its valid_until), so "in 40 minutes" or "around 4:00 PM" is never
  shown once it is wrong. These updates are silent.
- Announced now and then: the overview opens by itself on the first insight,
  when a different kind of insight takes over (say, a storm appears), and
  again after a random number of minutes from OVERVIEW_REPUBLISH_MINUTES,
  sooner for urgent insights.
- Varied wording: each announcement draws a new seed, which picks one of
  the message's wordings (CORE_OverviewMessages.py). Silent updates keep the
  seed, so the wording stays put while only the values change.
- Only while the "show-overview" setting is on: when it is off nothing is
  scheduled or worked out.

Publish / subscribe: the engine emits "overview-changed" with `announce`
(open the overview, or just update its text). Widgets connect to it and read
`overview_engine.insight` and `overview_engine.heading`.
"""

import random
import time
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import gi

gi.require_version("GLib", "2.0")

from gi.repository import GLib, GObject  # noqa: E402

from .configs import (  # noqa: E402
    OVERVIEW_FIRST_DELAY,
    OVERVIEW_REFRESH_DELAY,
    OVERVIEW_REPUBLISH_MINUTES,
)
from .CORE_Helpers import get_timezone_from_selected_city  # noqa: E402
from .CORE_Logging import get_logger  # noqa: E402
from .CORE_OverviewRules import Insight, OverviewContext, RuleBook  # noqa: E402
from .CORE_weatherData import weather_manager  # noqa: E402
from .settings import settings  # noqa: E402

logger = get_logger("overview")


class OverviewEngine(GObject.Object):
    """Runs the rules lazily and publishes the best insight."""

    __gsignals__ = {
        # announce: True to open the overview, False to only update its text
        "overview-changed": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    def __init__(self):
        super().__init__()
        self.insight: Optional[Insight] = None
        self.heading: Optional[str] = None
        self._timer_id = 0
        self._first_built = False
        self._scheduled_for = None  # the hourly data a run is scheduled or done for
        self._next_announce = 0.0  # when the overview may open by itself again
        self._seed = 0  # picks the wordings; new on each announcement
        weather_manager.connect("notify::is-ready", self._on_ready_changed)
        settings.connect("changed::show-overview", self._on_enabled_changed)

    # ---------- Reading ----------

    def current(self) -> Optional[Insight]:
        """The insight to show, or None when there is none or it is no
        longer true (the next run will replace it)."""
        if self.insight is None or self.insight.valid_until <= time.time():
            return None
        return self.insight

    # ---------- Scheduling ----------

    def _on_enabled_changed(self, *_args) -> None:
        if settings.show_overview:
            self._schedule()
        else:
            self._reset()

    def _on_ready_changed(self, *_args) -> None:
        # Emitted from the fetch worker threads: continue on the main loop
        GLib.idle_add(self._schedule)

    def _schedule(self) -> bool:
        if not settings.show_overview:
            return GLib.SOURCE_REMOVE

        if not weather_manager.is_ready:
            # Data cleared (location switch, failed fetch): drop the old overview
            self._reset()
            return GLib.SOURCE_REMOVE

        # is-ready fires once per update; schedule once per fetch
        hourly = weather_manager.hourly_forecast
        if hourly is self._scheduled_for:
            return GLib.SOURCE_REMOVE
        self._scheduled_for = hourly

        delay = OVERVIEW_REFRESH_DELAY if self._first_built else OVERVIEW_FIRST_DELAY
        self._run_in(delay)
        return GLib.SOURCE_REMOVE

    def _run_in(self, seconds: float) -> None:
        """The next run, replacing any already scheduled (a one-shot timer)."""
        self._cancel()
        seconds = max(1, int(seconds))
        logger.debug(f"Overview runs in {seconds}s")
        self._timer_id = GLib.timeout_add_seconds(seconds, self._run)

    def _run(self) -> bool:
        self._timer_id = 0
        self._first_built = True
        if not settings.show_overview or not weather_manager.is_ready:
            return GLib.SOURCE_REMOVE

        now = time.time()
        insight, heading = self._best_insight(now)
        if insight is None:
            self._set(None, None, announce=False)
            return GLib.SOURCE_REMOVE

        # Open the overview for something new, or when its time has come
        is_new = self.insight is None or insight.kind != self.insight.kind
        announce = is_new or now >= self._next_announce
        if announce:
            low, high = OVERVIEW_REPUBLISH_MINUTES[insight.severity]
            self._next_announce = now + random.uniform(low, high) * 60
            # A fresh wording for the announcement (same insight, same data)
            self._seed = random.getrandbits(32)
            insight, heading = self._best_insight(now)
            if insight is None:
                self._set(None, None, announce=False)
                return GLib.SOURCE_REMOVE

        logger.debug(
            f"Overview {'announced' if announce else 'updated'}: {insight.message} "
            f"(valid {int(insight.valid_until - now)}s)"
        )
        self._set(insight, heading, announce)

        # Run again before the message stops being true, or to announce it again
        self._run_in(min(insight.valid_until, self._next_announce) - now)
        return GLib.SOURCE_REMOVE

    def _best_insight(self, now: float):
        """(the most important insight, its heading), from the latest data."""
        try:
            tz = ZoneInfo(get_timezone_from_selected_city())
        except (ZoneInfoNotFoundError, ValueError):
            tz = None
        try:
            ctx = OverviewContext.from_models(
                weather_manager.hourly_forecast,
                weather_manager.daily_forecast,
                weather_manager.air_pollution,
                now,
                tz,
                imperial=settings.unit == "imperial",
                use_24h=settings.is_using_24h_clock,
                seed=self._seed,
            )
            insights = RuleBook.default().run(ctx)
        except Exception as e:  # noqa: BLE001 - ignore on fail: no overview this time
            logger.debug(f"Overview skipped: {e!r}")
            return None, None
        if not insights:
            return None, None
        best = insights[0]
        return best, best.heading or ctx.window.heading

    # ---------- Publishing ----------

    def _set(self, insight: Optional[Insight], heading: Optional[str], announce: bool) -> None:
        unchanged = (
            not announce
            and (insight.message if insight else None) == (self.insight.message if self.insight else None)
            and heading == self.heading
        )
        self.insight = insight
        self.heading = heading
        if not unchanged:
            self.emit("overview-changed", announce)

    def _reset(self) -> None:
        self._cancel()
        self._scheduled_for = None
        self._next_announce = 0.0
        self._set(None, None, announce=False)

    def _cancel(self) -> None:
        if self._timer_id:
            GLib.source_remove(self._timer_id)
            self._timer_id = 0


# Singleton instance
overview_engine = OverviewEngine()
