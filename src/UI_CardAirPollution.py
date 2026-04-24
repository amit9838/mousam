import gi
import time

from gi.repository import Gtk, Adw
from gettext import gettext as _, pgettext as C_

from .UI_CompDrawPollutionBar import PollutionBar
from .UI_CompDrawLineGraph import LineGraph
from .config import settings

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

class CardAirPollution:
    def __init__(self):
        from .CORE_weatherData import air_apllution_data, classify_aqi

        self.air_apllution_data = air_apllution_data
        self.classify_aqi = classify_aqi
        self.card = None
        self.create_card()

    def _get_pollutant_status_color(self, key, val):
        # Standard thresholds (approximate) for color coding
        thresholds = {
            "pm2_5": [(12, "success"), (35, "warning"), (55, "error")],
            "pm10": [(54, "success"), (154, "warning"), (254, "error")],
            "carbon_monoxide": [(4.4, "success"), (9.4, "warning"), (12.4, "error")],
            "carbon_dioxide": [(600, "success"), (1000, "warning"), (2000, "error")],
            "nitrogen_dioxide": [(53, "success"), (100, "warning"), (360, "error")],
            "sulphur_dioxide": [(35, "success"), (75, "warning"), (185, "error")],
            "ozone": [(54, "success"), (70, "warning"), (85, "error")],
            "ammonia": [(200, "success"), (400, "warning"), (800, "error")],
            "methane": [(1800, "success"), (2500, "warning"), (5000, "error")],
            "dust": [(50, "success"), (150, "warning"), (250, "error")],
            "alder_pollen": [(15, "success"), (90, "warning"), (1500, "error")],
            "birch_pollen": [(15, "success"), (90, "warning"), (1500, "error")],
            "grass_pollen": [(15, "success"), (90, "warning"), (1500, "error")],
            "mugwort_pollen": [(15, "success"), (90, "warning"), (1500, "error")],
            "olive_pollen": [(15, "success"), (90, "warning"), (1500, "error")],
            "ragweed_pollen": [(15, "success"), (90, "warning"), (1500, "error")],
        }
        
        if key not in thresholds:
            return "accent"
            
        for threshold, color in thresholds[key]:
            if val is not None and float(val) <= threshold:
                return color
        return "error"

    def _get_nearest_time_index(self):
        nearest_current_time_idx = 0
        air_poll_time = self.air_apllution_data["hourly"]["time"]
        for i in range(len(air_poll_time)):
            if (abs(time.time() - air_poll_time[i]) // 60) < 30:
                nearest_current_time_idx = i
                break

        return nearest_current_time_idx

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

        # Info button with Popover
        info_button = Gtk.MenuButton()
        info_button.set_icon_name("help-about-symbolic")
        info_button.set_halign(Gtk.Align.END)
        info_button.set_valign(Gtk.Align.START)
        info_button.set_css_classes(["flat", "circular", "opacity-75"])
        info_button.set_tooltip_text(_("Air Quality Components"))
        card.attach(info_button, 3, 0, 1, 2)

        popover = self._create_popover(idx)
        info_button.set_popover(popover)

        # Main value (like windspeed = 32km/h)
        info_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, hexpand=True, halign=Gtk.Align.START
        )
        card.attach(info_box, 0, 2, 4, 2)
        info_box.set_margin_start(10)
        info_box.set_margin_top(5)

        main_val = Gtk.Label(label=self.air_apllution_data["hourly"]["us_aqi"][idx])
        main_val.set_css_classes(["text-5xl", "font-medium"])
        main_val.set_halign(Gtk.Align.START)
        main_val.set_halign(Gtk.Align.END)
        main_val.set_margin_end(10)
        info_box.append(main_val)

        desc = Gtk.Label(
            label=self.classify_aqi(self.air_apllution_data["hourly"]["us_aqi"][idx])
        )
        desc.set_css_classes(["text-xl", "opacity-90", "font-semibold"])
        desc.set_margin_bottom(7)
        desc.set_valign(Gtk.Align.END)
        desc.set_halign(Gtk.Align.START)
        info_box.append(desc)

        # Pollution bar
        aqi = self.air_apllution_data["hourly"]["us_aqi"][idx]

        bar_level = aqi / 350
        pollution_bar = PollutionBar(min(bar_level, 0.99))
        # pollution_bar.set_margin_top()
        card.attach(pollution_bar, 0, 4, 4, 1)

    def _create_popover(self, idx):
        # Popover content
        popover = Gtk.Popover()
        popover_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        popover_content.set_margin_top(8)
        popover_content.set_margin_bottom(8)
        popover_content.set_margin_start(8)
        popover_content.set_margin_end(8)
        popover_content.set_size_request(280, -1)

        popover_title = Gtk.Label(label=_("Air Quality Index"))
        popover_title.set_css_classes(["text-lg", "font-medium"])
        popover_title.set_halign(Gtk.Align.START)
        popover_content.append(popover_title)

        # AQI Trend Graph
        aqi_trend = self.air_apllution_data["hourly"]["us_aqi"]
        aqi_times = self.air_apllution_data["hourly"]["time"]
        graph = LineGraph(aqi_trend, times=aqi_times, current_idx=idx)
        popover_content.append(graph.dw)

        separator = Gtk.Separator()
        popover_content.append(separator)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_propagate_natural_height(True)
        scrolled.set_max_content_height(400)
        popover_content.append(scrolled)

        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        list_box.add_css_class("boxed-list")
        scrolled.set_child(list_box)

        pollutants = [
            ("pm2_5", _("PM2.5")),
            ("pm10", _("PM10")),
            ("carbon_monoxide", _("CO")),
            ("carbon_dioxide", _("CO₂")),
            ("nitrogen_dioxide", _("NO₂")),
            ("sulphur_dioxide", _("SO₂")),
            ("ozone", _("O₃")),
            ("dust", _("Dust")),
            ("ammonia", _("NH₃")),
            ("methane", _("CH₄")),
            ("alder_pollen", _("Alder Pollen")),
            ("birch_pollen", _("Birch Pollen")),
            ("grass_pollen", _("Grass Pollen")),
            ("mugwort_pollen", _("Mugwort Pollen")),
            ("olive_pollen", _("Olive Pollen")),
            ("ragweed_pollen", _("Ragweed Pollen")),
        ]

        for key, name in pollutants:
            if key in self.air_apllution_data["hourly"]:
                val = self.air_apllution_data["hourly"][key][idx]

                # Skip if value is not available for the current hour
                if val is None:
                    continue

                unit = self.air_apllution_data["hourly_units"].get(key, "μg/m³")
                color_class = self._get_pollutant_status_color(key, val)

                row = Adw.ActionRow(title=name)

                # Indicator dot
                indicator = Gtk.Image.new_from_icon_name("media-record-symbolic")
                indicator.add_css_class(color_class)
                indicator.set_pixel_size(8)
                row.add_prefix(indicator)

                # Value label
                val_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
                val_label = Gtk.Label(label=str(val))
                val_label.add_css_class("font-medium")

                unit_label = Gtk.Label(label=unit)
                unit_label.add_css_class("dim-label")
                unit_label.add_css_class("text-sm")

                val_box.append(val_label)
                val_box.append(unit_label)
                row.add_suffix(val_box)

                list_box.append(row)

        popover.set_child(popover_content)
        return popover
