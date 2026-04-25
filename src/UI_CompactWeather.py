import gi
from gi.repository import Gtk, Adw, GLib
from .config import settings
from .constants import icons, condition, bg_css
from gettext import gettext as _

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

# ----- Helper to reset global data -----
# Removed _reset_weather_data as it causes crashes in the main window

class CompactWeather(Gtk.Overlay):
    def __init__(self, on_back_clicked, **kwargs):
        super().__init__(**kwargs)
        self.on_back_clicked = on_back_clicked
        self._poll_timeout_id = None    # store timeout for cleanup
        
        self.add_css_class("compact-container")
        self.set_valign(Gtk.Align.FILL)
        self.set_halign(Gtk.Align.FILL)
        self.set_size_request(280, 220)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.set_child(self.stack)

        self._setup_back_button()
        self._start_polling()


    def _cleanup_ui(self):
        """Remove old content overlays so fresh UI can be drawn."""
        # Collect overlays to remove (skip the back button and base stack)
        to_remove = []
        child = self.get_first_child()
        while child is not None:
            if child is not self.stack and child is not self.btn_back:
                to_remove.append(child)
            child = child.get_next_sibling()
        for w in to_remove:
            self.remove_overlay(w)

    def _trigger_fetch(self, is_auto=False):
        from .utils import fetch_all_weather_data_async, show_notification
        
        def on_success():
            if is_auto:
                root = self.get_root()
                if root:
                    app = root.get_application()
                    if app:
                        show_notification(app)

        fetch_all_weather_data_async(on_success=on_success)

    def _start_polling(self, is_auto=False):
        """Begin polling for data, store timeout id."""
        if self._is_data_ready():
            GLib.idle_add(self._build_ui)
        else:
            self._trigger_fetch(is_auto=is_auto)
            self._show_loader()
            self._poll_timeout_id = GLib.timeout_add(500, self._check_all_data_ready)

    def _show_loader(self):
        if not self.stack.get_child_by_name("loader"):
            spinner = Adw.Spinner()
            spinner.set_size_request(32, 32)
            spinner.set_halign(Gtk.Align.CENTER)
            spinner.set_valign(Gtk.Align.CENTER)
            self.stack.add_named(spinner, "loader")
        self.stack.set_visible_child_name("loader")

    def _is_data_ready(self):
        from .CORE_weatherData import current_weather_data, air_apllution_data
        import threading
        if current_weather_data is None or air_apllution_data is None:
            return False

        # This checks for the race condition of the threads in mousam.py with "cwt" and "apt" tags
        # If new data is actively being fetched, wait for it to finish
        if any(t.name in ("cwt", "apt", "compact_fetch") for t in threading.enumerate()):
            return False
        return True

    def _check_all_data_ready(self):
        """Polling callback. Returns False to stop when data is ready."""
        if self._poll_timeout_id is None:
            return False   # already stopped

        if not self._is_data_ready():
            self._show_loader()
            return True   # continue polling

        # Data ready → build UI and stop polling
        self._build_ui()
        self._stop_polling()
        return False

    def _stop_polling(self):
        if self._poll_timeout_id:
            GLib.source_remove(self._poll_timeout_id)
            self._poll_timeout_id = None

    def _build_ui(self):
        self._cleanup_ui()
        from .CORE_weatherData import current_weather_data as data, air_apllution_data as aq_data
        from .utils import JsonProcessor, get_timezone_from_selected_city
        import datetime
        from zoneinfo import ZoneInfo

        # Remove loader from stack
        loader = self.stack.get_child_by_name("loader")
        if loader:
            self.stack.remove(loader)

        # Apply dynamic background to root window (async)
        if settings.is_using_dynamic_bg:
            weather_code = data.weathercode.get("data", 0)
            is_day = data.is_day.get("data", 1)
            code_key = f"{weather_code}{'n' if is_day == 0 else ''}"
            css_class = bg_css.get(code_key, "")
            
            def update_root_bg():
                root = self.get_root()
                if root and css_class:
                    valid_bgs = set(bg_css.values())
                    for cls in root.get_css_classes():
                        if cls in valid_bgs:
                            root.remove_css_class(cls)
                    root.add_css_class(css_class)
                return False
            GLib.idle_add(update_root_bg)

        # ---- Content building (same as before, but without AQI spinner) ----
        grid = Gtk.Grid()
        grid.set_column_spacing(5)
        grid.set_row_spacing(0)
        grid.set_margin_start(25)
        grid.set_margin_end(25)
        grid.set_margin_top(25)
        grid.set_margin_bottom(25)

        # City
        city_list = JsonProcessor.str_list_to_json(settings.added_cities)
        selected_city_str = settings.selected_city
        city_name = "Unknown"
        for city in city_list:
            if f"{city.get('latitude')},{city.get('longitude')}" == selected_city_str:
                city_name = city.get("name")
                break
        if len(city_name) > 11:
            city_name = city_name[:8] + "..."

        lbl_city = Gtk.Label(label=city_name)
        lbl_city.set_halign(Gtk.Align.START)
        lbl_city.add_css_class("text-3xl")
        lbl_city.add_css_class("font-bold")
        lbl_city.add_css_class("opacity-90")
        grid.attach(lbl_city, 0, 0, 1, 1)

        # Condition
        weather_code = data.weathercode.get("data", 0)
        lbl_cond = Gtk.Label(label=condition.get(str(weather_code), condition.get("0", "Unknown")))
        lbl_cond.set_halign(Gtk.Align.START)
        lbl_cond.add_css_class("text-xl")
        grid.attach(lbl_cond, 0, 1, 1, 1)

        # Weather Icon
        icon_path = icons.get(str(weather_code), icons.get("unknown"))
        is_day_val = data.is_day.get("data", 1)
        if is_day_val == 0:
            icon_path = icons.get(str(weather_code) + "n", icon_path)

        img_cond = Gtk.Image.new_from_file(icon_path)
        img_cond.set_pixel_size(70)
        img_cond.set_halign(Gtk.Align.END)
        img_cond.set_valign(Gtk.Align.CENTER)
        grid.attach(img_cond, 2, 0, 1, 2)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        grid.attach(spacer, 0, 2, 1, 1)

        # Temperature
        temp_val = data.temperature_2m.get('data')
        temp_str = f"{temp_val:.0f}°" if temp_val is not None else "--°"
        lbl_temp = Gtk.Label(label=temp_str)
        lbl_temp.set_halign(Gtk.Align.START)
        lbl_temp.set_valign(Gtk.Align.START)
        lbl_temp.set_margin_top(25)
        lbl_temp.add_css_class("compact-temp")
        grid.attach(lbl_temp, 0, 3, 1, 1)

        # Details grid
        details_grid = Gtk.Grid()
        details_grid.set_column_spacing(8)
        details_grid.set_row_spacing(0)
        details_grid.set_valign(Gtk.Align.START)
        details_grid.set_halign(Gtk.Align.END)
        details_grid.set_margin_top(15)
        details_grid.set_hexpand(True)
        grid.attach(details_grid, 2, 3, 1, 1)

        def add_detail_row(label_text, value_text, row):
            lbl_label = Gtk.Label(label=label_text)
            lbl_label.set_halign(Gtk.Align.START)
            lbl_label.add_css_class("compact-detail-label")
            lbl_value = Gtk.Label(label=value_text)
            lbl_value.set_halign(Gtk.Align.END)
            lbl_value.add_css_class("compact-detail-value")
            details_grid.attach(lbl_label, 0, row, 1, 1)
            details_grid.attach(lbl_value, 1, row, 1, 1)
            return lbl_value

        # Time / Date
        self.lbl_time_val = Gtk.Label()
        self.lbl_time_val.set_halign(Gtk.Align.END)
        self.lbl_time_val.add_css_class("compact-detail-value")
        self.lbl_time_val.add_css_class("compact-time-value")
        self.lbl_time_val.set_use_markup(True)
        self.lbl_time_val.set_margin_bottom(5)

        from .utils import get_timezone_from_selected_city
        self.target_tz = ZoneInfo(get_timezone_from_selected_city())
        now = datetime.datetime.now(self.target_tz)
        date_str = now.strftime("%d %B")
        time_str = now.strftime("%H:%M" if settings.is_using_24h_clock else "%I:%M %p")
        self.lbl_time_val.set_markup(f"{date_str} • {time_str}")
        details_grid.attach(self.lbl_time_val, 0, 0, 2, 1)

        def update_clock():
            fmt = "%H:%M" if settings.is_using_24h_clock else "%I:%M %p"
            now = datetime.datetime.now(self.target_tz)
            d_str = now.strftime("%d %B")
            t_str = now.strftime(fmt)
            self.lbl_time_val.set_markup(f"{d_str} • {t_str}")
            return True
        GLib.timeout_add_seconds(1, update_clock)

        # Wind
        def get_wind_dir(deg):
            if deg is None:
                return "--"
            dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
            idx = int((deg + 11.25) / 22.5) % 16
            return dirs[idx]

        wind_deg = data.winddirection_10m.get('data')
        wind_dir = get_wind_dir(wind_deg)
        wind_speed = data.windspeed_10m.get('data')
        wind_speed_str = f"{wind_speed} {data.windspeed_10m.get('unit')}" if wind_speed is not None else "--"
        add_detail_row(_("Wind"), f"{wind_speed_str} • {wind_dir}", 1)

        hum = data.relativehumidity_2m.get('data')
        hum_str = f"{hum} %" if hum is not None else "-- %"
        add_detail_row(_("Hum."), hum_str, 2)

        pres = data.surface_pressure.get('data')
        pres_str = f"{pres} {data.surface_pressure.get('unit')}" if pres is not None else "--"
        add_detail_row(_("Pres."), pres_str, 3)

        # AQI (data is guaranteed ready)
        aqi_value = aq_data.get("current_us_aqi", "--") if aq_data else "--"
        add_detail_row(_("AQI"), str(aqi_value), 4)

        # Show content
        self.add_overlay(grid)
        loader = self.stack.get_child_by_name("loader")
        if loader:
            loader.set_visible(False)

    def _setup_back_button(self):
        self.btn_back = Gtk.Button()
        self.btn_back.set_icon_name("view-fullscreen-symbolic")
        self.btn_back.add_css_class("flat")
        self.btn_back.add_css_class("circular")
        self.btn_back.set_halign(Gtk.Align.END)
        self.btn_back.set_valign(Gtk.Align.START)
        self.btn_back.set_margin_top(5)
        self.btn_back.set_margin_end(5)
        self.btn_back.connect("clicked", self._on_back_clicked)
        self.btn_back.set_visible(False)
        self.add_overlay(self.btn_back)

        motion_ctrl = Gtk.EventControllerMotion()
        motion_ctrl.connect("enter", self._on_hover_enter)
        motion_ctrl.connect("leave", self._on_hover_leave)
        self.add_controller(motion_ctrl)

    def _on_back_clicked(self, button):
        # Stop polling before calling the callback
        self._stop_polling()
        if self.on_back_clicked:
            self.on_back_clicked()

    def _on_hover_enter(self, controller, x, y):
        self.btn_back.set_visible(True)

    def _on_hover_leave(self, controller):
        self.btn_back.set_visible(False)

    def dispose(self):
        self._stop_polling()
        super().dispose()


