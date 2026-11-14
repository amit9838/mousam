import time
from gettext import gettext as _
from typing import Optional
from zoneinfo import ZoneInfo

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402

from .configs import THRESHOLDS  # noqa: E402
from .CORE_Helpers import get_selected_city_name, get_time_difference  # noqa: E402
from .CORE_weatherData import WeatherDataManager, weather_manager  # noqa: E402
from .UI_CompDrawLineGraph import LineGraph  # noqa: E402

# The pollutants that make up the AQI, listed first
MAIN_POLLUTANTS = (
    ("pm2_5", _("PM2.5")),
    ("pm10", _("PM10")),
    ("nitrogen_dioxide", _("NO₂")),
    ("ozone", _("O₃")),
    ("sulphur_dioxide", _("SO₂")),
    ("carbon_monoxide", _("CO")),
)
# The rest, folded away
MORE_POLLUTANTS = (
    ("carbon_dioxide", _("CO₂")),
    ("methane", _("CH₄")),
    ("ammonia", _("NH₃")),
    ("dust", _("Dust")),
)
POLLEN = (
    ("alder_pollen", _("Alder")),
    ("birch_pollen", _("Birch")),
    ("grass_pollen", _("Grass")),
    ("mugwort_pollen", _("Mugwort")),
    ("olive_pollen", _("Olive")),
    ("ragweed_pollen", _("Ragweed")),
)

GRAPH_HEIGHT = 180
# Below this width (sp), on phones, everything is one column with the trend on top
NARROW_WIDTH = 600
# The dialog's smallest size (px): a small phone
MIN_WIDTH = 360
MIN_HEIGHT = 300


def nearest_index(times: list, now: float) -> int:
    """The index of the time closest to now."""
    if not times:
        return 0
    return min(range(len(times)), key=lambda i: abs(times[i] - now))


def format_value(value: float) -> str:
    """A pollutant's value: whole from 100, with one decimal below."""
    return f"{value:.0f}" if value >= 100 else f"{value:.1f}"


