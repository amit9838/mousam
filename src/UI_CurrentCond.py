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
from .settings import settings  # noqa: E402

# TODO: placeholder until the overview is generated from the forecast.
# Kept out of _() so translators don't get a throwaway string.
PLACEHOLDER_OVERVIEW = "Clear and calm. Cooling to 14° by 6 AM, with haze likely at sunrise."

# How long the overview stays open after the info button is clicked
OVERVIEW_SHOW_SECONDS = 5


class CurrentCondition(Gtk.Box):
    """Top section: current conditions, the location and its local time,
    and a one-line overview of the coming hours."""

    def __init__(self, *args, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, *args, **kwargs)
        self.set_hexpand(True)
        self._clock_id = 0
        self._overview_hide_id = 0
        self._timezone = self._city_timezone()
        self.paint_ui()

        # The clock only ticks while the section is on screen
        weak_connect(self, "map", self._start_clock)
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

        self.append(self._build_overview(data.is_day.data))

    # ---------- Conditions (left) ----------

    def _build_conditions(self, data, daily) -> Gtk.Box:
        box = Gtk.Box(spacing=24, valign=Gtk.Align.CENTER)

        condition_code = str(data.weathercode.data)
        if data.is_day.data == 0:
            condition_code += "n"
        icon = create_weather_icon(condition_code, settings.icon_theme, 96)
        icon.set_valign(Gtk.Align.CENTER)
        box.append(icon)

        # Temperature, with the unit raised beside it
        temp_box = Gtk.Box(valign=Gtk.Align.CENTER)
        box.append(temp_box)

        temp_label = Gtk.Label(label="{0:.0f}".format(data.temperature_2m.data))
        temp_label.set_css_classes(["text-8xl", "font-bold", "current-temp"])
        temp_box.append(temp_label)

        unit_label = Gtk.Label(
            label=data.temperature_2m.unit, valign=Gtk.Align.START, margin_top=14
        )
        unit_label.set_css_classes(["text-4xl", "font-medium", "opacity-90"])
        temp_box.append(unit_label)

        # Condition, feels like, today's high and low
        desc_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=4, valign=Gtk.Align.CENTER
        )
        box.append(desc_box)

        cond_label = Gtk.Label(
            label=condition[str(data.weathercode.data)],
            halign=Gtk.Align.START,
            xalign=0,
            wrap=True,
        )
        cond_label.set_css_classes(["text-2xl", "font-bold"])
        desc_box.append(cond_label)

        feels_label = Gtk.Label(
            # Translators: {0} is a temperature, like "22°"
            label=_("Feels like {0}").format(
                self._degrees(data.apparent_temperature.data)
            ),
            halign=Gtk.Align.START,
            xalign=0,
            wrap=True,
        )
        feels_label.set_css_classes(["text-sm", "opacity-80"])
        desc_box.append(feels_label)

        high_low = self._today_high_low(daily)
        if high_low:
            high_low_label = Gtk.Label(
                # Translators: today's highest and lowest temperatures, like "29°" and "14°"
                label=_("High {high} · Low {low}").format(
                    high=self._degrees(high_low[0]), low=self._degrees(high_low[1])
                ),
                halign=Gtk.Align.START,
                xalign=0,
                wrap=True,
            )
            high_low_label.set_css_classes(["text-sm", "opacity-80"])
            desc_box.append(high_low_label)

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
        region_label = Gtk.Label(label=region, margin_top=4)
        region_label.set_css_classes(["text-base", "opacity-80"])

        self._time_label = Gtk.Label(margin_top=4)
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

    def _build_overview(self, is_day: int) -> Gtk.Box:
        # Sized to its text, on the left under the conditions. Only the
        # info button shows until it is clicked.
        bar = Gtk.Box(margin_top=0, margin_start=3, margin_end=3, halign=Gtk.Align.START)
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

        self._overview_revealer = Gtk.Revealer(
            transition_type=Gtk.RevealerTransitionType.SLIDE_RIGHT,
        )
        bar.append(self._overview_revealer)
        weak_connect(self._overview_revealer, "notify::child-revealed", self._on_overview_revealed)

        content = Gtk.Box(spacing=12, margin_start=8, margin_end=12)
        self._overview_revealer.set_child(content)

        if is_day == 0:
            heading = C_("overview heading", "Tonight")
        else:
            heading = C_("overview heading", "Today")
        heading_label = Gtk.Label(label=heading.upper(), valign=Gtk.Align.CENTER)
        heading_label.set_css_classes(["text-xs", "font-bold", "accent", "current-overview-heading"])
        content.append(heading_label)

        content.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        # One line, as wide as its text; once the box spans the whole
        # section the text is ellipsized (the full text is in the tooltip)
        message = Gtk.Label(
            label=PLACEHOLDER_OVERVIEW,
            tooltip_text=PLACEHOLDER_OVERVIEW,
            xalign=0,
            ellipsize=Pango.EllipsizeMode.END,
        )
        message.set_css_classes(["text-sm", "opacity-75"])
        content.append(message)

        return bar

    def _on_overview_clicked(self, _button: Gtk.Button) -> None:
        """Show the overview for a few seconds; a second click hides it."""
        self._cancel_overview_hide()
        if self._overview_revealer.get_reveal_child():
            self._overview_revealer.set_reveal_child(False)
            return
        self._overview_bar.add_css_class("open")
        self._overview_revealer.set_reveal_child(True)
        self._overview_hide_id = GLib.timeout_add_seconds(
            OVERVIEW_SHOW_SECONDS, self._hide_overview
        )

    def _on_overview_revealed(self, revealer: Gtk.Revealer, _pspec) -> None:
        # Drop the tint once the message has slid away, not before
        if not revealer.get_child_revealed():
            self._overview_bar.remove_css_class("open")

    def _hide_overview(self) -> bool:
        self._overview_hide_id = 0
        self._overview_revealer.set_reveal_child(False)
        return GLib.SOURCE_REMOVE

    def _cancel_overview_hide(self) -> None:
        if self._overview_hide_id:
            GLib.source_remove(self._overview_hide_id)
            self._overview_hide_id = 0

    def _on_unmap(self, *_args) -> None:
        # Timers must not outlive the section (it is rebuilt on refresh)
        self._stop_clock()
        self._cancel_overview_hide()
        self._overview_revealer.set_reveal_child(False)

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
