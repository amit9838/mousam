import gi
import datetime
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw,Gdk,Gio,GLib

from .constants import API_KEY
from .windows import AboutWindow,WeatherPreferences
from .ui_current_w import current_weather
from .ui_forecast_w  import forecast_weather 

from .backend_current_w import fetch_weather
from .backend_forecast_w import fetch_forecast

settings = Gio.Settings.new("io.github.amit9838.weather")
selected_city = int(str(settings.get_value('selected-city')))
added_cities = list(settings.get_value('added-cities'))
cities = [x.split(',')[0] for x in added_cities]
updated_at = str(settings.get_value('updated-at'))[1:-1]

class WeatherWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'WeatherWindow'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        global application
        self.set_default_size(800, 400)
        
        # self.set_title(_("Weather"))
        self.set_app_title(title="Weather")

        self.main_window = application = self

        # Initial checks
        if len(added_cities) == 0:
            settings.reset('added-cities')
            settings.reset('selected-city')

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_hexpand(True)
        main_box.set_vexpand(True)
        self.toast_overlay = Adw.ToastOverlay.new()
        self.set_child(self.toast_overlay)
        self.toast_overlay.set_child(main_box)

        main_grid = Gtk.Grid()
        main_grid.set_hexpand(True)
        main_box.append(main_grid)
        
        self.upper_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,valign=Gtk.Align.CENTER)
        self.upper_row.set_hexpand(True)
        self.upper_row.set_size_request(800,160)
        main_grid.attach(self.upper_row,0,0,1,1)

        self.middle_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,valign=Gtk.Align.CENTER)
        self.middle_row.set_hexpand(True)
        self.middle_row.set_size_request(800,200)
        main_grid.attach(self.middle_row,0,1,1,1)

        #  Adding refresh button into header
        self.header = Adw.HeaderBar()
        self.header.add_css_class(css_class='flat')
        self.set_titlebar(self.header)
        self.refresh_button = Gtk.Button(label="refresh")
        self.header.pack_start(self.refresh_button)
        self.refresh_button.set_icon_name("view-refresh-symbolic")
        self.refresh_button.set_tooltip_text(_("Refresh"))
        self.refresh_button.connect('clicked',self.refresh_weather)

        # Create a popover
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
        action.connect("activate", self.show_preferences)
        self.add_action(action)
        menu.append(_("Preferences"), "win.preferences")
        #menu.append("Help", "help")

        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", AboutWindow)
        self.add_action(action)
        menu.append(_("About Weather"), "win.about")

        # Initial Fetch -------------------------
        self.fetch_weather_data()

        # Footer Section -------------------------
        footer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        footer_box.set_halign(Gtk.Align.CENTER)
        footer_box.set_size_request(800,10)
        footer_box.set_margin_bottom(0)
        main_box.append(footer_box)

    def set_app_title(self,title = "Wather"):
            self.set_title(title)

    def refresh_weather(self,widget,ignore=True):
        global settings,updated_at
        if len(added_cities) == 0:
            settings.reset('added-cities')
            settings.reset('selected-city')
            
        # Ignore refreshing weather within 3 second
        d_t = updated_at.split(" ")
        # Time
        tm = d_t[1]
        t_arr = tm.split(":")
        t_sec = float(t_arr[2])
        
        if ignore and abs(datetime.datetime.now().second - t_sec) < 3:
            refresh_toast = Adw.Toast.new(_("Refresh within 3 seconds is ignored!"))
            refresh_toast.set_priority(Adw.ToastPriority(1))
            self.toast_overlay.add_toast(refresh_toast)
            return

        date_time = datetime.datetime.now()
        updated_at = str(date_time)
        settings.set_value("updated-at",GLib.Variant("s",updated_at))
        upper_child = self.upper_row.get_first_child()
        if upper_child is not None:
            self.upper_row.remove(upper_child)
            
        middle_child = self.middle_row.get_first_child()
        if middle_child is not None:
            self.middle_row.remove(middle_child)
            

        self.fetch_weather_data()
        refresh_toast = Adw.Toast.new(_("Refreshing..."))
        refresh_toast.set_priority(Adw.ToastPriority(1))
        self.toast_overlay.add_toast(refresh_toast)
        
        
    def fetch_weather_data(self):
        settings = Gio.Settings.new("io.github.amit9838.weather")
        selected_city = int(str(settings.get_value('selected-city')))
        added_cities = list(settings.get_value('added-cities'))
        city_loc = added_cities[selected_city]
        city_loc = city_loc.split(',')
        latitude = (city_loc[-2])
        longitude = (city_loc[-1])
      
        w_data = fetch_weather(API_KEY,latitude,longitude)
        f_data = fetch_forecast(API_KEY,latitude,longitude)
        
        if w_data is  None and f_data is  None:
            error_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,halign=Gtk.Align.CENTER)
            error_box.set_margin_top(50)
            label = Gtk.Label(label = _("Failed to load Weather Data"))
            label.set_css_classes(['error_label'])

            icon = Gtk.Image()
            icon.set_from_icon_name("network-error-symbolic")  # Set the icon name and size
            icon.set_pixel_size(36)
            icon.set_margin_end(10)
            error_box.append(icon)
            error_box.append(label)
            self.upper_row.append(error_box)
        else:
            print("Plot data...")
            upper_child = self.upper_row.get_first_child()
            middle_child = self.middle_row.get_first_child()
            if upper_child is not None and middle_child is not None:
                self.upper_row.remove(upper_child)
                self.middle_row.remove(middle_child)
            current_weather(self.main_window,self.upper_row,self.middle_row,w_data)
            forecast_weather(self.middle_row,f_data)

    def show_preferences(self, action, param):
        adw_preferences_window = WeatherPreferences(application)
        adw_preferences_window.show()
