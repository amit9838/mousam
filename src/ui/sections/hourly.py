import datetime
import random
import time
import gi
from gi.repository import Gtk
from gettext import gettext as _, pgettext as C_

from ..icons import get_icon_path, create_weather_icon, ARROW_CENTER
from ..drawing.rotated_image import DrawImage
from ..drawing.bar import DrawBar
from ...services.settings import settings
from ..gtk_utils import weak_connect
from ...core.forecast import nearest_hour_index

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

# icon_loc imported for reference if needed


class HourlyDetails(Gtk.Grid):
    """The hourly card: temperature, wind and precipitation tabs, built from
    the hourly forecast passed in."""

    def __init__(self, hourly, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hourly = hourly
        self.set_hexpand(True)
        self.set_css_classes(["view", "card"])

        if settings.is_using_dynamic_bg:
            self.add_css_class("bg-dark-overlay")

        self.set_margin_top(10)
        self.set_margin_start(3)
        self.paint_ui()
        self.daily_forecast = None
        self.scrolled_window = None

    def paint_ui(self):
        # Hourly Stack
        self.hourly_stack = Gtk.Stack.new()
        self.hourly_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.attach(self.hourly_stack, 0, 1, 1, 1)

        # Hourly Buttons
        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True)
        self.attach(tab_box, 0, 0, 1, 1)

        style_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        style_buttons_box.add_css_class("linked")
        style_buttons_box.set_valign(Gtk.Align.CENTER)

        button_data = [
            (_("Hourly"), "hourly"),
            (_("Wind"), "wind"),
            (_("Precipitation"), "prec"),
        ]

        first_btn = None
        for label, page_name in button_data:
            button = Gtk.ToggleButton.new_with_label(label)
            button.set_size_request(80, 16)
            button.set_css_classes(["btn-sm"])
            if first_btn is None:
                first_btn = button
            else:
                button.set_group(first_btn)
            style_buttons_box.append(button)
            button._page_name = page_name  # store for use in handler
            weak_connect(button, "clicked", self._on_btn_clicked)

        # Initialize with first tab
        if first_btn:
            first_btn.set_active(True)
            self.create_stack_page("hourly")
        
        tab_box.append(style_buttons_box)

    def _on_btn_clicked(self, widget):
        if widget.get_active():
            page_name = getattr(widget, "_page_name", None)
            if not page_name:
                return
            if self.hourly_stack.get_child_by_name(page_name):
                self.hourly_stack.set_visible_child_name(page_name)
            else:
                self.create_stack_page(page_name)

    def create_stack_page(self, page_name):
        """Create a page in the hourly stack, the first time its tab is chosen."""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.set_size_request(-1, 180)
        self.hourly_stack.add_named(container, page_name)
        self.hourly_stack.set_visible_child_name(page_name)

        hourly_data = self._hourly
        page_grid = Gtk.Grid()
        container.append(page_grid)

        # Build Info Header
        info_grid = self._build_info_header(page_name, hourly_data)
        page_grid.attach(info_grid, 0, 1, 1, 1)

        # Build Scrolled List
        scrolled_window = self._build_hourly_list(page_name, hourly_data)
        page_grid.attach(scrolled_window, 0, 2, 1, 1)

    def _build_info_header(self, page_name, hourly_data):
        """Builds the top info grid with highlights (Day Max/High)."""
        info_grid = Gtk.Grid(margin_start=10, margin_top=20, margin_bottom=5, column_spacing=5)

        self.desc_label = Gtk.Label()
        self.desc_label.set_css_classes(["text-lg", "opacity-80", "font-medium"])
        info_grid.attach(self.desc_label, 0, 0, 1, 2)

        self.val_label = Gtk.Label(halign=Gtk.Align.START)
        self.val_label.set_css_classes(["text-xl", "opacity-80", "font-bold"])
        info_grid.attach(self.val_label, 1, 0, 2, 2)

        self.unit_label = Gtk.Label()
        self.unit_label.set_css_classes(["text-base", "opacity-90", "font-medium"])
        info_grid.attach(self.unit_label, 3, 0, 1, 2)

        # Dispatch to specialized header builders
        if page_name == "hourly":
            self._setup_temp_header(hourly_data)
        elif page_name == "wind":
            self._setup_wind_header(hourly_data)
        elif page_name == "prec":
            self._setup_prec_header(hourly_data)

        return info_grid

    def _setup_temp_header(self, hourly_data):
        self.desc_label.set_text(C_("temperature", "Day Max •"))
        max_temp = max(hourly_data.temperature_2m.data[:24])
        self.val_label.set_text(f"{max_temp}°")
        self.unit_label.set_text("")

    def _setup_wind_header(self, hourly_data):
        self.desc_label.set_text(C_("wind", "Day High •"))
        max_wind = max(hourly_data.windspeed_10m.data[:24])
        self.val_label.set_text(str(max_wind))
        self.unit_label.set_text(hourly_data.windspeed_10m.unit)

    def _setup_prec_header(self, hourly_data):
        max_prec = max(hourly_data.precipitation.data[:24])
        unit = hourly_data.precipitation.unit
        if settings.is_using_inch_for_prec:
            max_prec /= 25.4
            unit = "inch"
        self.desc_label.set_text(C_("precipitation", "Day High •"))
        self.val_label.set_text(f"{max_prec:.2f}")
        self.unit_label.set_text(unit)

    def _build_hourly_list(self, page_name, hourly_data):
        """Builds the horizontally scrollable list of hourly items."""
        scrolled_window = Gtk.ScrolledWindow(hexpand=True, margin_top=4, margin_bottom=4)
        # Scroll horizontally only. ALWAYS (not AUTOMATIC) makes GTK reserve
        # room for a classic, non-overlay scrollbar; with AUTOMATIC it took its
        # height from the tiles and cut off the temperatures.
        scrolled_window.set_policy(Gtk.PolicyType.ALWAYS, Gtk.PolicyType.NEVER)
        scrolled_window.set_kinetic_scrolling(True)
        self.scrolled_window = scrolled_window

        controller = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.BOTH_AXES)
        scrolled_window.add_controller(controller)
        weak_connect(controller, "scroll", self.on_scroll)

        graphic_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        scrolled_window.set_child(graphic_container)

        if page_name == "prec" and sum(hourly_data.precipitation.data[:24]) == 0:
            graphic_container.append(self._create_empty_prec_widget())
            return scrolled_window

        nearest_idx = nearest_hour_index(hourly_data.time.data, time.time())
        max_prec = max(hourly_data.precipitation.data[:24]) if page_name == "prec" else 0

        for i in range(24):
            item = self._create_hour_item(page_name, i, hourly_data, nearest_idx, max_prec)
            graphic_container.append(item)

        self._scroll_to_now_once_sized(scrolled_window, nearest_idx)
        return scrolled_window

    def _create_hour_item(self, page_name, index, hourly_data, nearest_idx, max_prec):
        """Factory method for creating an hour card."""
        item_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_start=4, margin_end=4)
        item_box.set_size_request(-1, 120)
        item_box.set_css_classes(["card-hourly", "bg-light-gray"])

        # Add time label
        self._add_time_label(item_box, index, hourly_data, nearest_idx)

        # Add visual and value components
        icon_box = Gtk.Box(halign=Gtk.Align.CENTER)
        item_box.append(icon_box)
        
        val_label = Gtk.Label()
        val_label.set_css_classes(["text-base", "font-semibold", "opacity-80"])
        item_box.append(val_label)

        # Specialized setup
        if page_name == "hourly":
            self._setup_temp_item(icon_box, val_label, index, hourly_data)
        elif page_name == "wind":
            self._setup_wind_item(icon_box, val_label, index, hourly_data)
        elif page_name == "prec":
            self._setup_prec_item(icon_box, val_label, index, hourly_data, max_prec)

        return item_box

    def _add_time_label(self, box, index, hourly_data, nearest_idx):
        from ...services.selected_city import get_timezone_from_selected_city
        from zoneinfo import ZoneInfo
        tz_str = get_timezone_from_selected_city()
        try:
            tz_info = ZoneInfo(tz_str)
        except Exception:
            tz_info = None
            
        ts = hourly_data.time.data[index]
        dt = datetime.datetime.fromtimestamp(ts, tz_info)
        time_str = dt.strftime("%H:%M") if settings.is_using_24h_clock else dt.strftime("%I:%M %p")
        
        label = Gtk.Label(label=time_str, margin_top=6)
        label.set_css_classes(["text-sm", "font-semibold", "opacity-60"])
        if index == nearest_idx:
            label.set_text(_("Now"))
            label.add_css_class("font-bold")
            box.add_css_class("card-hourly-now")
        box.append(label)

    def _setup_temp_item(self, icon_box, val_label, index, hourly_data):
        temp = hourly_data.temperature_2m.data[index]
        val_label.set_text(f"{temp:.0f}°")
        code = hourly_data.weathercode.data[index]
        icon_key = str(code) + ("n" if hourly_data.is_day.data[index] == 0 else "")
        img = create_weather_icon(icon_key, settings.icon_theme, 50)
        icon_box.append(img)
        icon_box.set_margin_bottom(5)
        icon_box.set_margin_top(5)

    def _setup_wind_item(self, icon_box, val_label, index, hourly_data):
        speed = hourly_data.windspeed_10m.data[index]
        direction = hourly_data.wind_direction_10m.data[index]
        val_label.set_text(str(speed))
        val_label.set_margin_top(0)
        
        icon_box.append(DrawImage(get_icon_path("arrow", settings.icon_theme), direction + 180, 32, 32, ARROW_CENTER).widget)
        icon_box.set_margin_top(5)
        icon_box.set_margin_bottom(5)

    def _setup_prec_item(self, icon_box, val_label, index, hourly_data, max_prec):
        val = hourly_data.precipitation.data[index]
        # The bar compares mm with the day's high in mm; only the label is in inches
        bar = DrawBar(val / max_prec if max_prec > 0 else 0)
        icon_box.append(bar.widget)
        if settings.is_using_inch_for_prec:
            val /= 25.4

        val_text = f"{val:.2f}" if val >= 0.01 else ("0" if val == 0 else f"{val:.1f}+")
        val_label.set_text(val_text)
        val_label.set_margin_top(0)

    def _create_empty_prec_widget(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_start=3, margin_end=3, hexpand=True)
        box.set_size_request(-1, 120)
        box.set_css_classes(["card-hourly", "bg-light-gray"])
        
        msgs = [
            _("No precipitation today !"),
            _("No precipitation expected today!"),
            _("Anticipate a precipitation-free day !"),
            _("Enjoy a rain-free day today!"),
            _("Umbrella status: resting. No precipitation in sight !"),
            _("No rain in sight today!"),
        ]
        label = Gtk.Label(label=random.choice(msgs))
        label.set_css_classes(["text-base", "font-medium", "opacity-90"])
        label.set_margin_top(40)
        label.set_margin_bottom(30)
        box.append(label)
        return box

    @staticmethod
    def _scroll_to_now_once_sized(scrolled: Gtk.ScrolledWindow, index: int) -> None:
        """Scroll to the current hour as soon as GTK gives the list its width.

        The list is often built while it is hidden (behind the loader), so it
        has no width yet. Wait for the adjustment's first real size instead of
        polling: a list that is never shown then costs nothing.
        """
        adjustment = scrolled.get_hadjustment()

        def on_changed(adj: Gtk.Adjustment) -> None:
            if adj.get_upper() <= 0:
                return
            adj.disconnect(handler_id)
            adj.set_value(max(0, adj.get_upper() / 24 * (index - 1)))

        # The handler only holds the index, not a widget, so it can't keep
        # the rebuilt grid alive.
        handler_id = adjustment.connect("changed", on_changed)


    def on_scroll(self, controller, dx, dy):
        widget = controller.get_widget()
        if not widget:
            return False
        hadj = widget.get_hadjustment()
        if dx == 0 and dy != 0:
            delta = hadj.get_step_increment() * (1 if dy > 0 else -1)
        else:
            delta = dx
        
        new_val = clamp(hadj.get_value() + delta, hadj.get_lower(), hadj.get_upper() - hadj.get_page_size())
        hadj.set_value(new_val)
        return True

def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))
