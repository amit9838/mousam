import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw,Gio,GLib

from .constants import API_KEY,COUNTRY_CODES
from .units import get_measurement_type
from .utils import create_toast

class WeatherPreferences(Adw.PreferencesWindow):
        def __init__(self, parent,  **kwargs):
                super().__init__(**kwargs)
                self.parent = parent
                self.set_transient_for(parent)
                self.set_default_size(600, 500)

                global selected_city,settings,added_cities,cities,use_personal_api,isValid_personal_api,personal_api_key,measurement_type
                settings = Gio.Settings.new("io.github.amit9838.weather")
                selected_city = settings.get_string('selected-city')
                personal_api_key = settings.get_string('personal-api-key')
                added_cities = list(settings.get_value('added-cities'))
                use_gradient = settings.get_boolean('use-gradient-bg')
                isValid_personal_api = settings.get_boolean('isvalid-personal-api-key')
                use_personal_api = settings.get_boolean('use-personal-api-key')
                cities = [x.split(',')[0] for x in added_cities]
                measurement_type = get_measurement_type()

      
        #  Appearance Page  --------------------------------------------------s
                appearance_page = Adw.PreferencesPage()
                appearance_page.set_title(_("Appearance"))
                appearance_page.set_icon_name('applications-graphics-symbolic')
                self.add(appearance_page)

                self.appearance_grp = Adw.PreferencesGroup()
                appearance_page.add(self.appearance_grp)

                gradient_row =  Adw.ActionRow.new()
                gradient_row.set_activatable(True)
                gradient_row.set_title(_("Dynamic Background"))
                gradient_row.set_subtitle(_("Background changes based on current weather condition (Restart required)"))

                self.g_switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.CENTER)
                self.gradient_switch = Gtk.Switch()
                self.gradient_switch.set_active(use_gradient)
                self.gradient_switch.connect("state-set",self._use_gradient_bg)
                self.g_switch_box.append(self.gradient_switch)
                gradient_row.add_suffix(self.g_switch_box)
                self.appearance_grp.add(gradient_row)

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
                self.imperial_unit.set_subtitle(_("IMPERIAL system with units like fahrenheit, mph, mile"))
                self.imperial_check_btn = Gtk.CheckButton.new()
                self.imperial_unit.add_prefix(self.imperial_check_btn)
                self.imperial_check_btn.set_group(self.metric_check_btn)
                self.imperial_unit.set_activatable_widget(self.imperial_check_btn)
                self.imperial_unit.connect("activated", self._change_unit,'imperial')
                self.measurement_group.add(self.imperial_unit)
                GLib.idle_add(self.metric_unit.activate) if measurement_type == 'metric' else  GLib.idle_add(self.imperial_unit.activate)

        #  Misc Page  --------------------------------------------------
                misc_page = Adw.PreferencesPage()
                misc_page.set_title(_("Misc"))
                misc_page.set_icon_name('application-x-addon-symbolic')
                misc_grp = Adw.PreferencesGroup()
                misc_page.add(misc_grp)
                self.add(misc_page)
                
                use_personal_key_switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.CENTER)
                use_personal_key_switch = Gtk.Switch.new()
                use_personal_key_switch.set_active(use_personal_api)
                use_personal_key_switch_box.append(use_personal_key_switch)

                personal_api_expander_row = Adw.ExpanderRow.new()
                personal_api_expander_row.set_title(_("Personal API Key"))
                personal_api_expander_row.set_subtitle(_("Use your personal api key from openweathermap.org (Restart Required)"))
                misc_grp.add(personal_api_expander_row)
                personal_api_expander_row.add_action(use_personal_key_switch_box)
                use_personal_key_switch.connect('state-set',self._on_use_personal_api_key_toggled,personal_api_expander_row)

                personal_api_row =  Adw.ActionRow.new()
                personal_api_row.set_activatable(True)
                personal_api_row.set_title(_("API Key"))
                personal_api_expander_row.connect('direction-changed',self._on_use_personal_api_key_toggled)

                api_key_entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.CENTER)
                api_key_entry = Gtk.Entry()
                api_key_entry_box.append(api_key_entry)

                save_api_key_btn = Gtk.Button()
                save_api_key_btn.set_icon_name("emblem-ok-symbolic")
                save_api_key_btn.set_tooltip_text(_("Save"))
                save_api_key_btn.set_css_classes(['circular'])
                save_api_key_btn.set_margin_start(5)

                api_key_entry_box.append(save_api_key_btn)                
                api_key_entry.set_placeholder_text(_("Enter your api-key"))
                api_key_entry.set_text(personal_api_key)
                if use_personal_api and isValid_personal_api and len(personal_api_key)>2:
                        personal_api_expander_row.set_expanded(True)
                        personal_api_row.set_subtitle(_("Active"))
                        api_key_entry.set_css_classes(['success'])
                elif len(personal_api_key)==0 or use_personal_api==False:
                        api_key_entry.set_css_classes(['opaque'])
                else:
                        personal_api_row.set_subtitle(_("Invalid Key"))
                        api_key_entry.set_css_classes(['error'])
                        
                api_key_entry.set_hexpand(True)
                save_api_key_btn.connect('clicked',self._save_api_key,api_key_entry)
                personal_api_row.add_suffix(api_key_entry_box)

                personal_api_expander_row.add_row(personal_api_row)

        # Apprearance page methods ---------------------------
        def _use_gradient_bg(self,widget,state):
                settings.set_value("use-gradient-bg",GLib.Variant("b",state))

        def _change_unit(self,widget,value):
                global measurement_type
                if measurement_type != value:
                        settings.set_value("measure-type",GLib.Variant("s",value))
                        GLib.idle_add(self.parent.refresh_weather,self.parent,False)
                        measurement_type = get_measurement_type()

        # Misc page methods ----------------------------------
        def _on_use_personal_api_key_toggled(self,widget,state,target):
                if state==True:
                        target.set_enable_expansion(True)
                        settings.set_value("use-personal-api-key",GLib.Variant("b",True))
                else:
                        target.set_enable_expansion(False)
                        settings.set_value("use-personal-api-key",GLib.Variant("b",False))

        def _save_api_key(self,widget,target):
                settings.set_value("personal-api-key",GLib.Variant("s",target.get_text()))
                settings.set_value("use-personal-api-key",GLib.Variant("b",True))
                self.add_toast(create_toast(_("Saved Successfully"),1))
