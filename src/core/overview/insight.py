"""Insight: one thing worth saying about the coming hours.

Rules (rules.py) return them; the planner decides which one to show.
Source of truth: docs/overview-rules.md.
"""

from dataclasses import dataclass, field
from typing import Optional

from ...config import OVERVIEW_PRIORITIES, OVERVIEW_SHOW_BASE_SECONDS, OVERVIEW_SHOW_EXTRA_SECONDS


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


SEVERITY_RANK = {"info": 0, "warning": 1, "error": 2}
