import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw,Gio,GLib

from .utils import create_toast
from .backendFindCity import find_city

class WeatherLocations(Adw.PreferencesWindow):
        def __init__(self, application,  **kwargs):
                super().__init__(**kwargs)
                self.application = application
                self.set_title(_("Locations"))
                self.set_transient_for(application)
                self.set_default_size(600, 500)

                global selected_city,added_cities,cities
                self.settings = application.settings
                selected_city = int(str(self.settings.get_value('selected-city')))
                added_cities = list(self.settings.get_strv('added-cities'))
                cities = [x.split(',')[0] for x in added_cities]

                #  Location Page  --------------------------------------------------
                location_page = Adw.PreferencesPage()
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
                add_loc_btn.connect('clicked',self._add_location_dialog)
                self.location_grp.set_header_suffix(add_loc_btn)

                self.location_rows = []
                self._create_cities_list(added_cities)

      
        # Location page methods ------------------------------------------
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
                        button.connect("clicked", self._remove_city,location_row)

        def switch_location(self,widget):
                global selected_city
                s_city = added_cities[selected_city].split(',')
                already_selected_cord = f"{s_city[-2]},{s_city[-1]}" #get lat,lon of the selected city
                title = widget.get_title()
                select_cord = f"{widget.get_subtitle()}"
                if already_selected_cord != select_cord:
                        selected_index = list(map(lambda city: select_cord in city,added_cities)).index(True)
                        selected_city = selected_index
                        self.settings.set_value("selected-city",GLib.Variant("i",selected_index))
                        self._create_cities_list(added_cities)
                        # GLib.idle_add(self.application.refresh_weather,self.application,False)
                        self.add_toast(create_toast(_("Selected - {}").format(title),1))

        def _add_location_dialog(self,application):
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
                self.search_entry.connect('icon-press',self._clear_search_box)
                search_box.append(self.search_entry)

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

        def _clear_search_box(self,widget,pos):
                self.search_entry.set_text("")

        def _on_find_city_clicked(self,widget):
                self._find_city(widget)

        def _find_city(self,widget):
                text = self.search_entry.get_text()
                city_data = find_city(text,5)

                if len(self._dialog.search_results)>0:
                        for action_row in self._dialog.search_results:
                                self._dialog.serach_res_grp.remove(action_row)
                        self._dialog.search_results.clear()

                if city_data:
                        for i,loc in enumerate(city_data):
                                res_row =  Adw.ActionRow.new()
                                res_row.set_activatable(True)
                                title_arr = [loc.name,loc.state,loc.country]
                                title_arr = [x for x in title_arr if x is not None]
                                title = ",".join(title_arr)
                                
                                res_row.set_title(title)
                                res_row.connect("activated", self._add_city)
                                res_row.set_subtitle(f"{loc.latitude},{loc.longitude}")
                                self._dialog.search_results.append(res_row)
                                self._dialog.serach_res_grp.add(res_row)
                else:
                        res_row =  Adw.ActionRow.new()
                        res_row.set_title(_("No results found !"))
                        self._dialog.search_results.append(res_row)
                        self._dialog.serach_res_grp.add(res_row)

        def _add_city(self,widget):
                title = widget.get_title()
                title_arr = title.split(',')
                modified_title = title_arr[0]
                if len(title_arr)>2:
                        modified_title = f"{title_arr[0]},{title_arr[2]}"
                elif len(title_arr)>1:
                        modified_title = f"{title_arr[0]},{title_arr[1]}"

                loc_city = f"{modified_title},{widget.get_subtitle()}"
                if loc_city not in added_cities:
                    added_cities.append(loc_city)
                    self.settings.set_value("added-cities",GLib.Variant("as",added_cities))
                    self._create_cities_list(added_cities)
                #     self.application.refresh_main_ui()
                    self._dialog.add_toast(create_toast(_("Added - {0}").format(title),1))
                else:
                    self._dialog.add_toast(create_toast(_("City already added!"),1))

        def _remove_city(self,btn,widget):
                global selected_city
                city = f"{widget.get_title()},{widget.get_subtitle()}"
                s_city = added_cities[selected_city]
                added_cities.remove(city)
                try:
                        selected_city = added_cities.index(s_city)
                except:
                        selected_city = 0
                self.settings.set_value("selected-city",GLib.Variant("i",selected_city))
                self.settings.set_value("added-cities",GLib.Variant("as",added_cities))
                self._create_cities_list(added_cities)
                if s_city == city:  # fetch weather only if selected_city was removed
                    self.application.refresh_weather(self.application)
                else:
                        pass
                #     self.application.refresh_main_ui()
                self.add_toast(create_toast(_("Removed - {0}".format(widget.get_title())),1))
