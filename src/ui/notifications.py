"""Desktop notifications for the overview, sent while the main window
can't be seen (see "Where it is shown" in docs/overview-rules.md)."""

import gi

gi.require_version("Gio", "2.0")

from gi.repository import Gio  # noqa: E402

from ..core.log import get_logger  # noqa: E402
from ..services.selected_city import get_selected_city_name  # noqa: E402

logger = get_logger("notifications")


# Notification priority for each overview insight severity
NOTIFICATION_PRIORITY = {
    "info": Gio.NotificationPriority.LOW,
    "warning": Gio.NotificationPriority.NORMAL,
    "error": Gio.NotificationPriority.HIGH,
}


def show_overview_notification(app, insight) -> None:
    """Send an overview insight as a desktop notification: the city as the
    title, the message as the body. It always replaces the previous one, so
    they never pile up; clicking it opens the main window."""
    notification = Gio.Notification.new(get_selected_city_name())
    notification.set_body(insight.message)
    notification.set_icon(Gio.ThemedIcon.new(insight.icon or "dialog-information-symbolic"))
    notification.set_priority(NOTIFICATION_PRIORITY.get(insight.severity, Gio.NotificationPriority.NORMAL))
    notification.set_default_action("app.show-normal")
    app.send_notification("overview", notification)
    logger.info(f"Overview notification sent: {insight.message}")
