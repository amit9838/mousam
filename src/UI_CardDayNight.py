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
        sun_rise, sun_set, degree = self.get_sunset_sunrise_degree()
        self.sun_rise = sun_rise
        self.sun_set = sun_set
        self.degree = degree

        self.card = None
        self.create_card()

    def get_sunset_sunrise_degree(self):
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

        sunrise = sunrise_dt.strftime("%I:%M %p")
        sunset = sunset_dt.strftime("%I:%M %p")

        if settings.is_using_24h_clock:
            sunrise = sunrise_dt.strftime("%H:%M")
            sunset = sunset_dt.strftime("%H:%M")

        angle = self._calculate_sun_rotation(target_dt, sunrise_dt, sunset_dt)
        return sunrise, sunset, angle

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

        sun_path = DrawDayNight(self.degree, 120, 90).drawing_area
        sun_path.set_valign(Gtk.Align.CENTER)
        content_box.append(sun_path)

    # Sun Rotation
    def _calculate_sun_rotation(self, target_dt, sunrise_dt, sunset_dt):
        angle = 0
        target_ctime_hr = target_dt.hour + (target_dt.minute / 60)
        target_sunrise_hr = sunrise_dt.hour + (sunrise_dt.minute / 60)
        target_sunset_hr = sunset_dt.hour + (sunset_dt.minute / 60)

        # day
        if target_ctime_hr > target_sunrise_hr and target_ctime_hr < target_sunset_hr:
            angle = (
                (target_ctime_hr - target_sunrise_hr)
                * 180
                / (target_sunset_hr - target_sunrise_hr)
            )
            angle += 180  # Sun is above the horizon

        # Night
        else:
            if target_ctime_hr < target_sunrise_hr:
                target_ctime_hr += 24  # Adjust for times after midnight
            angle = (
                (target_ctime_hr - target_sunset_hr)
                * 180
                / (24 - (target_sunset_hr - target_sunrise_hr))
            )

        return angle
