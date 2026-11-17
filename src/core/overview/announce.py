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
- group(): several urgent insights at about the same time open together,
  each with its own sentence, so one never hides another.
- should_notify(): which openings are also worth a notification.

No GTK, so it is tested on made-up insights (tests/test_overview_rules.py).
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from ...config import (
    OVERVIEW_FORGET_MINUTES,
    OVERVIEW_GROUP_MAX,
    OVERVIEW_GROUP_MIN_LEVEL,
    OVERVIEW_GROUP_WINDOW_MINUTES,
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
    members: Tuple[Insight, ...]  # everything shown (a group), `insight` first
    reason: Optional[str]  # NEWS or REMINDER when it opens; None: a silent update
    wake_at: Optional[float]  # when to run again; None: only after the next refresh
    topics: frozenset  # the topics of the insights taking turns now
    left_out: Tuple[Tuple[Insight, str], ...] = ()  # did not join the group, and why


def worth_saying(insights: Sequence[Insight]) -> List[Insight]:
    """The insights that take turns: calm only when there is nothing else."""
    return [i for i in insights if i.kind != "calm"] or list(insights[:1])


def importance(insight: Insight) -> Tuple[int, int]:
    """Higher is more important: the level first, then the priority."""
    return (insight.rank, insight.priority)


def decide(insights: Sequence[Insight], memory: AnnounceMemory, showing: Sequence[str],
           now: float) -> Decision:
    """What to show for the insights true now (most important first).
    `showing` are the kinds on screen, the first one leading, so a silent
    update keeps them. Updates `memory` when the overview opens."""
    memory.note_seen(insights, now)
    if not insights:
        return Decision(None, (), None, None, frozenset())

    pending = worth_saying(insights)
    gap_over = now >= memory.last_opening + OVERVIEW_MIN_GAP_MINUTES * MINUTE
    ready = [i for i in pending if _is_due(memory, i, now)]

    left_out: Tuple[Tuple[Insight, str], ...] = ()
    if ready and gap_over:
        # News before reminders, then the most important
        lead = max(ready, key=lambda i: (memory.is_new(i),) + importance(i))
        members, left_out = group(lead, pending, now)
        reason = NEWS if any(memory.is_new(m) for m in members) else REMINDER
        for member in members:
            memory.note_said(member, now)
        memory.last_opening = now
    else:
        members = _still_showing(insights, showing) or (max(pending, key=importance),)
        reason = None

    topics = frozenset(i.topic for i in pending)
    return Decision(members[0], members, reason, _wake_at(pending, memory, now), topics, left_out)


def group(lead: Insight, pending: Sequence[Insight], now: float
          ) -> Tuple[Tuple[Insight, ...], Tuple[Tuple[Insight, str], ...]]:
    """(the group `lead` opens, lead first; the others, each with why it
    didn't join). Up to OVERVIEW_GROUP_MAX insights of medium or above that
    happen within OVERVIEW_GROUP_WINDOW_MINUTES of the lead, one per topic,
    the most urgent first. The ones left out keep their own turn."""
    min_rank = LEVEL_RANK[OVERVIEW_GROUP_MIN_LEVEL]
    if lead.rank < min_rank:
        return (lead,), ()
    members = [lead]
    left_out = []
    for other in sorted(pending, key=importance, reverse=True):
        if other is lead:
            continue
        apart_minutes = abs(_when(other, now) - _when(lead, now)) / MINUTE
        if other.rank < min_rank:
            why = f"below {OVERVIEW_GROUP_MIN_LEVEL}"
        elif other.kind == "tomorrow":
            why = "about tomorrow"
        elif apart_minutes > OVERVIEW_GROUP_WINDOW_MINUTES:
            why = f"{apart_minutes:.0f} min from the lead"
        elif any(member.topic == other.topic for member in members):
            why = f"same topic as {next(m.kind for m in members if m.topic == other.topic)}"
        elif len(members) >= OVERVIEW_GROUP_MAX:
            why = f"already {OVERVIEW_GROUP_MAX}"
        else:
            members.append(other)
            continue
        left_out.append((other, why))
    return tuple(members), tuple(left_out)


def _when(insight: Insight, now: float) -> float:
    """When it happens: the hour or event it is about, or now."""
    return insight.about if insight.about is not None else now


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


def _still_showing(insights: Sequence[Insight], showing: Sequence[str]) -> Tuple[Insight, ...]:
    """The insights on screen that are still true, in the same order; none
    when the leading one has stopped being true."""
    by_kind = {i.kind: i for i in insights}
    if not showing or showing[0] not in by_kind:
        return ()
    return tuple(by_kind[kind] for kind in showing if kind in by_kind)


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
