import gi
from datetime import datetime
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk,Gio,GLib
from gettext import gettext as _

from .constants import icons,bg_css,air_quality_level
from .units import  measurements,get_measurement_type
from .utils import convert_to_local_time,wind_dir
from .backendCurrent_w import air_pollution

def current_weather(main_window,upper_row,data,air_pollution_data):
    global g_main_window,selected_city,settings,added_cities,cities,use_gradient
    settings = Gio.Settings.new("io.github.amit9838.weather")
    selected_city = int(str(settings.get_value('selected-city')))
    added_cities = list(settings.get_value('added-cities'))
    cities = [f"{x.split(',')[0]},{x.split(',')[1]}" for x in added_cities]
    settings.set_value("updated-at",GLib.Variant("s",str(datetime.now())))
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
    info_box_main = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,valign=Gtk.Align.START)
    info_box_main.set_margin_start(10)
    info_box_main.set_margin_top(0)
    left_section.append(info_box_main)

    icon_box_main = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    icon_box_main.set_size_request(92, 92)
    info_box_main.append(icon_box_main)

    icon_main = Gtk.Image().new_from_icon_name(icons.get(data['weather'][0]['icon']))
    icon_main.set_pixel_size(98)
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
    feels_like_label.set_halign(Gtk.Align.START)
    feels_like_label.set_margin_start(5)
    feels_like_label.set_css_classes(['secondary-light','f-mlg'])
    cond_box.append(feels_like_label)

    temp_box_r = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    temp_box_r.set_margin_start(10)
    temp_box.append(temp_box_r)

    temp_max_label = Gtk.Label(label = f"↑ {data['main']['temp_max']:.1f}°")
    temp_min_label = Gtk.Label(label = f"↓ {data['main']['temp_min']:.1f}°")
    temp_max_label.set_css_classes(['secondary-light','bold'])
    temp_min_label.set_css_classes(['secondary-light','f-xsm'])
    temp_min_label.set_halign(Gtk.Align.START)
    temp_max_label.set_margin_top(10)
    temp_min_label.set_margin_start(1)
    temp_max_label.set_margin_bottom(4)
    temp_box_r.append(temp_max_label)
    temp_box_r.append(temp_min_label)

    sun_grid = Gtk.Grid()
    sun_grid.set_row_spacing(2)
    sun_grid.set_column_spacing(0)
    sun_grid.set_margin_start(5)
    sun_grid.set_margin_top(5)
    cond_box.append(sun_grid)

    right_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    right_section.set_size_request(300,100)

    right_section.set_css_classes(['right_section'])

    box_city = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    box_city.set_margin_bottom(5)

    list_store = Gtk.ListStore(str)
    for city in cities:
        list_store.append([city])

    combo_box = Gtk.ComboBox.new_with_model(list_store)
    combo_box.connect("changed", _on_location_combo_changed)
    combo_box.set_model(list_store)
    renderer_text = Gtk.CellRendererText()
    combo_box.pack_start(renderer_text, True)
    combo_box.add_attribute(renderer_text, "text", 0)

    combo_box.set_active(selected_city)  #
    box_city.append(combo_box)

    weather_data = []

    sunrise_time = convert_to_local_time(data['sys']['sunrise'],data['timezone'] )
    sunset_time = convert_to_local_time(data['sys']['sunset'],data['timezone'] )

    sunrise_time_minute = sunrise_time.minute if len(str(sunrise_time.minute))==2 else str(sunrise_time.minute)+"0"
    sunrise_label = Gtk.Label(label=f"{sunrise_time.hour}:{sunrise_time_minute} AM")
    sunrise_label.set_margin_end(20)
    sunrise_label.set_css_classes(['secondary','f-sm'])

    sunrise_icon = Gtk.Image.new_from_icon_name('daytime-sunrise-symbolic')
    sunrise_icon.set_css_classes(['secondary-light'])
    sunrise_icon.set_pixel_size(12)
    sunrise_icon.set_margin_end(6)

    sunset_time_minute = sunset_time.minute if len(str(sunset_time.minute))==2 else str(sunset_time.minute)+"0"
    sunset_label = Gtk.Label(label= f"{sunset_time.hour-12}:{sunset_time_minute} PM")
    sunset_label.set_css_classes(['secondary','f-sm'])
    sunset_icon = Gtk.Image.new_from_icon_name('daytime-sunset-symbolic')
    sunset_icon.set_css_classes(['secondary-light'])
    sunset_icon.set_pixel_size(12)
    sunset_icon.set_margin_end(5)

    sun_grid.attach(sunrise_icon,0,0,1,1)
    sun_grid.attach(sunrise_label,1,0,1,1)
    sun_grid.attach(sunset_icon,2,0,1,1)
    sun_grid.attach(sunset_label,3,0,1,1)

    weather_data.append([_("Humidity"), _("{0}%").format(data['main']['humidity'])])
    weather_data.append([_("Pressure"), _("{0} hPa").format(data['main']['pressure'])])
    weather_data.append([_("Wind speed"), _("{0:.1f} {1} {2}").format(data['wind']['speed']*measurements[measurement_type]['speed_mul'],measurements[measurement_type]['speed_unit'],wind_dir(data['wind']['deg']))])
    weather_data.append([_("Visibility"), f"{data['visibility']*measurements[measurement_type]['dist_mul']:.1f} {measurements[measurement_type]['dist_unit']}"])
    weather_data.append([_("Air Quality"), air_quality_level[air_pollution_data['list'][0]['main']['aqi']]])

    label_grid = Gtk.Grid()
    label_grid.set_row_spacing(2)
    label_grid.set_column_spacing(2)
    label_grid.set_margin_start(10)

    for i,desc in enumerate(weather_data):
        key_label = Gtk.Label(label=desc[0])
        key_label.set_margin_end(8)
        desc_label = Gtk.Label(label = desc[1])
        key_label.set_halign(Gtk.Align.START)
        desc_label.set_halign(Gtk.Align.START)
        key_label.set_css_classes(['secondary'])
        desc_label.set_css_classes(['bold','secondary-light'])

        if desc[0]==_('Air Quality'):
            desc_box = _create_pollutents_popup(desc_label,air_pollution_data)
            label_grid.attach(key_label,0,i,1,1)
            label_grid.attach(desc_box,1,i,1,1)
        else:
            label_grid.attach(key_label,0,i,1,1)
            label_grid.attach(desc_label,1,i,1,1)

    summary_text = ""
    if data.get('rain'):
        if data['rain'].get('1h'):
            text = _("rain in next 1 hour")
            summary_text = f"<b>{data['rain']['1h']}mm</b> {text}"
    elif data.get('snow'):
        if data['snow'].get('1h'):
            text = _("snow in next 1 hour")
            summary_text = f"<b>{data['snow']['1h']}mm</b> {text}"
    else:
        temp_main = data['main']['temp']
        if measurement_type == 'imperial':
            temp_main = (data['main']['temp']-32)*(5/9)
        if temp_main <= 0:
            summary_text = _("No snow for atleast 1 hour")
        elif temp_main > 0 and temp_main < 3:
            summary_text = _("No rain/snow for atleast 1 hour")
        else:
            summary_text = _("No rain for atleast 1 hour")

    rain_summ_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,halign = Gtk.Align.START)
    rain_summ_box.set_size_request(100,20)
    rain_summ_box.set_margin_top(10)
    rain_summ_box.set_css_classes(['rain_summ_box','secondary-light'])

    rain_summ_label = Gtk.Label.new()
    rain_summ_label.props.wrap = True
    rain_summ_label.props.use_markup = True
    rain_summ_label.set_markup (summary_text)

    summ_icon = Gtk.Image()
    summ_icon.set_pixel_size(18)
    summ_icon.set_margin_end(6)
    if data.get('rain'):
        summ_icon.set_from_icon_name('weather-showers-scattered-symbolic')  # Set the icon name and size
        rain_summ_box.append(summ_icon)
    elif data.get('snow'):
        summ_icon.set_from_icon_name('weather-snow-symbolic')  # Set the icon name and size
        rain_summ_box.append(summ_icon)
        
    rain_summ_box.append(rain_summ_label)
    right_section.append(box_city)
    right_section.append(label_grid)
    right_section.append(rain_summ_box)
    condition_grid.attach(right_section, 1, 1, 1, 1)

