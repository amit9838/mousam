from gi.repository import Gtk, Gio
from .constants import icons
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')


class CurrentCondition(Gtk.Grid):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_hexpand(True)
        # self.set_css_classes(['cond_grid'])
        self.paint_ui()

    def paint_ui(self):
        from .weatherData import current_weather_data as data

        # ========== left section ===========
        box_left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True,
                           halign=Gtk.Align.START, margin_top=40)
        self.attach(box_left, 0, 0, 1, 1)

        condition_grid = Gtk.Grid()
        box_left.append(condition_grid)

        # condition icon
        weather_code = data.weathercode.get("data")
        condition_icon = icons[str(weather_code)]
        if data.is_day.get("data") == 0:
            condition_icon = icons[str(weather_code)+'n']

        icon_main = Gtk.Image().new_from_file(condition_icon)
        icon_main.set_hexpand(True)
        icon_main.set_pixel_size(140)
        condition_grid.attach(icon_main, 0, 0, 1, 2)

        # Condition label
        cond_label = Gtk.Label(
            label="Clear Sky", halign=Gtk.Align.START, valign=Gtk.Align.END)
        cond_label.set_css_classes(['text-1', 'light-4', 'bold-2'])
        condition_grid.attach(cond_label, 1, 0, 1, 1)

        # Condition temperature
        main_temp_label = Gtk.Label(label="{0:.0f}°C".format(data.temperature_2m.get(
            "data")), halign=Gtk.Align.START, valign=Gtk.Align.START)
        main_temp_label.set_css_classes(['main_temp_label', 'bold-1'])
        condition_grid.attach(main_temp_label, 1, 1, 1, 1)

        # ========== right  section ==========
        box_right = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, margin_top=30, margin_end=5)
        self.attach(box_right, 1, 0, 1, 1)

        loc_label = Gtk.Label(label="Delhi,India",
                              halign=Gtk.Align.END, margin_bottom=20)
        loc_label.set_css_classes(['text-2b', 'bold-2'])
        box_right.append(loc_label)

        feels_like_label = Gtk.Label(halign=Gtk.Align.END, margin_bottom=5)
        markup_text = "Feels Like • <b> {0}°C</b>".format(
            data.apparent_temperature.get("data"))
        feels_like_label.set_markup(markup_text)
        feels_like_label.set_css_classes(['text-4', 'bold-3'])
        box_right.append(feels_like_label)
