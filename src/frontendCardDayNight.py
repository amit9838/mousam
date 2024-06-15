from datetime import datetime
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk

from .frontendUiDrawDayNight import *
from .config import settings
from .utils import (
    get_cords,
    get_time_difference,
)


class CardDayNight:
    def __init__(self):
        sun_rise, sun_set, degree = self.get_sunset_sunrise_degree()
        self.sun_rise = sun_rise
        self.sun_set = sun_set
        self.degree = degree

        self.card = None
        self.create_card()

    def get_sunset_sunrise_degree(self):
        from .weatherData import daily_forecast_data as daily_data

        t_data = get_time_difference(*get_cords())
        time_diff = t_data.get("epoch_diff")
        target_time = t_data.get("target_time")

        sunrise_ts, sunset_ts = 0, 0
        for i, data in enumerate(daily_data.time.get("data")):
            date_ = int(
                datetime.fromtimestamp(
                    data + time_diff
                ).strftime(r"%d")
            )
            if date_ == datetime.today().date().day:
                sunrise_ts = daily_data.sunrise.get("data")[i]
                sunset_ts = daily_data.sunset.get("data")[i]
                break

        sunrise_dt = datetime.fromtimestamp(sunrise_ts - time_diff)
        sunset_dt = datetime.fromtimestamp(sunset_ts - time_diff)

        sunrise = sunrise_dt.strftime("%I:%M %p")
        sunset = sunset_dt.strftime("%I:%M %p")

        if settings.is_using_24h_clock:
            sunrise = sunrise_dt.strftime("%H:%M")
            sunset = sunset_dt.strftime("%H:%M")

        # Caclulate Sun rotation
        degree = 0
        # For Day
        if target_time < (sunset_ts - time_diff):
            degree = (target_time - (sunrise_ts - time_diff)) * 180 / (sunset_ts - sunrise_ts)
            degree = degree + 180 

        # For Night
        else:
            degree = (target_time - (sunset_ts-time_diff))*180/(86400-(sunset_ts-sunrise_ts))

        return sunrise, sunset, degree

    def create_card(self):
        card = Gtk.Grid(margin_top=10, margin_start=5, margin_bottom=0)
        self.card = card
        card.halign = Gtk.Align.FILL
        card.set_row_spacing(5)
        card.set_css_classes(["view", "card", "custom_card"])

        if settings.is_using_dynamic_bg:
            card.add_css_class("transparent_5")

        # Main title of the card
        title = Gtk.Label(label=_("Sunrise & Sunset"))
        title.set_hexpand(True)
        title.set_halign(Gtk.Align.START)
        title.set_css_classes(["text-4", "light-3", "bold"])
        card.attach(title, 0, 0, 1, 2)

        # Info Grid: It contains - Main value,units, short description, sub description
        card_info = Gtk.Grid()
        card_info.set_column_spacing(5)
        card.attach(card_info, 0, 2, 1, 2)

        sun_rise_label = Gtk.Label(label=_("Sunrise"))
        sun_rise_label.set_margin_top(5)
        sun_rise_label.set_halign(Gtk.Align.START)

        sun_rise_label.set_css_classes(["text-4", "light-4"])
        card_info.attach(sun_rise_label, 0, 1, 1, 2)

        sun_rise = Gtk.Label(label=self.sun_rise)
        sun_rise.set_margin_top(10)
        sun_rise.set_css_classes(["text-2a", "bold", "light-2"])
        sun_rise.set_halign(Gtk.Align.START)
        card_info.attach(sun_rise, 0, 2, 3, 3)

        sun_set_label = Gtk.Label(label=_("Sunset"))
        sun_set_label.set_halign(Gtk.Align.START)
        sun_set_label.set_margin_top(20)
        sun_set_label.set_css_classes(["text-4", "light-4"])
        card_info.attach(sun_set_label, 0, 4, 1, 2)

        sun_set = Gtk.Label(label=self.sun_set)
        sun_set.set_css_classes(["text-2a", "bold", "light-2"])
        sun_set.set_halign(Gtk.Align.START)
        card_info.attach(sun_set, 0, 6, 3, 3)

        card_icon = Gtk.Grid()
        card_icon.set_css_classes(["view", "card_infao"])
        card_icon.add_css_class("transparent_0")
        card.attach(card_icon, 1, 2, 2, 1)

        obj = DrawDayNight(self.degree, 200, 100)
        card_icon.attach(obj.img_box, 0, 1, 1, 1)
