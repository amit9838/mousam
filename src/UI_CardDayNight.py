from datetime import datetime
from zoneinfo import ZoneInfo
import gi

from gi.repository import Gtk
from gettext import gettext as _, pgettext as C_

from .UI_CompDrawDayNight import DrawDayNight
from .UI_CardSquare import CSS_TEXT_TITLE, CSS_TEXT_VALUE
from .settings import settings
from .CORE_Helpers import get_time_difference

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")


class CardDayNight:
    def __init__(self):
        self.card = None
        self.get_sun_times()
        self.create_card()

    def get_sun_times(self):
        """Set the sunrise and sunset texts, and where the sun is now."""
        from .CORE_weatherData import weather_manager
        daily_data = weather_manager.daily_forecast

        t_data = get_time_difference()
        target_time = t_data.get("target_time")
        timezone_str = t_data.get("timezone", "UTC")
        tz = ZoneInfo(timezone_str)

        sunrise_ts, sunset_ts = 0, 0
        for i, data in enumerate(daily_data.time.data):
            # Check date using target timezone
            dt = datetime.fromtimestamp(data, tz=tz)
            current_time = datetime.now(tz)
            if dt.date() == current_time.date():
                sunrise_ts = daily_data.sunrise.data[i]
                sunset_ts = daily_data.sunset.data[i]
                break

        target_dt = datetime.fromtimestamp(target_time, tz=tz)
        sunrise_dt = datetime.fromtimestamp(sunrise_ts, tz=tz)
        sunset_dt = datetime.fromtimestamp(sunset_ts, tz=tz)

        time_format = "%H:%M" if settings.is_using_24h_clock else "%I:%M %p"
        self.sun_rise = sunrise_dt.strftime(time_format)
        self.sun_set = sunset_dt.strftime(time_format)

        self.is_day, self.progress = self._calculate_sun_progress(target_dt, sunrise_dt, sunset_dt)
        # Share of the 24 hours the sun is up: sets the horizon's height
        self.day_fraction = (sunset_ts - sunrise_ts) / (24 * 3600)

    def create_card(self):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.set_margin_top(6)
        card.set_margin_start(3)
        card.set_css_classes(["view", "card"])
        self.card = card

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

        for label, time in ((_("Sunrise"), self.sun_rise), (_("Sunset"), self.sun_set)):
            time_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            lbl_name = Gtk.Label(label=label)
            lbl_name.set_halign(Gtk.Align.START)
            lbl_name.set_css_classes(["text-lg", "opacity-75"])
            lbl_time = Gtk.Label(label=time)
            lbl_time.set_halign(Gtk.Align.START)
            lbl_time.set_css_classes(CSS_TEXT_VALUE)
            time_box.append(lbl_name)
            time_box.append(lbl_time)
            times_box.append(time_box)

        sun_path = DrawDayNight(self.is_day, self.progress, self.day_fraction, 120, 90).drawing_area
        sun_path.set_valign(Gtk.Align.CENTER)
        content_box.append(sun_path)

    # How far the sun (by day) or the moon (by night) is along its way
    @staticmethod
    def _calculate_sun_progress(target_dt, sunrise_dt, sunset_dt) -> tuple:
        """Return (is_day, progress), progress from 0 (sunrise / sunset) to 1 (sunset / sunrise)."""
        target_ctime_hr = target_dt.hour + (target_dt.minute / 60)
        target_sunrise_hr = sunrise_dt.hour + (sunrise_dt.minute / 60)
        target_sunset_hr = sunset_dt.hour + (sunset_dt.minute / 60)

        # Day
        if target_sunrise_hr < target_ctime_hr < target_sunset_hr:
            progress = (target_ctime_hr - target_sunrise_hr) / (target_sunset_hr - target_sunrise_hr)
            return True, progress

        # Night
        if target_ctime_hr < target_sunrise_hr:
            target_ctime_hr += 24  # Adjust for times after midnight
        progress = (target_ctime_hr - target_sunset_hr) / (24 - (target_sunset_hr - target_sunrise_hr))
        return False, progress
