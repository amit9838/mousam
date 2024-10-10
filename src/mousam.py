import gi
import time
import threading

from gettext import gettext as _, pgettext as C_


# module import
from .utils import create_toast, check_internet_connection, get_time_difference
from .constants import bg_css
from .windowAbout import AboutWindow
from .windowPreferences import WeatherPreferences
from .shortcutsDialog import ShortcutsDialog
from .windowLocations import WeatherLocations
from .frontendCurrentCond import CurrentCondition
from .frontendHourlyDetails import HourlyDetails
from .frontendForecast import Forecast
from .frontendCardSquare import CardSquare
from .frontendCardDayNight import CardDayNight
from .frontendCardAirPollution import CardAirPollution
from .config import settings
from .weatherData import (
    fetch_current_weather,
    fetch_hourly_forecast,
    fetch_daily_forecast,
    fetch_current_air_pollution,
)

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, Gdk, GLib

global updated_at
updated_at = time.time()


class WeatherMainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.main_window = self
        self.set_default_size(settings.window_width, settings.window_height)
        self.connect("close-request", self.save_window_state)
        self.set_title("")
        self._use_dynamic_bg()

        # Global variable :
        self.added_cities = settings.added_cities
        # self.added_cities variable is being used to quickly check the added_added cities so that
        # there is no issue caused by dely in writing and reading in db

        #  Adding a button into header
        self.header = Adw.HeaderBar()
        self.header.set_css_classes(["flat"])

        self.set_titlebar(self.header)

        # Add refresh button to header
        self.refresh_button = Gtk.Button(label="Open")
        self.header.pack_start(self.refresh_button)
        self.refresh_button.set_icon_name("view-refresh-symbolic")
        self.refresh_button.connect("clicked", self._refresh_weather)

        # Create Menu
        menu = Gio.Menu.new()
        self.popover = Gtk.PopoverMenu()  # Create a new popover menu
        self.popover.set_menu_model(menu)

        # Create a menu button
        self.hamburger = Gtk.MenuButton()
        self.hamburger.set_popover(self.popover)
        self.hamburger.set_icon_name("open-menu-symbolic")  # Give it a nice icon
        self.header.pack_end(self.hamburger)

        # Create a menu button
        self.location_button = Gtk.Button(label=_("Location"))
        self.header.pack_end(self.location_button)
        self.location_button.set_icon_name("find-location-symbolic")
        self.location_button.connect("clicked", self._on_locations_clicked)

        # Add preferences option
        action = Gio.SimpleAction.new("preferences", None)
        action.connect("activate", self._on_preferences_clicked)
        self.add_action(action)
        menu.append(_("Preferences"), "win.preferences")

        action = Gio.SimpleAction.new("shortcuts", None)
        action.connect("activate", self._show_shortcuts_dialog)
        self.add_action(action)
        menu.append(_("Keyboard Shortcuts"), "win.shortcuts")

        # Add about option
        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self._on_about_clicked)
        self.add_action(action)
        menu.append(_("About Mousam"), "win.about")

        menu.append(_("Quit"), "app.quit")

        # Toast overlay
        self.toast_overlay = Adw.ToastOverlay.new()
        self.set_child(self.toast_overlay)

        # Scroll content on small screens
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC
        )
        self.scrolled_window.set_kinetic_scrolling(True)
        self.toast_overlay.set_child(self.scrolled_window)

        # Main _clamp
        self.clamp = Adw.Clamp(maximum_size=1400, tightening_threshold=100)
        self.scrolled_window.set_child(self.clamp)

        # main stack
        self.main_stack = Gtk.Stack.new()
        self.main_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.main_stack.set_transition_duration(duration=100)
        self.clamp.set_child(self.main_stack)

        # Start Loader and call paint UI
        # Initiate UI loading weather data and drawing UI
        thread = threading.Thread(target=self._load_weather_data, name="load_data")
        thread.start()

        # Set key listeners
        keycont = Gtk.EventControllerKey()
        keycont.connect("key-pressed", self.on_key_press)
        self.add_controller(keycont)

    # =========== Create Loader =============
    def show_loader(self):
        # Loader container
        child = self.main_stack.get_child_by_name("loader")
        if child is not None:
            self.main_stack.set_visible_child_name("loader")
            return

        container_loader = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container_loader.set_margin_top(200)
        container_loader.set_margin_bottom(200)

        # Create loader
        loader = Gtk.Spinner()
        loader.set_margin_top(50)
        loader.set_margin_bottom(50)
        loader.set_size_request(120, 120)

        loader.set_css_classes(["loader"])
        container_loader.append(loader)

        loader_label = Gtk.Label(label=_("Getting Weather Data"))
        loader_label.set_css_classes(["text-2a", "bold-2"])
        container_loader.append(loader_label)

        loader.start()
        self.main_stack.add_named(container_loader, "loader")
        self.main_stack.set_visible_child_name("loader")

    # =========== Create Welcome Screen =============
    def show_welcome_screen(self):
        child = self.main_stack.get_child_by_name("welcome")
        if child is not None:
            self.main_stack.set_visible_child_name("welcome")
            return

        container_welcome = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container_welcome.set_margin_top(180)
        container_welcome.set_margin_bottom(200)

        icon_mousam = Gtk.Image().new_from_icon_name("io.github.amit9838.mousam")
        icon_mousam.set_hexpand(True)
        icon_mousam.set_pixel_size(110)

        container_welcome.append(icon_mousam)

        welcome_label = Gtk.Label(label=_("Welcome to Mousam"))
        welcome_label.set_css_classes(["text-2a", "bold-2"])
        container_welcome.append(welcome_label)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,halign=Gtk.Align.CENTER)
        btn_box.set_margin_top(20)
        add_loc_button = Gtk.Button(label="Add Location")
        add_loc_button.connect("clicked", self._on_locations_clicked)
        add_loc_button.set_css_classes(["pill"])
        btn_box.append(add_loc_button)
        container_welcome.append(btn_box)


        self.main_stack.add_named(container_welcome, "welcome")
        self.main_stack.set_visible_child_name("welcome")

    # =========== Show No Internet =============
    def show_error(self, type: str = "no_internet", desc: str = ""):
        # Loader container
        message = _("No Internet")
        icon = "network-error-symbolic"
        desc = ""
        if type == "api_error":
            message = _("Could not fetch data from API")
            desc = desc
            icon = "computer-fail-symbolic"

        child = self.main_stack.get_child_by_name("error_box")
        self.toast_overlay.add_toast(create_toast(message, 1))
        if child is not None:
            self.main_stack.set_visible_child_name("error_box")
            return

        error_box = Gtk.Grid(halign=Gtk.Align.CENTER)
        error_box.set_margin_top(300)

        icon = Gtk.Image.new_from_icon_name(icon)
        icon.set_pixel_size(54)
        icon.set_margin_end(20)
        error_box.attach(icon, 0, 0, 1, 1)

        self.error_label = Gtk.Label.new()
        self.error_label.set_label(message)
        self.error_label.set_css_classes(["text-1", "bold-2"])
        error_box.attach(self.error_label, 1, 0, 1, 1)

        self.error_desc = Gtk.Label.new()
        self.error_desc.set_label(desc)
        self.error_desc.set_css_classes(["text-4", "bold-4", "light-3"])
        error_box.attach(self.error_desc, 1, 1, 1, 1)

        self.main_stack.add_named(error_box, "error_box")
        self.main_stack.set_visible_child_name("error_box")

    # =========== Load Weather data using threads =============
    def _load_weather_data(self):
        has_internet = check_internet_connection()
        if not has_internet:
            self.show_error()
            return
      
        if len(self.added_cities) == 0:
            self.show_welcome_screen()
            return

        self.show_loader()

        # cwd : current_weather_data
        # cwt : current_weather_thread
        cwd = threading.Thread(target=fetch_current_weather, name="cwt")
        cwd.start()
        cwd.join()

        hfd = threading.Thread(target=fetch_hourly_forecast, name="hft")
        hfd.start()

        dfd = threading.Thread(target=fetch_daily_forecast, name="dft")
        dfd.start()

        apd = threading.Thread(target=fetch_current_air_pollution, name="apt")
        apd.start()

        lat, lon = settings.selected_city.split(",")
        local_time = threading.Thread(
            target=get_time_difference, args=(lat, lon, True), name="local_time"
        )
        local_time.start()

        hfd.join()
        dfd.join()
        apd.join()
        local_time.join()
        self.get_weather()

    # ===========  Load weather data and create UI ============
    def get_weather(self, reload_type=None, title=""):
        from .weatherData import current_weather_data as cw_data

        self._use_dynamic_bg(
            cw_data.weathercode.get("data"), cw_data.is_day.get("data")
        )

        # Check if no city is added

        # Reset city to default if all cities are removed
        # if len(settings.added_cities) == 0:

        child = self.main_stack.get_child_by_name("main_grid")
        if child is not None:
            self.main_stack.remove(child)

        # ------- Main grid ---------

        self.main_grid = Gtk.Grid()
        self.main_grid.set_hexpand(True)
        self.main_grid.set_vexpand(True)
        self.main_stack.add_named(self.main_grid, "main_grid")

        # -------- Card Current condition  ---------
        current_container_clamp = Adw.Clamp(maximum_size=1400, tightening_threshold=200)
        self.main_grid.attach(current_container_clamp, 0, 0, 3, 1)
        current_container_clamp.set_child(CurrentCondition())
        self.main_grid.attach(HourlyDetails(), 0, 1, 2, 1)

        # --------- Card Forecast ----------
        forecast_container_clamp = Adw.Clamp(maximum_size=800, tightening_threshold=100)
        forecast_container_clamp.set_child(Forecast())
        self.main_grid.attach(forecast_container_clamp, 2, 1, 1, 2)

        # ========= widget grid to hold Cards ==========
        widget_grid = Gtk.Grid()
        self.main_grid.attach(widget_grid, 1, 2, 1, 1)

        # ------- Card Wind ----------
        card_obj = CardSquare(
            title="Wind",
            main_val=cw_data.windspeed_10m.get("data"),
            main_val_unit=cw_data.windspeed_10m.get("unit"),
            desc=cw_data.windspeed_10m.get("level_str"),
            sub_desc_heading=_("From"),
            sub_desc=_("Northwest"),
            text_up=_("N"),
        )
        widget_grid.attach(card_obj.card, 0, 0, 1, 1)

        # -------- Card Humidity ---------
        card_obj = CardSquare(
            title="Humidity",
            main_val=cw_data.relativehumidity_2m.get("data"),
            main_val_unit="%",
            desc=cw_data.relativehumidity_2m.get("level_str"),
            sub_desc_heading=_("Dewpoint"),
            sub_desc="{0} {1}".format(
                cw_data.dewpoint_2m.get("data"), cw_data.dewpoint_2m.get("unit")
            ),
            text_up="100",
            text_low="0",
        )
        widget_grid.attach(card_obj.card, 1, 0, 1, 1)

        # ------- Card Pressure -----------
        card_obj = CardSquare(
            title="Pressure",
            main_val=cw_data.surface_pressure.get("data"),
            main_val_unit="",
            desc=cw_data.surface_pressure.get("unit"),
            sub_desc_heading=cw_data.surface_pressure.get("level_str"),
            text_up=C_("pressure card", "High"),
            text_low=C_("pressure card", "Low"),
        )
        widget_grid.attach(card_obj.card, 0, 1, 1, 1)

        # -------- Card UV Index ---------
        card_obj = CardSquare(
            title="UV Index",
            main_val=cw_data.uv_index.get("data"),
            desc=cw_data.uv_index.get("level_str"),
            text_up=C_("uvindex card", "High"),
            text_low=C_("uvindex card", "Low"),
        )
        widget_grid.attach(card_obj.card, 1, 1, 1, 1)

        # -------- Card Pollution ---------
        card_obj = CardAirPollution()
        widget_grid.attach(card_obj.card, 2, 0, 2, 1)

        # -------- Card Day/Night --------
        card_obj = CardDayNight()
        widget_grid.attach(card_obj.card, 2, 1, 2, 1)

        self.main_stack.set_visible_child_name("main_grid")

        if reload_type == "switch":
            self.toast_overlay.add_toast(
                create_toast(_("Switched to {}".format(title)), 1)
            )
        elif reload_type == "refresh":
            self.toast_overlay.add_toast(create_toast(_("Refreshed Successfully"), 1))

    # ============= Refresh buttom methods ==============
    def _refresh_weather(self, widget=None):
        global updated_at
        # Ignore refreshing weather within 5 second

        if len(self.added_cities) == 0:
            thread = threading.Thread(target=self._load_weather_data, name="load_data")
            thread.start()

        elif time.time() - updated_at < 5:
            updated_at = time.time()
            self.toast_overlay.add_toast(
                create_toast(_("Refresh within 5 seconds is ignored!"), 1)
            )

        else:
            updated_at = time.time()
            self.toast_overlay.add_toast(create_toast(_("Refreshing..."), 1))
            thread = threading.Thread(target=self._load_weather_data, name="load_data")
            thread.start()

    # ============= Dynamic Background methods ==============
    def _use_dynamic_bg(self, weather_code: int = 0, is_day: int = 1):
        if settings.is_using_dynamic_bg:
            dont_delete_classes = ["backgrounds", "csd"]
            for cl in self.get_css_classes():
                if cl not in dont_delete_classes:
                    self.remove_css_class(cl)
            weather_code = str(weather_code)
            if is_day == 0:
                weather_code += "n"
            self.add_css_class(css_class=bg_css[weather_code])

    # ============= Menu button methods ==============
    def _on_about_clicked(self, *args, **kwargs):
        AboutWindow(self.main_window)

    def _on_preferences_clicked(self, *args, **kwargs):
        adw_preferences_window = WeatherPreferences(self.main_window)
        adw_preferences_window.show()

    def _on_locations_clicked(self, *args, **kwargs):
        adw_preferences_window = WeatherLocations(self.main_window)
        adw_preferences_window.show()

    def _show_shortcuts_dialog(self, *args, **kwargs):
        dialog = ShortcutsDialog(self)
        dialog.show()

    # Def shortcuts key listeners
    def on_key_press(self, key_controller, keyval, keycode, state, *args):
        if state & Gdk.ModifierType.CONTROL_MASK:
            if keyval == Gdk.KEY_r:
                self._refresh_weather(None)
            if keyval == Gdk.KEY_l:
                GLib.idle_add(self._on_locations_clicked)
            if keyval == Gdk.KEY_comma:
                GLib.idle_add(self._on_preferences_clicked)
            if keyval == Gdk.KEY_question:
                GLib.idle_add(self._show_shortcuts_dialog)

    def save_window_state(self, window):
        width, height = window.get_default_size()
        settings.window_width = width
        settings.window_height = height
        settings.window_maximized = window.is_maximized()
