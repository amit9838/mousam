import threading
import time
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

from .utils import create_toast
from .backendFindCity import find_city

global updated_at
updated_at = time.time()

class WeatherLocations(Adw.PreferencesWindow):
        def __init__(self, application,  **kwargs):
                super().__init__(**kwargs)
                self.application = application
                self.set_title(_("Locations"))
                self.set_transient_for(application)
                self.set_default_size(600, 500)

                # Settings 
                global selected_city,added_cities,cities
                self.settings = application.settings
                selected_city = self.settings.get_string('selected-city')
                added_cities = self.settings.get_strv('added-cities')
                cities = [x.split(',')[0] for x in added_cities]

                # ============= Location Page =============
                location_page = Adw.PreferencesPage()
                self.add(location_page)

                self.location_grp = Adw.PreferencesGroup()
                self.location_grp.set_title(_("Locations"))
                location_page.add(self.location_grp)
                
                # Add location button with plus icon
                add_loc_btn = Gtk.Button()
                add_loc_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.CENTER,spacing=4)
                label = Gtk.Label(label=_("Add"))
                add_loc_btn_box.append(label)

                add_icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
                add_icon.set_pixel_size(14)
                add_loc_btn_box.append(add_icon)
                add_loc_btn.set_child(add_loc_btn_box)
                add_loc_btn.connect('clicked',self._add_location_dialog)
                self.location_grp.set_header_suffix(add_loc_btn)

                self.location_rows = []
                self._create_cities_list(added_cities)

      
        # =========== Location page methods =============
        def _create_cities_list(self,data):
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

                        # Add ckeck icon if city is selected 
                        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.CENTER)
                        selected_city_index = list(map(lambda city: selected_city in city,added_cities)).index(True)
                        if added_cities[selected_city_index] == city:
                                check_icon = Gtk.Image()
                                check_icon.set_from_icon_name("emblem-ok-symbolic")  # Set the icon name and size
                                check_icon.set_pixel_size(18)
                                check_icon.set_margin_end(15)
                                box.append(check_icon)
                        box.append(button)

                        # Location Row
                        location_row =  Adw.ActionRow.new()
                        location_row.set_activatable(True)
                        location_row.set_title(f"{city.split(',')[0]},{city.split(',')[1]}")
                        location_row.set_subtitle(f"{city.split(',')[-2]},{city.split(',')[-1]}")
                        location_row.add_suffix(box)
                        
                        # Location row signal
                        location_row.connect("activated", self.switch_location)
                        self.location_rows.append(location_row)
                        self.location_grp.add(location_row)

                        button.connect("clicked", self._remove_city,location_row)

        # ========== Switch Location ============
        def switch_location(self,widget):
                global selected_city
                title = widget.get_title()
                select_cord = f"{widget.get_subtitle()}"
                
                if len(select_cord.split(",")) < 2:
                        return

                # Switch if location is not already selected
                if selected_city != select_cord:
                        selected_city = select_cord
                        self.settings.set_value("selected-city",GLib.Variant("s",selected_city))
                        self._create_cities_list(added_cities)
                        global updated_at      
                        # Ignore refreshing weather within 5 second

                        if time.time() - updated_at < 2:
                                updated_at = time.time()
                                self.add_toast(create_toast(_("Switch city within 2 seconds is ignored!"),1))
                        else:
                                updated_at = time.time()
                                self.add_toast(create_toast(_("Selected - {}").format(title),1))
                                thread = threading.Thread(target=self.application._load_weather_data,name="load_data")
                                thread.start()

        # ========== Add Location ===========
        def _add_location_dialog(self,application):

                # Create dialog to search and add location
                self._dialog = Adw.PreferencesWindow()
                self._dialog.set_search_enabled(False)
                self._dialog.set_title(title=_('Add New Location'))
                self._dialog.set_transient_for(self)
                self._dialog.set_default_size(300, 500)

                self._dialog.page = Adw.PreferencesPage()
                self._dialog.add(self._dialog.page)

                self._dialog.group = Adw.PreferencesGroup()
                self._dialog.page.add(self._dialog.group)
                
                # Create search box
                search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.CENTER, spacing = 6, margin_bottom=10,)
                search_box.set_hexpand(True)
                self._dialog.group.add(search_box)

                self.search_entry = Gtk.Entry()
                self.search_entry.set_icon_from_icon_name(Gtk.EntryIconPosition(1),'edit-clear-symbolic')
                self.search_entry.set_placeholder_text(_("Search for a city"))
                self.search_entry.set_hexpand(True)
                self.search_entry.connect('icon-press',self._clear_search_box)
                search_box.append(self.search_entry)

                # Create search button 
                button = Gtk.Button(label=_("Search"))
                button.set_icon_name('system-search-symbolic')
                button.set_tooltip_text(_("Search"))
                search_box.append(button)

                self._dialog.serach_res_grp = Adw.PreferencesGroup()
                self._dialog.serach_res_grp.set_hexpand(True)
                self._dialog.group.add(self._dialog.serach_res_grp)

                button.connect("clicked", self._on_find_city_clicked)
                self._dialog.search_results = []
                self._dialog.show()

        # ============ Clear Search results ============
        def _clear_search_box(self,widget,pos):
                self.search_entry.set_text("")

        # =========== Click on find city ===========
        def _on_find_city_clicked(self,widget):
                self._find_city(widget)

        # =========== Find city ===========
        def _find_city(self,widget):
                text = self.search_entry.get_text()
                
                # Matched city from api
                city_data = find_city(text,5)

                if len(self._dialog.search_results)>0:
                        for action_row in self._dialog.search_results:
                                self._dialog.serach_res_grp.remove(action_row)
                        self._dialog.search_results.clear()
                
                # Plot search results if found
                if city_data:
                        for loc in city_data:
                                res_row =  Adw.ActionRow.new()
                                res_row.set_activatable(True)
                                title_arr = [loc.name,loc.state,loc.country]
                                title_arr = [x for x in title_arr if x is not None]
                                title = ",".join(title_arr)
                                res_row.set_title(title)

                                # Skip plotting the location in the search results if it has invalid cords
                                if loc.latitude is None or loc.longitude is  None:
                                        continue
                                if loc.latitude == "" or loc.longitude == "":
                                        continue

                                res_row.set_subtitle(f"{loc.latitude},{loc.longitude}")
                                res_row.connect("activated", self._add_city)
                                self._dialog.search_results.append(res_row)
                                self._dialog.serach_res_grp.add(res_row)
                
                # If no search result is found
                else:
                        res_row =  Adw.ActionRow.new()
                        res_row.set_title(_("No results found !"))
                        self._dialog.search_results.append(res_row)
                        self._dialog.serach_res_grp.add(res_row)


        # =========== Add City on selection ===========
        def _add_city(self,widget):
                # get title,subtitle from selected item in search result
                title = widget.get_title()
                title_arr = title.split(',')
                modified_title = title_arr[0]
                if len(title_arr)>2:
                        modified_title = f"{title_arr[0]},{title_arr[2]}"
                elif len(title_arr)>1:
                        modified_title = f"{title_arr[0]},{title_arr[1]}"

                loc_city = f"{modified_title},{widget.get_subtitle()}"

                # Add city to db if it is not already added 
                if loc_city not in added_cities:
                    added_cities.append(loc_city)
                    self.settings.set_value("added-cities",GLib.Variant("as",added_cities))
                    self._create_cities_list(added_cities)
                #     self.application.refresh_main_ui()
                    self._dialog.add_toast(create_toast(_("Added - {0}").format(title),1))
                else:
                    self._dialog.add_toast(create_toast(_("Location already added!"),1))

        # ========== Remove City ===========
        def _remove_city(self,btn,widget):
                global selected_city
                city = f"{widget.get_title()},{widget.get_subtitle()}"

                # Don't delete city if only one item is present in the list
                if len(added_cities)==1:
                        self.add_toast(create_toast(_("Add more locations to delete!"),1))
                        return
                
                selected_city_index = list(map(lambda x: selected_city in x, added_cities)).index(True)
                s_city = added_cities[selected_city_index]
                added_cities.remove(city)

                # If selected city is removed then select first city in the list
                if widget.get_subtitle() == selected_city:
                        first_city = added_cities[0].split(",")
                        selected_city = f"{first_city[-2]},{first_city[-1]}"
                        self.settings.set_value("selected-city",GLib.Variant("s",selected_city))
                        thread = threading.Thread(target=self.application._load_weather_data,name="load_data")
                        thread.start()

                                
                self.settings.set_value("added-cities",GLib.Variant("as",added_cities))
                self._create_cities_list(added_cities)
                if s_city == city:  # fetch weather only if selected_city was removed
                    pass
                #     self.application.refresh_weather(self.application)
                else:
                        pass
                #     self.application.refresh_main_ui()
                self.add_toast(create_toast(_("Deleted - {0}".format(widget.get_title())),1))
