import datetime
import random
import time
import gi
from gi.repository import Gtk, GLib, Adw
import threading
from gettext import gettext as _, pgettext as C_

from .CORE_Icons import icons
from .UI_CompDrawImageIcon import DrawImage
from .UI_CompDrawbarLine import DrawBar
from .settings import settings
from .CORE_GTKUtils import weak_connect

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

# icon_loc imported for reference if needed


class HourlyDetails(Gtk.Grid):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            ("Hourly", "hourly"),
            ("Wind", "wind"),
            ("Precipitation", "prec"),
        ]

        first_btn = None
        for label, page_name in button_data:
            button = Gtk.ToggleButton.new_with_label(_(label))
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
        """Create a new page in the hourly stack with a loading indicator."""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.set_size_request(-1, 180)
        self.hourly_stack.add_named(container, page_name)
        self.hourly_stack.set_visible_child_name(page_name)

        spinner = Adw.Spinner(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, hexpand=True)
        spinner.set_size_request(32, 32)
        spinner.set_margin_top(80)
        container.append(spinner)

        from .CORE_weatherData import weather_manager
        if weather_manager.is_ready:
            self._on_data_loaded(page_name, container, spinner, weather_manager.hourly_forecast)
        else:
            def _wait_for_data(mgr, pspec):
                if mgr.is_ready:
                    GLib.idle_add(self._on_data_loaded, page_name, container, spinner, mgr.hourly_forecast)
                    mgr.disconnect_by_func(_wait_for_data)
            
            weather_manager.connect("notify::is-ready", _wait_for_data)

    def _on_data_loaded(self, page_name, container, spinner, hourly_data):
        """Callback to build the UI once data is fetched."""
        container.remove(spinner)

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
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
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

        nearest_idx = self._get_nearest_time_index(hourly_data.time.data)
        max_prec = max(hourly_data.precipitation.data[:24]) if page_name == "prec" else 0

        for i in range(24):
            item = self._create_hour_item(page_name, i, hourly_data, nearest_idx, max_prec)
            graphic_container.append(item)

        GLib.idle_add(self._scroll_to_now, scrolled_window, graphic_container, nearest_idx)
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
        from .CORE_Helpers import get_timezone_from_selected_city
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
        icon_path = icons.get(icon_key, icons.get("unknown"))
        
        img = Gtk.Image.new_from_file(icon_path)
        img.set_pixel_size(50)
        icon_box.append(img)
        icon_box.set_margin_bottom(5)
        icon_box.set_margin_top(5)

    def _setup_wind_item(self, icon_box, val_label, index, hourly_data):
        speed = hourly_data.windspeed_10m.data[index]
        direction = hourly_data.wind_direction_10m.data[index]
        val_label.set_text(str(speed))
        val_label.set_margin_top(0)
        
        icon_box.append(DrawImage(icons.get("arrow"), direction + 180, 32, 32).img_box)
        icon_box.set_margin_top(5)
        icon_box.set_margin_bottom(5)

    def _setup_prec_item(self, icon_box, val_label, index, hourly_data, max_prec):
        val = hourly_data.precipitation.data[index]
        if settings.is_using_inch_for_prec: val /= 25.4
        
        bar = DrawBar(val / max_prec if max_prec > 0 else 0)
        icon_box.append(bar.dw)
        
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

    def _get_nearest_time_index(self, time_list):
        now = time.time()
        for i, ts in enumerate(time_list):
            if abs(now - ts) < 1800:
                return i
        return 0

    def _scroll_to_now(self, scrolled, container, index):
        width = container.get_width()
        if width > 0:
            offset = (width / 24) * (index - 1)
            offset = max(0, offset)
            scrolled.get_hadjustment().set_value(offset)
            return GLib.SOURCE_REMOVE
        return GLib.SOURCE_CONTINUE


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
