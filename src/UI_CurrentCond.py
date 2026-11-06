from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import GLib, Gtk, Pango  # noqa: E402
from gettext import gettext as _, pgettext as C_  # noqa: E402

from .CORE_GTKUtils import weak_connect  # noqa: E402
from .CORE_Helpers import JsonProcessor, get_timezone_from_selected_city  # noqa: E402
from .CORE_Icons import condition, create_weather_icon  # noqa: E402
from .CORE_Overview import overview_engine  # noqa: E402
from .settings import settings  # noqa: E402

# Heading colour for each insight severity (libadwaita style classes)
SEVERITY_CSS = {"info": "accent", "warning": "warning", "error": "error"}


class CurrentCondition(Gtk.Box):
    """Top section: current conditions, the location and its local time,
    and a one-line overview of the coming hours."""

    def __init__(self, *args, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, *args, **kwargs)
        self.set_hexpand(True)
        self._clock_id = 0
        self._overview_hide_id = 0
        self._overview_handler_id = 0
        self._overview_setting_id = 0
        self._overview_insight = None
        self._timezone = self._city_timezone()
        self.paint_ui()

        # The clock ticks, and the overview is followed, only while the
        # section is on screen
        weak_connect(self, "map", self._on_map)
        weak_connect(self, "unmap", self._on_unmap)

    def paint_ui(self) -> None:
        from .CORE_weatherData import weather_manager
        data = weather_manager.current_weather

        # Conditions on the left, location on the right; in a narrow
        # window the location wraps onto its own line
        top = Gtk.FlowBox(
            selection_mode=Gtk.SelectionMode.NONE,
            min_children_per_line=1,
            max_children_per_line=2,
            column_spacing=24,
            row_spacing=12,
            margin_start=3,
            margin_end=3,
        )
        self.append(top)

        top.append(self._build_conditions(data, weather_manager.daily_forecast))
        top.append(self._build_location())

        # Flow box children look clickable by default (hover highlight);
        # nothing here is, so they ignore the pointer and keyboard focus
        for child in (top.get_child_at_index(0), top.get_child_at_index(1)):
            child.set_focusable(False)
            child.set_can_target(False)
        # The location takes the rest of the line, pushing it to the right
        top.get_child_at_index(1).set_hexpand(True)

        self.append(self._build_overview())

    # ---------- Conditions (left) ----------

    def _build_conditions(self, data, daily) -> Gtk.Box:
        box = Gtk.Box(spacing=12, valign=Gtk.Align.CENTER)

        condition_code = str(data.weathercode.data)
        if data.is_day.data == 0:
            condition_code += "n"
        icon = create_weather_icon(condition_code, settings.icon_theme, 80)
        icon.set_valign(Gtk.Align.CENTER)
        box.append(icon)

        reading_box = Gtk.Box(spacing=12, valign=Gtk.Align.CENTER)
        box.append(reading_box)

        # Temperature, with the unit beside it on the same baseline
        temp_box = Gtk.Box(valign=Gtk.Align.CENTER, spacing=1)
        temp_box.add_css_class("current-temp-box")
        reading_box.append(temp_box)

        temp_label = Gtk.Label(
            label="{0:.0f}".format(data.temperature_2m.data),
            valign=Gtk.Align.BASELINE_FILL,
        )
        temp_label.set_css_classes(["font-bold", "current-temp"])
        temp_box.append(temp_label)

        unit_label = Gtk.Label(
            label=data.temperature_2m.unit, valign=Gtk.Align.BASELINE_FILL
        )
        unit_label.set_css_classes(["text-4xl", "font-medium", "opacity-90"])
        temp_box.append(unit_label)

        # Condition, today's high and low, feels like
        desc_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6, valign=Gtk.Align.CENTER
        )
        reading_box.append(desc_box)

        cond_label = Gtk.Label(
            label=condition[str(data.weathercode.data)],
            halign=Gtk.Align.START,
            xalign=0,
            wrap=True,
        )
        cond_label.set_css_classes(["text-4xl", "font-bold"])
        desc_box.append(cond_label)

        # Today's high and low, then feels like, on one line
        details_box = Gtk.Box(spacing=12, halign=Gtk.Align.START)
        desc_box.append(details_box)

        high_low = self._today_high_low(daily)
        if high_low:
            high_low_label = Gtk.Label(
                # Translators: today's highest (H) and lowest (L) temperatures, like "29°" and "14°"
                label=GLib.markup_escape_text(_("H {high} · L {low}")).format(
                    high=self._bold_degrees(high_low[0]),
                    low=self._bold_degrees(high_low[1]),
                ),
                use_markup=True,
                xalign=0,
                wrap=True,
            )
            high_low_label.set_css_classes(["text-sm", "opacity-80"])
            details_box.append(high_low_label)

            separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            separator.set_margin_top(3)
            separator.set_margin_bottom(3)
            details_box.append(separator)

        feels_label = Gtk.Label(
            # Translators: {0} is a temperature, like "22°"
            label=GLib.markup_escape_text(_("Feels like {0}")).format(
                self._bold_degrees(data.apparent_temperature.data)
            ),
            use_markup=True,
            xalign=0,
            wrap=True,
        )
        feels_label.set_css_classes(["text-sm", "opacity-80"])
        details_box.append(feels_label)

        return box

    # ---------- Location (right) ----------

    def _build_location(self) -> Gtk.Box:
        city = self._selected_city()

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            hexpand=True,
            halign=Gtk.Align.END,
            valign=Gtk.Align.CENTER,
        )

        city_label = Gtk.Label(label=city.get("name", ""))
        city_label.set_css_classes(["text-4xl", "font-bold"])

        # Cities saved by older versions have no state
        region = ", ".join(p for p in (city.get("state"), city.get("country")) if p)
        region_label = Gtk.Label(label=region)
        region_label.set_css_classes(["text-base", "opacity-80"])

        self._time_label = Gtk.Label(margin_top=2)
        self._time_label.set_css_classes(["text-sm", "opacity-70"])
        self._update_clock()

        for label in (city_label, region_label, self._time_label):
            label.set_halign(Gtk.Align.END)
            label.set_xalign(1.0)
            label.set_justify(Gtk.Justification.RIGHT)
            label.set_wrap(True)
            box.append(label)

        return box

    # ---------- Overview bar ----------

    def _build_overview(self) -> Gtk.Box:
        # Sized to its text, on the left under the conditions. While the
        # overview is enabled the info button is always there (it keeps the
        # space), but it only works once the engine has an insight.
        bar = Gtk.Box(
            margin_top=12,
            margin_start=3,
            margin_end=3,
            halign=Gtk.Align.START,
            visible=settings.show_overview,
        )
        bar.add_css_class("current-overview")
        if settings.is_using_dynamic_bg:
            bar.add_css_class("on-dynamic-bg")
        self._overview_bar = bar

        button = Gtk.Button(
            icon_name="dialog-information-symbolic",
            tooltip_text=_("Show Overview"),
            valign=Gtk.Align.CENTER,
        )
        # A ghost button: only the icon, no background
        button.set_css_classes(["flat", "circular", "current-overview-button"])
        weak_connect(button, "clicked", self._on_overview_clicked)
        bar.append(button)
        self._overview_button = button

        self._overview_revealer = Gtk.Revealer(
            transition_type=Gtk.RevealerTransitionType.SLIDE_RIGHT,
        )
        bar.append(self._overview_revealer)
        weak_connect(self._overview_revealer, "notify::child-revealed", self._on_overview_revealed)

        content = Gtk.Box(spacing=12, margin_start=8, margin_end=12)
        self._overview_revealer.set_child(content)

        self._overview_heading = Gtk.Label(valign=Gtk.Align.CENTER)
        content.append(self._overview_heading)

        content.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        # The insight's icon, just before the message (hidden when it has none)
        message_box = Gtk.Box(spacing=6)
        content.append(message_box)
        self._overview_icon = Gtk.Image(valign=Gtk.Align.CENTER, visible=False)
        self._overview_icon.add_css_class("opacity-75")
        message_box.append(self._overview_icon)

        # One line, as wide as its text; once the box spans the whole
        # section the text is ellipsized (the full text is in the tooltip)
        self._overview_label = Gtk.Label(xalign=0, ellipsize=Pango.EllipsizeMode.END)
        self._overview_label.set_css_classes(["text-sm", "opacity-75"])
        message_box.append(self._overview_label)

        return bar

    def _set_overview(self, insight, heading: Optional[str]) -> None:
        """Show the engine's insight; without one the button does nothing."""
        self._overview_insight = insight
        self._overview_button.set_sensitive(insight is not None)
        if insight is None:
            self._close_overview()
            return

        # The heading's colour follows the severity, always with words
        self._overview_heading.set_label((heading or "").upper())
        self._overview_heading.set_css_classes(
            ["text-xs", "font-bold", "current-overview-heading", SEVERITY_CSS.get(insight.severity, "accent")]
        )
        self._overview_icon.set_visible(insight.icon is not None)
        if insight.icon:
            self._overview_icon.set_from_icon_name(insight.icon)
        self._overview_label.set_label(insight.message)
        self._overview_label.set_tooltip_text(insight.message)

    def _on_overview_setting_changed(self, *_args) -> None:
        self._overview_bar.set_visible(settings.show_overview)

    def _on_overview_changed(self, engine, announce: bool) -> None:
        # New text always; open it only when the engine announces it
        insight = engine.current()
        self._set_overview(insight, engine.heading)
        if announce and insight is not None:
            self._open_overview()

    def _on_overview_clicked(self, _button: Gtk.Button) -> None:
        """Show the overview for a while; a second click hides it."""
        if self._overview_revealer.get_reveal_child():
            self._close_overview()
        else:
            self._open_overview()

    def _open_overview(self) -> None:
        if self._overview_insight is None:
            return
        self._cancel_overview_hide()
        self._overview_bar.add_css_class("open")
        self._overview_revealer.set_reveal_child(True)
        # Severe insights stay open longer
        self._overview_hide_id = GLib.timeout_add_seconds(
            self._overview_insight.show_seconds, self._hide_overview
        )

    def _on_overview_revealed(self, revealer: Gtk.Revealer, _pspec) -> None:
        # Drop the tint once the message has slid away, not before
        if not revealer.get_child_revealed():
            self._overview_bar.remove_css_class("open")

    def _hide_overview(self) -> bool:
        self._overview_hide_id = 0
        self._overview_revealer.set_reveal_child(False)
        return GLib.SOURCE_REMOVE

    def _close_overview(self) -> None:
        self._cancel_overview_hide()
        self._overview_revealer.set_reveal_child(False)

    def _cancel_overview_hide(self) -> None:
        if self._overview_hide_id:
            GLib.source_remove(self._overview_hide_id)
            self._overview_hide_id = 0

    def _on_map(self, *_args) -> None:
        self._start_clock()
        # Subscribe to the overview; it may already have an insight
        self._set_overview(overview_engine.current(), overview_engine.heading)
        if not self._overview_handler_id:
            self._overview_handler_id = weak_connect(
                overview_engine, "overview-changed", self._on_overview_changed
            )
        # Follow the preference too, so the button comes and goes at once
        self._on_overview_setting_changed()
        if not self._overview_setting_id:
            self._overview_setting_id = weak_connect(
                settings, "changed::show-overview", self._on_overview_setting_changed
            )

    def _on_unmap(self, *_args) -> None:
        # Timers and the engine's handler must not outlive the section
        # (it is rebuilt on refresh)
        self._stop_clock()
        self._close_overview()
        if self._overview_handler_id:
            overview_engine.disconnect(self._overview_handler_id)
            self._overview_handler_id = 0
        if self._overview_setting_id:
            settings.disconnect(self._overview_setting_id)
            self._overview_setting_id = 0

    # ---------- Clock ----------

    def _start_clock(self, *_args) -> None:
        self._stop_clock()
        self._update_clock()
        self._clock_id = GLib.timeout_add_seconds(1, self._update_clock)

    def _stop_clock(self, *_args) -> None:
        if self._clock_id:
            GLib.source_remove(self._clock_id)
            self._clock_id = 0
        self._overview_hide_id = 0

    def _update_clock(self) -> bool:
        now = datetime.now(self._timezone)
        # Translators: strftime format of the date above the overview ("Saturday, 7 Nov")
        date_str = now.strftime(C_("current date", "%A, %-d %b"))
        time_str = now.strftime("%H:%M" if settings.is_using_24h_clock else "%-I:%M %p")
        self._time_label.set_label(f"{date_str} · {time_str}")
        return GLib.SOURCE_CONTINUE

    # ---------- Helpers ----------

    @staticmethod
    def _degrees(value: float) -> str:
        return "{0:.0f}°".format(value)

    @classmethod
    def _bold_degrees(cls, value: float) -> str:
        """A temperature as Pango markup, in bold."""
        return "<b>{0}</b>".format(cls._degrees(value))

    @staticmethod
    def _city_timezone() -> Optional[ZoneInfo]:
        try:
            return ZoneInfo(get_timezone_from_selected_city())
        except (ZoneInfoNotFoundError, ValueError):
            return None

    def _today_high_low(self, daily) -> Optional[tuple]:
        """Today's (max, min) in the selected city, or None.

        Daily data is requested in GMT, so each day's timestamp is its
        midnight in UTC: compare its UTC date with the city's today.
        """
        if daily is None:
            return None
        today = datetime.now(self._timezone).date()
        for i, ts in enumerate(daily.time.data):
            if datetime.fromtimestamp(ts, tz=timezone.utc).date() == today:
                high = daily.temperature_2m_max.data[i]
                low = daily.temperature_2m_min.data[i]
                if high is None or low is None:
                    return None
                return high, low
        return None

    @staticmethod
    def _selected_city() -> dict:
        cities = JsonProcessor.str_list_to_json(settings.added_cities)
        for city in cities:
            if settings.selected_city == f"{city.get('latitude')},{city.get('longitude')}":
                return city
        return cities[0] if cities else {}
