import json
import time
from typing import List, Dict, Optional
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from .utils import create_toast
from .backendFindCity import find_city
from .config import settings
from gettext import gettext as _, pgettext as C_

# --- Data Layer Utilities ---


class LocationData:
    """Helper to handle serialization and formatting of city data."""

    @staticmethod
    def to_storage_string(city_dict: Dict) -> str:
        """Converts a city dictionary to a JSON string for settings."""
        return json.dumps(city_dict)

    @staticmethod
    def from_storage_string(json_str: str) -> Dict:
        """Converts a JSON string from settings back to a dictionary."""
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return {}

    @staticmethod
    def format_display_name(data: Dict) -> str:
        """Creates a clean 'City, State, Country' string."""
        parts = [data.get("name"), data.get("state"), data.get("country")]
        return ", ".join(filter(None, parts))

    @staticmethod
    def get_coords_key(data: Dict) -> str:
        """Returns a unique coordinate string used for selection tracking."""
        return f"{data.get('latitude')},{data.get('longitude')}"


# --- Components ---


class CitySearchDialog(Adw.PreferencesWindow):
    """Encapsulated search UI."""

    def __init__(self, parent, on_selection_callback):
        super().__init__(transient_for=parent, default_width=350, default_height=500)
        self.set_title(_("Add New Location"))
        self.callback = on_selection_callback
        self.results_rows = []
        self._init_ui()

    def _init_ui(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup()
        self.add(page)
        page.add(group)

        # Search Entry Box
        header_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6, margin_bottom=10
        )
        self.search_entry = Gtk.Entry(
            placeholder_text=_("Search for a city"), hexpand=True
        )
        self.search_entry.connect("activate", self._perform_search)

        search_btn = Gtk.Button(icon_name="system-search-symbolic")
        search_btn.connect("clicked", self._perform_search)

        header_box.append(self.search_entry)
        header_box.append(search_btn)
        group.add(header_box)

        # Results List
        self.results_group = Adw.PreferencesGroup()
        group.add(self.results_group)
        self._set_placeholder(_("Search for your city..."))

    def _set_placeholder(self, text):
        self.placeholder = Gtk.Label(label=text, margin_top=40)
        self.placeholder.add_css_class("dim-label")
        self.results_group.add(self.placeholder)

    def _perform_search(self, _widget):
        query = self.search_entry.get_text().strip()
        if not query:
            return

        # Logic to clear results
        if hasattr(self, "placeholder"):
            self.results_group.remove(self.placeholder)
        for row in self.results_rows:
            self.results_group.remove(row)
        self.results_rows.clear()

        cities = find_city(query, 5)  # Returns list of dicts

        if not cities:
            self._set_placeholder(_("No cities found."))
            return

        for city in cities:
            display = LocationData.format_display_name(city)
            row = Adw.ActionRow(
                title=display,
                subtitle=f"{city.get('latitude')}, {city.get('longitude')}",
            )
            row.set_activatable(True)
            # Store the raw dict on the row object for easy retrieval
            row.connect("activated", self._on_row_selected, city)
            self.results_group.add(row)
            self.results_rows.append(row)

    def _on_row_selected(self, row, city_data):
        self.callback(city_data)
        self.destroy()


# --- Main Application Window ---


class WeatherLocations(Adw.PreferencesWindow):
    def __init__(self, application, **kwargs):
        super().__init__(**kwargs)
        self.application = application
        self.last_switch_time = 0
        self.row_map = {}  # Track rows to prevent full UI rebuilds

        self.set_title(_("Locations"))
        self.set_transient_for(application)
        self.set_default_size(550, 450)

        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        page = Adw.PreferencesPage()
        self.location_grp = Adw.PreferencesGroup(title=_("Saved Locations"))

        add_btn = Gtk.Button(label=_("Add"), icon_name="list-add-symbolic")
        add_btn.connect(
            "clicked",
            lambda _: CitySearchDialog(self, self._handle_city_added).present(),
        )

        self.location_grp.set_header_suffix(add_btn)
        page.add(self.location_grp)
        self.add(page)

    def _refresh_list(self):
        """Clears and re-populates the location rows."""
        # Senior move: Clear rows efficiently
        while child := self.location_grp.get_row(0):
            if isinstance(child, Adw.ActionRow):
                self.location_grp.remove(child)
            else:
                break  # Keep the header suffix if it's there

        for city_str in settings.added_cities:
            if not city_str:
                continue

            city_data = LocationData.from_storage_string(city_str)
            row = self._create_row(city_data)
            self.location_grp.add(row)

    def _create_row(self, data: Dict) -> Adw.ActionRow:
        display_name = LocationData.format_display_name(data)
        coords = LocationData.get_coords_key(data)

        row = Adw.ActionRow(title=display_name, subtitle=coords, activatable=True)

        # Selection Indicator
        suffix_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        if settings.selected_city == coords:
            indicator = Gtk.Image.new_from_icon_name("object-select-symbolic")
            indicator.add_css_class("accent")
            suffix_box.append(indicator)

        # Delete Button
        del_btn = Gtk.Button(icon_name="user-trash-symbolic", has_frame=False)
        del_btn.add_css_class("circular")
        del_btn.connect("clicked", self._handle_city_removed, data)

        suffix_box.append(del_btn)
        row.add_suffix(suffix_box)
        row.connect("activated", self._handle_city_switched, data)

        return row

    def _handle_city_added(self, city_dict: Dict):
        json_str = LocationData.to_storage_string(city_dict)

        if json_str in settings.added_cities:
            self.add_toast(Adw.Toast(title=_("Location already exists")))
            return


        # Update settings
        settings.added_cities = [*settings.added_cities, json_str]
        self.application.added_cities = settings.added_cities

        self._refresh_list()

        if len(settings.added_cities) == 1:
            self._handle_city_switched(None, city_dict)

    def _handle_city_switched(self, _row, city_dict: Dict):
        new_coords = LocationData.get_coords_key(city_dict)

        if settings.selected_city == new_coords and not len(settings.added_cities):
            return

        # Rate limiting switch
        now = time.time()
        if now - self.last_switch_time < 2:
            self.add_toast(Adw.Toast(title=_("Please wait before switching again")))
            return

        settings.selected_city = new_coords
        self.last_switch_time = now

        self._refresh_list()
        self.application._start_data_refresh()
        self.add_toast(Adw.Toast(title=_("Selected {}").format(city_dict.get("name"))))

    def _handle_city_removed(self, _btn, city_data: str):
        coords_to_remove = LocationData.get_coords_key(city_data)
        json_str = LocationData.to_storage_string(city_data)
        new_list = [item for item in settings.added_cities if item != json_str]
        settings.added_cities = new_list
        self.application.added_cities = settings.added_cities

        if len(self.application.added_cities) == 0:
            self.application._start_data_refresh()

        # Reset selection if we deleted the active city
        if settings.selected_city == coords_to_remove and new_list:
            first_city = LocationData.from_storage_string(new_list[0])
            settings.selected_city = LocationData.get_coords_key(first_city)

            self.application._start_data_refresh()

        self._refresh_list()