class CompactWeatherWindow(Adw.ApplicationWindow):
    def __init__(self, app, bg_classes=None, on_back_to_normal=None, **kwargs):
        super().__init__(application=app, **kwargs)
        self.on_back_to_normal = on_back_to_normal
        self.set_title(_("Mousam Compact"))
        self.set_default_size(280, 220)
        self.set_resizable(False)

        self.connect("destroy", self._on_window_destroy)

        handle = Gtk.WindowHandle()
        self.set_content(handle)

        self.compact_view = CompactWeather(on_back_clicked=self._on_back)
        handle.set_child(self.compact_view)
        
        self.update_bg(bg_classes)

    def update_bg(self, bg_classes):
        if settings.is_using_dynamic_bg:
            self.add_css_class("bg-dark-overlay")
            valid_bgs = set(bg_css.values())
            
            # Remove existing weather backgrounds
            for cls in list(self.get_css_classes()):
                if cls in valid_bgs:
                    self.remove_css_class(cls)
                    
            # Add new ones
            if bg_classes:
                for cls in bg_classes:
                    if cls in valid_bgs:
                        self.add_css_class(cls)
        
        # Trigger a refresh of the compact view data/UI
        if hasattr(self, "compact_view"):
            self.compact_view._start_polling()

    def _on_back(self):
        # Trigger the show-normal action on the application
        app = self.get_application()
        if app:
            app.activate_action("show-normal", None)

    def update_ui(self):
        # Re-trigger polling/build
        if hasattr(self, "compact_view"):
            self.compact_view._start_polling()

    def _on_window_destroy(self, *args):
        app = self.get_application()
        if app and hasattr(app, "compact_window"):
            app.compact_window = None