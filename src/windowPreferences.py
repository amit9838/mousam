import gi
import time
import threading

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw,GLib

from .utils import create_toast
from .config import settings

global updated_at
updated_at = time.time()


class WeatherPreferences(Adw.PreferencesWindow):
    def __init__(self, application,  **kwargs):
        super().__init__(**kwargs)
        self.application = application
        self.set_transient_for(application)
        self.set_default_size(600, 500)

        # =============== Appearance Page  ===============
        appearance_page = Adw.PreferencesPage()
        appearance_page.set_title(_("Appearance"))
        appearance_page.set_icon_name('applications-graphics-symbolic')
        self.add(appearance_page)

        self.appearance_grp = Adw.PreferencesGroup()
        appearance_page.add(self.appearance_grp)

        # Dynamic Background 
        gradient_row =  Adw.ActionRow.new()
        gradient_row.set_activatable(True)
        gradient_row.set_title(_("Dynamic Background"))
        gradient_row.set_subtitle(_("Background changes based on current weather condition (Restart required)"))

        self.g_switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.CENTER)
        self.gradient_switch = Gtk.Switch()
        self.gradient_switch.set_active(settings.is_using_dynamic_bg)
        self.gradient_switch.connect("state-set",self._use_gradient_bg)
        self.g_switch_box.append(self.gradient_switch)
        gradient_row.add_suffix(self.g_switch_box)
        self.appearance_grp.add(gradient_row)

        #  Launch the app in maximize mode
        launch_maximized =  Adw.ActionRow.new()
        launch_maximized.set_activatable(True)
        launch_maximized.set_title(_("Launch Maximized"))
        launch_maximized.set_subtitle(_("Launch the weather app in maximized mode (Refresh required)"))

        self.g_switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.CENTER)
        self.launch_max_switch = Gtk.Switch()
        self.launch_max_switch.set_active(settings.should_launch_maximized)
        self.launch_max_switch.connect("state-set",self._on_click_launch_maximixed)
        self.g_switch_box.append(self.launch_max_switch)
        launch_maximized.add_suffix(self.g_switch_box)
        self.appearance_grp.add(launch_maximized)

        #  Units and measurement
        self.measurement_group = Adw.PreferencesGroup.new()
        self.measurement_group.set_margin_top(20)
        self.measurement_group.set_title(_('Units &amp; Measurements'))
        self.appearance_grp.add(self.measurement_group)

        self.metric_unit = Adw.ActionRow.new()
        self.metric_unit.set_title(_('°C'))
        self.metric_unit.set_subtitle(_("METRIC system with units like celcuis, km/h, kilometer"))
        self.metric_check_btn = Gtk.CheckButton.new()
        self.metric_unit.add_prefix(self.metric_check_btn)
        self.metric_unit.set_activatable_widget(self.metric_check_btn)
        self.metric_unit.connect("activated", self._change_unit,'metric')
        self.measurement_group.add(self.metric_unit)

        self.imperial_unit = Adw.ActionRow.new()
        self.imperial_unit.set_title(_('°F'))
        self.imperial_unit.set_subtitle(_("IMPERIAL system with units like fahrenheit, mph, miles"))
        self.imperial_check_btn = Gtk.CheckButton.new()
        self.imperial_unit.add_prefix(self.imperial_check_btn)
        self.imperial_check_btn.set_group(self.metric_check_btn)
        self.imperial_unit.set_activatable_widget(self.imperial_check_btn)
        self.imperial_unit.connect("activated", self._change_unit,'imperial')
        self.measurement_group.add(self.imperial_unit)
        GLib.idle_add(self.metric_unit.activate) if settings.unit == 'metric' else  GLib.idle_add(self.imperial_unit.activate)

        self.prec_unit_group = Adw.PreferencesGroup.new()
        self.prec_unit_group.set_margin_top(20)
        self.appearance_grp.add(self.prec_unit_group)
        
        self.prec_unit = Adw.ActionRow.new()
        self.prec_unit.set_title(_('Show precipitation in inch'))
        self.prec_unit.set_subtitle(_("This option better works during heavy preciptaion (Refresh required)"))
        self.prec_unit_switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.CENTER)
        self.prec_unit.set_activatable(True)
        self.use_inch_switch = Gtk.Switch()
        self.use_inch_switch.set_active(settings.is_using_inch_for_prec)
        self.use_inch_switch.connect("state-set",self._use_inch_for_precipation)
        self.prec_unit_switch_box.append(self.use_inch_switch)
        self.prec_unit.add_suffix(self.prec_unit_switch_box)
        self.prec_unit_group.add(self.prec_unit)
        
    # =============== Appearance Methods  ===============
    def _use_gradient_bg(self,widget,state):
        settings.is_using_dynamic_bg = state

    def _on_click_launch_maximixed(self,widget,state):
        settings.should_launch_maximized = state

    def _change_unit(self,widget,value):
        if settings.unit != value:
            settings.unit = value

            # Ignore refreshing weather within 5 second
            global updated_at      

            if time.time() - updated_at < 2:
                updated_at = time.time()
                self.add_toast(create_toast(_("Switching within 2 seconds is ignored!"),1))
            else:
                updated_at = time.time()
                self.add_toast(create_toast(_("Switched to - {}").format(value.capitalize()),1))
                thread = threading.Thread(target=self.application._load_weather_data,name="load_data")
                thread.start()
    
    def _use_inch_for_precipation(self,widget,state):
        settings.is_using_inch_for_prec = state
