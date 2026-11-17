"""Desktop notifications for the overview, sent while the main window
can't be seen (see "Where it is shown" in docs/overview-rules.md).

Each topic has its own notification (ID "overview-<topic>"), so air quality
and rain can be there side by side, and a new message replaces only the one
on the same topic. A group is one notification, under its lead's topic.
OverviewNotifications remembers what it has sent and withdraws a
notification as soon as it is no longer right.
"""

from typing import Dict, Optional, Sequence, Tuple

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
        # notification ID -> the topics it covers, its lead's first
        self._sent: Dict[str, Tuple[str, ...]] = {}
        # Older versions sent every message under this one ID
        app.withdraw_notification("overview")

    def send(self, members: Sequence[Insight]) -> None:
        """Send `members` (a group, the lead first) under the lead's topic.
        Their own topics' notifications are withdrawn: the group covers them."""
        topics = tuple(m.topic for m in members)
        sent_id = self._send(members)
        for other_id, covered in list(self._sent.items()):
            if other_id != sent_id and covered[0] in topics:
                self._withdraw(other_id, f"in the group of {sent_id}")
        self._sent[sent_id] = topics

    def withdraw_gone(self, topics: frozenset, members: Sequence[Insight]) -> None:
        """Keep the notifications right for the topics true now (`topics`)
        and the group on screen (`members`, the lead first)."""
        for sent_id, covered in list(self._sent.items()):
            if covered[0] not in topics:
                self._withdraw(sent_id, f"{covered[0]} is no longer true")
            elif not set(covered) <= topics and members and members[0].topic == covered[0]:
                # A member stopped being true: the same notification without it,
                # quietly, since nothing new happened
                self._send(members, Gio.NotificationPriority.LOW)
                self._sent[sent_id] = tuple(m.topic for m in members)
                logger.info(f"Notification {sent_id} updated: {' + '.join(m.kind for m in members)}")

    def withdraw_all(self, why: str) -> None:
        for sent_id in list(self._sent):
            self._withdraw(sent_id, why)

    def _send(self, members: Sequence[Insight],
              priority: Optional[Gio.NotificationPriority] = None) -> str:
        """The city as the title, each sentence on its own line, the lead
        first (its icon and priority); clicking it opens the main window."""
        lead = members[0]
        notification = Gio.Notification.new(get_selected_city_name())
        notification.set_body("\n".join(m.message for m in members))
        notification.set_icon(Gio.ThemedIcon.new(lead.icon or "dialog-information-symbolic"))
        if priority is None:
            priority = NOTIFICATION_PRIORITY.get(lead.level, Gio.NotificationPriority.NORMAL)
        notification.set_priority(priority)
        notification.set_default_action("app.show-normal")
        sent_id = notification_id(lead.topic)
        self._app.send_notification(sent_id, notification)
        logger.info(f"Notification {sent_id} sent: {' + '.join(m.kind for m in members)}")
        return sent_id

    def _withdraw(self, sent_id: str, why: str) -> None:
        self._app.withdraw_notification(sent_id)
        self._sent.pop(sent_id, None)
        logger.info(f"Notification {sent_id} withdrawn: {why}")
