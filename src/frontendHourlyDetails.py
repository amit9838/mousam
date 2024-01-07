from gi.repository import Gtk
import gi
import random
import datetime
from gettext import gettext as _

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from .frontendUiDrawbarLine import DrawBar
from .frontendUiDrawImageIcon import DrawImage
from .constants import icons, icon_loc
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
        self.hourly_stack.set_transition_type(
            Gtk.StackTransitionType.CROSSFADE)
        self.attach(self.hourly_stack, 0, 1, 1, 1)

        # Tab Box
        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True)
        self.attach(tab_box, 0, 0, 1, 1)
        
        style_buttons_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, halign=Gtk.Align.START
        )
        style_buttons_box.add_css_class("linked")
        style_buttons_box.set_margin_start(2)
        style_buttons_box.set_valign(Gtk.Align.CENTER)

        # Temperature Button -------------
        temp_btn = Gtk.ToggleButton.new_with_label(_("Hourly"))
        temp_btn.set_css_classes(["pill", "btn_sm"])
        temp_btn.do_clicked(temp_btn)
        style_buttons_box.append(temp_btn)
        temp_btn.connect("clicked",self._on_btn_clicked,"hourly")

        # Wind Button -------------
        wind_btn = Gtk.ToggleButton.new_with_label(_("Wind"))
        wind_btn.set_css_classes(["pill", "btn_sm"])
        wind_btn.set_group(temp_btn)
        style_buttons_box.append(wind_btn)
        wind_btn.connect("clicked",self._on_btn_clicked,"wind" )

        # Precipitation Button -------------
        prec_btn = Gtk.ToggleButton.new_with_label(_("Precipitation"))
        prec_btn.set_css_classes(["pill", "btn_sm"])
        prec_btn.set_group(temp_btn)
        style_buttons_box.append(prec_btn)
        prec_btn.connect("clicked", self._on_btn_clicked,"prec")

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

        info_grid = Gtk.Grid(margin_start=20, margin_top=15)
        page_grid.attach(info_grid, 0, 1, 1, 1)

        desc_label = Gtk.Label(label="Day High", halign=Gtk.Align.START)
        desc_label.set_css_classes(["text-4", "light-2", "bold-2"])
        info_grid.attach(desc_label, 0, 0, 3, 1)

        val_label = Gtk.Label(label="18", halign=Gtk.Align.START)
        val_label.set_css_classes(["text-l4", "light-3", "bold-1"])
        info_grid.attach(val_label, 0, 1, 2, 2)
        unit_label = Gtk.Label(label="km/h")
        unit_label.set_css_classes(["text-5", "light-2", "bold-3"])
        info_grid.attach(unit_label, 2, 2, 1, 1)

        # Hourly Page
        if page_name == "hourly":
            desc_label.set_text("Day Max")
            val_label.set_text(str(max(daily_data.temperature_2m_max.get("data")))+"°")
            unit_label.set_text("")

        # Precipitation page
        max_prec = max(hourly_data.precipitation.get("data"))
        max_prec = max(max_prec,1)
        if page_name == "prec":
            desc_label.set_text("Day High")
            val_label.set_text(f"{max_prec:.2f}")
            unit_label.set_text(hourly_data.precipitation.get('unit'))


        scrolled_window = Gtk.ScrolledWindow(hexpand=True, halign=Gtk.Align.FILL)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        scrolled_window.set_margin_bottom(0)
        scrolled_window.set_margin_top(2)
        scrolled_window.set_kinetic_scrolling(True)
        page_grid.attach(scrolled_window, 0, 2, 1, 1)

        graphic_container = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL,
                halign=Gtk.Align.START,
                margin_top=5,
                margin_bottom=0,
            )
        scrolled_window.set_child(graphic_container)

        for i in range(24):
            graphic_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_start=5, margin_end=5)
            graphic_container.append(graphic_box)

            icon_box = Gtk.Box(halign=Gtk.Align.CENTER)
            graphic_box.append(icon_box)

            label_top = Gtk.Label(label="")
            label_top.set_css_classes(["text-4", "bold-2", "light-3"])
            graphic_box.append(label_top)

            label_bottom = Gtk.Label(label="")
            label_bottom.set_css_classes(["text-6", "bold-2", "light-6"])
            graphic_box.append(label_bottom)

            if page_name == "wind":
                label_top.set_text(
                    str(hourly_data.windspeed_10m.get("data")[i]))
                label_top.set_margin_top(15)
                tm = datetime.datetime.fromtimestamp(
                    hourly_data.time.get("data")[i])
                tm = tm.strftime("%I:%M %p")
                label_bottom.set_text(tm)
                label_bottom.set_margin_top(5)

                img = DrawImage(icon_loc,hourly_data.wind_direction_10m.get("data")[i] + 180,30,30,)

                icon_box.set_margin_top(10)
                icon_box.append(img.img_box)

            elif page_name == "hourly":
                label_top.set_text(str(hourly_data.temperature_2m.get("data")[i])+"°")
                label_top.set_margin_top(5)
                tm = datetime.datetime.fromtimestamp(
                    hourly_data.time.get("data")[i])
                tm = tm.strftime("%I:%M %p")
                label_bottom.set_margin_top(5)
                label_bottom.set_text(tm)

                weather_code = hourly_data.weathercode.get("data")[i]
                condition_icon = icons[str(weather_code)]

                # if it is night
                if hourly_data.is_day.get("data")[i] == 0:
                    condition_icon = icons[str(weather_code)+'n'] 

                icon_main = Gtk.Image().new_from_file(condition_icon)
                icon_main.set_hexpand(True)
                icon_main.set_pixel_size(50)
                icon_box.set_margin_bottom(10)
                icon_box.append(icon_main)

            elif page_name == "prec":
                tm = datetime.datetime.fromtimestamp(
                    hourly_data.time.get("data")[i])
                tm = tm.strftime("%I:%M %p")
                label_bottom.set_text(tm)
                label_bottom.set_margin_top(5)
                label_top.set_text("{:.2f}".format(hourly_data.precipitation.get("data")[i]/max_prec))
                label_top.set_margin_top(5)
                bar_obj = DrawBar(hourly_data.precipitation.get("data")[i])
                icon_box.append(bar_obj.dw)
