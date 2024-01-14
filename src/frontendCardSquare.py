from gi.repository import Gtk
import gi
from .constants import icon_loc
from .frontendUiDrawBar import *
from .frontendUiDrawImageIcon import *

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

icon_loc += "arrow.svg"


class CardSquare:
    def __init__(
        self,
        title,
        main_val,
        main_val_unit="",
        desc="",
        sub_desc_heading="",
        sub_desc="",
        text_up="",
        text_low="",
    ):
        self.title = title
        self.main_val = main_val
        self.main_val_unit = main_val_unit
        self.desc = desc
        self.sub_desc_heading = sub_desc_heading
        self.sub_desc = sub_desc
        self.text_up = text_up
        self.text_low = text_low

        from .weatherData import current_weather_data

        self.curr_w = current_weather_data
        if self.title.lower() == "wind":
            self.sub_desc = self._get_wind_dir(
                self.curr_w.winddirection_10m.get("data")
            )

        self.card = None
        self.create_card()

    def create_card(self):
        card = Gtk.Grid(
            margin_top=10,
            margin_start=5,
            margin_end=5,
            row_spacing=5,
            column_spacing=25,
        )
        card.halign = Gtk.Align.FILL
        card.set_size_request(200, 150)
        card.set_css_classes(["view", "card", "custom_card"])
        self.card = card

        # Main title of the card
        title = Gtk.Label(label=self.title)
        title.set_hexpand(True)
        title.set_halign(Gtk.Align.START)
        title.set_css_classes(["text-4", "light-3", "bold"])
        card.attach(title, 0, 0, 1, 2)

        # Info Grid: It contains - Main value,units, short description, sub description
        card_info = Gtk.Grid(margin_top=15, row_spacing=0, column_spacing=5)

        card_info.set_css_classes(["view"])
        card.attach(card_info, 0, 2, 1, 2)

        # Main value (like windspeed = 32km/h)
        self.main_val = int(self.main_val) if self.title == 'Pressure' else self.main_val
        main_val = Gtk.Label(label=self.main_val)
        main_val.set_css_classes(["text-1", "bold"])
        main_val.set_halign(Gtk.Align.START)
        card_info.attach(main_val, 0, 1, 3, 3)

        # Unit if the main value
        main_val_unit = Gtk.Label(label=self.main_val_unit)
        main_val_unit.set_css_classes(["text-5", "light-3"])
        main_val_unit.set_halign(Gtk.Align.START)
        card_info.attach(main_val_unit, 3, 3, 1, 1)

        # Short description
        desc_box = Gtk.Box()
        desc_box.set_size_request(10, 40)
        card_info.attach(desc_box, 0, 4, 6, 1)

        desc = Gtk.Label(label=self.desc)
        desc.set_css_classes(["text-5", "light-2", "bold-2"])
        desc.set_wrap(True)
        desc.set_margin_start(0)
        desc.set_halign(Gtk.Align.START)
        desc.set_valign(Gtk.Align.START)
        desc_box.append(desc)

        # Sub description heading
        sub_desc_heading = Gtk.Label(label=self.sub_desc_heading)
        sub_desc_heading.set_css_classes(["text-4", "light-1"])
        sub_desc_heading.set_halign(Gtk.Align.START)
        card_info.attach(sub_desc_heading, 0, 5, 4, 1)

        sub_desc = Gtk.Label(label=self.sub_desc)
        sub_desc.set_css_classes(["text-4", "bold-2"])
        sub_desc.set_halign(Gtk.Align.START)
        card_info.attach(sub_desc, 0, 6, 4, 1)

        card_icon = Gtk.Grid(halign=Gtk.Align.END)
        card_icon.set_margin_top(15)
        card_icon.set_css_classes(["view", "card_infao"])
        card.attach(card_icon, 1, 2, 2, 1)

        icon_upper_text = Gtk.Label(label=self.text_up)
        if self.title.lower() == "wind":
            icon_upper_text.set_css_classes(["text-4", "bold-3"])
        else:
            icon_upper_text.set_css_classes(["title-5"])

        icon_upper_text.set_halign(Gtk.Align.CENTER)
        icon_upper_text.set_margin_bottom(5)
        card_icon.attach(icon_upper_text, 0, 0, 1, 1)

        if self.title.lower() == "wind":
            obj = DrawImage(
                icon_loc, self.curr_w.winddirection_10m.get("data") + 180, 35, 35
            )

            card_icon.attach(obj.img_box, 0, 1, 1, 1)

        elif self.title.lower() == "humidity":
            level_obj = DrawLevelBar(
                self.curr_w.relativehumidity_2m.get("data") / 100,
                rounded_cap=True,
                rgb_color=[0.588, 0.937, 1],
            )
            card_icon.attach(level_obj.dw, 0, 1, 1, 1)

        elif self.title.lower() == "pressure":
            level_obj = DrawLevelBar(
                (self.curr_w.surface_pressure.get("data") - 872) / (1080 - 872),
                rounded_cap=True,
            )
            card_icon.attach(level_obj.dw, 0, 1, 1, 1)

        elif self.title.lower() == "uv index":
            level_obj = DrawLevelBar(
                self.curr_w.uv_index.get("data") / 12,
                rounded_cap=True,
                rgb_color=[0.408, 0.494, 1.000],
            )
            card_icon.attach(level_obj.dw, 0, 1, 1, 1)

        icon_bottom_text = Gtk.Label(label=self.text_low)
        if self.title.lower() == "wind":
            icon_bottom_text.set_css_classes(["text-4", "bold"])
        else:
            icon_bottom_text.set_css_classes(["title-5"])
        icon_bottom_text.set_valign(Gtk.Align.CENTER)
        card_icon.attach(icon_bottom_text, 0, 2, 1, 1)

    def _get_wind_dir(self, angle):
        directions = [
            "North",
            "Northeast",
            "East",
            "Southeast",
            "South",
            "Southwest",
            "West",
            "Northwest",
            "North",
        ]

        angle = angle % 360
        index = round(angle / 45) % 8
        return directions[index]
