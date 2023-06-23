import gi
import datetime
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk,Gio,GLib

from .constants import icons,API_KEY
from .units import  measurements,get_measurement_type
from .backend_forecast_w import fetch_forecast, extract_forecast_data

def forecast_weather(middle_row,f_data):

        forecast_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,halign = Gtk.Align.CENTER)
        forecast_container.set_size_request(800,230)
        middle_row.append(forecast_container)

        forecast_stack = Gtk.Stack.new()
        forecast_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        style_buttons_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        style_buttons_box.add_css_class('linked')
        style_buttons_box.set_margin_start(8)
        style_buttons_box.set_valign(Gtk.Align.CENTER)
        
        today_btn = Gtk.ToggleButton.new_with_label('Today')
        today_btn.set_css_classes(['pill','btn_sm'])
        today_btn.do_clicked(today_btn)
        today_btn.connect('clicked',show_todays_forecast,None,forecast_stack)
        style_buttons_box.append(today_btn)

        tomorrow_btn = Gtk.ToggleButton.new_with_label('Tomorrow')
        tomorrow_btn.set_css_classes(['pill','btn_sm'])
        tomorrow_btn.set_group(today_btn)
        tomorrow_btn.connect('clicked',show_tomorrows_forecast,None,forecast_stack)
        style_buttons_box.append(tomorrow_btn)

        forecast_container.append(style_buttons_box)
        forecast_container.append(forecast_stack)

        plot_forecast_data(forecast_stack,f_data,'today')

        container_loader = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container_loader.set_margin_top(80)
        loader = Gtk.Spinner()
        loader.set_css_classes(['loader'])
        loader.start()
        container_loader.append(loader)
        forecast_stack.add_named(container_loader,"loader")

def show_todays_forecast(self,widget,stack):
    stack.set_visible_child_name('today')

def show_tomorrows_forecast(self,widget,stack):
    if stack.get_child_by_name("tomorrow"):
        stack.set_visible_child_name("tomorrow")
        return
    
    stack.set_visible_child_name('loader')
    settings = Gio.Settings.new("io.github.amit9838.weather")
    selected_city = int(str(settings.get_value('selected-city')))
    added_cities = list(settings.get_value('added-cities'))
    city_loc = added_cities[selected_city]
    city_loc = city_loc.split(',')
    latitude = (city_loc[-2])
    longitude = (city_loc[-1])
    GLib.idle_add(fetch_and_plot,stack,latitude,longitude)

def fetch_and_plot(stack,latitude,longitude):
    f_data = fetch_forecast(API_KEY,latitude,longitude,2)
    f_data_new = extract_forecast_data(f_data.get('list'),"tomorrow")
    plot_forecast_data(stack,f_data_new,"tomorrow")

def plot_forecast_data(stack,f_data,page_name):
        if stack.get_child_by_name(page_name):
            stack.set_visible_child_name(page_name)
            return
        measurement_type = get_measurement_type()
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER) 
        scrolled_window.set_min_content_height(190)
        scrolled_window.set_margin_bottom(8)
        scrolled_window.set_margin_top(8)
        scrolled_window.set_kinetic_scrolling(True)
        scrolled_window.set_halign(Gtk.Align.CENTER)
        stack.add_named(scrolled_window,page_name)
        stack.set_visible_child_name(page_name)
        scrolled_window.set_size_request(800,190)

        forecast_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        forecast_box.set_css_classes(['forecast_box'])
        scrolled_window.set_child(forecast_box)

        for data in f_data:
            forecast_item = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            forecast_item.set_margin_start(2)
            forecast_item.set_margin_end(2)
            forecast_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            forecast_content.set_halign(Gtk.Align.CENTER)
            forecast_item.set_size_request(110,160)

            forecast_item.set_css_classes(['f_box'])
            forecast_content.set_css_classes(['f_box_t'])
            forecast_content.set_margin_top(10)
            forecast_content.set_margin_bottom(10)
            forecast_content.set_margin_start(10)
            forecast_content.set_margin_end(10)
            date_time = datetime.datetime.fromtimestamp(data['dt'])

            hr = date_time.hour
            tpe = _("AM")
            if date_time.hour > 12:
                hr = date_time.hour - 12
                tpe = _("PM")

            minute = str(date_time.minute)+'0'  if date_time.minute==0 else date_time.minute
            time = f"{hr}:{minute} {tpe}"

            forecast_time = Gtk.Label(label=f"{time}")
            forecast_time.set_css_classes(['secondary-lighter'])

            forecast_time.set_halign(Gtk.Align.CENTER)
            forecast_content.append(forecast_time)
            forecast_item.append(forecast_content)
            forecast_box.append(forecast_item)


            forecast_icon = Gtk.Image()
            forecast_icon.set_from_icon_name(icons.get(data['weather'][0]['icon']))
            forecast_icon.set_pixel_size(36)
            forecast_icon.set_margin_top(15)
            forecast_icon.set_margin_bottom(10)
            forecast_content.append(forecast_icon)

            grid = Gtk.Grid()
            grid.set_row_spacing(5)
            grid.set_column_spacing(10)
            grid.set_margin_top(20)
            forecast_content.append(grid)

            prec_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            rain_icon = Gtk.Image()
            rain_icon.set_from_icon_name("weather-showers-scattered-symbolic")
            rain_icon.set_pixel_size(16)
            rain_icon.set_margin_end(5)
            prec_box.append(rain_icon)

            pop = int(data.get('pop')*100) if data.get('pop') else 0
            prec_label = Gtk.Label(label=_("{0}%").format(pop))
            prec_label.set_css_classes(['secondary-light'])
            prec_box.append(prec_label)
            grid.attach(prec_box, 0, 0, 1, 1)

            wind_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            wind_icon = Gtk.Image()
            wind_icon.set_from_icon_name("weather-windy-symbolic")
            wind_icon.set_pixel_size(16)
            wind_icon.set_css_classes(['secondary'])
            wind_icon.set_margin_end(5)
            wind_box.append(wind_icon)

            wind_label = Gtk.Label(label=_("{0:.1f} {1}").format(data['wind']['speed']*measurements[measurement_type]['speed_mul'],measurements[measurement_type]['speed_unit']))
            wind_label.set_css_classes(['secondary-light'])
            wind_box.append(wind_label)
            grid.attach(wind_box, 0, 1, 1, 1)

            temp_label = Gtk.Label(label=_("{0:.0f}°").format(data['main']['temp']))
            temp_label.set_css_classes(['forecast_temp_label'])
            temp_label.set_margin_top(10)
            forecast_content.append(temp_label)
