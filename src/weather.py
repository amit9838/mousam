import gi
import time
import threading

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio

# module import
from .utils import create_toast,check_internet_connection
from .windowAbout import AboutWindow
from .windowPreferences import WeatherPreferences
from .windowLocations import WeatherLocations
from .frontendCurrentCond import CurrentCondition
from .frontendHourlyDetails import HourlyDetails
from .frontendForecast import Forecast
from .frontendCardSquare import CardSquare
from .frontendCardDayNight import CardDayNight
from .frontendCardAirPollution import CardAirPollution
from .weatherData import (
    fetch_current_weather,
    fetch_hourly_forecast,
    fetch_daily_forecast,
    fetch_current_air_pollution,
)

global updated_at
updated_at = time.time()

class WeatherMainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        global application
        self.main_window = application = self
        self.settings = Gio.Settings(schema_id="io.github.amit9838.weather")
        self.set_default_size(1220, 860)
        self.set_title("")
        #  Adding a button into header
        self.header = Adw.HeaderBar()
        self.header.add_css_class(css_class="flat")
        self.set_titlebar(self.header)

        # Add refresh button to header
        self.refresh_button = Gtk.Button(label="Open")
        self.header.pack_start(self.refresh_button)
        self.refresh_button.set_icon_name("view-refresh-symbolic")
        self.refresh_button.connect('clicked',self._refresh_weather)

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
        self.location_button = Gtk.Button(label="Open")
        self.header.pack_end(self.location_button)
        self.location_button.set_icon_name("find-location-symbolic")
        self.location_button.connect('clicked',self._on_locations_clicked)

        # Add preferences option
        action = Gio.SimpleAction.new("preferences", None)
        action.connect("activate", self._on_preferences_clicked)
        self.add_action(action)
        menu.append(_("Preferences"), "win.preferences")

        # menu.append("Help", "help")

        # Add about option
        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self._on_about_clicked)
        self.add_action(action)
        menu.append(_("About Weather"), "win.about")

        # Toast overlay
        self.toast_overlay = Adw.ToastOverlay.new()
        self.set_child(self.toast_overlay)

        # Main _clamp
        self.clamp = Adw.Clamp(maximum_size=1400, tightening_threshold=100)
        self.toast_overlay.set_child(self.clamp)

        # main stack
        self.main_stack = Gtk.Stack.new()
        self.main_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.main_stack.set_transition_duration(duration=100)
        self.clamp.set_child(self.main_stack)

        # Start Loader and call paint UI
        # Initiate UI loading weather data and drawing UI
        thread = threading.Thread(target=self._load_weather_data,name="load_data")
        thread.start()

    # =========== Create Loader =============
    def show_loader(self):
        # Loader container
        child = self.main_stack.get_child_by_name('loader')
        if child is not None:
                self.main_stack.set_visible_child_name("loader")
                return

        container_loader = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container_loader.set_margin_top(250)
        container_loader.set_margin_bottom(300)


        # Create loader
        loader = Gtk.Spinner()
        loader.set_margin_top(50)
        loader.set_margin_bottom(50)
        loader.set_size_request(120, 120)

        loader.set_css_classes(['loader'])
        container_loader.append(loader)


        loader_label = Gtk.Label(label=f"Getting Weather Data")
        loader_label.set_css_classes(["text-2a", "bold-2"])
        container_loader.append(loader_label)

        loader.start()
        # loader.set_hexpand(True)
        # loader.set_vexpand(True)
        self.main_stack.add_named(container_loader, "loader")
        self.main_stack.set_visible_child_name("loader")


    # =========== Show No Internet =============
    def show_error(self,type:str="no_internet",desc : str = ""):
        # Loader container
        message = "No Internet"
        icon = "network-error-symbolic"
        desc = ""
        if type == "api_error":
            message = "Could not fetch data from API"
            desc = desc
            icon = "computer-fail-symbolic"
            

        child = self.main_stack.get_child_by_name('error_box')
        self.toast_overlay.add_toast(create_toast(message,1))
        if child is not None:
                self.main_stack.set_visible_child_name("error_box")
                return

        error_box = Gtk.Grid(halign=Gtk.Align.CENTER)
        error_box.set_margin_top(300)

        icon = Gtk.Image.new_from_icon_name(icon)
        icon.set_pixel_size(54)
        icon.set_margin_end(20)
        error_box.attach(icon,0,0,1,1)

        self.error_label = Gtk.Label.new()
        self.error_label.set_label(message)
        self.error_label.set_css_classes(["text-1", "bold-2"])
        error_box.attach(self.error_label,1,0,1,1)
       
        self.error_desc = Gtk.Label.new()
        self.error_desc.set_label(desc)
        self.error_desc.set_css_classes(["text-4", "bold-4",'light-3'])
        error_box.attach(self.error_desc,1,1,1,1)

        self.main_stack.add_named(error_box,'error_box')
        self.main_stack.set_visible_child_name("error_box")

    # =========== Load Weather data using threads =============
    def _load_weather_data(self):

        has_internet = check_internet_connection()
        if not has_internet:
            self.show_error()
            return
        
        self.show_loader()
        
        # cwd : current_weather_data
        # cwt : current_weather_thread
        cwd = threading.Thread(target=fetch_current_weather,name="cwt")
        cwd.start()
        cwd.join()

        hfd = threading.Thread(target=fetch_hourly_forecast,name="hft")
        hfd.start()

        dfd = threading.Thread(target=fetch_daily_forecast,name="dft")
        dfd.start()

        apd = threading.Thread(target=fetch_current_air_pollution,name="apt")
        apd.start()
        
        apd.join()
        hfd.join()
        dfd.join()
        self.get_weather()
        

    # ===========  Load weather data and create UI ============
    def get_weather(self,reload_type=None,title = ""):
        from .weatherData import current_weather_data as cw_data
        # Check if no city is added
        added_cities = self.settings.get_strv('added-cities')

        if len(added_cities) == 0:  # Reset city to default if all cities are removed
            self.settings.reset('added-cities')
            self.settings.reset('selected-city')
        
        child = self.main_stack.get_child_by_name('main_grid')
        if child is not None:
            self.main_stack.remove(child)

        # ------- Main grid ---------
        self.main_grid = Gtk.Grid()
        self.main_grid.set_hexpand(True)
        self.main_grid.set_vexpand(True)
        self.main_stack.add_named(self.main_grid, "main_grid")

        # -------- Current condition Card ---------
        current_container_clamp = Adw.Clamp(maximum_size=1400, tightening_threshold=200)
        self.main_grid.attach(current_container_clamp, 0, 0, 3, 1)
        current_container_clamp.set_child(CurrentCondition())
        self.main_grid.attach(HourlyDetails(), 0, 1, 2, 1)

        # --------- Forecast card ----------
        forecast_container_clamp = Adw.Clamp(maximum_size=800, tightening_threshold=100)
        forecast_container_clamp.set_child(Forecast())
        self.main_grid.attach(forecast_container_clamp, 2, 1, 1, 2)

        # ========= Card widget grid ==========
        widget_grid = Gtk.Grid()
        self.main_grid.attach(widget_grid, 1, 2, 1, 1)

        # ------- Wind card ----------
        card_obj = CardSquare(
            title="Wind",
            main_val=cw_data.windspeed_10m.get("data"),
            main_val_unit=cw_data.windspeed_10m.get("unit"),
            desc=cw_data.windspeed_10m.get("level_str"),
            sub_desc_heading="From",
            sub_desc="Northwest",
            text_up="N",
        )
        widget_grid.attach(card_obj.card, 0, 0, 1, 1)

        # -------- Humidity card  ---------
        card_obj = CardSquare(
            title="Humidity",
            main_val=cw_data.relativehumidity_2m.get("data"),
            main_val_unit="%",
            desc=cw_data.relativehumidity_2m.get("level_str"),
            sub_desc_heading="Dewpoint",
            sub_desc="{0} {1}".format(cw_data.dewpoint_2m.get('data'),cw_data.dewpoint_2m.get('unit')),
            text_up="100",
            text_low="0",
        )
        widget_grid.attach(card_obj.card, 1, 0, 1, 1)

        # ------- Pressure card -----------
        card_obj = CardSquare(
            title="Pressure",
            main_val=cw_data.surface_pressure.get("data"),
            main_val_unit="",
            desc=cw_data.surface_pressure.get("unit"),
            sub_desc_heading=cw_data.surface_pressure.get("level_str"),
            text_up="High",
            text_low="Low",
        )
        widget_grid.attach(card_obj.card, 0, 1, 1, 1)

        # -------- UV Index card ---------
        card_obj = CardSquare(
            title="UV Index",
            main_val=cw_data.uv_index.get("data"),
            desc=cw_data.uv_index.get("level_str"),
            text_up="High",
            text_low="Low",
        )
        widget_grid.attach(card_obj.card, 1, 1, 1, 1)

        # -------- Card Rectangle ---------
        card_obj = CardAirPollution()
        widget_grid.attach(card_obj.card, 2, 0, 2, 1)

        # -------- Card Day/Night --------
        card_obj = CardDayNight()
        widget_grid.attach(card_obj.card, 2, 1, 2, 1)

        self.main_stack.set_visible_child_name("main_grid")

        if reload_type == 'switch':
            self.toast_overlay.add_toast(create_toast(("Switched to {}".format(title)),1))
        elif reload_type == "refresh":
            self.toast_overlay.add_toast(create_toast(("Refreshed Successfully"),1))


    # ============= Refresh buttom methods ==============
    def _refresh_weather(self,widget):
        global updated_at      
        # Ignore refreshing weather within 5 second

        if time.time() - updated_at < 5:
            updated_at = time.time()
            self.toast_overlay.add_toast(create_toast(_("Refresh within 5 seconds is ignored!"),1))

        else:
            updated_at = time.time()
            self.toast_overlay.add_toast(create_toast(_("Refreshing..."),1))
            thread = threading.Thread(target=self._load_weather_data,name="load_data")
            thread.start()


    # ============= Menu buttom methods ==============
    def _on_about_clicked(self, *args, **kwargs ):
        AboutWindow(application)

    def _on_preferences_clicked(self,  *args, **kwargs):
        adw_preferences_window = WeatherPreferences(application)
        adw_preferences_window.show()

    def _on_locations_clicked(self, *args, **kwargs):
        adw_preferences_window = WeatherLocations(application)
        adw_preferences_window.show()