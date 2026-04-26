import gi
from datetime import datetime
from zoneinfo import ZoneInfo

from gi.repository import Gtk, Adw
from gettext import gettext as _, pgettext as C_

from .UI_CompDrawPollutionBar import PollutionBar
from .UI_CompDrawLineGraph import LineGraph
from .settings import settings
from .CORE_Helpers import get_time_difference
from .configs import THRESHOLDS

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

class CardAirPollution:
    def __init__(self):
        from .CORE_weatherData import weather_manager

        self.air_pollution_data = weather_manager.air_pollution
        self.classify_aqi = weather_manager.classify_aqi
        self.card = None
        self.create_card()

    # Thresholds based on WHO Global Air Quality Guidelines 2021 (in µg/m³)
    THRESHOLDS = {
        "pm2_5": [(15, "success"), (35, "warning"), (75, "error")],
        "pm10": [(45, "success"), (100, "warning"), (150, "error")],
        "carbon_monoxide": [(4000, "success"), (7000, "warning"), (10000, "error")],
        "carbon_dioxide": [(1000, "success"), (2000, "warning"), (5000, "error")],
        "nitrogen_dioxide": [(25, "success"), (50, "warning"), (120, "error")],
        "sulphur_dioxide": [(40, "success"), (50, "warning"), (125, "error")],
        "ozone": [(100, "success"), (120, "warning"), (160, "error")],
        "ammonia": [(100, "success"), (200, "warning"), (400, "error")],
        "methane": [(1900, "success"), (2500, "warning"), (5000, "error")],
        "dust": [(45, "success"), (100, "warning"), (150, "error")],
        "alder_pollen": [(15, "success"), (90, "warning"), (500, "error")],
        "birch_pollen": [(15, "success"), (90, "warning"), (500, "error")],
        "grass_pollen": [(15, "success"), (90, "warning"), (500, "error")],
        "mugwort_pollen": [(15, "success"), (90, "warning"), (500, "error")],
        "olive_pollen": [(15, "success"), (90, "warning"), (500, "error")],
        "ragweed_pollen": [(15, "success"), (90, "warning"), (500, "error")],
    }

    def _get_pollutant_status_color(self, key, val):
        if key not in THRESHOLDS:
            return "accent"
            
        for threshold, color in THRESHOLDS[key]:
            if val is not None and float(val) <= threshold:
                return color
        return "error"


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

    def _create_popover(self, idx):
        # Popover content
        popover = Gtk.Popover()
        popover_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        popover_content.set_margin_top(8)
        popover_content.set_margin_bottom(8)
        popover_content.set_margin_start(8)
        popover_content.set_margin_end(8)
        popover_content.set_size_request(340, -1)

        popover_title = Gtk.Label(label=_("Air Quality Index"))
        popover_title.set_css_classes(["text-lg", "font-medium"])
        popover_title.set_halign(Gtk.Align.START)
        popover_content.append(popover_title)

        # AQI Trend Graph
        aqi_trend = self.air_pollution_data.us_aqi.data
        aqi_times = self.air_pollution_data.time.data
        timezone_str = get_time_difference().get("timezone", "UTC")
        tz = ZoneInfo(timezone_str)
        graph = LineGraph(aqi_trend, times=aqi_times, current_idx=idx, tz=tz)
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
            if hasattr(self.air_pollution_data, key):
                field = getattr(self.air_pollution_data, key)
                val = field.data[idx]

                # Skip if value is not available for the current hour
                if val is None:
                    continue

                unit = field.unit if field.unit else "μg/m³"
                color_class = self._get_pollutant_status_color(key, val)

                row = Adw.ActionRow(title=name)
                
                # Recommended safe limit
                if key in THRESHOLDS:
                    safe_limit = THRESHOLDS[key][0][0]
                    row.set_subtitle(_("Safe limit: ≤ {0} {1}").format(safe_limit, unit))

                # Format value
                val_str = f"{val:.1f}" if isinstance(val, float) else str(val)

                # Indicator dot
                indicator = Gtk.Image.new_from_icon_name("media-record-symbolic")
                indicator.add_css_class(color_class)
                indicator.set_pixel_size(10)
                row.add_prefix(indicator)

                # Right-aligned value container
                val_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
                val_box.set_valign(Gtk.Align.CENTER)
                
                val_label = Gtk.Label(label=val_str)
                val_label.add_css_class("font-bold")

                unit_label = Gtk.Label(label=unit)
                unit_label.add_css_class("dim-label")
                unit_label.add_css_class("text-sm")

                val_box.append(val_label)
                val_box.append(unit_label)
                row.add_suffix(val_box)

                list_box.append(row)

        info_text = _("AQI: US EPA Standard\nPollutant limits: WHO Guidelines (2021)")
        info_label = Gtk.Label(label=info_text)
        info_label.set_wrap(True)
        info_label.add_css_class("dim-label")
        info_label.add_css_class("text-xs")
        info_label.set_margin_top(4)
        info_label.set_justify(Gtk.Justification.CENTER)
        popover_content.append(info_label)

        popover.set_child(popover_content)
        return popover
