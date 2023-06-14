import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw,Gio,GLib

from .constants import API_KEY
from .backend_current_w import fetch_city_info

def AboutWindow(self, action,*args):
        dialog = Adw.AboutWindow()
        dialog.set_application_name("Weather")
        dialog.set_application_icon("io.github.amit9838.weather")
        dialog.set_version("1.0")
        dialog.set_developer_name("Amit Chaudhary")
        dialog.set_license_type(Gtk.License(Gtk.License.GPL_3_0))
        dialog.set_comments(_("Beautiful and light weight weather app build using Gtk and python."))
        dialog.set_website("https://github.com/amit9838/weather")
        dialog.set_issue_url("https://github.com/amit9838/weather/issues")
        # dialog.add_credit_section("Contributors", ["name url"])
        # dialog.set_translator_credits("Name1 url")
        dialog.set_copyright("© 2023 developer")
        dialog.set_developers(["Amit Chaudhary"])
        dialog.show()

class WeatherPreferences(Adw.PreferencesWindow):
        def __init__(self, parent,  **kwargs):
                super().__init__(**kwargs)
                self.parent = parent
                self.set_transient_for(parent)
                self.set_default_size(600, 500)

                global selected_city,settings,added_cities,cities
                settings = Gio.Settings.new("io.github.amit9838.weather")
                selected_city = int(str(settings.get_value('selected-city')))
                added_cities = list(settings.get_value('added-cities'))
                use_gradient = settings.get_boolean('use-gradient-bg')
                cities = [x.split(',')[0] for x in added_cities]

                appearance_page = Adw.PreferencesPage();
                appearance_page.set_title(_("Appearance"))
                appearance_page.set_icon_name('applications-graphics-symbolic')
                self.add(appearance_page);


                self.appearance_grp = Adw.PreferencesGroup();
                appearance_page.add(self.appearance_grp);

                gradient_row =  Adw.ActionRow.new()
                gradient_row.set_activatable(True)
                gradient_row.set_title(_("Use Dynamic Background"))
                gradient_row.set_subtitle(_("Background Changes based on weather conditions (Reastart required)"))

                self.g_switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.CENTER)
                self.gradient_switch = Gtk.Switch()
                self.gradient_switch.set_active(use_gradient)
                self.gradient_switch.connect("state-set",self.use_gradient_bg)
                self.g_switch_box.append(self.gradient_switch)
                gradient_row.add_suffix(self.g_switch_box)
                self.appearance_grp.add(gradient_row)

                location_page = Adw.PreferencesPage()
                location_page.set_title(_("Locations"))
                location_page.set_icon_name('mark-location-symbolic')

                self.add(location_page);
                self.location_grp = Adw.PreferencesGroup()
                self.location_grp.set_title(_("Locations"))
                location_page.add(self.location_grp);

                add_loc_btn = Gtk.Button()
                add_loc_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.CENTER,spacing=4)
                # Create a label
                label = Gtk.Label(label=_("Add"))
                add_loc_btn_box.append(label)
                # Create an icon
                add_icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
                add_icon.set_pixel_size(14)
                add_loc_btn_box.append(add_icon)
                add_loc_btn.set_child(add_loc_btn_box)
                add_loc_btn.connect('clicked',self.add_location_dialog)

                self.location_grp.set_header_suffix(add_loc_btn)

                self.location_rows = []
                self.refresh_cities_list(added_cities)


        def refresh_cities_list(self,data):
                if len(self.location_rows)>0:
                        for action_row in self.location_rows:
                                self.location_grp.remove(action_row)

                for city in added_cities:
                        button = Gtk.Button()
                        button.set_icon_name("edit-delete-symbolic")
                        button.set_tooltip_text(_("Remove location"))
                        button.set_has_frame(False)
                        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.CENTER)
                        if added_cities[selected_city] == city:
                                check_icon = Gtk.Image()
                                check_icon.set_from_icon_name("emblem-ok-symbolic")  # Set the icon name and size
                                # icon.set_hexpand(True)
                                check_icon.set_pixel_size(18)
                                check_icon.set_margin_end(15)
                                box.append(check_icon)
                        box.append(button)

                        location_row =  Adw.ActionRow.new()
                        location_row.set_activatable(True)
                        location_row.set_title(f"{city.split(',')[0]},{city.split(',')[1]}")
                        location_row.set_subtitle(f"{city.split(',')[-2]},{city.split(',')[-1]}")
                        location_row.add_suffix(box)
                        self.location_rows.append(location_row)
                        self.location_grp.add(location_row);
                        button.connect("clicked", self.remove_city,location_row)

        def add_location_dialog(self,parent):
                self._dialog = Adw.PreferencesWindow()
                self._dialog.set_search_enabled(False)
                self._dialog.set_title(title=_('Add new location'))
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
                self.search_entry.set_placeholder_text(_("Search for a city"))
                self.search_entry.set_hexpand(True)
                search_box.append(self.search_entry)

                button = Gtk.Button(label=_("Search"))
                search_box.append(button)

                self._dialog.serach_res_grp = Adw.PreferencesGroup()
                self._dialog.serach_res_grp.set_hexpand(True)
                self._dialog.group.add(self._dialog.serach_res_grp)

                button.connect("clicked", self.find_city)
                self._dialog.search_results = []

                self._dialog.show()

        def find_city(self,widget):
                text = self.search_entry.get_text()
                city_data = fetch_city_info(API_KEY,text)
   
                if len(self._dialog.search_results)>0:
                        for action_row in self._dialog.search_results:
                                self._dialog.serach_res_grp.remove(action_row)

                for i,loc in enumerate(city_data):
                        res_row =  Adw.ActionRow.new()
                        res_row.set_activatable(True)
                        title = f"{loc['name']},{loc['country']}"
                        res_row.set_title(title)
                        res_row.connect("activated", self.add_city)
                        res_row.set_subtitle(f"{loc['lat']},{loc['lon']}")
                        self._dialog.search_results.append(res_row)
                        self._dialog.serach_res_grp.add(res_row);


        def add_city(self,widget):
                loc_city = f"{widget.get_title()},{widget.get_subtitle()}"
                if loc_city not in added_cities:
                        added_cities.append(loc_city)
                        settings.set_value("added-cities",GLib.Variant("as",added_cities))
                        self.refresh_cities_list(added_cities)
                        self.parent.fetch_weather_data()

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
                self.parent.fetch_weather_data()


        def use_gradient_bg(self,widget,state):
                settings.set_value("use-gradient-bg",GLib.Variant("b",state))


