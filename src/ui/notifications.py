"""Desktop notifications for the overview, sent while the main window
can't be seen (see "Where it is shown" in docs/overview-rules.md).

Each topic has its own notification (ID "overview-<topic>"), so air quality
and rain can be there side by side, and a new message replaces only the one
on the same topic. OverviewNotifications remembers what it has sent and
withdraws a notification as soon as it is no longer right.
"""

from typing import Dict, Tuple

import gi

gi.require_version("Gio", "2.0")

from gi.repository import Gio  # noqa: E402

from ..core.log import get_logger  # noqa: E402
from ..core.overview.insight import Insight  # noqa: E402
from ..services.selected_city import get_selected_city_name  # noqa: E402

logger = get_logger("notifications")

# Notification priority for each overview insight level
NOTIFICATION_PRIORITY = {
    "low": Gio.NotificationPriority.LOW,
    "medium": Gio.NotificationPriority.LOW,
    "high": Gio.NotificationPriority.NORMAL,
    "extreme": Gio.NotificationPriority.HIGH,
}


def notification_id(topic: str) -> str:
    return f"overview-{topic}"


class OverviewNotifications:
    """The overview's notifications for one app: sent per topic, withdrawn
    once their topic is no longer true."""

    def __init__(self, app: Gio.Application):
        self._app = app
        # notification ID -> the topics its sentence names, its own first
        self._sent: Dict[str, Tuple[str, ...]] = {}
        # Older versions sent every message under this one ID
        app.withdraw_notification("overview")

    def send(self, insight: Insight) -> None:
        """Send `insight` under its topic. Notifications for the topics it
        covers (combined or folded into it) are withdrawn: it says the same."""
        sent_id = self._send(insight)
        for other_id, named in list(self._sent.items()):
            if other_id != sent_id and named[0] in insight.covers:
                self._withdraw(other_id, f"covered by {sent_id}")
        self._sent[sent_id] = insight.topics

    def withdraw_gone(self, topics: frozenset) -> None:
        """Withdraw the notifications that are no longer true: a topic their
        sentence names isn't among those true now (`topics`). A combined one
        names two, so it goes as soon as either does."""
        for sent_id, named in list(self._sent.items()):
            if not set(named) <= topics:
                gone = ", ".join(t for t in named if t not in topics)
                self._withdraw(sent_id, f"{gone} no longer true")

    def withdraw_all(self, why: str) -> None:
        for sent_id in list(self._sent):
            self._withdraw(sent_id, why)

    def _send(self, insight: Insight) -> str:
        """The city as the title, the sentence as the body; clicking it opens
        the main window."""
        notification = Gio.Notification.new(get_selected_city_name())
        notification.set_body(insight.message)
        notification.set_icon(Gio.ThemedIcon.new(insight.icon or "dialog-information-symbolic"))
        notification.set_priority(NOTIFICATION_PRIORITY.get(insight.level, Gio.NotificationPriority.NORMAL))
        notification.set_default_action("app.show-normal")
        sent_id = notification_id(insight.topic)
        self._app.send_notification(sent_id, notification)
        logger.info(f"Notification {sent_id} sent: {insight.kind} ({insight.key})")
        return sent_id

    def _withdraw(self, sent_id: str, why: str) -> None:
        self._app.withdraw_notification(sent_id)
        self._sent.pop(sent_id, None)
        logger.info(f"Notification {sent_id} withdrawn: {why}")
