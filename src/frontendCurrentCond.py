import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk
from .weatherData import fetch_current_weather

class CurrentCondition(Gtk.Grid):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_hexpand(True)
        # self.set_css_classes(['cond_grid'])
        self.paint_ui()

    def paint_ui(self):
        from .weatherData import current_weather_data as data

        box_left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, halign=Gtk.Align.START,margin_start=5,margin_top=40)
        self.attach(box_left,0,0,1,1)

        cond_label = Gtk.Label(label = "Clear Sky",halign=Gtk.Align.START)
        cond_label.set_css_classes(['text-1','light-4','bold-2'])
        box_left.append(cond_label)

        main_temp_label = Gtk.Label(label = "{0:.0f}°C".format(data.temperature_2m.get("data")),halign=Gtk.Align.START)
        main_temp_label.set_css_classes(['main_temp_label','bold-1'])
        box_left.append(main_temp_label)

        box_right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=30,margin_end=5)
        self.attach(box_right,1,0,1,1)
        
        loc_label = Gtk.Label(label = "Delhi,India",halign=Gtk.Align.END,margin_bottom=20)
        loc_label.set_css_classes(['text-2b','bold-2'])
        box_right.append(loc_label)
        
        feels_like_label = Gtk.Label(halign=Gtk.Align.END,margin_bottom=5)
        # feels_like_label.use_markup(True)
        markup_text = "Feels Like • <b>{0}°C</b>".format(data.apparent_temperature.get("data"))
        feels_like_label.set_markup(markup_text)
        feels_like_label.set_css_classes(['text-4','bold-3'])
        box_right.append(feels_like_label)

        # feels_temp_value = Gtk.Label(label = "{0}°C".format(data['current']['apparent_temperature']),halign=Gtk.Align.END)
        # feels_temp_value.set_css_classes(['text-5','bold-3'])
        # box_right.append(feels_temp_value)
