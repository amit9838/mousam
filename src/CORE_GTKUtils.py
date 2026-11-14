import math
import weakref
from typing import Callable, Tuple
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import GLib, Gio, GObject, Gtk, PangoCairo  # noqa: E402
from .settings import settings  # noqa: E402
from .CORE_Helpers import get_selected_city_name  # noqa: E402
from .CORE_Logging import get_logger  # noqa: E402

logger = get_logger("utils")

class AutoRefreshTimer:
    def __init__(self, callback: Callable):
        self._timer_id = None
        self._callback = callback

    def setup(self):
        self.stop()
        interval = settings.auto_refresh_interval
        if interval > 0:
            self._timer_id = GLib.timeout_add_seconds(interval * 60, self._on_tick)

    def stop(self):
        if self._timer_id is not None:
            GLib.source_remove(self._timer_id)
            self._timer_id = None

    def _on_tick(self):
        self._callback()
        return GLib.SOURCE_CONTINUE

def safe_set_draw_func(drawing_area, obj, draw_method_name):
    drawing_area._keep_alive_obj = obj
    weak_obj = weakref.ref(obj)
    def wrapper(area, cr, width, height, _user_data):
        target = weak_obj()
        if target:
            method = getattr(target, draw_method_name, None)
            if method:
                method(area, cr, width, height, _user_data)
    drawing_area.set_draw_func(wrapper, None)

def theme_rgba(widget: Gtk.Widget, alpha: float = 1.0) -> Tuple[float, float, float, float]:
    """The widget's CSS text colour, with extra opacity.

    Use it for text and neutral lines in drawings: it is dark in light mode
    and white in dark mode and on dynamic backgrounds (bg-dark-overlay).
    """
    color = widget.get_color()
    return (color.red, color.green, color.blue, color.alpha * alpha)


def text_layout(widget: Gtk.Widget, text: str, size: str = "small", bold: bool = False):
    """A Pango layout for text in the widget's font.

    size is a Pango size name ("x-small", "small", "medium"), so the text
    follows the user's font and text scaling. get_pixel_size() measures it.
    """
    layout = widget.create_pango_layout(None)
    weight = "bold" if bold else "normal"
    layout.set_markup(f'<span size="{size}" weight="{weight}">{GLib.markup_escape_text(text)}</span>', -1)
    return layout


def draw_text(
    widget: Gtk.Widget,
    cr,
    text: str,
    x: float,
    y: float,
    size: str = "small",
    bold: bool = False,
    alpha: float = 1.0,
    align: float = 0.5,
) -> Tuple[int, int]:
    """Draw text in the widget's font and colour, and return its size.

    x is where the text is anchored (align 0 = left edge, 0.5 = centre,
    1 = right edge); y is its top.
    """
    layout = text_layout(widget, text, size, bold)
    width, height = layout.get_pixel_size()
    cr.set_source_rgba(*theme_rgba(widget, alpha))
    cr.move_to(x - width * align, y)
    PangoCairo.show_layout(cr, layout)
    return width, height


def draw_knob(cr, x: float, y: float, radius: float, rgb) -> None:
    """A filled circle with a white ring and a soft shadow (slider knob, "now" marker).

    The ring and shadow keep it visible on any background, light or dark.
    """
    cr.new_sub_path()
    cr.arc(x, y + 0.5, radius + 2.5, 0, 2 * math.pi)
    cr.set_source_rgba(0, 0, 0, 0.22)
    cr.fill()

    cr.arc(x, y, radius + 1.5, 0, 2 * math.pi)
    cr.set_source_rgba(1, 1, 1, 1)
    cr.fill()

    cr.arc(x, y, radius - 0.5, 0, 2 * math.pi)
    cr.set_source_rgba(*rgb, 1)
    cr.fill()


def weak_connect(widget, signal_name, bound_method, *data):
    """Connect without the handler keeping its object alive. Extra data is
    passed to the handler after the signal's own arguments."""
    target = bound_method.__self__
    # Since PyGObject 3.55 a GObject's Python wrapper is freed while the
    # GObject lives on, so a Python weakref to it goes dead too early:
    # GObject.Object.weak_ref() follows the GObject itself.
    if isinstance(target, GObject.Object):
        weak_self = target.weak_ref()
    else:
        weak_self = weakref.ref(target)
    func_name = bound_method.__name__
    def wrapper(*args, **kwargs):
        target = weak_self()
        if target:
            method = getattr(target, func_name, None)
            if method:
                return method(*args, **kwargs)
    return widget.connect(signal_name, wrapper, *data)

def remove_rootwindow_drop_target(window: Gtk.Window) -> None:
    """Remove GTK's own drop target from a window that reorders things by drag.

    Every Gtk.Window has one, for a format this app never uses. GTK leaves it
    holding the previous drop, so each later drag logs a warning from
    gtk_drop_target_async_handle_crossing. Safe to call more than once.
    """
    controllers = window.observe_controllers()
    found = [
        controllers.get_item(index)
        for index in range(controllers.get_n_items())
        if controllers.get_item(index).get_name() == "gtk-window-rootwindow-drop"
    ]
    for controller in found:
        window.remove_controller(controller)


def is_on_screen(window) -> bool:
    """Whether a window can be seen: shown, and not suspended (minimized, on
    another workspace, or covered by other windows)."""
    return window is not None and window.get_visible() and not window.is_suspended()


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
