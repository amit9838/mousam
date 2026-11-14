import json
import threading
from datetime import datetime
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gdk, Adw, GLib, GObject, Pango  # noqa: E402

from .API_FindCity import find_city  # noqa: E402
from .CORE_GTKUtils import remove_rootwindow_drop_target, weak_connect  # noqa: E402
from .CORE_Helpers import create_toast  # noqa: E402
from .CORE_Icons import create_weather_icon, get_icon_path  # noqa: E402
from .CORE_Networking import fetch_saved_locations_weather_async  # noqa: E402
from .CORE_weatherData import weather_manager  # noqa: E402
from .configs import (  # noqa: E402
    CITY_SEARCH_DELAY_MS,
    CITY_SEARCH_MAX_RESULTS,
    CITY_SEARCH_MIN_CHARS,
    CITY_SEARCH_PAGE_SIZE,
)
from .settings import settings  # noqa: E402
from gettext import gettext as _  # noqa: E402

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
    def format_place(data: Dict, with_region: bool = False) -> str:
        """Creates the '[Region,] State, Country' line under a city's name."""
        name = data.get("name")
        # A state named like its city (Delhi, Delhi) adds nothing
        state = data.get("state") if data.get("state") != name else None
        region = data.get("region") if with_region else None
        if region in (name, state):
            region = None
        return ", ".join(filter(None, [region, state, data.get("country")]))

    @staticmethod
    def format_place_and_coords(data: Dict) -> str:
        """Creates the 'Region, State, Country · 9.93, 76.26' line of a search result."""
        place = LocationData.format_place(data, with_region=True)
        latitude, longitude = data.get("latitude"), data.get("longitude")
        coords = f"{latitude:.2f}, {longitude:.2f}" if None not in (latitude, longitude) else ""
        return " · ".join(filter(None, [place, coords]))

    @staticmethod
    def format_place_and_time(data: Dict) -> str:
        """Creates the 'State, Country · 9:14 PM' line of a saved city."""
        place = LocationData.format_place(data)
        return " · ".join(filter(None, [place, LocationData.format_local_time(data)]))

    @staticmethod
    def format_local_time(data: Dict) -> str:
        """The city's current time, or an empty string if its timezone is unknown."""
        timezone = data.get("timezone")
        if not timezone:
            return ""
        try:
            now = datetime.now(ZoneInfo(timezone))
        except (ZoneInfoNotFoundError, ValueError, OSError):
            return ""
        return now.strftime("%H:%M" if settings.is_using_24h_clock else "%-I:%M %p")

    @staticmethod
    def get_coords_key(data: Dict) -> str:
        """Returns a unique coordinate string used for selection tracking."""
        return f"{data.get('latitude')},{data.get('longitude')}"

    @staticmethod
    def saved_coords() -> set:
        """The coordinate keys of every saved city."""
        cities = [LocationData.from_storage_string(item) for item in settings.added_cities if item]
        return {LocationData.get_coords_key(city) for city in cities if city}


# --- Components ---


class RowWeather(Gtk.Stack):
    """A saved location's weather: holds its space and fades in when loaded."""

    def __init__(self, size_group: Gtk.SizeGroup):
        super().__init__(
            transition_type=Gtk.StackTransitionType.CROSSFADE,
            valign=Gtk.Align.CENTER,
        )
        self.icon = create_weather_icon("3", settings.icon_theme, 40)
        self.temperature = Gtk.Label(label="--°", xalign=1)
        self.temperature.set_css_classes(["text-lg", "font-semibold", "opacity-80"])
        size_group.add_widget(self.temperature)

        weather = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        weather.append(self.icon)
        weather.append(self.temperature)

        self.add_named(Adw.Spinner(halign=Gtk.Align.END, margin_end=8), "loading")
        self.add_named(Gtk.Box(), "empty")
        self.add_named(weather, "weather")

    def update(self, weather, is_loading: bool) -> None:
        if weather is None:
            self.set_visible_child_name("loading" if is_loading else "empty")
            return

        code = str(weather.weathercode.data) + ("n" if weather.is_day.data == 0 else "")
        self.icon.set_from_file(get_icon_path(code, settings.icon_theme))
        self.temperature.set_label(f"{round(weather.temperature_2m.data)}°")
        self.set_visible_child_name("weather")


