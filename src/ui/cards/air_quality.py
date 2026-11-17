import gi

from gi.repository import Gtk
from gettext import gettext as _

from ..drawing.pollution_bar import PollutionBar
from ...services.settings import settings
from ...core.levels import classify_aqi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

class CardAirPollution:
    """The US AQI now, its level and a bar, with a button to the details.

    Takes the air-quality model; its current_us_aqi is this hour's value.
    Without one (None: the air quality couldn't be fetched), it says so.
    """

    def __init__(self, air):
        self.card = self._build_card(air.current_us_aqi if air is not None else None)

    def _build_card(self, aqi) -> Gtk.Widget:
        card = Gtk.Grid(margin_top=6, margin_start=3)
        card.halign = Gtk.Align.FILL
        card.set_row_spacing(5)
        card.set_css_classes(["view", "card"])
        if settings.is_using_dynamic_bg:
            card.add_css_class("bg-dark-overlay")

        # Main title of the card
        title = Gtk.Label(label=_("Air Pollution"))
        title.set_hexpand(True)
        title.set_halign(Gtk.Align.START)
        title.set_css_classes(["text-lg", "opacity-80", "font-medium"])
        card.attach(title, 0, 0, 4, 2)

        if aqi is None:
            card.attach(self._unavailable_label(), 0, 2, 4, 2)
            return card

        # Opens the air quality details (the window's "air-quality" action)
        info_button = Gtk.Button(icon_name="info-outline-symbolic", action_name="win.air-quality")
        info_button.set_halign(Gtk.Align.END)
        info_button.set_valign(Gtk.Align.START)
        info_button.set_css_classes(["flat", "circular", "opacity-75"])
        info_button.set_tooltip_text(_("Air Quality Details"))
        card.attach(info_button, 3, 0, 1, 2)

        # Main value (like windspeed = 32km/h)
        info_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, hexpand=True, halign=Gtk.Align.START
        )
        card.attach(info_box, 0, 2, 4, 2)
        info_box.set_margin_start(10)
        info_box.set_margin_top(5)

        main_val = Gtk.Label(label=str(aqi))
        main_val.set_css_classes(["text-5xl", "font-medium"])
        main_val.set_halign(Gtk.Align.START)
        main_val.set_halign(Gtk.Align.END)
        main_val.set_margin_end(10)
        info_box.append(main_val)

        desc = Gtk.Label(label=classify_aqi(aqi))
        desc.set_css_classes(["text-xl", "opacity-90", "font-semibold"])
        desc.set_margin_bottom(7)
        desc.set_valign(Gtk.Align.END)
        desc.set_halign(Gtk.Align.START)
        info_box.append(desc)

        # Pollution bar
        bar_level = aqi / 350
        pollution_bar = PollutionBar(min(bar_level, 0.99))
        # pollution_bar.set_margin_top()
        card.attach(pollution_bar, 0, 4, 4, 1)
        return card

    @staticmethod
    def _unavailable_label() -> Gtk.Label:
        label = Gtk.Label(label=_("Air quality isn't available right now."))
        label.set_css_classes(["text-base", "opacity-80"])
        label.set_wrap(True)
        label.set_xalign(0)
        label.set_margin_start(10)
        label.set_margin_end(10)
        label.set_margin_top(15)
        label.set_margin_bottom(15)
        return label