# data = [{'name': 'Delhi',
#          'local_names': {'ko': '델리', 'he': 'דלהי', 'fa': 'دهلی', 'pa': 'ਦਿੱਲੀ', 'kn': 'ದೆಹಲಿ', 'el': 'Δελχί', 'en': 'Delhi', 'ta': 'தில்லி', 'hi': 'दिल्ली', 'th': 'เดลี', 'bn': 'দিল্লি', 'fr': 'Delhi', 'ja': 'デリー', 'ru': 'Дели', 'ur': 'دہلی', 'uk': 'Делі', 'de': 'Delhi', 'cs': 'Dillí', 'oc': 'Delhi', 'eo': 'Delhio', 'es': 'Delhi', 'ms': 'Delhi', 'ml': 'ഡെൽഹി', 'pt': 'Deli', 'te': 'ఢిల్లీ', 'ku': 'Delhî', 'ne': 'दिल्ली', 'ar': 'دلهي', 'my': 'ဒေလီမြို့', 'zh': '德里', 'lv': 'Deli'},
#          'lat': 28.6517178, 'lon': 77.2219388, 'country': 'IN', 'state': 'Delhi'},

#          {'name': 'Del', 'lat': 7.8280947, 'lon': 35.8220579, 'country': 'ET'},
#          {'name': 'Del', 'lat': 45.7692659, 'lon': 7.5569758, 'country': 'IT', 'state': 'Aosta Valley'},
#          {'name': 'Del', 'lat': 43.1167167, 'lon': -8.4662065, 'country': 'ES', 'state': 'Galicia'},
#          {'name': 'Del', 'lat': 46.6390735, 'lon': 9.567217, 'country': 'CH', 'state': 'Grisons'}]
