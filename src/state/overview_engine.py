"""Overview engine: runs the overview rules and publishes what to show.

What to say comes from the rules (core/overview/rules.py, described in
docs/overview-rules.md). Which insight to show, and when the overview opens
by itself, is the AnnouncePlanner's call (same file): a busy forecast opens
it more often, each opening shows the insight whose turn it is, and
something turning severe opens it at once.

The engine adds the timing around them:

- Lazy: nothing is worked out while the app starts. The first run is
  OVERVIEW_FIRST_DELAY seconds after the first data load, later ones
  OVERVIEW_REFRESH_DELAY seconds after each refresh.
- Always true: the rules run again before the shown insight stops being
  true (its valid_until), so "in 40 minutes" or "around 4:00 PM" is never
  shown once it is wrong. These updates are silent.
- Refreshes don't count: a refresh clears the weather data for a moment, but
  the engine keeps what it has shown and when it opens next, so Ctrl+R,
  auto-refresh or a units change neither open the overview nor reset its
  turns. Only a location change (or turning the overview off) starts over.
- Varied wording: each opening draws a new seed, which picks one of the
  message's wordings (core/overview/messages.py). Silent updates keep the
  seed, so the wording stays put while only the values change.
- Only while it has somewhere to go: the overview ("show-overview") or
  notifications ("show-notifications") is on. With both off nothing is
  scheduled or worked out.
- Where it goes is up to the subscribers: the main window's overview while
  the window can be seen, a notification (sent by the app) otherwise.

Publish / subscribe: the engine emits "overview-changed" with `announce`
(open the overview, or just update its text). Widgets connect to it and read
`overview_engine.current()` and `overview_engine.heading`.
"""

import logging
import random
import time
from typing import List, Optional, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import gi

gi.require_version("GLib", "2.0")

from gi.repository import GLib, GObject  # noqa: E402

from ..config import OVERVIEW_FIRST_DELAY, OVERVIEW_REFRESH_DELAY  # noqa: E402
from ..services.selected_city import get_timezone_from_selected_city  # noqa: E402
from ..core.log import get_logger  # noqa: E402
from ..core.overview.context import OverviewContext  # noqa: E402
from ..core.overview.insight import Insight  # noqa: E402
from ..core.overview.rules import AnnouncePlanner, RuleBook  # noqa: E402
from .weather_store import weather_store  # noqa: E402
from ..services.settings import settings  # noqa: E402

logger = get_logger("overview")


