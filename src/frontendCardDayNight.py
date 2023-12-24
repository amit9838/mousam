import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk

from datetime import datetime
import time

from .frontendUiDrawDayNight import *

image_path = "/home/amit/Drive-D/Code/Gnome/weather/src/frontend/ui/arrowA.png"  # Replace with the path to your image file
angle = 120


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

        sunrise_t, sunset_t = 0, 0
        for i, data in enumerate(daily_data["daily"]["time"]):
            
            date_ = int(datetime.fromtimestamp(data).strftime(r"%d"))
            if date_ == datetime.today().date().day:
                sunrise_t = daily_data["daily"]["sunrise"][i]
                sunset_t = daily_data["daily"]["sunset"][i]

        sunrise = datetime.fromtimestamp(sunrise_t).strftime("%I:%M %p")
        sunset = datetime.fromtimestamp(sunset_t).strftime("%I:%M %p")

        # Caclulate Sun rotation
        current_time = int(time.time())
        degree = 0
        # For Day
        if current_time < sunset_t:
            degree = ((current_time - sunrise_t) / (sunset_t - sunrise_t)) * 180
            degree = degree + 180

        # For Night
        else:
            degree = ((current_time - sunset_t) / (86400-(sunset_t-sunrise_t))) * 180
            degree = degree

        return sunrise, sunset, degree

    def create_card(self):
        card = Gtk.Grid(margin_top=10, margin_start=5, margin_bottom=5)
        self.card = card
        card.halign = Gtk.Align.FILL
        card.set_row_spacing(5)
        card.set_css_classes(["view", "card", "custom_card"])

        # Main title of the card
        title = Gtk.Label(label="Sunset & Sunrise")
        title.set_hexpand(True)
        title.set_halign(Gtk.Align.START)
        title.set_css_classes(["text-4", "light-3", "bold"])
        card.attach(title, 0, 0, 1, 2)

        # Info Grid: It contains - Main value,units, short description, sub description
        card_info = Gtk.Grid()
        card_info.set_column_spacing(5)
        card.attach(card_info, 0, 2, 1, 2)

        sun_rise_label = Gtk.Label(label="Sunrise")
        sun_rise_label.set_margin_top(5)
        sun_rise_label.set_halign(Gtk.Align.START)

        sun_rise_label.set_css_classes(["text-4", "light-4"])
        card_info.attach(sun_rise_label, 0, 1, 1, 2)

        sun_rise = Gtk.Label(label=self.sun_rise)
        sun_rise.set_css_classes(["text-2a", "bold", "light-2"])
        sun_rise.set_halign(Gtk.Align.START)
        card_info.attach(sun_rise, 0, 2, 3, 3)

        sun_set_label = Gtk.Label(label="Sunset")
        sun_set_label.set_halign(Gtk.Align.START)
        sun_set_label.set_margin_top(40)
        sun_set_label.set_css_classes(["text-4", "light-4"])
        card_info.attach(sun_set_label, 0, 4, 1, 2)

        sun_set = Gtk.Label(label=self.sun_set)
        sun_set.set_css_classes(["text-2a", "bold", "light-2"])
        sun_set.set_halign(Gtk.Align.START)
        card_info.attach(sun_set, 0, 6, 3, 3)

        card_icon = Gtk.Grid()
        card_icon.set_css_classes(["view", "card_infao"])
        card.attach(card_icon, 1, 2, 2, 1)

        obj = DrawDayNight(self.degree, 220, 120)
        card_icon.attach(obj.img_box, 0, 1, 1, 1)
