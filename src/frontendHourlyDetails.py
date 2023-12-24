import gi
import random
import datetime

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw
from gettext import gettext as _
from .frontendUiDrawImageIcon import DrawImage
from .frontendUiDrawbarLine import DrawBar

image_path = "/home/amit/Drive-D/weather/src/frontend/ui/arrowA.png"  # Replace with the path to your image file


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
        self.hourly_stack = Gtk.Stack.new()
        self.hourly_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.attach(self.hourly_stack, 0, 1, 1, 1)

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
        temp_btn.set_css_classes(["pilal", "btn_sm"])
        temp_btn.do_clicked(temp_btn)
        style_buttons_box.append(temp_btn)
        temp_btn.connect("clicked", self._on_hourly_btn_clicked)

        # Wind Button -------------
        wind_btn = Gtk.ToggleButton.new_with_label(_("Wind"))
        wind_btn.set_css_classes(["pill", "btn_sm"])
        wind_btn.set_group(temp_btn)
        style_buttons_box.append(wind_btn)
        wind_btn.connect("clicked", self._on_wind_btn_clicked)

        # Precipitation Button -------------
        prec_btn = Gtk.ToggleButton.new_with_label(_("Precipitation"))
        prec_btn.set_css_classes(["pilla", "btn_sm"])
        prec_btn.set_group(temp_btn)
        style_buttons_box.append(prec_btn)
        prec_btn.connect("clicked", self._on_prec_btn_clicked)
        # prec_btn.connect('clicked',_on_prec_btn_forecast_btn_clicked,None,forecast_stack)

        tab_box.append(style_buttons_box)
        self.page_stacks("hourly")

    def _on_hourly_btn_clicked(self, widget):
        page_name = "hourly"
        if self.hourly_stack.get_child_by_name(page_name):
            self.hourly_stack.set_visible_child_name(page_name)
            return
        self.page_stacks("hourly")

    def _on_wind_btn_clicked(self, widget):
        page_name = "wind"
        if self.hourly_stack.get_child_by_name(page_name):
            self.hourly_stack.set_visible_child_name(page_name)
            return
        self.page_stacks("wind")

    def _on_prec_btn_clicked(self, widget):
        page_name = "prec"
        if self.hourly_stack.get_child_by_name(page_name):
            self.hourly_stack.set_visible_child_name(page_name)
            return
        self.page_stacks("prec")
        # self.show_loader()

    def show_loader(self):
        page_name = "loader"
        if self.hourly_stack.get_child_by_name(page_name):
            self.hourly_stack.set_visible_child_name(page_name)
            return
        container_loader = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container_loader.set_margin_top(80)
        loader = Gtk.Spinner()
        loader.set_css_classes(["loader"])
        loader.start()
        container_loader.append(loader)
        self.hourly_stack.add_named(container_loader, "loader")
        self.hourly_stack.set_visible_child_name(page_name)

    # ---------- Create page stack --------------
    def page_stacks(self, page_name):
        from .weatherData import daily_forecast_data as daily_data
        from .weatherData import hourly_forecast_data as hourly_data

        # self.daily_forecast = d
        # print("adding page",page_name)
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

        if page_name == "hourly":
            desc_label.set_text("Day Max")
            val_label.set_text(str(max(daily_data["daily"]["temperature_2m_max"])))
            unit_label.set_text("")

        if page_name == "prec":
            desc_label.set_text("Day High")
            val_label.set_text(
                str(max(daily_data["daily"]["precipitation_probability_max"]))
            )
            unit_label.set_text("cm")

        width, height = 35, 35

        scrolled_window = Gtk.ScrolledWindow(hexpand=True, halign=Gtk.Align.FILL)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        # scrolled_window.set_min_content_height(200)
        scrolled_window.set_margin_bottom(0)
        scrolled_window.set_margin_top(2)
        scrolled_window.set_kinetic_scrolling(True)
        # scrolled_window.set_size_request(800,190)
        page_grid.attach(scrolled_window, 0, 2, 1, 1)

        graphic_container = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            halign=Gtk.Align.START,
            margin_top=5,
            margin_bottom=0,
        )
        scrolled_window.set_child(graphic_container)


        for i in range(24):
            graphic_box = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL, margin_start=10, margin_end=10
            )
            graphic_container.append(graphic_box)

            icon_box = Gtk.Box()
            graphic_box.append(icon_box)

            label_top = Gtk.Label(label="")
            label_top.set_css_classes(["text-4", "bold-2", "light-3"])
            graphic_box.append(label_top)

            label_bottom = Gtk.Label(label="")
            label_bottom.set_css_classes(["text-6", "bold-2", "light-6"])
            graphic_box.append(label_bottom)

            if page_name == "wind":
                label_top.set_text(str(hourly_data["hourly"]["windspeed_10m"][i]))
                label_top.set_margin_top(5)
                tm = datetime.datetime.fromtimestamp(hourly_data["hourly"]["time"][i])
                tm = tm.strftime("%I:%M %p")
                label_bottom.set_text(tm)
                label_bottom.set_margin_top(5)

                img = DrawImage(
                    image_path,
                    hourly_data["hourly"]["wind_direction_10m"][i] + 180,
                    width,
                    height,
                )
                icon_box.set_margin_top(10)
                icon_box.append(img.img_box)

            elif page_name == "hourly":
                label_top.set_text(str(hourly_data["hourly"]["temperature_2m"][i]))
                label_top.set_margin_top(5)
                tm = datetime.datetime.fromtimestamp(hourly_data["hourly"]["time"][i])
                tm = tm.strftime("%I:%M %p")
                label_bottom.set_margin_top(5)
                label_bottom.set_text(tm)

                img = DrawImage(
                    image_path,
                    hourly_data["hourly"]["wind_direction_10m"][i],
                    width,
                    height,
                )
                icon_box.set_margin_top(10)
                icon_box.append(img.img_box)

            elif page_name == "prec":
                tm = datetime.datetime.fromtimestamp(hourly_data["hourly"]["time"][i])
                tm = tm.strftime("%I:%M %p")
                label_bottom.set_text(tm)
                label_bottom.set_margin_top(5)

                random_number = random.random()
                random_number = int(random_number * 10) / 10

                label_top.set_text(str(random_number))
                label_top.set_margin_top(5)
                # print(i,"-> ",random_number)
                bar_obj = DrawBar(random_number)
                icon_box.append(bar_obj.dw)
