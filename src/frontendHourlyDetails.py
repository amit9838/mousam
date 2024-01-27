import datetime
import random
import time
import gi
from gettext import gettext as _
from gi.repository import Gtk
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from .constants import icons, icon_loc
from .frontendUiDrawImageIcon import DrawImage
from .frontendUiDrawbarLine import DrawBar

icon_loc += "arrow.svg"


class HourlyDetails(Gtk.Grid):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_hexpand(True)
        self.set_css_classes(["view", "card", "custom_card"])
        self.set_margin_top(20)
        self.set_margin_start(5)
        self.paint_ui()
        self.daily_forecast = None

    def paint_ui(self):
        # Hourly Stack
        self.hourly_stack = Gtk.Stack.new()
        self.hourly_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.attach(self.hourly_stack, 0, 1, 1, 1)

        # Tab Box
        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True)
        self.attach(tab_box, 0, 0, 1, 1)

        style_buttons_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            halign=Gtk.Align.START,
            margin_start=2,
        )
        style_buttons_box.add_css_class("linked")
        style_buttons_box.set_valign(Gtk.Align.CENTER)

        # Temperature Button -------------
        temp_btn = Gtk.ToggleButton.new_with_label(_("Hourly"))
        temp_btn.set_css_classes(["pill", "btn_sm"])
        temp_btn.do_clicked(temp_btn)
        style_buttons_box.append(temp_btn)
        temp_btn.connect("clicked", self._on_btn_clicked, "hourly")

        # Wind Button -------------
        wind_btn = Gtk.ToggleButton.new_with_label(_("Wind"))
        wind_btn.set_css_classes(["pill", "btn_sm"])
        wind_btn.set_group(temp_btn)
        style_buttons_box.append(wind_btn)
        wind_btn.connect("clicked", self._on_btn_clicked, "wind")

        # Precipitation Button -------------
        prec_btn = Gtk.ToggleButton.new_with_label(_("Precipitation"))
        prec_btn.set_css_classes(["pill", "btn_sm"])
        prec_btn.set_group(temp_btn)
        style_buttons_box.append(prec_btn)
        prec_btn.connect("clicked", self._on_btn_clicked, "prec")

        tab_box.append(style_buttons_box)
        self.create_stack_page("hourly")

    def _on_btn_clicked(self, widget, page_name):
        if self.hourly_stack.get_child_by_name(page_name):
            self.hourly_stack.set_visible_child_name(page_name)
            return

        self.create_stack_page(page_name)

    # ---------- Create page stack --------------
    def create_stack_page(self, page_name):
        from .weatherData import daily_forecast_data as daily_data
        from .weatherData import hourly_forecast_data as hourly_data

        page_grid = Gtk.Grid()
        self.hourly_stack.add_named(page_grid, page_name)
        self.hourly_stack.set_visible_child_name(page_name)

        info_grid = Gtk.Grid(margin_start=20, margin_top=10)
        page_grid.attach(info_grid, 0, 1, 1, 1)

        desc_label = Gtk.Label(label="Day High", halign=Gtk.Align.START)
        desc_label.set_css_classes(["text-4", "light-2", "bold-2"])
        info_grid.attach(desc_label, 0, 0, 3, 1)

        val_label = Gtk.Label(label=str(max(hourly_data.windspeed_10m.get("data")[:24])), halign=Gtk.Align.START)
        val_label.set_css_classes(["text-l4", "light-3", "bold-1"])
        info_grid.attach(val_label, 0, 1, 2, 2)
        unit_label = Gtk.Label(label=hourly_data.windspeed_10m.get("unit"))
        unit_label.set_css_classes(["text-5", "light-2", "bold-3"])
        info_grid.attach(unit_label, 2, 2, 1, 1)

        # Hourly Page
        if page_name == "hourly":
            desc_label.set_text("Day Max")
            val_label.set_text(
                str(max(hourly_data.temperature_2m.get("data"))) + "°"
            )
            unit_label.set_text("")

        # Precipitation page
        max_prec = max(hourly_data.precipitation.get("data")[:24])
        if page_name == "prec":
            desc_label.set_text("Day High")
            val_label.set_text(f"{max_prec:.2f}")
            unit_label.set_text(hourly_data.precipitation.get("unit"))

        scrolled_window = Gtk.ScrolledWindow(
            hexpand=True, halign=Gtk.Align.FILL, margin_top=2
        )
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        scrolled_window.set_kinetic_scrolling(True)
        page_grid.attach(scrolled_window, 0, 2, 1, 1)

        graphic_container = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            halign=Gtk.Align.FILL,
            margin_top=0,
            margin_bottom=0,
        )

        scrolled_window.set_child(graphic_container)

        nearest_current_time_idx = 0
        for i in range(len(hourly_data.time.get("data"))):
            if (abs(time.time() - hourly_data.time.get("data")[i]) // 60) < 30:
                nearest_current_time_idx = i
                break

        if page_name == "prec":
            total_sum = sum(hourly_data.precipitation.get("data")[:24])
            if total_sum == 0:
                graphic_box = Gtk.Box(
                    orientation=Gtk.Orientation.VERTICAL,
                    margin_start=3,
                    margin_end=3,
                    halign=Gtk.Align.FILL,
                    hexpand=True,
                )

                no_prec_labels = [
                    "No precipitation today !",
                    "No precipitation expected today!",
                    "Anticipate a precipitation-free day !",
                    "Enjoy a rain-free day today!",
                    "Umbrella status: resting. No precipitation in sight !",
                    "No rain in sight today!"
                ]
                no_prec_label = Gtk.Label(label=no_prec_labels[random.randint(0,len(no_prec_labels)-1)])
                no_prec_label.set_css_classes(["text-3a", "bold-3", "light-2"])
                no_prec_label.set_halign(Gtk.Align.CENTER)
                no_prec_label.set_margin_top(40)
                no_prec_label.set_margin_bottom(40)
                graphic_box.set_css_classes(["custom_card_hourly"])
                graphic_box.append(no_prec_label)
                graphic_container.append(graphic_box)
                return

        for i in range(24):
            graphic_box = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL, margin_start=4, margin_end=4
            )
            graphic_box.set_css_classes(["custom_card_hourly"])

            graphic_container.append(graphic_box)

            label_timestamp = Gtk.Label(label="")
            label_timestamp.set_css_classes(["text-6", "bold-2", "light-6"])
            tm = datetime.datetime.fromtimestamp(hourly_data.time.get("data")[i])
            tm = tm.strftime("%I:%M %p")
            label_timestamp.set_text(tm)

            if i == nearest_current_time_idx:
                label_timestamp.set_text("Now")
                label_timestamp.set_css_classes(["bold-1"])
                graphic_box.set_css_classes(["custom_card_hourly","custom_card_hourly_now"])


            graphic_box.append(label_timestamp)

            icon_box = Gtk.Box(halign=Gtk.Align.CENTER)
            graphic_box.append(icon_box)

            label_val = Gtk.Label(label="")
            label_val.set_css_classes(["text-4", "bold-2", "light-3"])
            graphic_box.append(label_val)

            if page_name == "wind":
                label_val.set_text(str(hourly_data.windspeed_10m.get("data")[i]))
                label_val.set_margin_top(10)

                img = DrawImage(
                    icon_loc,
                    hourly_data.wind_direction_10m.get("data")[i] + 180,
                    30,
                    30,
                )

                icon_box.set_margin_top(10)
                icon_box.append(img.img_box)

            elif page_name == "hourly":
                label_val.set_text(
                    str(hourly_data.temperature_2m.get("data")[i]) + "°"
                )
                label_timestamp.set_margin_bottom(5)

                weather_code = hourly_data.weathercode.get("data")[i]
                condition_icon = icons[str(weather_code)]

                # if it is night
                if hourly_data.is_day.get("data")[i] == 0:
                    condition_icon = icons[str(weather_code) + "n"]

                icon_main = Gtk.Image().new_from_file(condition_icon)
                icon_main.set_hexpand(True)
                icon_main.set_pixel_size(50)
                icon_box.set_margin_bottom(10)
                icon_box.append(icon_main)

            elif page_name == "prec":
                bar_obj = None
                if max_prec == 0:
                    bar_obj = DrawBar(0)
                else:
                    bar_obj = DrawBar(
                        hourly_data.precipitation.get("data")[i] / max_prec
                    )
                icon_box.append(bar_obj.dw)
                prec = hourly_data.precipitation.get("data")[i]
                if prec > 0:
                    label_val.set_text("{:.1f}".format(prec))
                else:
                    label_val.set_text("0")

                label_val.set_margin_top(0)
