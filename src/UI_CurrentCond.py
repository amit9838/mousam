import gi
from gi.repository import Gtk
from .CORE_Icons import icons, condition
from .settings import settings
from .CORE_Helpers import JsonProcessor
from gettext import gettext as _, pgettext as C_


gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")


class CurrentCondition(Gtk.Grid):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_hexpand(True)
        # self.set_halign(Gtk.Align.FILL)
        # self.set_css_classes(['cond_grid'])
        self.paint_ui()

    def paint_ui(self):
        from .CORE_weatherData import weather_manager
        data = weather_manager.current_weather

        # ========== left section ===========
        box_left = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            hexpand=True,
            halign=Gtk.Align.START,
            margin_top=10,
        )
        self.attach(box_left, 0, 0, 1, 1)

        condition_grid = Gtk.Grid()
        box_left.append(condition_grid)

        # condition icon
        weather_code = data.weathercode.data
        condition_icon = icons[str(weather_code)]
        if data.is_day.data == 0:
            condition_icon = icons[str(weather_code) + "n"]

        icon_main = Gtk.Image().new_from_file(condition_icon)
        icon_main.set_hexpand(True)
        icon_main.set_pixel_size(90)
        condition_grid.attach(icon_main, 0, 0, 1, 2)

        # Condition label
        cond_label = Gtk.Label(
            label=condition[str(data.weathercode.data)],
            halign=Gtk.Align.START,
            valign=Gtk.Align.END,
        )
        cond_label.set_css_classes(["text-2xl", "opacity-75", "font-semibold"])
        condition_grid.attach(cond_label, 1, 0, 1, 1)

        # Condition temperature
        main_temp_label = Gtk.Label(
            label="{0:.0f} {1}".format(
                data.temperature_2m.data, data.temperature_2m.unit
            ),
            halign=Gtk.Align.START,
            valign=Gtk.Align.START,
        )
        main_temp_label.set_css_classes(["text-6xl", "font-bold"])
        condition_grid.attach(main_temp_label, 1, 1, 1, 1)

        # ========== right  section ==========
        box_right = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, margin_top=16, margin_end=5
        )
        self.attach(box_right, 1, 0, 1, 1)

        city_list_json = JsonProcessor.str_list_to_json(settings.added_cities)

        self.selected_city_index = self._get_selected_city(
            settings.selected_city, city_list_json
        )

        city_info = city_list_json[self.selected_city_index]

        box_label = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_bottom=10)
        box_right.append(box_label)

        loc_label_city = Gtk.Label(
            label=city_info.get("name"), halign=Gtk.Align.END, margin_bottom=1
        )
        loc_label_city.set_css_classes(["text-2xl", "font-semibold"])
        box_label.append(loc_label_city)

        loc_label_country = Gtk.Label(
            label=city_info.get("country"), valign=Gtk.Align.END, halign=Gtk.Align.END
        )
        loc_label_country.set_css_classes(["text-lg", "opacity-80"])
        box_label.append(loc_label_country)

        feels_like_label = Gtk.Label(halign=Gtk.Align.END, margin_bottom=5)
        markup_text = _("Feels like • <b> {0} {1}</b>").format(
            data.apparent_temperature.data, data.apparent_temperature.unit
        )
        feels_like_label.set_markup(markup_text)
        feels_like_label.set_css_classes(["text-base", "font-medium"])
        box_right.append(feels_like_label)

        # visibility_label = Gtk.Label(halign=Gtk.Align.END, margin_bottom=5)
        # markup_text = "Visibility • <b> {0:.1f} {1}</b>".format(
        #     data.visibility.get("data"), data.visibility.get("unit")
        # )
        # visibility_label.set_markup(markup_text)
        # visibility_label.set_css_classes(["text-4", "bold-3"])
        # box_right.append(visibility_label)

    def _get_selected_city(self, selected_city, cities):
        for i, city in enumerate(cities):
            if selected_city == f"{city.get("latitude")},{city.get("longitude")}":
                return i
        return 0
