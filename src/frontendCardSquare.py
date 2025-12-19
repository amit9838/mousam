import gi
from gettext import gettext as _, pgettext as C_
from typing import Optional, Union

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from .constants import icons
from .config import settings
from .frontendUiDrawBar import DrawLevelBar
from .frontendUiDrawImageIcon import DrawImage

# Standardizing CSS classes for reuse
CSS_CARD_BASE = ["view", "card", "custom_card"]
CSS_TEXT_TITLE = ["text-4", "light-3", "bold"]
CSS_TEXT_VALUE = ["text-2a", "bold"]
CSS_TEXT_UNIT = ["text-7", "light-3"]
CSS_TEXT_DESC = ["text-5", "light-2", "bold-2"]


class CardSquare:
    """
    A reusable Card component for displaying weather metrics (Wind, Humidity, etc.).
    Displays a title, main value, description, and a visual indicator (Icon or Bar).
    """

    # Static mapping for translations to avoid recreating dict on every init
    TITLES_MAP = {
        "wind": _("Wind"),
        "pressure": _("Pressure"),
        "humidity": _("Humidity"),
        "uv index": _("UV Index"),
    }

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
        visual_data: Optional[float] = None,  # Passed explicitly now
    ):
        self.title_key = title.lower()
        self.main_val = main_val
        self.main_val_unit = main_val_unit
        self.desc = desc
        self.sub_desc_heading = sub_desc_heading
        self.sub_desc = sub_desc
        self.text_up = text_up
        self.text_low = text_low

        # Data needed for the visual (Wind Degree, Pressure Value, etc.)
        # If not provided, fallback to main_val (useful for Humidity/UV)
        self.visual_data = visual_data if visual_data is not None else main_val

        # Pre-process specific logic
        if self.title_key == "pressure":
            self.main_val = int(self.main_val)

        if self.title_key == "wind" and isinstance(self.visual_data, (int, float)):
            self.sub_desc = self._get_wind_direction_str(self.visual_data)

        self.card = self._build_ui()

    def _build_ui(self) -> Gtk.Widget:
        """Constructs the UI using Box layout for better performance than Grid."""

        # 1. Main Container (Vertical Box)
        # We use a Box instead of Grid because we are just stacking Title on top of Content
        card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card_box.set_size_request(170, 100)
        card_box.set_css_classes(CSS_CARD_BASE)
        card_box.set_margin_top(6)
        card_box.set_margin_start(3)
        card_box.set_margin_end(3)

        if settings.is_using_dynamic_bg:
            card_box.add_css_class("transparent_5")

        # 2. Title Area
        display_title = self.TITLES_MAP.get(self.title_key, self.title_key.capitalize())
        lbl_title = Gtk.Label(label=display_title)
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
            sub_box.set_margin_top(4)

            if self.sub_desc_heading:
                lbl_head = Gtk.Label(label=self.sub_desc_heading)
                lbl_head.set_css_classes(["text-6", "light-1"])
                lbl_head.set_halign(Gtk.Align.START)
                sub_box.append(lbl_head)

            if self.sub_desc:
                lbl_sub = Gtk.Label(label=self.sub_desc)
                lbl_sub.set_css_classes(["text-4", "bold-2"])
                lbl_sub.set_halign(Gtk.Align.START)
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
            css = ["text-4", "bold-3"] if self.title_key == "wind" else ["title-5"]
            lbl_up.set_css_classes(css)
            visual_box.append(lbl_up)

        # The Graphic (Canvas)
        graphic_widget = self._create_visual_widget()
        if graphic_widget:
            visual_box.append(graphic_widget)

        # Lower Text
        if self.text_low:
            lbl_low = Gtk.Label(label=self.text_low)
            css = ["text-4", "bold"] if self.title_key == "wind" else ["title-5"]
            lbl_low.set_css_classes(css)
            visual_box.append(lbl_low)

        return card_box

    def _create_visual_widget(self) -> Optional[Gtk.Widget]:
        """Generates the central graphic (Arrow or Bar) based on title."""
        try:
            val = float(self.visual_data)
        except (ValueError, TypeError):
            return None

        if self.title_key == "wind":
            # Arrow Icon
            # icons['arrow'] should be a resource path or similar
            return DrawImage(icons["arrow"], val + 180, 35, 35).img_box

        elif self.title_key == "humidity":
            # Level Bar (0.0 - 1.0)
            return DrawLevelBar(
                val / 100.0, rounded_cap=True, rgb_color=[0.588, 0.937, 1]
            ).dw

        elif self.title_key == "pressure":
            # Pressure Calculation
            low, high = 872.0, 1080.0
            if settings.unit == "imperial":
                low *= 0.02953
                high *= 0.02953

            level = (val - low) / (high - low)
            return DrawLevelBar(max(0.0, min(level, 1.0)), rounded_cap=True).dw

        elif self.title_key == "uv index":
            # UV Level (Assuming Max 12)
            return DrawLevelBar(
                val / 12.0, rounded_cap=True, rgb_color=[0.408, 0.494, 1.000]
            ).dw

        return None

    def _get_wind_direction_str(self, angle: float) -> str:
        """Converts degrees to cardinal direction."""
        directions = [
            _("North"),
            _("Northeast"),
            _("East"),
            _("Southeast"),
            _("South"),
            _("Southwest"),
            _("West"),
            _("Northwest"),
            _("North"),
        ]
        index = round(angle % 360 / 45) % 8
        return directions[index]
