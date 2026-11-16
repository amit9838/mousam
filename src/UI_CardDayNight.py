import time
from datetime import datetime
from zoneinfo import ZoneInfo
import gi

from gi.repository import Gtk
from gettext import gettext as _

from .UI_CompDrawDayNight import DrawDayNight
from .UI_CardSquare import CSS_TEXT_TITLE, CSS_TEXT_VALUE
from .settings import settings
from .CORE_Forecast import today_sun_times

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")


class CardDayNight:
    """Today's sunrise and sunset, with the sun's path across the day.

    Takes the daily forecast, the city's time-zone name and its latitude
    (the sun's path runs the other way in the southern hemisphere).
    """

    def __init__(self, daily, timezone_name: str, latitude: float):
        tz = ZoneInfo(timezone_name)
        self.sunrise_ts, self.sunset_ts = today_sun_times(
            daily.time.data, daily.sunrise.data, daily.sunset.data, tz, time.time()
        )
        time_format = "%H:%M" if settings.is_using_24h_clock else "%I:%M %p"
        self.sun_rise = datetime.fromtimestamp(self.sunrise_ts, tz=tz).strftime(time_format)
        self.sun_set = datetime.fromtimestamp(self.sunset_ts, tz=tz).strftime(time_format)
        self.card = self._build_card(southern=latitude < 0)

    def _build_card(self, southern: bool) -> Gtk.Widget:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.set_margin_top(6)
        card.set_margin_start(3)
        card.set_css_classes(["view", "card"])

        if settings.is_using_dynamic_bg:
            card.add_css_class("bg-dark-overlay")

        title = Gtk.Label(label=_("Sunrise & Sunset"))
        title.set_halign(Gtk.Align.START)
        title.set_css_classes(CSS_TEXT_TITLE)
        card.append(title)

        # Times on the left, the sun's path on the right
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        card.append(content_box)

        times_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        times_box.set_hexpand(True)
        times_box.set_valign(Gtk.Align.CENTER)
        content_box.append(times_box)

        for label, time_text in ((_("Sunrise"), self.sun_rise), (_("Sunset"), self.sun_set)):
            time_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            lbl_name = Gtk.Label(label=label)
            lbl_name.set_halign(Gtk.Align.START)
            lbl_name.set_css_classes(["text-lg", "opacity-75"])
            lbl_time = Gtk.Label(label=time_text)
            lbl_time.set_halign(Gtk.Align.START)
            lbl_time.set_css_classes(CSS_TEXT_VALUE)
            time_box.append(lbl_name)
            time_box.append(lbl_time)
            times_box.append(time_box)

        sun_path = DrawDayNight(self.sunrise_ts, self.sunset_ts, southern, 120, 90).widget
        sun_path.set_valign(Gtk.Align.CENTER)
        content_box.append(sun_path)
        return card
