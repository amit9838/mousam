import gi
from datetime import datetime
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk,Adw,Gio,GLib

from .constants import API_KEY
from .windowPreferences import WeatherPreferences
from .windowAbout import AboutWindow
from .uiCurrent_w import current_weather,air_pollution
from .uiForecast_w  import forecast_weather 
from .utils import *

from .backendCurrent_w import fetch_weather
from .backendForecast_w import fetch_forecast

settings = Gio.Settings.new("io.github.amit9838.weather")
selected_city = int(str(settings.get_value('selected-city')))
added_cities = list(settings.get_value('added-cities'))
cities = [x.split(',')[0] for x in added_cities]
updated_at = settings.get_string('updated-at')

class WeatherWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'WeatherWindow'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        global application
        self.set_default_size(800, 400)
        self.set_app_title(title="Weather")
        self.main_window = application = self

        # Initial checks
        if len(added_cities) == 0:
            settings.reset('added-cities')
            settings.reset('selected-city')

        self.toast_overlay = Adw.ToastOverlay.new()
        self.clamp = Adw.Clamp(maximum_size=1000, tightening_threshold=900)
        self.set_child(self.toast_overlay)
        self.toast_overlay.set_child(self.clamp)

        self.main_stack = Gtk.Stack.new()
        self.clamp.set_child(self.main_stack)

        self.main_grid = Gtk.Grid()
        self.main_grid.set_hexpand(True)
        self.main_stack.add_named(self.main_grid,'main_grid')
        
        self.upper_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,valign=Gtk.Align.CENTER, vexpand=True, halign=Gtk.Align.FILL)
        self.upper_row.set_hexpand(True)
        self.upper_row.set_size_request(800,160)
        self.main_grid.attach(self.upper_row,0,0,1,1)

        self.middle_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,valign=Gtk.Align.CENTER, vexpand=True, halign=Gtk.Align.FILL)
        self.middle_row.set_hexpand(True)
        self.middle_row.set_size_request(800,200)
        self.main_grid.attach(self.middle_row,0,1,1,1)

        #  Adding refresh button into header
        self.header = Adw.HeaderBar()
        self.header.add_css_class(css_class='flat')
        self.set_titlebar(self.header)
        self.refresh_button = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        self.refresh_button.set_tooltip_text(_("Refresh"))
        self.refresh_button.connect('clicked',self.refresh_weather)
        self.header.pack_start(self.refresh_button)

        # Create a popover
        menu = Gio.Menu.new()
        self.popover = Gtk.PopoverMenu()
        self.popover.set_menu_model(menu)

        # Create a menu button
        self.hamburger = Gtk.MenuButton()
        self.hamburger.set_popover(self.popover)
        self.hamburger.set_icon_name("open-menu-symbolic")
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

        error_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,halign=Gtk.Align.CENTER)
        error_box.set_margin_bottom(100)
        self.main_stack.add_named(error_box,'error_box')

        self.error_label = Gtk.Label.new()
        self.error_label.set_label("Failed to load Weather Data")
        self.error_label.set_css_classes(['error_label'])

        icon = Gtk.Image.new_from_icon_name("network-error-symbolic")
        icon.set_pixel_size(36)
        icon.set_margin_end(10)

        error_box.append(icon)
        error_box.append(self.error_label)

        # Initial Fetch -------------------------
        has_internet, response_text = check_internet_connection()
        if has_internet == False:
            self.error_label.set_label(response_text)
            self.main_stack.set_visible_child_name("error_box")
        else:
            self.fetch_weather_data()

    def set_app_title(self,title = "Weather"):
            self.set_title(title)

    def refresh_weather(self,widget,ignore=True):
        global settings,updated_at
        has_internet, response_text = check_internet_connection()
        if has_internet == False:
            self.toast_overlay.add_toast(create_toast(_("No internet!"),1))
            return
        if len(added_cities) == 0:  # Reset city to default if all cities are removed
            settings.reset('added-cities')
            settings.reset('selected-city')
            
        # Ignore refreshing weather within 5 second
        extract_seconds = lambda x: float(x.split(" ")[1].split(":")[2])

        if ignore and abs(datetime.now().second - extract_seconds(updated_at)) < 5:
            self.toast_overlay.add_toast(create_toast(_("Refresh within 5 seconds is ignored!"),1))
            return

        date_time = datetime.now()
        updated_at = str(date_time)
        settings.set_value("updated-at",GLib.Variant("s",updated_at))
        self.clear_main_ui_grid()
        self.fetch_weather_data()
        if ignore:
            self.toast_overlay.add_toast(create_toast(_("Refreshing..."),1))

    def fetch_weather_data(self):
        latitude,longitude = get_selected_city_coords()
        w_data = fetch_weather(API_KEY,latitude,longitude)
        f_data = fetch_forecast(API_KEY,latitude,longitude)
        ap_data = air_pollution(API_KEY,latitude,longitude)

        if w_data is None and f_data is  None:
            self.main_stack.set_visible_child_name("error_box")
        else:
            self.main_stack.set_visible_child_name('main_grid')
            self.clear_main_ui_grid()
            f_data = f_data.get('list')
            set_weather_data(w_data,ap_data,f_data) # Save weather data as cache
            self.plot_current(self.upper_row,w_data,ap_data)
            self.plot_forecast(self.middle_row,f_data)

    def plot_current(self,widget,w_data,ap_data):
        current_weather(self.main_window,widget,w_data,ap_data)
         
    def plot_forecast(self,widget,f_data):
        forecast_weather(widget,f_data)

    def refresh_main_ui(self):  # Repaint main UI with previously fetched data
        self.clear_main_ui_grid()
        w_data,ap_data, f_data = get_weather_data()
        self.plot_current(self.upper_row,w_data,ap_data)
        self.plot_forecast(self.middle_row,f_data)

    def _on_about_clicked(self, widget, param):
        AboutWindow(application)

    def _on_preferences_clicked(self, widget, param):
        adw_preferences_window = WeatherPreferences(application)
        adw_preferences_window.show()

    def clear_main_ui_grid(self):
            upper_child = self.upper_row.get_first_child()
            middle_child = self.middle_row.get_first_child()
            if upper_child is not None and middle_child is not None:
                self.upper_row.remove(upper_child)
                self.middle_row.remove(middle_child)