class CitySearchDialog(Adw.PreferencesDialog):
    """Encapsulated search UI.

    A dialog is closed, not destroyed, so every handler here is connected with
    weak_connect: a strong one would keep the dialog alive after it closes.
    """

    def __init__(self, on_selection_callback):
        super().__init__(
            title=_("Add New Location"),
            content_width=350,
            content_height=500,
            search_enabled=False,
        )
        self.callback = on_selection_callback
        self.results_rows = []
        self.cities: List[Dict] = []  # Every result of the search, shown or not
        self.placeholder = None
        self._search_id = 0
        self._last_query = ""
        # Only one request runs at a time. While it does, only the newest
        # query waits, so a slow network never queues up stale searches.
        self._is_searching = False
        self._waiting_query: Optional[str] = None
        self._init_ui()
        # Drop the results of a search still running when the dialog closes
        weak_connect(self, "closed", self._on_closed)

        # Capture phase: the search field would otherwise keep Escape for itself
        key_controller = Gtk.EventControllerKey(propagation_phase=Gtk.PropagationPhase.CAPTURE)
        weak_connect(key_controller, "key-pressed", self._on_dialog_key_pressed)
        self.add_controller(key_controller)

    def _on_closed(self, _dialog) -> None:
        self._search_id += 1
        self._waiting_query = None

    def _init_ui(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup()
        self.add(page)
        page.add(group)

        # search-changed fires CITY_SEARCH_DELAY_MS after the last keypress
        self.search_entry = Gtk.SearchEntry(
            placeholder_text=_("Search cities, e.g. Kochi"),
            hexpand=True,
            search_delay=CITY_SEARCH_DELAY_MS,
        )
        weak_connect(self.search_entry, "search-changed", self._on_search_requested)
        weak_connect(self.search_entry, "activate", self._on_entry_activated)
        key_controller = Gtk.EventControllerKey(propagation_phase=Gtk.PropagationPhase.CAPTURE)
        weak_connect(key_controller, "key-pressed", self._on_entry_key_pressed)
        self.search_entry.add_controller(key_controller)

        # Sits inside the field, so results don't move while it spins
        self.spinner = Adw.Spinner(
            visible=False,
            can_target=False,
            halign=Gtk.Align.END,
            valign=Gtk.Align.CENTER,
            margin_end=32,
        )
        entry_overlay = Gtk.Overlay(child=self.search_entry, margin_bottom=10)
        entry_overlay.add_overlay(self.spinner)
        group.add(entry_overlay)

        # Results List
        self.results_group = Adw.PreferencesGroup()
        group.add(self.results_group)

        # The last row of the list; only added while there is more to show
        self.more_row = Adw.ButtonRow(
            title=_("Show More"), start_icon_name="pan-down-symbolic"
        )
        weak_connect(self.more_row, "activated", self._on_show_more)

        self._show_prompt()
        self.set_focus(self.search_entry)

    def _show_status(
        self, icon_name: str, title: str, description: str = "", child: Optional[Gtk.Widget] = None
    ) -> None:
        """Show a single status page in place of the results."""
        status = Adw.StatusPage(
            icon_name=icon_name, title=title, description=description, child=child
        )
        status.add_css_class("compact")
        status.add_css_class("search-status")
        self.placeholder = status
        self.results_group.add(status)

    def _show_prompt(self) -> None:
        self._show_status("system-search-symbolic", _("Search for Your City"))

    def _show_error(self) -> None:
        retry_btn = Gtk.Button(label=_("Retry"), halign=Gtk.Align.CENTER)
        retry_btn.add_css_class("pill")
        retry_btn.add_css_class("suggested-action")
        weak_connect(retry_btn, "clicked", self._on_retry)
        self._show_status(
            "network-offline-symbolic",
            _("Couldn't Search for Cities"),
            _("Please check your connection."),
            retry_btn,
        )

    def _clear_placeholder(self) -> None:
        if self.placeholder is not None:
            self.results_group.remove(self.placeholder)
            self.placeholder = None

    def _clear_results(self) -> None:
        self._clear_placeholder()
        for row in self.results_rows:
            self.results_group.remove(row)
        self.results_rows.clear()
        self.cities = []
        self._remove_more_row()

    def _on_retry(self, _button) -> None:
        self._last_query = ""
        self._on_search_requested(self.search_entry)

    def _first_selectable_row(self) -> Optional[Adw.ActionRow]:
        return next((row for row in self.results_rows if row.get_activatable()), None)

    def _on_entry_activated(self, entry: Gtk.SearchEntry) -> None:
        """Enter adds the top result once it is up to date, or else searches now."""
        row = self._first_selectable_row()
        is_current = entry.get_text().strip() == self._last_query
        if row is not None and is_current and not self.spinner.get_visible():
            row.activate()
        else:
            self._on_search_requested(entry)

    def _on_dialog_key_pressed(self, _controller, keyval, _keycode, _state) -> bool:
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False

    def _on_entry_key_pressed(self, _controller, keyval, _keycode, _state) -> bool:
        if keyval == Gdk.KEY_Down and self.results_rows:
            self.results_rows[0].grab_focus()
            return True
        return False

    def _on_first_row_key_pressed(self, _controller, keyval, _keycode, _state) -> bool:
        if keyval == Gdk.KEY_Up:
            self.search_entry.grab_focus()
            return True
        return False

    def _on_search_requested(self, _entry) -> None:
        query = self.search_entry.get_text().strip()
        if query == self._last_query:
            return
        self._last_query = query

        # A newer query makes the results of older ones stale
        self._search_id += 1
        self._waiting_query = None

        if len(query) < CITY_SEARCH_MIN_CHARS:
            self.spinner.set_visible(False)
            self._clear_results()
            self._show_prompt()
            return

        # The current results stay until the new ones are here, so nothing flickers
        self._clear_placeholder()
        self.spinner.set_visible(True)
        if self._is_searching:
            self._waiting_query = query
        else:
            self._start_search(query)

    def _start_search(self, query: str) -> None:
        # The request can take up to TIMEOUT seconds, so run it off the main thread
        self._is_searching = True
        threading.Thread(
            target=self._search_worker, args=(query, self._search_id), daemon=True
        ).start()

    def _search_worker(self, query: str, search_id: int) -> None:
        cities = find_city(query, CITY_SEARCH_MAX_RESULTS)
        GLib.idle_add(self._show_results, search_id, cities)

    def _show_results(self, search_id: int, cities: Optional[List[Dict]]) -> bool:
        self._is_searching = False
        if self._waiting_query is not None:
            query, self._waiting_query = self._waiting_query, None
            self._start_search(query)
            return GLib.SOURCE_REMOVE

        self.spinner.set_visible(False)
        if search_id != self._search_id:
            return GLib.SOURCE_REMOVE

        self._clear_results()
        if cities is None:
            # Pressing Enter on the same text tries again too
            self._last_query = ""
            self._show_error()
            return GLib.SOURCE_REMOVE

        if not cities:
            self._show_status(
                "system-search-symbolic",
                _("No Cities Found"),
                _("Check the spelling or try a nearby city."),
            )
            return GLib.SOURCE_REMOVE

        self.cities = cities
        self._show_next_page()
        key_controller = Gtk.EventControllerKey()
        weak_connect(key_controller, "key-pressed", self._on_first_row_key_pressed)
        self.results_rows[0].add_controller(key_controller)
        return GLib.SOURCE_REMOVE

    def _show_next_page(self) -> None:
        self._remove_more_row()
        saved_coords = LocationData.saved_coords()
        start = len(self.results_rows)
        for city in self.cities[start:start + CITY_SEARCH_PAGE_SIZE]:
            self._add_result_row(city, LocationData.get_coords_key(city) in saved_coords)
        if len(self.results_rows) < len(self.cities):
            self.results_group.add(self.more_row)

    def _remove_more_row(self) -> None:
        if self.more_row.get_parent() is not None:
            self.results_group.remove(self.more_row)

    def _on_show_more(self, _row) -> None:
        first_new = len(self.results_rows)
        self._show_next_page()
        self.results_rows[first_new].grab_focus()

    def _add_result_row(self, city: Dict, is_saved: bool) -> None:
        row = Adw.ActionRow(
            title=city.get("name") or "",
            subtitle=LocationData.format_place_and_coords(city),
            use_markup=False,
        )
        if is_saved:
            saved_icon = Gtk.Image.new_from_icon_name("object-select-symbolic")
            saved_icon.add_css_class("accent")
            saved_icon.set_tooltip_text(_("Already saved"))
            row.add_suffix(saved_icon)
        else:
            row.set_activatable(True)
            # Store the raw dict on the row object for easy retrieval
            weak_connect(row, "activated", self._on_row_selected, city)
        self.results_group.add(row)
        self.results_rows.append(row)

    def _on_row_selected(self, row, city_data):
        self.callback(city_data)
        self.close()


# --- Main Application Window ---


class WeatherLocations(Adw.PreferencesDialog):
    def __init__(self, application, **kwargs):
        super().__init__(title=_("Locations"), content_width=560, **kwargs)
        self.application = application
        remove_rootwindow_drop_target(application)
        self.cities: List[Dict] = []  # In the order of the rows
        self.location_rows: List[Adw.ActionRow] = []
        self.row_weather: Dict[str, RowWeather] = {}  # By "lat,lon"
        self._weather_loading = True
        self._closed = False
        self.connect("closed", self._on_closed)

        self._build_ui()
        self._refresh_list()
        self._load_weather()

    def _on_closed(self, _dialog) -> None:
        self._closed = True
        # A dialog isn't destroyed like a window: its widgets' handlers would
        # keep it alive, so let go of every widget that has one.
        self._clear_rows()
        self.location_grp.set_header_suffix(None)

    def _build_ui(self):
        page = Adw.PreferencesPage()
        self.location_grp = Adw.PreferencesGroup(title=_("Saved Locations"))

        add_btn = Gtk.Button(
            child=Adw.ButtonContent(icon_name="list-add-symbolic", label=_("Add Location"))
        )
        add_btn.add_css_class("flat")
        add_btn.connect("clicked", self._on_add_clicked)

        self.location_grp.set_header_suffix(add_btn)
        page.add(self.location_grp)
        self.add(page)

    def _on_add_clicked(self, _button) -> None:
        CitySearchDialog(self._handle_city_added).present(self)

    def _load_weather(self) -> None:
        """Fetch the weather of every saved city, in a single request."""
        if self.cities:
            coords = [LocationData.get_coords_key(city) for city in self.cities]
            fetch_saved_locations_weather_async(coords, self._on_weather_loaded)

    def _on_weather_loaded(self) -> bool:
        # Fill the rows in place: rebuilding them would lose focus or a drag
        if not self._closed:
            self._weather_loading = False
            for coords in self.row_weather:
                self._update_row_weather(coords)
        return GLib.SOURCE_REMOVE

    def _update_row_weather(self, coords: str) -> None:
        weather = weather_manager.saved_locations_weather.get(coords)
        self.row_weather[coords].update(weather, self._weather_loading)

    def _clear_rows(self) -> None:
        for row in self.location_rows:
            self.location_grp.remove(row)
        self.location_rows.clear()
        self.row_weather.clear()

    def _refresh_list(self) -> bool:
        """Clears and re-populates the location rows."""
        if self._closed:
            return GLib.SOURCE_REMOVE
        self._clear_rows()

        parsed = [LocationData.from_storage_string(item) for item in settings.added_cities if item]
        self.cities = [city for city in parsed if city]

        # Keeps the weather icons in one column, whatever the temperature's length
        size_group = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)
        for index, city in enumerate(self.cities):
            row = self._create_row(city, index, size_group)
            self.location_grp.add(row)
            self.location_rows.append(row)
        return GLib.SOURCE_REMOVE

    def _create_row(self, data: Dict, index: int, size_group: Gtk.SizeGroup) -> Adw.ActionRow:
        coords = LocationData.get_coords_key(data)

        # The row's own title can't have anything right after it, so the name
        # sits in a prefix and the empty title just fills the remaining space
        row = Adw.ActionRow(activatable=True)
        row.update_property([Gtk.AccessibleProperty.LABEL], [data.get("name") or ""])
        # Each prefix goes in front of the previous one
        row.add_prefix(self._create_name_column(data, settings.selected_city == coords))
        row.add_prefix(self._create_drag_handle(data))
        self.row_weather[coords] = RowWeather(size_group)
        self._update_row_weather(coords)
        row.add_suffix(self.row_weather[coords])

        # Delete Button
        del_btn = Gtk.Button(
            icon_name="user-trash-symbolic",
            has_frame=False,
            valign=Gtk.Align.CENTER,
            tooltip_text=_("Remove"),
        )
        del_btn.add_css_class("circular")
        del_btn.add_css_class("location-delete-button")
        del_btn.connect("clicked", self._handle_city_removed, data)
        row.add_suffix(del_btn)

        row.connect("activated", self._on_row_activated, data)

        drop_target = Gtk.DropTarget.new(GObject.TYPE_STRING, Gdk.DragAction.MOVE)
        drop_target.connect("drop", self._on_row_dropped, coords)
        row.add_controller(drop_target)

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_row_key_pressed, index)
        row.add_controller(key_controller)
        return row

    def _create_name_column(self, data: Dict, is_selected: bool) -> Gtk.Box:
        name = Gtk.Label(
            label=data.get("name") or "", xalign=0, ellipsize=Pango.EllipsizeMode.END
        )
        name_line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        name_line.append(name)
        if is_selected:
            indicator = Gtk.Image.new_from_icon_name("object-select-symbolic")
            indicator.add_css_class("accent")
            name_line.append(indicator)

        details = Gtk.Label(
            label=LocationData.format_place_and_time(data),
            xalign=0,
            ellipsize=Pango.EllipsizeMode.END,
        )
        details.set_css_classes(["caption", "dim-label"])

        column = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=2, valign=Gtk.Align.CENTER
        )
        column.append(name_line)
        column.append(details)
        return column

    def _create_drag_handle(self, data: Dict) -> Gtk.Image:
        handle = Gtk.Image(
            icon_name="list-drag-handle-symbolic",
            tooltip_text=_("Drag to reorder, or press Alt+Up / Alt+Down"),
        )
        handle.add_css_class("dim-label")
        drag_source = Gtk.DragSource(actions=Gdk.DragAction.MOVE)
        drag_source.connect("prepare", self._on_drag_prepare, LocationData.get_coords_key(data))
        drag_source.connect("drag-begin", self._on_drag_begin, data)
        handle.add_controller(drag_source)
        return handle

    # --- Reordering ---

    def _on_drag_prepare(self, _source, _x, _y, coords: str) -> Gdk.ContentProvider:
        return Gdk.ContentProvider.new_for_value(GObject.Value(str, coords))

    def _on_drag_begin(self, source: Gtk.DragSource, drag: Gdk.Drag, data: Dict) -> None:
        # What follows the pointer: a copy of the row in a list of its own,
        # which gives it the normal row background
        row = source.get_widget().get_ancestor(Adw.ActionRow)
        preview = Adw.ActionRow(
            title=data.get("name") or "",
            subtitle=LocationData.format_place_and_time(data),
            use_markup=False,
        )
        preview.add_prefix(Gtk.Image(icon_name="list-drag-handle-symbolic"))

        preview_list = Gtk.ListBox(
            selection_mode=Gtk.SelectionMode.NONE,
            width_request=row.get_width(),
            height_request=row.get_height(),
        )
        preview_list.add_css_class("boxed-list")
        preview_list.append(preview)

        Gtk.DragIcon.get_for_drag(drag).set_child(preview_list)
        drag.set_hotspot(20, row.get_height() // 2)

    def _on_row_dropped(self, _target, dragged_coords: str, _x, _y, target_coords: str) -> bool:
        keys = [LocationData.get_coords_key(city) for city in self.cities]
        if dragged_coords not in keys or dragged_coords == target_coords:
            return False
        self._move_city(keys.index(dragged_coords), keys.index(target_coords))
        # The row being dropped on can't be rebuilt from inside its own handler
        GLib.idle_add(self._refresh_list)
        return True

    def _on_row_key_pressed(self, _controller, keyval, _keycode, state, index: int) -> bool:
        step = {Gdk.KEY_Up: -1, Gdk.KEY_Down: 1}.get(keyval)
        if step is None or not state & Gdk.ModifierType.ALT_MASK:
            return False

        target = index + step
        if 0 <= target < len(self.cities):
            self._move_city(index, target)
            self._refresh_list()
            self.location_rows[target].grab_focus()
        return True

    def _move_city(self, from_index: int, to_index: int) -> None:
        self.cities.insert(to_index, self.cities.pop(from_index))
        settings.added_cities = [LocationData.to_storage_string(city) for city in self.cities]
        self.application.added_cities = settings.added_cities

    # --- Adding, switching and removing ---

    def _on_row_activated(self, _row, city: Dict) -> None:
        if LocationData.get_coords_key(city) != settings.selected_city:
            self._handle_city_switched(city)

    def _handle_city_added(self, city_dict: Dict):
        json_str = LocationData.to_storage_string(city_dict)

        if LocationData.get_coords_key(city_dict) in LocationData.saved_coords():
            self.add_toast(create_toast(_("Location already exists")))
            return

        # Update settings
        settings.added_cities = [*settings.added_cities, json_str]
        self.application.added_cities = settings.added_cities

        self._weather_loading = True
        self._refresh_list()
        self._load_weather()

        if len(settings.added_cities) == 1:
            self._handle_city_switched(city_dict)

    def _handle_city_switched(self, city_dict: Dict):
        settings.selected_city = LocationData.get_coords_key(city_dict)
        self._refresh_list()
        self.application._start_data_refresh()
        self.add_toast(create_toast(_("Switched to {}").format(city_dict.get("name"))))

    def _handle_city_removed(self, _btn, city_data: Dict):
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
