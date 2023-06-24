import gi
import json
import datetime
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk,Gio,GLib

from .constants import icons,bg_css
from .units import  measurements,get_measurement_type

def current_weather(main_window,upper_row,data):
    global g_main_window,selected_city,settings,added_cities,cities,use_gradient

    settings = Gio.Settings.new("io.github.amit9838.weather")
    selected_city = int(str(settings.get_value('selected-city')))
    added_cities = list(settings.get_value('added-cities'))
    cities = [f"{x.split(',')[0]},{x.split(',')[1]}" for x in added_cities]
    settings.set_value("updated-at",GLib.Variant("s",str(datetime.datetime.now())))
    measurement_type = get_measurement_type()

    g_main_window = main_window
    use_gradient = settings.get_boolean('use-gradient-bg')

    # Add a grid in upper row to place left and right section
    condition_grid = Gtk.Grid()
    condition_grid.set_row_spacing(10)
    condition_grid.set_column_spacing(10)
    condition_grid.set_halign(Gtk.Align.CENTER)
    condition_grid.set_margin_top(10)
    condition_grid.set_hexpand(True)
    upper_row.append(condition_grid)

    left_section = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    left_section.set_size_request(500,100)
    condition_grid.attach(left_section, 0, 1, 1, 1)

    # Main info box, contains weather icon, temp info
    info_box_main = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.CENTER)
    info_box_main.set_margin_start(10)
    left_section.append(info_box_main)

    icon_box_main = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    icon_box_main.set_size_request(92, 92)
    info_box_main.append(icon_box_main)

    icon_main = Gtk.Image()
    icon_main.set_from_icon_name(icons.get(data['weather'][0]['icon']))  # Set the icon name and size
    icon_main.set_pixel_size(92)
    icon_box_main.append(icon_main)
    
    if use_gradient: 
        main_window.set_css_classes(['main_window',bg_css.get(data['weather'][0]['icon'])])

    # Condition box contains weather type (cloudy, rain), temps,feels like, min-max temp
    cond_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    cond_box.set_margin_start(20)
    info_box_main.append(cond_box)

    condition_label = Gtk.Label(label=data['weather'][0]['description'].capitalize())
    condition_label.set_margin_start(5)
    condition_label.set_halign(Gtk.Align.START)
    condition_label.set_css_classes(['condition_label'])
    cond_box.append(condition_label)

    # Temp box contains temp,feels like, min-max temp
    temp_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    cond_box.append(temp_box)

    temp_box_l = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    temp_box.append(temp_box_l)

    temp_label = Gtk.Label(label=f"{data['main']['temp']:.0f}{measurements[measurement_type]['temp_unit']}")
    temp_label.set_halign(Gtk.Align.START)
    temp_label.set_css_classes(['temp_label'])
    temp_box_l.append(temp_label)

    feels_like_label = Gtk.Label(label=_(f"Feels like {data['main']['feels_like']:.1f}{measurements[measurement_type]['temp_unit']}"))
    feels_like_label.set_margin_start(5)
    feels_like_label.set_halign(Gtk.Align.START)
    temp_box_l.append(feels_like_label)

    temp_box_r = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    temp_box_r.set_margin_start(10)
    temp_box.append(temp_box_r)

    temp_max_label = Gtk.Label(label = f"↑ {data['main']['temp_max']:.1f}°")
    temp_min_label = Gtk.Label(label = f"↓ {data['main']['temp_min']:.1f}°")
    temp_max_label.set_margin_top(10)
    temp_max_label.set_margin_bottom(30)
    temp_box_r.append(temp_max_label)
    temp_box_r.append(temp_min_label)


    right_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    right_section.set_size_request(300,100)

    right_section.set_css_classes(['right_section'])

    box_city = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    box_city.set_margin_bottom(5)

    list_store = Gtk.ListStore(str)
    for city in cities:
        list_store.append([city])

    combo_box = Gtk.ComboBox.new_with_model(list_store)
    combo_box.connect("changed", switch_location)
    combo_box.set_model(list_store)
    renderer_text = Gtk.CellRendererText()
    combo_box.pack_start(renderer_text, True)
    combo_box.add_attribute(renderer_text, "text", 0)

    combo_box.set_active(selected_city)  #
    box_city.append(combo_box)

    weather_data = []

    # sunrise_time = datetime.datetime.fromtimestamp(data['sys']['sunrise'])
    # sunset_time = datetime.datetime.fromtimestamp(data['sys']['sunset'])

    weather_data.append([_("Humidity"), _("{0}%").format(data['main']['humidity'])])
    weather_data.append([_("Pressure"), _("{0} hPa").format(data['main']['pressure'])])
    weather_data.append([_("Wind speed"), _("{0:.1f} {1} {2}").format(data['wind']['speed']*measurements[measurement_type]['speed_mul'],measurements[measurement_type]['speed_unit'],wind_dir(data['wind']['deg']))])
    weather_data.append([_("Visibility"), f"{data['visibility']*measurements[measurement_type]['dist_mul']:.1f} {measurements[measurement_type]['dist_unit']}"])
    # weather_data.append(["Sunrise", f"{sunrise_time.hour}:{sunrise_time.minute} AM"])
    # weather_data.append(["Sunset", f"{sunset_time.hour-12}:{sunset_time.minute} PM"])

    label_grid = Gtk.Grid()
    label_grid.set_row_spacing(2)
    label_grid.set_column_spacing(10)
    for i,disc in enumerate(weather_data):
        key_label = Gtk.Label(label=disc[0])
        disc_label = Gtk.Label(label = disc[1])
        key_label.set_halign(Gtk.Align.START)
        disc_label.set_halign(Gtk.Align.START)
        key_label.set_css_classes(['secondary'])
        disc_label.set_css_classes(['bold','secondary-light'])
        label_grid.attach(key_label,0,i,1,1)
        label_grid.attach(disc_label,1,i,1,1)

    right_section.append(box_city)
    right_section.append(label_grid)
    condition_grid.attach(right_section, 1, 1, 1, 1)

def on_city_combo_changed(combo):
    global cities,selected_city,g_main_window
    tree_iter = combo.get_active_iter()
    s_city = cities[selected_city]

    if tree_iter is not None:
        model = combo.get_model()
        city = model[tree_iter][0]
        if s_city != city:
            selected_city = cities.index(city)
            settings.set_value("selected-city",GLib.Variant("i",selected_city))
            g_main_window.refresh_weather(g_main_window,ignore=False)


def switch_location(combo):
    GLib.idle_add(on_city_combo_changed,combo)

# converts wind degrees to direction 
def wind_dir(angle):
        directions = [
            _("N"), _("NNE"), _("NE"), _("ENE"), _("E"), _("ESE"), _("SE"), _("SSE"),
            _("S"), _("SSW"), _("SW"), _("WSW"), _("W"), _("WNW"), _("NW"), _("NNW"),
        ]
        index = round(angle / (360.0 / len(directions))) % len(directions)
        return directions[index]

