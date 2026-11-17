"""Announcing: which insight the overview shows, and when it opens by itself.

Source of truth: "When the overview opens, and with what" in
docs/overview-rules.md. In short, the overview opens when it has something
new to say, and only now and then to remind of something it said:

- AnnounceMemory: what has been said for one location (by fingerprint),
  when, and how many times. The engine keeps it across refreshes and
  forgets it when the location changes.
- decide(): a pure function of the insights true now, the memory and the
  clock. Each insight is due now when it is news, later when it was said
  before (a reminder that waits longer each time), or never (low and calm,
  said once). It returns a Decision: what to show, whether it opens, and
  when to run again.
- should_notify(): which openings are also worth a notification.

No GTK, so it is tested on made-up insights (tests/test_overview_rules.py).
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from ...config import (
    OVERVIEW_FORGET_MINUTES,
    OVERVIEW_MIN_GAP_MINUTES,
    OVERVIEW_REMIND_BACKOFF,
    OVERVIEW_REMIND_MAX_MINUTES,
    OVERVIEW_REMIND_MINUTES,
)
from .insight import LEVEL_RANK, Insight

MINUTE = 60

# Why the overview opens
NEWS = "news"  # something not said before
REMINDER = "reminder"  # something said before, whose reminder is due


@dataclass
class Said:
    """What the memory knows about one insight."""

    last: float  # unix time it was last announced
    times: int  # how many times it has been announced
    seen: float  # unix time it was last true


class AnnounceMemory:
    """What has been said for one location, by fingerprint."""

    def __init__(self):
        self.forget()

    def forget(self) -> None:
        self.said: Dict[tuple, Said] = {}
        self.last_opening = -math.inf

    def is_new(self, insight: Insight) -> bool:
        return insight.fingerprint not in self.said

    def times_said(self, insight: Insight) -> int:
        said = self.said.get(insight.fingerprint)
        return said.times if said else 0

    def due_at(self, insight: Insight) -> Optional[float]:
        """When `insight` may open the overview: -inf when it is news, the
        time of its next reminder, or None when it is never repeated (low and
        calm are said once)."""
        said = self.said.get(insight.fingerprint)
        if said is None:
            return -math.inf
        first_minutes = OVERVIEW_REMIND_MINUTES.get(insight.level)
        if first_minutes is None:
            return None
        minutes = first_minutes * OVERVIEW_REMIND_BACKOFF ** (said.times - 1)
        return said.last + min(minutes, OVERVIEW_REMIND_MAX_MINUTES) * MINUTE

    def note_seen(self, insights: Sequence[Insight], now: float) -> None:
        """These insights are true now. One that hasn't been true for
        OVERVIEW_FORGET_MINUTES is forgotten, so the memory stays small. Not
        straight away: a storm that comes and goes still counts once."""
        for insight in insights:
            said = self.said.get(insight.fingerprint)
            if said is not None:
                said.seen = now
        too_old = now - OVERVIEW_FORGET_MINUTES * MINUTE
        self.said = {fp: said for fp, said in self.said.items() if said.seen >= too_old}

    def note_said(self, insight: Insight, now: float) -> None:
        """`insight` was just announced (or the user opened the overview on it)."""
        said = self.said.get(insight.fingerprint)
        if said is None:
            self.said[insight.fingerprint] = Said(last=now, times=1, seen=now)
        else:
            said.last, said.times, said.seen = now, said.times + 1, now


@dataclass(frozen=True)
class Decision:
    """What decide() made of the insights true now."""

    insight: Optional[Insight]  # what the overview shows; None: nothing
    reason: Optional[str]  # NEWS or REMINDER when it opens; None: a silent update
    wake_at: Optional[float]  # when to run again; None: only after the next refresh
    topics: frozenset  # the topics of the insights taking turns now
    waiting: Tuple[Insight, ...] = ()  # due too, but not shown now: the next turns


def worth_saying(insights: Sequence[Insight]) -> List[Insight]:
    """The insights that take turns: calm only when there is nothing else."""
    return [i for i in insights if i.kind != "calm"] or list(insights[:1])


def importance(insight: Insight) -> Tuple[int, int]:
    """Higher is more important: the level first, then the priority."""
    return (insight.rank, insight.priority)


def decide(insights: Sequence[Insight], memory: AnnounceMemory, showing: Optional[str],
           now: float) -> Decision:
    """What to show for the insights true now (most important first).
    `showing` is the kind on screen, so a silent update keeps it. Updates
    `memory` when the overview opens."""
    memory.note_seen(insights, now)
    if not insights:
        return Decision(None, None, None, frozenset())

    pending = worth_saying(insights)
    gap_over = now >= memory.last_opening + OVERVIEW_MIN_GAP_MINUTES * MINUTE
    ready = [i for i in pending if _is_due(memory, i, now)]

    if ready and gap_over:
        # News before reminders, then the most important; the others that
        # are due get the next turns, one opening each
        chosen = max(ready, key=lambda i: (memory.is_new(i),) + importance(i))
        reason = NEWS if memory.is_new(chosen) else REMINDER
        memory.note_said(chosen, now)
        memory.last_opening = now
    else:
        same = next((i for i in insights if i.kind == showing), None)
        chosen = same or max(pending, key=importance)
        reason = None

    waiting = tuple(i for i in ready if i is not chosen)
    topics = frozenset(i.topic for i in pending)
    return Decision(chosen, reason, _wake_at(pending, memory, now), topics, waiting)


def should_notify(reason: Optional[str], level: str) -> bool:
    """Whether an opening is also sent as a notification (while the window
    can't be seen): news of medium or above, and reminders of extreme ones.
    Low and calm never are."""
    if reason == NEWS:
        return LEVEL_RANK[level] >= LEVEL_RANK["medium"]
    if reason == REMINDER:
        return level == "extreme"
    return False


def _is_due(memory: AnnounceMemory, insight: Insight, now: float) -> bool:
    due = memory.due_at(insight)
    return due is not None and due <= now


def _wake_at(pending: Sequence[Insight], memory: AnnounceMemory, now: float) -> float:
    """The next moment something changes: an insight stops being true, a
    reminder is due, or the gap ends for one that is waiting."""
    gap_end = memory.last_opening + OVERVIEW_MIN_GAP_MINUTES * MINUTE
    moments = [i.valid_until for i in pending]
    for insight in pending:
        due = memory.due_at(insight)
        if due is not None:
            moments.append(max(due, gap_end))
    return max(min(moments), now + 1)
