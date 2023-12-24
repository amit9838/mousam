import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk, Gio, GLib

# module import
from .windowAbout import AboutWindow
from .windowPreferences import WeatherPreferences
from .frontendCurrentCond import CurrentCondition
from .frontendHourlyDetails import HourlyDetails
from .frontendForecast import Forecast
from .frontendCardSquare import CardSquare
from .frontendCardDayNight import CardDayNight
from .frontendCardAirPollution import *
from .weatherData import (
    fetch_current_weather,
    fetch_hourly_forecast,
    fetch_daily_forecast,
    fetch_current_air_pollution,
)


# global css_provider
# css_provider = Gtk.CssProvider()
# css_provider.load_from_path("application.css")
# Gtk.StyleContext.add_provider_for_display(
#     Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
# )


class WeatherMainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        global application
        self.main_window = application = self

        self.set_default_size(1220, 840)
        self.set_title("")

        #  Adding a button into header
        self.header = Adw.HeaderBar()
        self.header.add_css_class(css_class="flat")
        self.set_titlebar(self.header)
        self.open_button = Gtk.Button(label="Open")
        self.header.pack_start(self.open_button)
        self.open_button.set_icon_name("view-refresh-symbolic")


        # Create Menu -----------------------------
        menu = Gio.Menu.new()
        self.popover = Gtk.PopoverMenu()  # Create a new popover menu
        self.popover.set_menu_model(menu)

        # Create a menu button
        self.hamburger = Gtk.MenuButton()
        self.hamburger.set_popover(self.popover)
        self.hamburger.set_icon_name("open-menu-symbolic")  # Give it a nice icon
        self.header.pack_end(self.hamburger)


        # Create a new action
        action = Gio.SimpleAction.new("preferences", None)
        action.connect("activate", self._on_preferences_clicked)
        self.add_action(action)
        menu.append(_("Preferences"), "win.preferences")
        #menu.append("Help", "help")

        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self._on_about_clicked)
        self.add_action(action)
        menu.append(_("About Weather"), "win.about")


        # Toast overlay
        self.toast_overlay = Adw.ToastOverlay.new()
        self.set_child(self.toast_overlay)

        # Main _clamp
        self.clamp = Adw.Clamp(maximum_size=1600, tightening_threshold=100)
        self.toast_overlay.set_child(self.clamp)

        # main stack
        self.main_stack = Gtk.Stack.new()
        self.clamp.set_child(self.main_stack)

        self.show_loader()

    def show_loader(self):
        container_loader = Gtk.Box()
        container_loader.set_margin_top(200)
        container_loader.set_margin_bottom(300)

        loader = Gtk.Label(label=f"Loading…")
        loader.set_css_classes(['text-1','bold-2'])

        loader.set_hexpand(True)
        loader.set_vexpand(True)
        container_loader.append(loader)
        self.main_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.main_stack.set_transition_duration(duration=100)
        self.main_stack.add_named(container_loader,'loader')
        self.main_stack.set_visible_child_name('loader')
        
        GLib.idle_add(self.draw_ui)


    def draw_ui(self):
        # Initial fetch ----------------------------------------------
        cw_data = fetch_current_weather()
        hf_data = fetch_hourly_forecast()
        df_data = fetch_daily_forecast()
        air_poll = fetch_current_air_pollution()

        # Main grid
        self.main_grid = Gtk.Grid()
        self.main_grid.set_hexpand(True)
        self.main_grid.set_vexpand(True)
        self.main_stack.add_named(self.main_grid, "main_grid")

        # self.set_css_classes(['main_window','gradient-bg','dark'])

        current_container_clamp = Adw.Clamp(maximum_size=1400, tightening_threshold=40)
        self.main_grid.attach(current_container_clamp, 0, 0, 3, 1)
        current_container_clamp.set_child(CurrentCondition())
        self.main_grid.attach(HourlyDetails(), 0, 1, 2, 1)

        hourly_container_clamp = Adw.Clamp(maximum_size=800, tightening_threshold=100)
        hourly_container_clamp.set_child(Forecast())
        self.main_grid.attach(hourly_container_clamp, 2, 1, 1, 4)
        # self.main_grid.attach(Forecast(),2,1,1,1)

        widget_grid = Gtk.Grid()
        self.main_grid.attach(widget_grid, 1, 2, 1, 1)

        # container_clamp = Adw.Clamp(maximum_size=350, tightening_threshold=10,margin_top=10)
        # widget_grid.attach(container_clamp,0,0,1,1)
        # card_obj = CardSquare("Wind",28,"km/h","Moderate","From","Northwest")
        # container_clamp.set_child(card_obj.card)

        card_obj = CardSquare(
            "Wind",
            cw_data["current"]["windspeed_10m"],
            "km/h",
            "Moderate",
            "From",
            "Northwest",
            "N",
        )
        widget_grid.attach(card_obj.card, 0, 0, 1, 1)

        card_obj = CardSquare(
            "Humidity",
            88,
            "%",
            "High",
            "Dew Point",
            "23°C",
            text_up="100",
            text_low="0",
        )
        widget_grid.attach(card_obj.card, 1, 0, 1, 1)

        card_obj = CardSquare(
            "Pressure",
            cw_data["current"]["surface_pressure"],
            cw_data["current_units"]["surface_pressure"],
            "Normal",
            text_up="High",
            text_low="Low",
        )
        widget_grid.attach(card_obj.card, 0, 1, 1, 1)

        card_obj = CardSquare(
            "UV Index", cw_data["uv_index"], "", "High", text_up="High", text_low="Low"
        )
        widget_grid.attach(card_obj.card, 1, 1, 1, 1)

        card_obj = CardRectangle()
        widget_grid.attach(card_obj.card, 2, 0, 2, 1)

        card_obj = CardDayNight()
        widget_grid.attach(card_obj.card, 2, 1, 2, 1)
        self.main_stack.set_visible_child_name("main_grid")


    def _on_about_clicked(self, widget, param):
        AboutWindow(application)

    def _on_preferences_clicked(self, widget, param):
        adw_preferences_window = WeatherPreferences(application)
        adw_preferences_window.show()