import gi
from gettext import gettext as _, pgettext as C_
from typing import Optional, Union

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk

from .CORE_Icons import get_icon_path, ARROW_CENTER
from .configs import HPA_TO_INHG, PRESSURE_GAUGE_CENTER, PRESSURE_GAUGE_SPAN  # noqa: E402
from .settings import settings
from .UI_CompDrawBar import DrawLevelBar
from .UI_CompDrawTickGauge import DrawTickGauge  # noqa: E402
from .UI_CompDrawImageIcon import DrawImage
from .CORE_Levels import compass_direction

# Standardizing CSS classes for reuse
CSS_CARD_BASE = ["view", "card"]
CSS_TEXT_TITLE = ["text-lg", "opacity-80", "font-medium"]
CSS_TEXT_VALUE = ["text-3xl", "font-medium"]
CSS_TEXT_UNIT = ["text-sm", "opacity-80"]
CSS_TEXT_DESC = ["text-base", "opacity-90", "font-semibold"]
# "Low" / "High" at the ends of a gauge
CSS_TEXT_GAUGE_END = ["text-xs", "opacity-70"]
# The vertical gauges are a little shorter than DrawLevelBar's default, so
# with "High" and "Low" around them the cards stay as tall as their row
LEVEL_BAR_HEIGHT = 88


class CardSquare:
    """
    A reusable Card component for displaying weather metrics (Wind, Humidity, etc.).
    Displays a title, main value, description, and a visual passed in: on the
    right between text_up and text_low, or under the text, full width
    (visual_below).
    """

    def __init__(
        self,
        title: str,
        main_val: Union[str, int, float],
        main_val_unit: str = "",
        desc: str = "",
        sub_desc_heading: str = "",
        sub_desc: str = "",
        text_up: str = "",
        text_low: str = "",
        visual: Optional[Gtk.Widget] = None,
        visual_below: Optional[Gtk.Widget] = None,
        ends_css: Optional[list] = None,
    ):
        self.title = title
        self.main_val = main_val
        self.main_val_unit = main_val_unit
        self.desc = desc
        self.sub_desc_heading = sub_desc_heading
        self.sub_desc = sub_desc
        self.text_up = text_up
        self.text_low = text_low
        self.ends_css = ends_css or CSS_TEXT_GAUGE_END
        self.card = self._build_ui(visual, visual_below)

    def _build_ui(self, visual: Optional[Gtk.Widget], visual_below: Optional[Gtk.Widget]) -> Gtk.Widget:
        """Constructs the UI using Box layout for better performance than Grid."""

        # 1. Main Container (Vertical Box)
        card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card_box.set_size_request(170, 140)
        card_box.set_css_classes(CSS_CARD_BASE)
        card_box.set_margin_top(6)
        card_box.set_margin_start(3)
        card_box.set_margin_end(3)

        if settings.is_using_dynamic_bg:
            card_box.add_css_class("bg-dark-overlay")

        # 2. Title Area
        lbl_title = Gtk.Label(label=self.title)
        lbl_title.set_halign(Gtk.Align.START)
        lbl_title.set_css_classes(CSS_TEXT_TITLE)
        card_box.append(lbl_title)

        # 3. Content Area (Horizontal Split: Text Left | Graphic Right)
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        content_box.set_hexpand(True)
        card_box.append(content_box)

        # --- Left Side: Text Info ---
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_hexpand(True)
        content_box.append(info_box)

        # Value & Unit Row
        val_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        lbl_val = Gtk.Label(label=str(self.main_val))
        lbl_val.set_css_classes(CSS_TEXT_VALUE)

        lbl_unit = Gtk.Label(label=self.main_val_unit)
        lbl_unit.set_css_classes(CSS_TEXT_UNIT)
        # Align unit to the baseline of the value
        lbl_unit.set_valign(Gtk.Align.BASELINE)

        val_box.append(lbl_val)
        val_box.append(lbl_unit)
        info_box.append(val_box)

        # Description (Wrapped)
        if self.desc:
            lbl_desc = Gtk.Label(label=self.desc)
            lbl_desc.set_css_classes(CSS_TEXT_DESC)
            lbl_desc.set_wrap(True)
            lbl_desc.set_halign(Gtk.Align.START)
            lbl_desc.set_max_width_chars(10)  # Prevent text from pushing box too wide
            info_box.append(lbl_desc)

        # Sub-Description (Dewpoint / Wind Dir)
        if self.sub_desc_heading or self.sub_desc:
            sub_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            sub_box.set_margin_top(10)

            if self.sub_desc_heading:
                lbl_head = Gtk.Label(label=self.sub_desc_heading)
                lbl_head.set_css_classes(["text-sm", "opacity-95"])
                lbl_head.set_halign(Gtk.Align.START)
                sub_box.append(lbl_head)

            if self.sub_desc:
                lbl_sub = Gtk.Label(label=self.sub_desc)
                lbl_sub.set_css_classes(["text-lg", "font-semibold"])
                lbl_sub.set_halign(Gtk.Align.START)
                # A long translated direction wraps in narrow windows
                lbl_sub.set_wrap(True)
                lbl_sub.set_xalign(0)
                sub_box.append(lbl_sub)

            info_box.append(sub_box)

        # --- Right Side: Visual/Graphic ---
        visual_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        visual_box.set_halign(Gtk.Align.END)
        visual_box.set_valign(Gtk.Align.CENTER)
        content_box.append(visual_box)

        # Upper Text (N, High, etc)
        if self.text_up:
            lbl_up = Gtk.Label(label=self.text_up)
            lbl_up.set_css_classes(self.ends_css)
            visual_box.append(lbl_up)

        # The Graphic (Canvas)
        if visual_below:
            card_box.append(visual_below)
        elif visual:
            visual_box.append(visual)

        # Lower Text
        if self.text_low:
            lbl_low = Gtk.Label(label=self.text_low)
            lbl_low.set_css_classes(self.ends_css)
            visual_box.append(lbl_low)

        return card_box


