import weakref
import time
from typing import Callable
from gi.repository import GLib, Gio
from .settings import settings
from .CORE_Helpers import get_selected_city_name
from gettext import gettext as _

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

def weak_connect(widget, signal_name, bound_method):
    weak_self = weakref.ref(bound_method.__self__)
    func_name = bound_method.__name__
    def wrapper(*args, **kwargs):
        target = weak_self()
        if target:
            method = getattr(target, func_name, None)
            if method:
                return method(*args, **kwargs)
    return widget.connect(signal_name, wrapper)

def show_notification(app):
    from .CORE_weatherData import weather_manager
    cw_data = weather_manager.current_weather
    if not app or not settings.show_notifications:
        return
    from .CORE_Icons import condition as cond_map
    if not cw_data:
        return
    city_name = get_selected_city_name()
    temp = cw_data.temperature_2m.data
    unit = cw_data.temperature_2m.unit
    w_code = str(cw_data.weathercode.data)
    cond_str = cond_map.get(w_code, _("Unknown"))
    notification = Gio.Notification.new(f"{city_name} • {temp}{unit}")
    notification.set_body(f"{cond_str}")
    try:
        notification.set_icon(Gio.ThemedIcon.new("weather-few-clouds-symbolic"))
    except:
        pass
    notification.set_default_action("app.show-normal")
    notif_id = f"mousam-upd-{int(time.time())}"
    app.send_notification(notif_id, notification)
