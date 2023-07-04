import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw,Gio,GLib

from .constants import API_KEY,COUNTRY_CODES
from .units import get_measurement_type
from .backend_current_w import fetch_city_info


def AboutWindow(self, action,*args):
        dialog = Adw.AboutWindow()
        dialog.set_application_name(_("Weather"))
        dialog.set_application_icon("io.github.amit9838.weather")
        dialog.set_version("0.4.0")
        dialog.set_developer_name("Amit Chaudhary")
        dialog.set_license_type(Gtk.License(Gtk.License.GPL_3_0))
        dialog.set_comments(_("Beautiful and light weight weather app build using Gtk and python"))
        dialog.set_website("https://github.com/amit9838/weather")
        dialog.set_issue_url("https://github.com/amit9838/weather/issues")
        # dialog.add_credit_section("Contributors", ["name url"])
        dialog.set_copyright(_("Copyright © 2023 Weather Developers"))
        dialog.set_developers(["Amit Chaudhary"])
        # Translators: Please enter your credits here. (format: "Name https://example.com" or "Name <email@example.com>", no quotes)
        dialog.set_translator_credits(_("translator_credits"))
        dialog.show()

class WeatherPreferences(Adw.PreferencesWindow):
        def __init__(self, parent,  **kwargs):
                super().__init__(**kwargs)
                self.parent = parent
                self.set_transient_for(parent)
                self.set_default_size(600, 500)

                global selected_city,settings,added_cities,cities,using_personal_api,isValid_personal_api,personal_api_key,measurement_type
                settings = Gio.Settings.new("io.github.amit9838.weather")
                selected_city = int(str(settings.get_value('selected-city')))
                personal_api_key = str(settings.get_value('personal-api-key'))
                personal_api_key = personal_api_key if len(personal_api_key)==2 else personal_api_key[1:-1]
                added_cities = list(settings.get_value('added-cities'))
                use_gradient = settings.get_boolean('use-gradient-bg')
                isValid_personal_api = settings.get_boolean('isvalid-personal-api-key')
                using_personal_api = settings.get_boolean('using-personal-api-key')
                cities = [x.split(',')[0] for x in added_cities]
                measurement_type = get_measurement_type()

        #  Location Page  --------------------------------------------------
                location_page = Adw.PreferencesPage()
                location_page.set_title(_("Locations"))
                location_page.set_icon_name('mark-location-symbolic')
                self.add(location_page)

                self.location_grp = Adw.PreferencesGroup()
                self.location_grp.set_title(_("Locations"))
                location_page.add(self.location_grp)

                add_loc_btn = Gtk.Button()
                add_loc_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.CENTER,spacing=4)
                label = Gtk.Label(label=_("Add"))
                add_loc_btn_box.append(label)

                add_icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
                add_icon.set_pixel_size(14)
                add_loc_btn_box.append(add_icon)
                add_loc_btn.set_child(add_loc_btn_box)
                add_loc_btn.connect('clicked',self.add_location_dialog)
                self.location_grp.set_header_suffix(add_loc_btn)

                self.location_rows = []
                self.refresh_cities_list(added_cities)

        #  Appearance Page  --------------------------------------------------s
                appearance_page = Adw.PreferencesPage()
                appearance_page.set_title(_("Appearance"))
                appearance_page.set_icon_name('applications-graphics-symbolic')
                self.add(appearance_page)

                self.appearance_grp = Adw.PreferencesGroup()
                appearance_page.add(self.appearance_grp)

                gradient_row =  Adw.ActionRow.new()
                gradient_row.set_activatable(True)
                gradient_row.set_title(_("Use Dynamic Background"))
                gradient_row.set_subtitle(_("Background changes based on current weather conditions (Reastart required)"))

                self.g_switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.CENTER)
                self.gradient_switch = Gtk.Switch()
                self.gradient_switch.set_active(use_gradient)
                self.gradient_switch.connect("state-set",self.use_gradient_bg)
                self.g_switch_box.append(self.gradient_switch)
                gradient_row.add_suffix(self.g_switch_box)
                self.appearance_grp.add(gradient_row)

                self.measurement_group = Adw.PreferencesGroup.new()
                self.measurement_group.set_margin_top(20)
                self.measurement_group.set_title(_('Units &amp; Measurements'))
                self.appearance_grp.add(self.measurement_group)

                self.metric_unit = Adw.ActionRow.new()
                self.metric_unit.set_title(_('°C'))
                self.metric_unit.set_subtitle(_("Use METRIC system with units like celcuis, km/h, kilometer"))
                self.metric_check_btn = Gtk.CheckButton.new()
                self.metric_unit.add_prefix(self.metric_check_btn)
                self.metric_unit.set_activatable_widget(self.metric_check_btn)
                self.metric_unit.connect("activated", self.change_unit,'metric')
                self.measurement_group.add(self.metric_unit)
                
                self.imperial_unit = Adw.ActionRow.new()
                self.imperial_unit.set_title(_('°F'))
                self.imperial_unit.set_subtitle(_("Use IMPERIAL system with units like fahrenheit, mph, mile"))
                self.imperial_check_btn = Gtk.CheckButton.new()
                self.imperial_unit.add_prefix(self.imperial_check_btn)
                self.imperial_check_btn.set_group(self.metric_check_btn)
                self.imperial_unit.set_activatable_widget(self.imperial_check_btn)
                self.imperial_unit.connect("activated", self.change_unit,'imperial')
                self.measurement_group.add(self.imperial_unit)
                GLib.idle_add(self.metric_unit.activate) if measurement_type == 'metric' else  GLib.idle_add(self.imperial_unit.activate)

        #  Misc Page  --------------------------------------------------
                misc_page = Adw.PreferencesPage()
                self.add(misc_page)

                misc_page.set_title(_("Misc"))
                misc_page.set_icon_name('application-x-addon-symbolic')
                misc_grp = Adw.PreferencesGroup()
                misc_page.add(misc_grp)

                personal_api_row =  Adw.ActionRow.new()
                personal_api_row.set_activatable(True)
                personal_api_row.set_title(_("API Key"))

                api_key_entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.CENTER)
                api_key_entry = Gtk.Entry()
                api_key_entry_box.append(api_key_entry)

                set_key_btn = Gtk.Button()
                set_key_btn.set_icon_name("emblem-ok-symbolic")
                set_key_btn.set_tooltip_text(_("Save"))
                set_key_btn.set_css_classes(['circular'])
                set_key_btn.set_margin_start(5)

                api_key_entry_box.append(set_key_btn)                
                api_key_entry.set_placeholder_text(_("Enter your api-key"))
                api_key_entry.set_text(personal_api_key)
                personal_key_status = ""
                if isValid_personal_api and len(personal_api_key)>2:
                        personal_api_row.set_subtitle(_("Active"))
                        api_key_entry.set_css_classes(['success'])
                        personal_key_status = _("(Active)")
                elif len(personal_api_key)==2:
                        api_key_entry.set_text("")
                        api_key_entry.set_css_classes(['opaque'])
                else:
                        personal_key_status = _("(Invalid Key)")
                        personal_api_row.set_subtitle(_("Invalid Key"))
                        api_key_entry.set_css_classes(['error'])
                        
                api_key_entry.set_hexpand(True)
                set_key_btn.connect('clicked',self.save_api_key,api_key_entry)
                personal_api_row.add_suffix(api_key_entry_box)

                personal_api_expander_row = Adw.ExpanderRow.new()
                personal_api_expander_row.set_activatable(True)
                personal_api_expander_row.set_title(_("Use Personal API Key {0}".format(personal_key_status)))
                personal_api_expander_row.set_subtitle(_("Generate api key from openweathermap.org and paste it here (Restart Required)"))
                personal_api_expander_row.add_row(personal_api_row)
                misc_grp.add(personal_api_expander_row)

        # Location page methods ------------------------------------------
        def refresh_cities_list(self,data):
                if len(self.location_rows)>0:
                        for action_row in self.location_rows:
                                self.location_grp.remove(action_row)
                        self.location_rows.clear()

                for city in added_cities:
                        button = Gtk.Button()
                        button.set_icon_name("edit-delete-symbolic")
                        button.set_css_classes(['circular'])
                        button.set_tooltip_text(_("Remove location"))
                        button.set_has_frame(False)
                        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.CENTER)
                        if added_cities[selected_city] == city:
                                check_icon = Gtk.Image()
                                check_icon.set_from_icon_name("emblem-ok-symbolic")  # Set the icon name and size
                                check_icon.set_pixel_size(18)
                                check_icon.set_margin_end(15)
                                box.append(check_icon)
                        box.append(button)
                        location_row =  Adw.ActionRow.new()
                        location_row.set_activatable(True)
                        location_row.set_title(f"{city.split(',')[0]},{city.split(',')[1]}")
                        location_row.set_subtitle(f"{city.split(',')[-2]},{city.split(',')[-1]}")
                        location_row.add_suffix(box)
                        location_row.connect("activated", self.switch_location)
                        self.location_rows.append(location_row)
                        self.location_grp.add(location_row)
                        button.connect("clicked", self.remove_city,location_row)

        def switch_location(self,widget):
                global selected_city
                s_city = added_cities[selected_city]
                title = widget.get_title()
                if len(title.split(',')) > 2:
                        title = title.split(',')
                        title = f"{title[0]},{title[2]}"
                loc_city = f"{title},{widget.get_subtitle()}"
                if s_city != loc_city:
                        selected_city = added_cities.index(loc_city) # Update selected_city
                        settings.set_value("selected-city",GLib.Variant("i",selected_city))
                        self.refresh_cities_list(added_cities)
                        GLib.idle_add(self.parent.refresh_weather,self.parent,False)
                        loc_switch_toast = Adw.Toast.new(_("Selected - {}".format(title)))
                        loc_switch_toast.set_priority(Adw.ToastPriority(1))
                        self.add_toast(loc_switch_toast)

        def add_location_dialog(self,parent):
                self._dialog = Adw.PreferencesWindow()
                self._dialog.set_search_enabled(False)
                self._dialog.set_title(title=_('Add New Location'))
                self._dialog.set_transient_for(self)
                self._dialog.set_default_size(300, 500)

                self._dialog.page = Adw.PreferencesPage()
                self._dialog.add(self._dialog.page)

                self._dialog.group = Adw.PreferencesGroup()
                self._dialog.page.add(self._dialog.group)

                search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.CENTER, spacing = 6)
                search_box.set_hexpand(True)
                search_box.set_margin_bottom(10)
                self._dialog.group.add(search_box)

                self.search_entry = Gtk.Entry()

                self.search_entry.set_icon_from_icon_name(Gtk.EntryIconPosition(1),'edit-clear-symbolic')
                self.search_entry.set_placeholder_text(_("Search for a city"))
                self.search_entry.set_hexpand(True)
                self.search_entry.connect('icon-press',self.clear_search_box)
                search_box.append(self.search_entry)

                button = Gtk.Button(label=_("Search"))
                button.set_icon_name('system-search-symbolic')
                button.set_tooltip_text(_("Search"))
                search_box.append(button)

                self._dialog.serach_res_grp = Adw.PreferencesGroup()
                self._dialog.serach_res_grp.set_hexpand(True)
                self._dialog.group.add(self._dialog.serach_res_grp)

                button.connect("clicked", self.find_city_caller)
                self._dialog.search_results = []
                self._dialog.show()

        def clear_search_box(self,widget,pos):
                self.search_entry.set_text("")

        def find_city_caller(self,widget):
                self.find_city(widget)

        def find_city(self,widget):
                text = self.search_entry.get_text()
                city_data = fetch_city_info(API_KEY,text)
   
                if len(self._dialog.search_results)>0:
                        for action_row in self._dialog.search_results:
                                self._dialog.serach_res_grp.remove(action_row)
                        self._dialog.search_results.clear()

                if city_data:
                        for i,loc in enumerate(city_data):
                                res_row =  Adw.ActionRow.new()
                                res_row.set_activatable(True)

                                title = None
                                country = COUNTRY_CODES.get(loc.get('country'))
                                country_mod = country[0:15]+"..." if len(country) > 15 else country
                                if loc.get('state'):
                                        title = f"{loc.get('name')},{loc.get('state')},{country_mod}"
                                else:
                                        title = f"{loc.get('name')},{country_mod}"

                                res_row.set_title(title)
                                res_row.connect("activated", self.add_city)
                                res_row.set_subtitle(f"{loc['lat']},{loc['lon']}")
                                self._dialog.search_results.append(res_row)
                                self._dialog.serach_res_grp.add(res_row)
                else:
                        res_row =  Adw.ActionRow.new()
                        res_row.set_title(_("No results found !"))
                        self._dialog.search_results.append(res_row)
                        self._dialog.serach_res_grp.add(res_row)

        def add_city(self,widget):
                title = widget.get_title()
                if len(title.split(',')) > 2:
                        title = title.split(',')
                        title = f"{title[0]},{title[2]}"
                loc_city = f"{title},{widget.get_subtitle()}"
                if loc_city not in added_cities:
                        added_cities.append(loc_city)
                        settings.set_value("added-cities",GLib.Variant("as",added_cities))
                        self.refresh_cities_list(added_cities)
                        #self.parent.fetch_weather_data()
                        self.parent.refresh_main_ui()
                        loc_add_toast = Adw.Toast.new(_("Added - {0}".format(title)))
                        loc_add_toast.set_priority(Adw.ToastPriority(1))
                        self._dialog.add_toast(loc_add_toast)
                else:
                        loc_add_toast = Adw.Toast.new(_("City already added!"))
                        loc_add_toast.set_priority(Adw.ToastPriority(1))
                        self._dialog.add_toast(loc_add_toast)

        def remove_city(self,btn,widget):
                global selected_city
                city = f"{widget.get_title()},{widget.get_subtitle()}"
                s_city = added_cities[selected_city]
                added_cities.remove(city)
                try:
                        selected_city = added_cities.index(s_city)
                except:
                        selected_city = 0
                settings.set_value("selected-city",GLib.Variant("i",selected_city))
                settings.set_value("added-cities",GLib.Variant("as",added_cities))
                self.refresh_cities_list(added_cities)
                if s_city == city:  # fetch weather only if selected_city was removed
                    self.parent.refresh_weather(self.parent)
                else:
                    self.parent.refresh_main_ui()
                loc_remove_toast = Adw.Toast.new(_("Removed - {0}".format(widget.get_title())))
                loc_remove_toast.set_priority(Adw.ToastPriority(1))
                self.add_toast(loc_remove_toast)
        
        # Apprearance page methods ---------------------------
        def use_gradient_bg(self,widget,state):
                settings.set_value("use-gradient-bg",GLib.Variant("b",state))

        def change_unit(self,widget,value):
                global measurement_type
                if measurement_type != value:
                        settings.set_value("measure-type",GLib.Variant("s",value))
                        GLib.idle_add(self.parent.refresh_weather,self.parent,False)
                        measurement_type = get_measurement_type()

        # Misc page methods ----------------------------------
        def save_api_key(self,widget,target):
                settings.set_value("personal-api-key",GLib.Variant("s",target.get_text()))
                settings.set_value("using-personal-api-key",GLib.Variant("b",True))
                loc_add_toast = Adw.Toast.new(_("Saved Successfully"))
                self.add_toast(loc_add_toast)