class OverviewEngine(GObject.Object):
    """Runs the rules lazily and publishes the insight to show."""

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
        self._planner = AnnouncePlanner()  # what was shown when, and the next opening
        self._location = None  # the selected city the planner's memory belongs to
        self._seed = 0  # picks the wordings; new on each opening
        weather_store.connect("notify::is-ready", self._on_ready_changed)
        settings.connect("changed::show-overview", self._on_enabled_changed)
        settings.connect("changed::show-notifications", self._on_enabled_changed)

    # ---------- Reading ----------

    def current(self) -> Optional[Insight]:
        """The insight to show, or None when there is none or it is no
        longer true (the next run will replace it)."""
        if self.insight is None or self.insight.valid_until <= time.time():
            return None
        return self.insight

    @staticmethod
    def enabled() -> bool:
        """Whether the overview has somewhere to go: the overview or the
        notifications are on."""
        return settings.show_overview or settings.show_notifications

    def note_shown(self) -> None:
        """The user opened the overview: that counts as the insight's turn."""
        if self.insight is not None:
            self._planner.note_shown(self.insight.kind, time.time())

    # ---------- Scheduling ----------

    def _on_enabled_changed(self, *_args) -> None:
        if self.enabled():
            self._schedule()
        else:
            self._reset()

    def _on_ready_changed(self, *_args) -> None:
        self._schedule()

    def _schedule(self) -> None:
        if not self.enabled():
            return

        if not weather_store.is_ready:
            if settings.selected_city != self._location:
                # Another city: start over
                self._reset()
            else:
                # A refresh (or a failed one): keep what was shown and when it
                # opens next; the shown insight stays until it stops being true
                self._cancel()
                self._scheduled_for = None
            return

        # Once per fetch: turning a setting on again doesn't move a run
        # already scheduled for this data
        hourly = weather_store.hourly_forecast
        if hourly is self._scheduled_for:
            return
        self._scheduled_for = hourly

        delay = OVERVIEW_REFRESH_DELAY if self._first_built else OVERVIEW_FIRST_DELAY
        self._run_in(delay)

    def _run_in(self, seconds: float) -> None:
        """The next run, replacing any already scheduled (a one-shot timer)."""
        self._cancel()
        seconds = max(1, int(seconds))
        logger.debug(f"Overview runs in {seconds}s")
        self._timer_id = GLib.timeout_add_seconds(seconds, self._run)

    def _run(self) -> bool:
        self._timer_id = 0
        self._first_built = True
        if not self.enabled() or not weather_store.is_ready:
            return GLib.SOURCE_REMOVE

        now = time.time()
        if settings.selected_city != self._location:
            self._planner.forget()
            self._location = settings.selected_city

        insights, window_heading = self._insights(now)
        showing = self.insight.kind if self.current() is not None else None
        insight, announce = self._planner.decide(insights, showing, now)
        if logger.isEnabledFor(logging.DEBUG):
            self._log_turns(insights, insight, announce, now)
        if insight is None:
            self._set(None, None, announce=False)
            return GLib.SOURCE_REMOVE

        if announce:
            # A fresh wording for the opening (same insight, same data)
            self._seed = random.getrandbits(32)
            fresh, window_heading = self._insights(now)
            insight = next((i for i in fresh if i.kind == insight.kind), insight)

        heading = insight.heading or window_heading
        logger.debug(
            f"Overview {'announced' if announce else 'updated'}: {insight.message} "
            f"(valid {int(insight.valid_until - now)}s, "
            f"next opening in {int(self._planner.next_announce - now)}s)"
        )
        self._set(insight, heading, announce)

        # Run again before the message stops being true, or to open it again
        self._run_in(min(insight.valid_until, self._planner.next_announce) - now)
        return GLib.SOURCE_REMOVE

    def _log_turns(self, insights: List[Insight], chosen: Optional[Insight],
                   announce: bool, now: float) -> None:
        """Debug log: every insight with its priority and turn, the score,
        the one chosen now and the one in line for the next opening."""
        planner = self._planner
        pending = planner.worth_saying(insights)
        next_at = planner.next_announce
        logger.debug(
            f"Overview: {len(insights)} insights, {len(pending)} taking turns, "
            f"score {planner.score(pending):.2f}"
        )
        # The turns as they stand now, after decide() noted any opening;
        # the ones not taking turns (calm beside something else) go last
        resting = [i for i in insights if i not in pending]
        for insight in planner.turn_order(pending, now) + resting:
            never_shown, value = planner.turn(insight, now)
            turn = "never shown" if never_shown else f"turn {value:.0f}"
            taking_turns = "" if insight in pending else ", not taking turns"
            logger.debug(
                f"  {insight.kind}: priority {insight.priority}, "
                f"{insight.severity}, {turn}{taking_turns}"
            )
        if chosen is None:
            return
        winner = f"{chosen.kind} ({'opens' if announce else 'silent update'})"
        following = planner.turn_order(pending, next_at)
        logger.debug(
            f"Overview winner: {winner}; next: {following[0].kind} "
            f"at the next opening in {int(next_at - now)}s"
        )

    def _insights(self, now: float) -> Tuple[List[Insight], Optional[str]]:
        """(every insight true now, most important first; the window's
        heading), from the latest data. Ignore on fail: ([], None)."""
        try:
            tz = ZoneInfo(get_timezone_from_selected_city())
        except (ZoneInfoNotFoundError, ValueError):
            tz = None
        try:
            ctx = OverviewContext.from_models(
                weather_store.hourly_forecast,
                weather_store.daily_forecast,
                weather_store.air_pollution,
                now,
                tz,
                imperial=settings.unit == "imperial",
                use_24h=settings.is_using_24h_clock,
                seed=self._seed,
            )
            return RuleBook.default().run(ctx), ctx.window.heading
        except Exception as e:  # noqa: BLE001 - ignore on fail: no overview this time
            logger.debug(f"Overview skipped: {e!r}")
            return [], None

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
        """Start over: another city, or both overview and notifications were
        turned off."""
        self._cancel()
        self._scheduled_for = None
        self._planner.forget()
        self._location = None
        self._set(None, None, announce=False)

    def _cancel(self) -> None:
        if self._timer_id:
            GLib.source_remove(self._timer_id)
            self._timer_id = 0


# Singleton instance
overview_engine = OverviewEngine()
