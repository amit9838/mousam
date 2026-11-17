from typing import Callable

import gi
from gi.repository import Adw, Gtk
from gettext import gettext as _


from ...services.settings import settings
from ..gtk_utils import create_toast
from ...config import AUTO_REFRESH_OPTIONS
from ...core.log import log_manager

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")


class WeatherPreferences(Adw.PreferencesDialog):
    """Preferences dialog, shown over the main window with present(window)."""

    def __init__(self, window: Adw.ApplicationWindow, **kwargs):
        super().__init__(**kwargs)
        self.window = window
        self.set_title(_("Preferences"))

        self._build_ui()
        self._bind_settings_to_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        """Create all preference pages and groups."""
        general_page = Adw.PreferencesPage()
        general_page.set_title(_("General"))
        general_page.set_icon_name("preferences-system-symbolic")
        self.add(general_page)

        general_page.add(self._build_appearance_group())
        general_page.add(self._build_overview_group())
        general_page.add(self._build_general_group())

        advanced_page = Adw.PreferencesPage()
        advanced_page.set_title(_("Advanced"))
        advanced_page.set_icon_name("applications-engineering-symbolic")
        self.add(advanced_page)

        advanced_page.add(self._build_debug_group())
        advanced_page.add(self._build_reset_group())

    def _build_general_group(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(title=_("General"))

        self._unit_btn_celsius, self._unit_btn_fahrenheit = self._add_toggle_row(
            group,
            _("Units"),
            _("Metric (°C, km/h) or Imperial (°F, mph)"),
            "preferences-desktop-locale-symbolic",
            (_("Metric"), _("Imperial")),
            self._on_unit_toggled,
            ("metric", "imperial"),
        )
        self._precip_btn_mm, self._precip_btn_inch = self._add_toggle_row(
            group,
            _("Precipitation"),
            _("Unit of the hourly precipitation graph"),
            "weather-showers-symbolic",
            # Translators: short unit names for millimetres and inches
            (_("mm"), _("in")),
            self._on_precip_unit_toggled,
            (False, True),
        )
        self._time_btn_24h, self._time_btn_12h = self._add_toggle_row(
            group,
            _("Time Format"),
            None,
            "preferences-system-time-symbolic",
            (_("24-hour"), _("AM/PM")),
            self._on_24h_clock_toggled,
            (True, False),
        )
        self._background_switch = Adw.SwitchRow(
            title=_("Run in Background"),
            subtitle=_("Keep Mousam running when its window is closed"),
        )
        self._add_prefix_icon(self._background_switch, "application-x-executable-symbolic")
        self._background_switch.set_active(settings.run_in_background)
        self._background_switch.connect("notify::active", self._on_run_in_background_toggled)
        group.add(self._background_switch)
        return group

    def _build_appearance_group(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(title=_("Appearance"))

        self._dynamic_bg_switch = Adw.SwitchRow(
            title=_("Dynamic Background"),
            subtitle=_("Change the background to match the current weather"),
        )
        self._add_prefix_icon(self._dynamic_bg_switch, "preferences-desktop-wallpaper-symbolic")
        self._dynamic_bg_switch.set_active(settings.is_using_dynamic_bg)
        self._dynamic_bg_switch.connect("notify::active", self._on_dynamic_bg_toggled)
        group.add(self._dynamic_bg_switch)

        self._icon_theme_btn_default, self._icon_theme_btn_material = self._add_toggle_row(
            group,
            _("Weather Icons"),
            None,
            "weather-few-clouds-symbolic",
            (_("Default"), _("Material")),
            self._on_icon_theme_toggled,
            ("default", "material"),
        )
        return group

    def _build_overview_group(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(title=_("Weather Overview"))

        self._overview_switch = Adw.SwitchRow(
            title=_("Show Overview"),
            subtitle=_("A short summary of the coming hours"),
        )
        self._add_prefix_icon(self._overview_switch, "dialog-information-symbolic")
        self._overview_switch.set_active(settings.show_overview)
        self._overview_switch.connect("notify::active", self._on_overview_toggled)
        group.add(self._overview_switch)

        self._notification_switch = Adw.SwitchRow(
            title=_("Notifications"),
            subtitle=_("Send the overview as a notification while the window is minimized or in compact mode"),
        )
        self._add_prefix_icon(self._notification_switch, "preferences-system-notifications-symbolic")
        self._notification_switch.set_active(settings.show_notifications)
        self._notification_switch.connect("notify::active", self._on_notifications_toggled)
        group.add(self._notification_switch)

        self._add_auto_refresh_row(group)
        return group

    def _build_debug_group(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(title=_("Logging and Debugging"))

        self._debug_switch = Adw.SwitchRow(
            title=_("Debug Mode"),
            subtitle=_("Enable verbose logging and console output"),
        )
        self._add_prefix_icon(self._debug_switch, "system-run-symbolic")
        self._debug_switch.set_active(settings.debug_mode)
        self._debug_switch.connect("notify::active", self._on_debug_mode_toggled)
        group.add(self._debug_switch)

        open_logs_row = Adw.ActionRow(
            title=_("Open Logs Folder"),
            activatable=True,
        )
        self._add_prefix_icon(open_logs_row, "text-x-generic-symbolic")
        open_logs_row.add_suffix(Gtk.Image(icon_name="folder-open-symbolic"))
        open_logs_row.connect("activated", self._on_open_logs_clicked)
        group.add(open_logs_row)

        clear_logs_row = Adw.ActionRow(
            title=_("Clear Log File"),
            subtitle=_("Delete all contents of the current log file"),
        )
        self._add_prefix_icon(clear_logs_row, "edit-clear-all-symbolic")
        clear_btn = Gtk.Button(label=_("Clear"), valign=Gtk.Align.CENTER)
        clear_btn.connect("clicked", self._on_clear_logs_clicked)
        clear_logs_row.add_suffix(clear_btn)
        group.add(clear_logs_row)
        return group

    def _build_reset_group(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(title=_("Data Management"))

        row = Adw.ActionRow(
            title=_("Reset to Default"),
            subtitle=_("Clear all preferences and restore default values"),
        )
        self._add_prefix_icon(row, "edit-undo-symbolic")
        reset_btn = Gtk.Button.new_with_label(_("Reset…"))
        reset_btn.set_valign(Gtk.Align.CENTER)
        reset_btn.add_css_class("destructive-action")
        reset_btn.connect("clicked", self._on_reset_clicked)
        row.add_suffix(reset_btn)
        group.add(row)
        return group

    def _add_toggle_row(
        self,
        group: Adw.PreferencesGroup,
        title: str,
        subtitle: str | None,
        icon_name: str,
        labels: tuple[str, str],
        handler: Callable,
        values: tuple,
    ) -> tuple[Gtk.ToggleButton, Gtk.ToggleButton]:
        """A row with two linked toggle buttons; returns the two buttons."""
        row = Adw.ActionRow(title=title)
        if subtitle:
            row.set_subtitle(subtitle)
        self._add_prefix_icon(row, icon_name)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.add_css_class("linked")
        button_box.set_valign(Gtk.Align.CENTER)
        row.add_suffix(button_box)

        buttons = []
        for label, value in zip(labels, values):
            button = Gtk.ToggleButton.new_with_label(label)
            button.set_size_request(80, -1)
            button.set_css_classes(["btn-sm"])
            if buttons:
                button.set_group(buttons[0])
            button.connect("clicked", handler, value)
            button_box.append(button)
            buttons.append(button)

        group.add(row)
        return buttons[0], buttons[1]

    @staticmethod
    def _add_prefix_icon(row: Adw.ActionRow, icon_name: str) -> None:
        """Show a symbolic icon at the start of a row."""
        row.add_prefix(Gtk.Image(icon_name=icon_name))

    def _add_auto_refresh_row(self, parent: Adw.PreferencesGroup) -> None:
        row = Adw.ComboRow(title=_("Auto Refresh"))
        self._add_prefix_icon(row, "view-refresh-symbolic")
        self._auto_refresh_row = row
        self._auto_refresh_options = AUTO_REFRESH_OPTIONS
        self._auto_refresh_handler = row.connect("notify::selected", self._on_auto_refresh_changed)
        self._update_auto_refresh_row()
        parent.add(row)

    def _update_auto_refresh_row(self) -> None:
        """Show the saved interval, offering "Off" only while the overview and
        notifications are both off: they need auto refresh."""
        required = settings.auto_refresh_required
        self._auto_refresh_options = [
            option for option in AUTO_REFRESH_OPTIONS if option[0] > 0 or not required
        ]
        values = [option[0] for option in self._auto_refresh_options]
        current = settings.auto_refresh_interval
        selected_idx = values.index(current) if current in values else 0

        # A new model moves the selection; that isn't the user choosing an interval
        row = self._auto_refresh_row
        with row.handler_block(self._auto_refresh_handler):
            row.set_model(Gtk.StringList.new([option[1] for option in self._auto_refresh_options]))
            row.set_selected(selected_idx)
        row.set_subtitle(_("Needed by the overview and notifications") if required else "")

    # ------------------------------------------------------------------
    # UI Binding & Initial State
    # ------------------------------------------------------------------
    def _bind_settings_to_ui(self) -> None:
        """Set initial UI state from current settings."""
        self._dynamic_bg_switch.set_active(settings.is_using_dynamic_bg)
        self._notification_switch.set_active(settings.show_notifications)
        self._overview_switch.set_active(settings.show_overview)
        self._background_switch.set_active(settings.run_in_background)
        self._set_toggle_buttons()

    def _set_toggle_buttons(self) -> None:
        """Select the toggle button that matches each setting."""
        if settings.unit == "metric":
            self._unit_btn_celsius.set_active(True)
        else:
            self._unit_btn_fahrenheit.set_active(True)

        if settings.is_using_inch_for_prec:
            self._precip_btn_inch.set_active(True)
        else:
            self._precip_btn_mm.set_active(True)

        if settings.is_using_24h_clock:
            self._time_btn_24h.set_active(True)
        else:
            self._time_btn_12h.set_active(True)

        if settings.icon_theme == "material":
            self._icon_theme_btn_material.set_active(True)
        else:
            self._icon_theme_btn_default.set_active(True)

    # ------------------------------------------------------------------
    # Signal Handlers
    # ------------------------------------------------------------------
    def _on_dynamic_bg_toggled(self, row: Adw.SwitchRow, _pspec) -> None:
        settings.is_using_dynamic_bg = row.get_active()
        self._refresh_weather()

    def _on_icon_theme_toggled(self, button: Gtk.ToggleButton, theme: str) -> None:
        if settings.icon_theme == theme:
            return
        settings.icon_theme = theme
        self._refresh_weather()

    def _on_24h_clock_toggled(self, button: Gtk.ToggleButton, use_24h: bool) -> None:
        if settings.is_using_24h_clock == use_24h:
            return
        settings.is_using_24h_clock = use_24h
        self._refresh_weather()

    def _on_unit_toggled(self, button: Gtk.ToggleButton, unit: str) -> None:
        if settings.unit == unit:
            return
        settings.unit = unit
        self._refresh_weather()

    def _on_precip_unit_toggled(self, button: Gtk.ToggleButton, use_inch: bool) -> None:
        if settings.is_using_inch_for_prec == use_inch:
            return
        settings.is_using_inch_for_prec = use_inch
        self._refresh_weather()

    def _on_notifications_toggled(self, row: Adw.SwitchRow, _pspec) -> None:
        settings.show_notifications = row.get_active()
        settings.require_auto_refresh()
        self._update_auto_refresh_row()

    def _on_overview_toggled(self, row: Adw.SwitchRow, _pspec) -> None:
        # The overview engine and section follow the setting themselves
        settings.show_overview = row.get_active()
        settings.require_auto_refresh()
        self._update_auto_refresh_row()

    def _on_run_in_background_toggled(self, row: Adw.SwitchRow, _pspec) -> None:
        # The main window follows the setting itself
        settings.run_in_background = row.get_active()

    def _on_debug_mode_toggled(self, row: Adw.SwitchRow, _pspec) -> None:
        settings.debug_mode = row.get_active()
        log_manager.update_level(settings.debug_mode)

    def _on_open_logs_clicked(self, _row: Adw.ActionRow) -> None:
        log_manager.open_log_folder()

    def _on_clear_logs_clicked(self, _button: Gtk.Button) -> None:
        if log_manager.clear_logs():
            self.add_toast(create_toast(_("Logs cleared"), 1))
        else:
            self.add_toast(create_toast(_("Failed to clear logs"), 1))

    def _on_auto_refresh_changed(self, combo: Adw.ComboRow, _pspec) -> None:
        idx = combo.get_selected()
        if idx >= len(self._auto_refresh_options):
            return
        settings.auto_refresh_interval = self._auto_refresh_options[idx][0]

    def _on_reset_clicked(self, _button: Gtk.Button) -> None:
        dialog = Adw.AlertDialog.new(
            _("Reset Settings?"),
            _(
                "This will restore all settings to default and will clear your saved cities. "
                "This action cannot be undone."
            ),
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("reset", _("Reset"))
        dialog.set_response_appearance("reset", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_reset_dialog_response)
        dialog.present(self)

    def _on_reset_dialog_response(self, dialog: Adw.AlertDialog, response: str) -> None:
        if response == "reset":
            self._perform_reset()

    def _perform_reset(self) -> None:
        """Reset settings and refresh UI + data."""
        settings.reset_to_defaults()

        # Update UI widgets
        self._dynamic_bg_switch.set_active(settings.is_using_dynamic_bg)
        self._notification_switch.set_active(settings.show_notifications)
        self._overview_switch.set_active(settings.show_overview)
        self._background_switch.set_active(settings.run_in_background)
        self._debug_switch.set_active(settings.debug_mode)
        settings.require_auto_refresh()
        self._update_auto_refresh_row()
        self._set_toggle_buttons()

        self.add_toast(create_toast(_("Preferences have been reset"), 1))

        # Refresh the weather data (the welcome screen if there are no cities)
        self._refresh_weather()

    def _refresh_weather(self):
        """Fetch again with the new preferences (the store fetches off the main loop)."""
        self.window._start_data_refresh()
