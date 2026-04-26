import threading
import time
from enum import IntEnum

import gi
from gi.repository import Adw, Gtk
from gettext import gettext as _, pgettext as C_


from .settings import settings
from .CORE_Helpers import create_toast
from .configs import AUTO_REFRESH_OPTIONS
from .CORE_Logging import log_manager

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

# Using centralized constants from .configs


class WeatherPreferences(Adw.PreferencesWindow):
    """Preferences window for weather application."""

    def __init__(self, application: Adw.Application, **kwargs):
        super().__init__(**kwargs)
        self.application = application
        self.set_transient_for(application)
        self.set_default_size(600, 500)
        self.set_title(_("Weather Preferences"))

        # Internal state
        self._last_unit_switch_time: float = time.time()

        self._build_ui()
        self._bind_settings_to_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        """Create all preference pages and groups."""
        appearance_page = Adw.PreferencesPage()
        appearance_page.set_title(_("Appearance"))
        appearance_page.set_icon_name("applications-graphics-symbolic")
        self.add(appearance_page)

        general_group = Adw.PreferencesGroup()
        appearance_page.add(general_group)

        self._add_dynamic_background_row(general_group)
        self._add_notification_row(general_group)
        self._add_time_format_row(general_group)
        self._add_auto_refresh_row(general_group)
        self._add_units_and_measurements_group(general_group)

        advanced_page = Adw.PreferencesPage()
        advanced_page.set_title(_("Advanced"))
        advanced_page.set_icon_name("preferences-system-symbolic")
        self.add(advanced_page)

        debug_group = Adw.PreferencesGroup()
        debug_group.set_title(_("Logging &amp; Debugging"))
        advanced_page.add(debug_group)

        self._add_debug_mode_row(debug_group)
        self._add_open_logs_row(debug_group)
        self._add_clear_logs_row(debug_group)
        self._add_reset_row(advanced_page)

    def _add_dynamic_background_row(self, parent: Adw.PreferencesGroup) -> None:
        row = Adw.ActionRow(
            title=_("Dynamic Background"),
            subtitle=_(
                "App background changes based on current weather conditions"
            ),
            icon_name="preferences-color-symbolic",
            activatable=True,
        )
        switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        switch.set_active(settings.is_using_dynamic_bg)
        switch.connect("state-set", self._on_dynamic_bg_toggled)
        row.add_suffix(switch)
        self._dynamic_bg_switch = switch
        parent.add(row)

    def _add_time_format_row(self, parent: Adw.PreferencesGroup) -> None:
        row = Adw.ActionRow(
            title=_("Time Format"),
            subtitle=_("Weather time format"),
            icon_name="preferences-system-time-symbolic",
            activatable=True,
        )
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.add_css_class("linked")
        button_box.set_margin_start(2)
        button_box.set_valign(Gtk.Align.CENTER)
        row.add_suffix(button_box)

        btn_24h = Gtk.ToggleButton.new_with_label(_("24 Hour"))
        btn_24h.set_size_request(80, 20)
        btn_24h.set_css_classes(["btn-sm"])
        btn_24h.connect("clicked", self._on_24h_clock_toggled, True)

        btn_12h = Gtk.ToggleButton.new_with_label(_("AM / PM"))
        btn_12h.set_size_request(80, 20)
        btn_12h.set_css_classes(["btn-sm"])
        btn_12h.set_group(btn_24h)
        btn_12h.connect("clicked", self._on_24h_clock_toggled, False)

        button_box.append(btn_24h)
        button_box.append(btn_12h)

        self._time_btn_24h = btn_24h
        self._time_btn_12h = btn_12h
        parent.add(row)

    def _add_auto_refresh_row(self, parent: Adw.PreferencesGroup) -> None:
        labels = Gtk.StringList.new([opt[1] for opt in AUTO_REFRESH_OPTIONS])
        row = Adw.ComboRow(
            title=_("Auto Refresh"),
            subtitle=_("Automatically refresh weather data at a set interval"),
            icon_name="view-refresh-symbolic",
            model=labels,
        )
        current = settings.auto_refresh_interval
        selected_idx = 0
        for i, (val, label) in enumerate(AUTO_REFRESH_OPTIONS):
            if val == current:
                selected_idx = i
                break
        row.set_selected(selected_idx)
        row.connect("notify::selected", self._on_auto_refresh_changed)
        self._auto_refresh_row = row
        parent.add(row)

    def _add_notification_row(self, parent: Adw.PreferencesGroup) -> None:
        row = Adw.ActionRow(
            title=_("Show Notifications"),
            subtitle=_("Show notification when weather is refreshed automatically"),
            icon_name="preferences-system-notifications-symbolic",
            activatable=True,
        )
        switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        switch.set_active(settings.show_notifications)
        switch.connect("state-set", self._on_notifications_toggled)
        row.add_suffix(switch)
        self._notification_switch = switch
        parent.add(row)

    def _add_units_and_measurements_group(self, parent: Adw.PreferencesGroup) -> None:
        """Units selection: Celsius / Fahrenheit as linked toggle buttons."""
        group = Adw.PreferencesGroup()
        group.set_margin_top(20)
        group.set_title(_("Units &amp; Measurements"))
        parent.add(group)

        # Create a single row for temperature unit selection
        unit_row = Adw.ActionRow(
            title=_("System Unit"),
            subtitle=_("Metric (C, mm, km/h) or Imperial (F, inches, mph) [restart required]"),
            icon_name="power-profile-balanced-symbolic",
            activatable=True,
        )

        # Linked buttons container
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.add_css_class("linked")
        button_box.set_margin_start(2)
        button_box.set_valign(Gtk.Align.CENTER)

        btn_celsius = Gtk.ToggleButton.new_with_label(_("Metric"))
        btn_celsius.set_size_request(80, 20)
        btn_celsius.set_css_classes(["btn-sm"])
        btn_celsius.connect("clicked", self._on_unit_toggled, "metric")

        btn_fahrenheit = Gtk.ToggleButton.new_with_label(_("Imperial"))
        btn_fahrenheit.set_size_request(80, 20)
        btn_fahrenheit.set_css_classes(["btn-sm"])
        btn_fahrenheit.set_group(btn_celsius)
        btn_fahrenheit.connect("clicked", self._on_unit_toggled, "imperial")

        button_box.append(btn_celsius)
        button_box.append(btn_fahrenheit)
        unit_row.add_suffix(button_box)

        group.add(unit_row)

        # Store references for reset and binding
        self._unit_btn_celsius = btn_celsius
        self._unit_btn_fahrenheit = btn_fahrenheit

        # Precipitation unit (inches/mm) - unchanged
        prec_row = Adw.ActionRow(
            title=_("Precipitation in inches"),
            subtitle=_("This option works better in heavy precipitation"),
            icon_name="function-linear-symbolic",
            activatable=True,
        )
        prec_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        prec_switch.set_active(settings.is_using_inch_for_prec)
        prec_switch.connect("state-set", self._on_precip_unit_toggled)
        prec_row.add_suffix(prec_switch)
        self._precip_switch = prec_switch

        group.add(prec_row)

    def _add_reset_row(self, parent: Adw.PreferencesPage) -> None:
        data_group = Adw.PreferencesGroup()
        data_group.set_title(_("Data Management"))
        data_group.set_margin_top(20)
        parent.add(data_group)

        row = Adw.ActionRow(
            title=_("Reset to Default"),
            subtitle=_("Clear all preferences and restore default values"),
            icon_name="object-rotate-left-symbolic",
        )
        reset_btn = Gtk.Button.new_with_label(_("Reset…"))
        reset_btn.set_valign(Gtk.Align.CENTER)
        reset_btn.add_css_class("destructive-action")
        reset_btn.connect("clicked", self._on_reset_clicked)
        row.add_suffix(reset_btn)
        data_group.add(row)

    def _add_debug_mode_row(self, parent: Adw.PreferencesGroup) -> None:
        row = Adw.ActionRow(
            title=_("Debug Mode"),
            subtitle=_("Enable verbose logging and console output"),
            icon_name="utilities-terminal-symbolic",
            activatable=True,
        )
        switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        switch.set_active(settings.debug_mode)
        switch.connect("state-set", self._on_debug_mode_toggled)
        row.add_suffix(switch)
        self._debug_switch = switch
        parent.add(row)

    def _add_open_logs_row(self, parent: Adw.PreferencesGroup) -> None:
        row = Adw.ActionRow(
            title=_("Open Logs Folder"),
            subtitle=_("Access the application log files"),
            icon_name="folder-open-symbolic",
            activatable=True,
        )
        btn = Gtk.Button(icon_name="folder-open-symbolic")
        btn.set_valign(Gtk.Align.CENTER)
        btn.add_css_class("flat")
        btn.connect("clicked", self._on_open_logs_clicked)
        row.add_suffix(btn)
        parent.add(row)

    def _add_clear_logs_row(self, parent: Adw.PreferencesGroup) -> None:
        row = Adw.ActionRow(
            title=_("Clear Log File"),
            subtitle=_("Delete all contents of the current log file"),
            icon_name="edit-clear-all-symbolic",
            activatable=True,
        )
        btn = Gtk.Button(icon_name="edit-clear-all-symbolic")
        btn.set_valign(Gtk.Align.CENTER)
        btn.add_css_class("flat")
        btn.connect("clicked", self._on_clear_logs_clicked)
        row.add_suffix(btn)
        parent.add(row)

    # ------------------------------------------------------------------
    # UI Binding & Initial State
    # ------------------------------------------------------------------
    def _bind_settings_to_ui(self) -> None:
        """Set initial UI state from current settings."""
        self._dynamic_bg_switch.set_active(settings.is_using_dynamic_bg)

        # Time format
        if settings.is_using_24h_clock:
            self._time_btn_24h.set_active(True)
        else:
            self._time_btn_12h.set_active(True)

        # Temperature unit
        if settings.unit == "metric":
            self._unit_btn_celsius.set_active(True)
        else:
            self._unit_btn_fahrenheit.set_active(True)

        # Precipitation unit
        self._precip_switch.set_active(settings.is_using_inch_for_prec)

        # Notifications
        self._notification_switch.set_active(settings.show_notifications)

    # ------------------------------------------------------------------
    # Signal Handlers
    # ------------------------------------------------------------------
    def _on_dynamic_bg_toggled(self, switch: Gtk.Switch, state: bool) -> None:
        settings.is_using_dynamic_bg = state
        self._start_refresh_thread()

    def _on_24h_clock_toggled(self, button: Gtk.ToggleButton, use_24h: bool) -> None:
        settings.is_using_24h_clock = use_24h
        self._start_refresh_thread()

    def _on_unit_toggled(self, button: Gtk.ToggleButton, unit: str) -> None:
        settings.unit = unit
        self.add_toast(create_toast(_("Switched to - {}").format(unit.capitalize()), 1))


    def _on_precip_unit_toggled(self, switch: Gtk.Switch, state: bool) -> None:
        settings.is_using_inch_for_prec = state
        self._start_refresh_thread()

    def _on_notifications_toggled(self, switch: Gtk.Switch, state: bool) -> None:
        settings.show_notifications = state

    def _on_debug_mode_toggled(self, switch: Gtk.Switch, state: bool) -> None:
        settings.debug_mode = state
        log_manager.update_level()

    def _on_open_logs_clicked(self, _button: Gtk.Button) -> None:
        log_manager.open_log_folder()

    def _on_clear_logs_clicked(self, _button: Gtk.Button) -> None:
        if log_manager.clear_logs():
            self.add_toast(create_toast(_("Logs cleared"), 1))
        else:
            self.add_toast(create_toast(_("Failed to clear logs"), 1))

    def _on_auto_refresh_changed(self, combo: Adw.ComboRow, _pspec) -> None:
        idx = combo.get_selected()
        if idx >= len(AUTO_REFRESH_OPTIONS):
            return

        interval_val, interval_label = AUTO_REFRESH_OPTIONS[idx]
        settings.auto_refresh_interval = interval_val

        if interval_val == 0:
            msg = _("Auto refresh disabled")
        else:
            msg = _("Auto refresh every {} min").format(interval_val)

        self.add_toast(create_toast(msg, 1))

    def _on_reset_clicked(self, _button: Gtk.Button) -> None:
        dialog = Adw.MessageDialog.new(
            self,
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
        dialog.present()

    def _on_reset_dialog_response(self, dialog: Adw.MessageDialog, response: str) -> None:
        if response == "reset":
            self._perform_reset()

    def _perform_reset(self) -> None:
        """Reset settings and refresh UI + data."""
        settings.reset_to_defaults()

        # Update UI widgets
        self._dynamic_bg_switch.set_active(settings.is_using_dynamic_bg)
        self._precip_switch.set_active(settings.is_using_inch_for_prec)
        self._notification_switch.set_active(settings.show_notifications)

        # Auto refresh combo
        self._auto_refresh_row.set_selected(0) # 0 is always OFF in our list

        # Temperature unit buttons
        if settings.unit == "metric":
            self._unit_btn_celsius.set_active(True)
        else:
            self._unit_btn_fahrenheit.set_active(True)

        # Time format buttons
        if settings.is_using_24h_clock:
            self._time_btn_24h.set_active(True)
        else:
            self._time_btn_12h.set_active(True)

        self.add_toast(create_toast(_("Preferences have been reset"), 1))

        # Force a refresh of weather data (showing welcome screen)
        self._start_refresh_thread()


    def _start_refresh_thread(self):
        thread = threading.Thread(
            target=self.application._start_data_refresh,
            name="refresh_after_unit_change"
        )
        thread.daemon = True
        thread.start()