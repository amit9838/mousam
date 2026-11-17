"""Insight: one thing worth saying about the coming hours.

Rules (rules.py) return them; the planner decides which one to show.
Source of truth: docs/overview-rules.md.
"""

from dataclasses import dataclass, field
from typing import Optional

from ...config import OVERVIEW_PRIORITIES, OVERVIEW_SHOW_BASE_SECONDS, OVERVIEW_SHOW_EXTRA_SECONDS

# From nothing to say to danger, in order (see "Levels" in docs/overview-rules.md)
LEVELS = ("calm", "low", "medium", "high", "extreme")
LEVEL_RANK = {level: rank for rank, level in enumerate(LEVELS)}


@dataclass
class Insight:
    """One thing worth saying about the coming hours."""

    kind: str  # a key of OVERVIEW_PRIORITIES: the rule that said it
    message: str  # one whole translated sentence
    valid_until: float  # unix time from which the message is no longer true
    level: str = "medium"  # one of LEVELS
    icon: Optional[str] = None  # symbolic icon shown before the message
    heading: Optional[str] = None  # None: the window's heading (Today / Tonight)
    topic: str = ""  # what it is about, one notification each ("rain", "air"); "" = kind
    key: str = ""  # the message key it was said with ("rain.start")
    about: Optional[float] = None  # the forecast hour or event it is about; None: now
    priority: int = field(init=False)
    show_seconds: int = field(init=False)  # how long the message stays open

    def __post_init__(self):
        if self.level not in LEVEL_RANK:
            raise ValueError(f"Unknown overview level {self.level!r}")
        self.topic = self.topic or self.kind
        self.priority = OVERVIEW_PRIORITIES[self.kind]
        self.show_seconds = OVERVIEW_SHOW_BASE_SECONDS + OVERVIEW_SHOW_EXTRA_SECONDS[self.level]

    @property
    def rank(self) -> int:
        """The level as a number, higher is more urgent."""
        return LEVEL_RANK[self.level]

    @property
    def fingerprint(self) -> tuple:
        """What makes two insights the same: it changes when the forecast
        does (another hour, another message, another level), not as time
        passes ("in 40 minutes" becoming "in 35 minutes")."""
        return (self.kind, self.key, self.level, self.about)
