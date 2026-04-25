import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib

# Localization
from gettext import gettext as _, pgettext as C_

# Module imports
from .utils import create_toast, check_internet_connection, get_time_difference, local_time_data, AutoRefreshTimer, fetch_all_weather_data_async, show_notification
from .constants import bg_css
from .windowAbout import show_about_window
from .windowPreferences import WeatherPreferences
from .shortcutsDialog import ShortcutsDialog
from .windowLocations import WeatherLocations

# Frontend Components
from .UI_CurrentCond import CurrentCondition
from .UI_HourlyDetails import HourlyDetails
from .UI_Forecast import Forecast
from .UI_CardSquare import CardSquare
from .UI_CardDayNight import CardDayNight
from .UI_CardAirPollution import CardAirPollution
from .UI_CompactWeather import CompactWeatherWindow

from .config import settings
from .CORE_weatherData import (
    fetch_current_weather,
    fetch_hourly_forecast,
    fetch_daily_forecast,
    fetch_current_air_pollution,
)


class WeatherMainWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Window Setup
        self.set_title("Mousam")
        self.set_default_size(settings.window_width, settings.window_height)
        self.connect("close-request", self._save_window_state)
        self.connect("destroy", self._on_window_destroy)

        # State Tracking
        self.added_cities = settings.added_cities
        self._needs_render = False

        # --- UI Construction ---
        self._setup_actions()
        self._setup_ui()
        self._use_dynamic_bg()

        # Initial Data Load
        self._start_data_refresh(is_initial=True)

        # Auto-refresh setup
        settings.connect(
            "changed::auto-refresh-interval",
            lambda *_: self.get_application().auto_refresh.setup(),
        )

    def _setup_ui(self):
        """Initialize the main UI skeleton using Adwaita patterns."""
        self.toolbar_view = Adw.ToolbarView()
        self.set_content(self.toolbar_view)

        # Header Bar
        self.header = Adw.HeaderBar()
        self.header.add_css_class("flat")
        self.toolbar_view.add_top_bar(self.header)

        # Toast Overlay
        self.toast_overlay = Adw.ToastOverlay()
        self.toolbar_view.set_content(self.toast_overlay)

        # Main Content Stack
        self.main_stack = Gtk.Stack()
        self.main_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        # Scrolled Window & Clamp
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC
        )

        self.clamp = Adw.Clamp(maximum_size=1400, tightening_threshold=100)
        self.clamp.set_child(self.main_stack)
        self.scrolled_window.set_child(self.clamp)

        self.toast_overlay.set_child(self.scrolled_window)

        self._build_header_controls()

    def _build_header_controls(self):
        # Refresh Button
        btn_refresh = Gtk.Button(icon_name="view-refresh-symbolic")
        btn_refresh.set_tooltip_text(_("Refresh weather"))
        btn_refresh.set_action_name("win.refresh")
        self.header.pack_start(btn_refresh)

        # Menu
        menu_model = Gio.Menu()
        self._populate_menu(menu_model)

        btn_menu = Gtk.MenuButton()
        btn_menu.set_icon_name("open-menu-symbolic")
        btn_menu.set_menu_model(menu_model)
        self.header.pack_end(btn_menu)

        # Locations Button
        btn_loc = Gtk.Button(icon_name="mark-location-symbolic")
        btn_loc.set_tooltip_text(_("Locations"))
        btn_loc.set_action_name("win.locations")
        self.header.pack_end(btn_loc)

        # Compact Mode Button
        btn_compact = Gtk.Button(icon_name="view-restore-symbolic")
        btn_compact.set_tooltip_text(_("Compact Mode"))
        btn_compact.set_action_name("win.compact")
        self.header.pack_end(btn_compact)

    def _setup_actions(self):
        action_group = Gio.SimpleActionGroup()
        self.insert_action_group("win", action_group)

        actions = [
            ("refresh", self._on_action_refresh, ["<Control>r"]),
            ("locations", self._on_action_locations, ["<Control>l"]),
            ("compact", self._on_action_compact, ["<Control>m"]),
            ("preferences", self._on_action_preferences, ["<Control>comma"]),
            ("shortcuts", self._on_action_shortcuts, ["<Control>question"]),
            ("about", self._on_action_about, None),
        ]

        for name, callback, accel in actions:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            action_group.add_action(action)
            if accel:
                self.get_application().set_accels_for_action(f"win.{name}", accel)

    def _populate_menu(self, menu):
        menu.append(_("Preferences"), "win.preferences")
        menu.append(_("Keyboard Shortcuts"), "win.shortcuts")
        menu.append(_("About Mousam"), "win.about")
        menu.append(_("Quit"), "app.quit")

    # ================= Data Handling =================

    def _start_data_refresh(self, is_initial=False, force_welcome=False, is_auto=False):
        if force_welcome:
            self._update_view_state("welcome")
            return

        if not check_internet_connection():
            self._update_view_state("error_no_internet")
            return


        if not self.added_cities:
            self._update_view_state("welcome")
            return


        self._update_view_state("loader")
        fetch_all_weather_data_async(
            on_success=lambda: self._on_data_fetch_success(is_auto),
            on_error=lambda err: self._update_view_state("error_api")
        )

    # _worker_fetch_data moved to utils.fetch_all_weather_data_async

    def _on_data_fetch_success(self, is_auto=False):
        """Called on Main Thread after the worker has populated weatherData."""
        if self.get_visible():
            self._render_weather_grid()
        else:
            self._needs_render = True
            
        self._update_view_state("content")

    # ================= UI Rendering =================

    def _render_weather_grid(self):
        """
        Now that fetching is done, we can safely import and read the data.
        """
        # Clear previous grid if exists
        child = self.main_stack.get_child_by_name("content")
        if child:
            self.main_stack.remove(child)

        from .CORE_weatherData import current_weather_data as cw_data
        if cw_data is None:
            return

        # Dynamic Background
        w_code = cw_data.weathercode.get("data")
        is_day = cw_data.is_day.get("data")
        self._use_dynamic_bg(
            w_code if w_code is not None else 0,
            is_day if is_day is not None else 1
        )

        # Main Grid Layout
        grid = Gtk.Grid()
        grid.set_margin_top(20)
        grid.set_margin_bottom(10)
        grid.set_margin_start(12)
        grid.set_margin_end(12)
        grid.set_hexpand(True)

        # --- Top Section ---
        current_clamp = Adw.Clamp(maximum_size=1400, tightening_threshold=200)
        curr_cond = CurrentCondition()
        curr_cond.set_size_request(-1, 100)
        current_clamp.set_child(curr_cond)
        grid.attach(current_clamp, 0, 0, 3, 1)

        hourly = HourlyDetails()
        hourly.set_size_request(-1, 180)
        grid.attach(hourly, 0, 1, 2, 1)

        # --- Forecast Section ---
        forecast_clamp = Adw.Clamp()
        forecast = Forecast()
        # forecast.set_size_request(-1, 500)
        forecast_clamp.set_child(forecast)
        grid.attach(forecast_clamp, 2, 1, 1, 2)

        # --- Small Widgets Grid ---
        widget_grid = Gtk.Grid()
        grid.attach(widget_grid, 1, 2, 1, 1)

        def add_card(widget, col, row, width=1):
            # widget.set_size_request(-1, 120)
            widget_grid.attach(widget, col, row, width, 1)

        # Wind
        wind_card = CardSquare(
            title="Wind",
            main_val=cw_data.windspeed_10m.get("data"),
            main_val_unit=cw_data.windspeed_10m.get("unit"),
            desc=cw_data.windspeed_10m.get("level_str"),
            sub_desc_heading=_("From"),
            sub_desc=_("Northwest"),
            text_up=_("N"),
            visual_data=cw_data.winddirection_10m.get("data")
        ).card
        add_card(wind_card, 0, 0)

        # Humidity
        hum_card = CardSquare(
            title="Humidity",
            main_val=cw_data.relativehumidity_2m.get("data"),
            main_val_unit="%",
            desc=cw_data.relativehumidity_2m.get("level_str"),
            sub_desc_heading=_("Dewpoint"),
            sub_desc=f"{cw_data.dewpoint_2m.get('data')} {cw_data.dewpoint_2m.get('unit')}",
            text_up="100",
            text_low="0",
            visual_data=cw_data.relativehumidity_2m.get("data")
        ).card
        add_card(hum_card, 1, 0)

        # Pressure
        low = 872.0
        high = 1080.0
        if settings.unit == 'imperial':
            low *= 0.02953
            high *= 0.02953
        pres_card = CardSquare(
            title="Pressure",
            main_val=cw_data.surface_pressure.get("data"),
            main_val_unit=cw_data.surface_pressure.get("unit"),
            desc=cw_data.surface_pressure.get("level_str"),
            text_up=C_("pressure card", "High"),
            text_low=C_("pressure card", "Low"),
            visual_data=cw_data.surface_pressure.get("data")
        ).card
        add_card(pres_card, 0, 1)

        # UV Index
        uv_card = CardSquare(
            title="UV Index",
            main_val=cw_data.uv_index.get("data"),
            desc=cw_data.uv_index.get("level_str"),
            text_up=C_("uvindex card", "High"),
            text_low=C_("uvindex card", "Low"),
            visual_data=cw_data.uv_index.get("data"),
        ).card
        add_card(uv_card, 1, 1)

        # Pollution & Sun
        add_card(CardAirPollution().card, 2, 0, width=2)
        add_card(CardDayNight().card, 2, 1, width=2)

        self.main_stack.add_named(grid, "content")

    def _update_view_state(self, state: str):
        # Lazy Loading Views
        if self.main_stack.get_child_by_name(state) is None:
            if state == "loader":
                self.main_stack.add_named(self._create_loader_page(), state)
            elif state == "welcome":
                self.main_stack.add_named(self._create_welcome_page(), state)
            elif state == "error_no_internet":
                self.main_stack.add_named(
                    self._create_error_page("network-error-symbolic", _("No Internet")),
                    state,
                )
            elif state == "error_api":
                self.main_stack.add_named(
                    self._create_error_page("computer-fail-symbolic", _("API Error")),
                    state,
                )

        if self.main_stack.get_child_by_name(state):
            self.main_stack.set_visible_child_name(state)

    def _create_loader_page(self):
        spinner = Adw.Spinner()
        spinner.set_size_request(64, 64)
        page = Adw.StatusPage()
        page.set_title(_("Getting Weather Data"))
        page.set_child(spinner)
        return page

    def _create_welcome_page(self):
        page = Adw.StatusPage()
        page.set_icon_name("io.github.amit9838.mousam")
        page.set_title(_("Welcome to Mousam"))
        page.set_description(_("Add a location to get started."))
        btn = Gtk.Button(label=_("Add Location"))
        btn.add_css_class("pill")
        btn.add_css_class("suggested-action")
        btn.set_action_name("win.locations")
        btn.set_halign(Gtk.Align.CENTER)
        page.set_child(btn)
        return page

    def _create_error_page(self, icon, title):
        page = Adw.StatusPage()
        page.set_icon_name(icon)
        page.set_title(title)
        return page

    def _use_dynamic_bg(self, weather_code: int = 0, is_day: int = 1) -> None:
        # Always required classes
        required = {"background", "csd", "dynamic-bg"}
        
        # Add weather class if dynamic backgrounds are on
        if settings.is_using_dynamic_bg:
            key = f"{weather_code}{'' if is_day else 'n'}"
            if weather_cls := bg_css.get(key):
                required.add(weather_cls)
        
        current = set(self.get_css_classes())
        weather_classes = set(bg_css.values())
        
        # Keep all non-weather classes, but enforce the required ones
        target = (current - weather_classes) | required
        
        # Sync current classes to target
        # classes that are currently on the widget but not in the target. These need to be removed.
        for cls in current - target:
            self.remove_css_class(cls)

        # classes that are in the target but not currently on the widget. These need to be added.
        for cls in target - current:
            self.add_css_class(cls)

    # Removed _setup_auto_refresh, logic moved to utils.AutoRefreshTimer

    def _pre_refresh_cleanup(self):
        from .API_Weather import Weather
        from .API_AirPollution import AirPollution

        # Evict old content widget tree (weak refs in draw funcs handle GC cleanly)
        child = self.main_stack.get_child_by_name("content")
        if child:
            self.main_stack.remove(child)

        # Clear API response caches so the next fetch goes to network
        Weather.current_weather.__func__.cache_clear()
        Weather.forecast_hourly.__func__.cache_clear()
        Weather.forecast_daily.__func__.cache_clear()
        AirPollution.current_air_pollution.cache_clear()

        # Clear timezone cache (will be repopulated during fetch)
        local_time_data.clear()


    def _save_window_state(self, window):

        width, height = window.get_default_size()
        settings.window_width = width
        settings.window_height = height
        settings.window_maximized = window.is_maximized()

    def _on_window_destroy(self, *args):
        app = self.get_application()
        if app and hasattr(app, "main_window"):
            app.main_window = None

    def present(self):
        if getattr(self, "_needs_render", False):
            self._render_weather_grid()
            self._needs_render = False
        super().present()

    # --- Callbacks ---
    def _on_action_refresh(self, action, param):
        self._start_data_refresh()

    def _on_action_locations(self, action, param):
        win = WeatherLocations(self)
        win.present()

    def _on_action_compact(self, action, param):
        self.get_application().activate_action("show-compact", None)

    def _on_action_preferences(self, action, param):
        win = WeatherPreferences(self)
        win.present()

    def _on_action_shortcuts(self, action, param):
        ShortcutsDialog(self).present()

    def _on_action_about(self, action, param):
        show_about_window(self)