class AirQualityDialog(Adw.Dialog):
    """The air quality in detail: the AQI, what to do, its trend, and every
    pollutant and pollen count.

    The summary and the trend are on the left; the details on the right,
    which scroll on their own. On phones it is one column, the trend on top.
    """

    def __init__(self):
        super().__init__(title=_("Air Quality"))
        self.set_content_width(840)
        # Dialogs with breakpoints need a minimum size: a small phone
        self.set_size_request(MIN_WIDTH, MIN_HEIGHT)

        data = weather_manager.air_pollution
        self.idx = nearest_index(data.time.data, time.time())

        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title=_("Air Quality"), subtitle=get_selected_city_name()))
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(header)

        # The summary column sets the dialog's height; the details beside it
        # fill that height and scroll
        summary = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18,
                          hexpand=True, valign=Gtk.Align.START)
        advice = self._advice(data)
        trend = self._trend(data)
        summary.append(self._summary(data))
        summary.append(advice)
        summary.append(trend)

        # Only the details scroll; the summary stays in view. They don't ask
        # for their own height, so they take the summary column's
        details_list = self._details(data)
        details = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, vexpand=True)
        details.set_child(details_list)

        sources = Gtk.Label(
            label=_("AQI by the US EPA; limits from the WHO guidelines (2021). Data by Open-Meteo."),
            xalign=0, wrap=True,
        )
        sources.set_css_classes(["caption", "dim-label"])
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)

        # The summary on the left, the details on the right, the sources under both
        grid = Gtk.Grid(column_spacing=24, row_spacing=18)
        for side in ("top", "bottom", "start", "end"):
            getattr(grid, f"set_margin_{side}")(18)
        grid.attach(summary, 0, 0, 1, 1)
        grid.attach(separator, 1, 0, 1, 1)
        grid.attach(details, 2, 0, 1, 1)
        grid.attach(sources, 0, 1, 3, 1)

        # Scrolls only when the window is too short for the summary column;
        # otherwise everything fits and just the details scroll
        page = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, propagate_natural_height=True)
        page.set_child(grid)
        toolbar.set_content(page)
        self.set_child(toolbar)

        # Phones: one column, the trend on top, then the summary, the details
        # and the sources; the whole column scrolls (no scrolling inside it)
        narrow = Adw.Breakpoint.new(Adw.BreakpointCondition.parse(f"max-width: {NARROW_WIDTH}sp"))
        layout = grid.get_layout_manager()
        details_child = layout.get_layout_child(details)
        narrow.add_setter(details_child, "column", 0)
        narrow.add_setter(details_child, "row", 1)
        sources_child = layout.get_layout_child(sources)
        narrow.add_setter(sources_child, "row", 2)
        narrow.add_setter(sources_child, "column-span", 1)
        narrow.add_setter(separator, "visible", False)
        narrow.add_setter(details, "vscrollbar-policy", Gtk.PolicyType.NEVER)
        narrow.add_setter(details, "propagate-natural-height", True)
        narrow.add_setter(details_list, "width-request", -1)  # as wide as the phone
        narrow.add_setter(grid, "margin-start", 12)
        narrow.add_setter(grid, "margin-end", 12)
        # Moving a child within a box is no property, so it is done on the
        # breakpoint's signals; they hold the boxes, never the dialog
        narrow.connect("apply", lambda _bp: summary.reorder_child_after(trend, None))
        narrow.connect("unapply", lambda _bp: summary.reorder_child_after(trend, advice))
        self.add_breakpoint(narrow)

    # ---------- Left: the summary ----------

    def _summary(self, data) -> Gtk.Widget:
        """The US AQI, its level, the EU AQI and the main pollutant."""
        us_aqi = data.us_aqi.data[self.idx]
        box = Gtk.Box(spacing=14)
        if us_aqi is None:
            box.append(self._label(_("No air quality data for now."), ["dim-label"]))
            return box

        value = self._label(str(int(us_aqi)), ["title-1", "numeric"], wrap=False)
        value.set_valign(Gtk.Align.CENTER)
        box.append(value)

        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, valign=Gtk.Align.CENTER)
        level_class = WeatherDataManager.aqi_level_class(us_aqi)
        side.append(self._label(WeatherDataManager.classify_aqi(us_aqi), ["title-4", level_class]))

        eu_aqi = data.european_aqi.data[self.idx]
        if eu_aqi is not None:
            # Translators: the European AQI beside the US one; {aqi} is its
            # value and {level} its level name ("Fair")
            eu_text = _("US AQI · EU AQI {aqi}, {level}").format(
                aqi=int(eu_aqi), level=WeatherDataManager.classify_eu_aqi(eu_aqi))
        else:
            eu_text = _("US AQI")
        side.append(self._label(eu_text, ["caption", "dim-label"]))

        main = WeatherDataManager.main_pollutant(
            {key: self._value(data, key) for key, _name in MAIN_POLLUTANTS})
        if main:
            # Translators: {name} is a pollutant, like "PM2.5"
            text = _("Main pollutant: {name}").format(name=dict(MAIN_POLLUTANTS)[main])
            side.append(self._label(text, ["caption", "dim-label"]))
        box.append(side)
        return box

    def _advice(self, data) -> Gtk.Widget:
        us_aqi = data.us_aqi.data[self.idx]
        text = WeatherDataManager.aqi_advice(us_aqi) if us_aqi is not None else ""
        label = self._label(text, [])
        label.set_visible(bool(text))
        return label

    def _trend(self, data) -> Gtk.Widget:
        """The US AQI over the last and next three days."""
        group = Adw.PreferencesGroup(title=_("Trend"), description=_("Last 3 days and next 3 days"))
        tz = ZoneInfo(get_time_difference().get("timezone", "UTC"))
        graph = LineGraph(data.us_aqi.data, times=data.time.data, current_idx=self.idx, tz=tz).dw
        graph.set_size_request(-1, GRAPH_HEIGHT)
        graph.set_hexpand(True)
        group.add(graph)
        return group

    # ---------- Right: the details ----------

    def _details(self, data) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18, valign=Gtk.Align.START)
        box.set_size_request(340, -1)

        pollutants = Adw.PreferencesGroup(title=_("Pollutants"))
        for key, name in MAIN_POLLUTANTS:
            row = self._pollutant_row(data, key, name)
            if row:
                pollutants.add(row)

        more = [(key, name) for key, name in MORE_POLLUTANTS if self._value(data, key) is not None]
        if more:
            expander = Adw.ExpanderRow(
                title=_("More Pollutants"), subtitle=", ".join(name for _key, name in more))
            for key, name in more:
                row = Adw.ActionRow(title=name)
                field = getattr(data, key)
                row.add_suffix(self._label(f"{format_value(field.data[self.idx])} {field.unit}",
                                           ["dim-label", "numeric"], wrap=False))
                expander.add_row(row)
            pollutants.add(expander)
        box.append(pollutants)

        # Pollen is only measured in some places (Europe): leave it out elsewhere
        pollen = [(key, name) for key, name in POLLEN if self._value(data, key) is not None]
        if pollen:
            group = Adw.PreferencesGroup(title=_("Pollen"))
            for key, name in pollen:
                word, level_class = WeatherDataManager.classify_pollen(self._value(data, key))
                row = Adw.ActionRow(title=name)
                row.add_suffix(self._label(word, [level_class], wrap=False))
                group.add(row)
            box.append(group)
        return box

    def _pollutant_row(self, data, key: str, name: str) -> Optional[Adw.ActionRow]:
        """A pollutant's value and level, with its WHO limit."""
        value = self._value(data, key)
        if value is None:
            return None
        unit = getattr(data, key).unit or "μg/m³"
        row = Adw.ActionRow(title=name)
        if key in THRESHOLDS:
            # Translators: the WHO guideline for a pollutant; {limit} is a
            # number and {unit} its unit, like "μg/m³"
            row.set_subtitle(_("WHO limit {limit} {unit}").format(limit=THRESHOLDS[key][0][0], unit=unit))

        word, level_class = WeatherDataManager.classify_pollutant(key, value)
        values = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER)
        amount = self._label(f"{format_value(value)} {unit}", ["numeric"], wrap=False)
        amount.set_xalign(1)
        level = self._label(word, ["caption", level_class], wrap=False)
        level.set_xalign(1)
        values.append(amount)
        values.append(level)
        row.add_suffix(values)
        return row

    # ---------- Helpers ----------

    def _value(self, data, key: str):
        """A field's value for now, or None when it is missing."""
        field = getattr(data, key, None)
        if field is None or self.idx >= len(field.data):
            return None
        return field.data[self.idx]

    @staticmethod
    def _label(text: str, classes: list, wrap: bool = True) -> Gtk.Label:
        """A label; values and level words (wrap=False) stay on one line."""
        label = Gtk.Label(label=text, xalign=0, wrap=wrap)
        label.set_css_classes(classes)
        return label
