"""Desktop notifications for the overview, sent while the main window
can't be seen (see "Where it is shown" in docs/overview-rules.md)."""

import gi

gi.require_version("Gio", "2.0")

from gi.repository import Gio  # noqa: E402

from ..core.log import get_logger  # noqa: E402
from ..services.selected_city import get_selected_city_name  # noqa: E402

logger = get_logger("notifications")


# Notification priority for each overview insight level
NOTIFICATION_PRIORITY = {
    "low": Gio.NotificationPriority.LOW,
    "medium": Gio.NotificationPriority.LOW,
    "high": Gio.NotificationPriority.NORMAL,
    "extreme": Gio.NotificationPriority.HIGH,
}


def show_overview_notification(app, members) -> None:
    """Send overview insights as a desktop notification: the city as the
    title, each insight's sentence on its own line, the lead first (its icon
    and priority). It always replaces the previous one, so they never pile
    up; clicking it opens the main window."""
    lead = members[0]
    notification = Gio.Notification.new(get_selected_city_name())
    notification.set_body("\n".join(m.message for m in members))
    notification.set_icon(Gio.ThemedIcon.new(lead.icon or "dialog-information-symbolic"))
    notification.set_priority(NOTIFICATION_PRIORITY.get(lead.level, Gio.NotificationPriority.NORMAL))
    notification.set_default_action("app.show-normal")
    app.send_notification("overview", notification)
    logger.info(f"Overview notification sent: {' + '.join(m.kind for m in members)}")
