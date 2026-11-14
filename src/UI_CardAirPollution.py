import gi
from datetime import datetime
from zoneinfo import ZoneInfo

from gi.repository import Gtk
from gettext import gettext as _, pgettext as C_

from .UI_CompDrawPollutionBar import PollutionBar
from .settings import settings
from .CORE_Helpers import get_time_difference

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

class CardAirPollution:
    def __init__(self):
        from .CORE_weatherData import weather_manager

        self.air_pollution_data = weather_manager.air_pollution
        self.classify_aqi = weather_manager.classify_aqi
        self.card = None
        self.create_card()

    def _get_nearest_time_index(self):
        t_data = get_time_difference()
        target_time = t_data.get("target_time")
        timezone_str = t_data.get("timezone", "UTC")
        tz = ZoneInfo(timezone_str)
        
        target_dt = datetime.fromtimestamp(target_time, tz=tz)

        # convet target dt into timestamp
        target_timestamp = target_dt.timestamp()
        
        air_poll_times = self.air_pollution_data.time.data
        if not air_poll_times:
            return 0

        best_idx = 0
        min_diff = float('inf')

        for i, ts in enumerate(air_poll_times):
            diff = abs(target_timestamp - ts)
            if diff < min_diff:
                min_diff = diff
                best_idx = i
        
        return best_idx

    def create_card(self):
        idx = self._get_nearest_time_index()
        card = Gtk.Grid(margin_top=6, margin_start=3)
        self.card = card
        card.halign = Gtk.Align.FILL
        card.set_row_spacing(5)
        card.set_css_classes(["view", "card"])
        if settings.is_using_dynamic_bg:
            card.add_css_class("bg-dark-overlay")

        # Main title of the card
        title = Gtk.Label(label=_("Air Pollution"))
        title.set_hexpand(True)
        title.set_halign(Gtk.Align.START)
        title.set_css_classes(["text-lg", "opacity-80", "font-medium"])
        card.attach(title, 0, 0, 4, 2)

        # Opens the air quality details (the window's "air-quality" action)
        info_button = Gtk.Button(icon_name="info-outline-symbolic", action_name="win.air-quality")
        info_button.set_halign(Gtk.Align.END)
        info_button.set_valign(Gtk.Align.START)
        info_button.set_css_classes(["flat", "circular", "opacity-75"])
        info_button.set_tooltip_text(_("Air Quality Details"))
        card.attach(info_button, 3, 0, 1, 2)

        # Main value (like windspeed = 32km/h)
        info_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, hexpand=True, halign=Gtk.Align.START
        )
        card.attach(info_box, 0, 2, 4, 2)
        info_box.set_margin_start(10)
        info_box.set_margin_top(5)

        main_val = Gtk.Label(label=str(self.air_pollution_data.us_aqi.data[idx]))
        main_val.set_css_classes(["text-5xl", "font-medium"])
        main_val.set_halign(Gtk.Align.START)
        main_val.set_halign(Gtk.Align.END)
        main_val.set_margin_end(10)
        info_box.append(main_val)

        desc = Gtk.Label(
            label=self.classify_aqi(self.air_pollution_data.us_aqi.data[idx])
        )
        desc.set_css_classes(["text-xl", "opacity-90", "font-semibold"])
        desc.set_margin_bottom(7)
        desc.set_valign(Gtk.Align.END)
        desc.set_halign(Gtk.Align.START)
        info_box.append(desc)

        # Pollution bar
        aqi = self.air_pollution_data.us_aqi.data[idx]

        bar_level = aqi / 350
        pollution_bar = PollutionBar(min(bar_level, 0.99))
        # pollution_bar.set_margin_top()
        card.attach(pollution_bar, 0, 4, 4, 1)