def _on_location_combo_changed(combo):
    GLib.idle_add(_on_switch_city,combo)

def _on_switch_city(combo):
    global cities,selected_city,g_main_window
    tree_iter = combo.get_active_iter()
    s_city = cities[selected_city]

    if tree_iter is not None:
        model = combo.get_model()
        city = model[tree_iter][0]  # get selected city from combo
        if s_city != city:
            selected_city = cities.index(city)
            settings.set_value("selected-city",GLib.Variant("i",selected_city))
            g_main_window.refresh_weather(g_main_window,ignore=False)


def _create_pollutents_popup(desc_label,air_pollution_data):
        desc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        desc_box.append(desc_label)

        gas_labels = [
            'CO',
            'NO',
            'NO<sub>2</sub>',
            'O<sub>3</sub>',
            'SO<sub>2</sub>',
            'PM<sub>2.5</sub>',
            'PM<sub>10</sub>',
            'NH<sub>3</sub>',
        ]
        popover = Gtk.Popover.new()
        
        popover_menu = Gtk.MenuButton()
        popover_menu.set_popover(popover)
        popover_menu.set_margin_start(6)
        popover_menu.set_has_frame(False)

        popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        popover_box.set_margin_top(10)
        popover_box.set_margin_bottom(10)
        popover_box.set_margin_start(10)
        popover_box.set_margin_end(10)
        popover.set_child(popover_box)

        heading_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        heading_box.set_margin_bottom(10)
        heading_box.set_hexpand(True)
        heading_box.set_css_classes(['border_bottom1'])
        air_pollution_val_list = list(air_pollution_data['list'][0]['components'].values())
        pollution_heading = Gtk.Label(label="Air Pollutents",halign = Gtk.Align.START)
        pollution_heading.set_css_classes(['f-lg'])
        hint_url = 'https://www.who.int/teams/environment-climate-change-and-health/air-quality-and-health/health-impacts/types-of-pollutants'
        pollution_hint = Gtk.LinkButton.new(hint_url)
        pollution_hint.set_icon_name("dialog-question-symbolic")
        pollution_hint.set_has_frame(False)

        pollution_hint.set_margin_start(30)
        pollution_hint.set_margin_bottom(2)

        heading_box.append(pollution_heading)
        heading_box.append(pollution_hint)
        popover_box.append(heading_box)

        popover_grid = Gtk.Grid()
        popover_grid.set_row_spacing(2)
        popover_grid.set_column_spacing(2)
        popover_box.append(popover_grid)

        for ind in range(len(gas_labels)):
            gas_label = Gtk.Label(halign = Gtk.Align.START)
            gas_label.set_css_classes(['secondary-light','f-mlg'])
            gas_label.set_margin_end(50)
            gas_label.props.use_markup = True
            gas_label.set_markup(gas_labels[ind])
            popover_grid.attach(gas_label,0,ind,1,1)
            gas_label_desc = Gtk.Label(label=air_pollution_val_list[ind],halign = Gtk.Align.START)
            gas_label_desc.set_css_classes(['secondary-light','f-mlg','bold'])
            popover_grid.attach(gas_label_desc,1,ind,1,1)

        pollution_note = Gtk.Label(halign = Gtk.Align.START)
        pollution_note.set_margin_top(5)
        pollution_note.props.wrap = True
        pollution_note.props.use_markup = True
        pollution_note.set_css_classes(['secondary','f-msm'])
        pollution_note.set_markup('Concentration units in μg/m<sup>3</sup>')
        popover_box.append(pollution_note)

        desc_box.append(popover_menu)
        return desc_box