def _number(value) -> Optional[float]:
    """value as a float, or None when it is missing or not a number."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def wind_card(current) -> Gtk.Widget:
    """Wind speed, its level and where it comes from, with a compass arrow."""
    degrees = _number(current.winddirection_10m.data)
    arrow = None
    if degrees is not None:
        arrow = DrawImage(
            get_icon_path("arrow", settings.icon_theme), degrees + 180, 35, 35, ARROW_CENTER
        ).widget
    return CardSquare(
        title=_("Wind"),
        main_val=current.windspeed_10m.data,
        main_val_unit=current.windspeed_10m.unit,
        desc=current.windspeed_10m.level_str,
        # Translators: wind direction is where the wind blows from
        sub_desc_heading=_("Direction (from)"),
        sub_desc=(
            compass_direction(degrees) if degrees is not None
            else str(current.winddirection_10m.data) + "°"
        ),
        # Translators: "North" on the wind direction compass, as short as possible
        text_up=C_("compass", "N"),
        visual=arrow,
        ends_css=["text-lg", "font-medium"],
    ).card


def humidity_card(current) -> Gtk.Widget:
    """Relative humidity and the dew point, with a level gauge."""
    value = _number(current.relativehumidity_2m.data)
    gauge = None
    if value is not None:
        # In a bright ocean blue (#219eed)
        gauge = DrawLevelBar(value / 100.0, height=LEVEL_BAR_HEIGHT, rgb_color=(0.13, 0.62, 0.93)).widget
    return CardSquare(
        title=_("Humidity"),
        main_val=current.relativehumidity_2m.data,
        main_val_unit="%",
        desc=current.relativehumidity_2m.level_str,
        sub_desc_heading=_("Dewpoint"),
        sub_desc=f"{current.dewpoint_2m.data} {current.dewpoint_2m.unit}",
        # Translators: the high and low ends of the humidity, UV index and pressure gauges
        text_up=C_("level gauge", "High"),
        text_low=C_("level gauge", "Low"),
        visual=gauge,
    ).card


def pressure_card(current) -> Gtk.Widget:
    """Sea-level pressure, with a tick gauge centred on standard pressure."""
    value = _number(current.pressure_msl.data)
    gauge = None
    if value is not None:
        if settings.unit == "imperial":
            value /= HPA_TO_INHG
        # 0.5 is best, 0 and 1 the extremes
        level = 0.5 + (value - PRESSURE_GAUGE_CENTER) / (2 * PRESSURE_GAUGE_SPAN)
        gauge = _pressure_gauge(DrawTickGauge(level).widget)
    return CardSquare(
        title=_("Pressure"),
        main_val=int(current.pressure_msl.data),
        main_val_unit=current.pressure_msl.unit,
        desc=current.pressure_msl.level_str,
        visual_below=gauge,
    ).card


def uv_card(current) -> Gtk.Widget:
    """The UV index, with a level gauge (assuming 12 at most)."""
    value = _number(current.uv_index.data)
    gauge = None
    if value is not None:
        # In a bright violet-blue (#5c66ff)
        gauge = DrawLevelBar(value / 12.0, height=LEVEL_BAR_HEIGHT, rgb_color=(0.36, 0.40, 1.0)).widget
    return CardSquare(
        title=_("UV Index"),
        main_val=current.uv_index.data,
        main_val_unit="",
        desc=current.uv_index.level_str,
        text_up=C_("level gauge", "High"),
        text_low=C_("level gauge", "Low"),
        visual=gauge,
    ).card


def _pressure_gauge(gauge: Gtk.Widget) -> Gtk.Widget:
    """The horizontal tick gauge, full width under the text, with "Low" and
    "High" under its two ends."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    gauge.set_margin_top(8)
    box.append(gauge)
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    for text, halign in ((C_("level gauge", "Low"), Gtk.Align.START),
                         (C_("level gauge", "High"), Gtk.Align.END)):
        label = Gtk.Label(label=text)
        label.set_css_classes(CSS_TEXT_GAUGE_END)
        label.set_halign(halign)
        label.set_hexpand(True)
        row.append(label)
    box.append(row)
    return box
