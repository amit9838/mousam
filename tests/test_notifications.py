"""Tests for the overview's notifications (src/ui/notifications.py).

One notification per topic, a group under its lead's topic, and each one
withdrawn once it is no longer right. Needs PyGObject (Gio only: no display);
the app is a fake that records what is sent and withdrawn.

Run: python3 tests/test_notifications.py (also run by `meson test`).
"""

import os
import sys
import types
import unittest

TESTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TESTS)
from fakes import FakeSettings, settings_module  # noqa: E402

# src/ is imported as the `mousam` package, as in the installed app; the real
# settings need the installed schema
package = types.ModuleType("mousam")
package.__path__ = [os.path.join(TESTS, "..", "src")]
sys.modules.setdefault("mousam", package)
sys.modules["mousam.services.settings"] = settings_module(FakeSettings())

from gi.repository import Gio  # noqa: E402

from mousam.core.overview.insight import Insight  # noqa: E402
from mousam.ui import notifications  # noqa: E402
from mousam.ui.notifications import OverviewNotifications  # noqa: E402

LATER = 4e9


class FakeNotification:
    """Gio.Notification has no getters: this one keeps what it is given."""

    def __init__(self, title):
        self.title = title
        self.body = ""
        self.priority = None

    @classmethod
    def new(cls, title):
        return cls(title)

    def set_body(self, body):
        self.body = body

    def set_priority(self, priority):
        self.priority = priority

    def set_icon(self, _icon):
        pass

    def set_default_action(self, _action):
        pass


notifications.Gio = types.SimpleNamespace(
    Notification=FakeNotification,
    ThemedIcon=Gio.ThemedIcon,
    NotificationPriority=Gio.NotificationPriority,
)


class FakeApp:
    """Records the notifications in the tray, by ID."""

    def __init__(self):
        self.tray = {}

    def send_notification(self, notification_id, notification):
        self.tray[notification_id] = notification

    def withdraw_notification(self, notification_id):
        self.tray.pop(notification_id, None)


def insight(kind: str, topic: str, level: str = "high") -> Insight:
    return Insight(kind, f"{kind} message", LATER, level, topic=topic)


class TestNotifications(unittest.TestCase):
    def setUp(self):
        self.app = FakeApp()
        self.app.tray["overview"] = object()  # left by an older version
        self.notes = OverviewNotifications(self.app)
        self.air = insight("air_quality", "air")
        self.rain = insight("precipitation", "rain", "medium")
        self.heavy = insight("heavy_precipitation", "rain")
        self.storm = insight("storm", "storm", "extreme")
        self.wind = insight("wind", "wind")

    def test_the_old_single_notification_is_withdrawn(self):
        self.assertNotIn("overview", self.app.tray)

    def test_one_per_topic(self):
        self.notes.send([self.air])
        self.notes.send([self.rain])
        self.assertEqual(set(self.app.tray), {"overview-air", "overview-rain"})

    def test_same_topic_replaces(self):
        self.notes.send([self.rain])
        self.notes.send([self.heavy])
        self.assertEqual(set(self.app.tray), {"overview-rain"})
        self.assertIn("heavy_precipitation", self.app.tray["overview-rain"].body)

    def test_a_group_is_one_notification_and_covers_its_members(self):
        self.notes.send([self.wind])
        self.notes.send([self.storm, self.wind, self.rain])
        self.assertEqual(set(self.app.tray), {"overview-storm"})
        self.assertEqual(self.app.tray["overview-storm"].body.count("\n"), 2)

    def test_withdrawn_when_its_topic_is_gone(self):
        self.notes.send([self.air])
        self.notes.send([self.rain])
        self.notes.withdraw_gone(frozenset({"rain"}), [self.rain])
        self.assertEqual(set(self.app.tray), {"overview-rain"})
        self.notes.withdraw_gone(frozenset(), [])  # another city: nothing true yet
        self.assertEqual(self.app.tray, {})

    def test_a_group_that_shrinks_is_resent_without_the_member(self):
        self.notes.send([self.storm, self.wind])
        self.notes.withdraw_gone(frozenset({"storm"}), [self.storm])
        self.assertEqual(self.app.tray["overview-storm"].body, "storm message")
        # Quietly: nothing new happened
        self.assertEqual(self.app.tray["overview-storm"].priority, Gio.NotificationPriority.LOW)
        self.notes.withdraw_gone(frozenset({"storm"}), [self.storm])  # no change: not resent
        self.assertEqual(set(self.app.tray), {"overview-storm"})

    def test_withdraw_all(self):
        self.notes.send([self.air])
        self.notes.send([self.storm])
        self.notes.withdraw_all("the window is in view")
        self.assertEqual(self.app.tray, {})


if __name__ == "__main__":
    unittest.main()
