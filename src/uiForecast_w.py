import gi
from datetime import datetime, timedelta
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk,GLib,Gio

from .constants import icons,API_KEY
from .units import  measurements,get_measurement_type
from .utils import get_selected_city_coords
from .backendForecast_w import fetch_forecast, extract_forecast_data

def forecast_weather(middle_row,f_data):

        forecast_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,halign = Gtk.Align.FILL, margin_start=10, margin_end=10)
        forecast_container.set_size_request(800,230)
        middle_row.append(forecast_container)

        forecast_stack = Gtk.Stack.new()
        forecast_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        style_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, halign=Gtk.Align.START)
        style_buttons_box.add_css_class('linked')
        style_buttons_box.set_margin_start(2)
        style_buttons_box.set_valign(Gtk.Align.CENTER)
        
        today_btn = Gtk.ToggleButton.new_with_label(_('Today'))
        today_btn.set_css_classes(['pill','btn_sm'])
        today_btn.do_clicked(today_btn)
        today_btn.connect('clicked',_on_today_forecast_btn_clicked,None,forecast_stack)

        tomorrow_btn = Gtk.ToggleButton.new_with_label(_('Tomorrow'))
        tomorrow_btn.set_css_classes(['pill','btn_sm'])
        tomorrow_btn.set_group(today_btn)
        tomorrow_btn.connect('clicked',_on_tomorrow_forecast_btn_clicked,None,forecast_stack)
        
        five_d = Gtk.ToggleButton.new_with_label(_('5 Days'))
        five_d.set_css_classes(['pill','btn_sm'])
        five_d.set_group(today_btn)
        five_d.connect('clicked',_on_five_d_forecast_btn_clicked,None,forecast_stack)

        style_buttons_box.append(today_btn)
        style_buttons_box.append(tomorrow_btn)
        style_buttons_box.append(five_d)
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

def _on_today_forecast_btn_clicked(self,widget,stack):
    stack.set_visible_child_name('today')

def _on_tomorrow_forecast_btn_clicked(self,widget,stack):
    if stack.get_child_by_name("tomorrow"):
        stack.set_visible_child_name("tomorrow")
        return
    stack.set_visible_child_name('loader')
    latitude,longitude = get_selected_city_coords()
    GLib.idle_add(fetch_and_plot,stack,latitude,longitude,2,'tomorrow')

def _on_five_d_forecast_btn_clicked(self,widget,stack):
    if stack.get_child_by_name("five_d"):
        stack.set_visible_child_name("five_d")
        return
    stack.set_visible_child_name('loader')
    latitude,longitude = get_selected_city_coords()
    GLib.idle_add(fetch_and_plot,stack,latitude,longitude,5,"five_d")

def fetch_and_plot(stack,latitude,longitude,days=1,d_type='tomorrow'):
    f_data = fetch_forecast(API_KEY,latitude,longitude,days)
    f_data_new = extract_forecast_data(f_data.get('list'),d_type)
    plot_forecast_data(stack,f_data_new,d_type)

def plot_forecast_data(stack,f_data,page_name):
        measurement_type = get_measurement_type()
        
        scrolled_window = Gtk.ScrolledWindow(hexpand=True, halign=Gtk.Align.FILL)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        scrolled_window.set_min_content_height(190)
        scrolled_window.set_margin_bottom(8)
        scrolled_window.set_margin_top(8)
        scrolled_window.set_kinetic_scrolling(True)
        scrolled_window.set_size_request(800,190)

        stack.add_named(scrolled_window,page_name)
        stack.set_visible_child_name(page_name)

        forecast_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True)
        forecast_box.set_css_classes(['forecast_box'])
        scrolled_window.set_child(forecast_box)

        for data in f_data:
            forecast_item = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            forecast_item.set_margin_start(2)
            forecast_item.set_margin_end(2)
            forecast_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            forecast_content.set_halign(Gtk.Align.CENTER)
            if page_name == 'five_d':
                forecast_item.set_size_request(180,200)
            else:
                forecast_item.set_size_request(130,160)

            forecast_item.set_css_classes(['f_box'])
            forecast_content.set_css_classes(['f_box_t'])
            forecast_content.set_margin_top(10)
            forecast_content.set_margin_bottom(10)
            forecast_content.set_margin_start(10)
            forecast_content.set_margin_end(10)
            date_time = datetime.fromtimestamp(data['dt'])

            d_t = ""
            if page_name == 'five_d':
                d_t = date_time.strftime("%A")
                if date_time.date().day == datetime.today().date().day:
                      d_t = _('Today')
                elif date_time.date().day == (datetime.today()+timedelta(days=1)).date().day:
                      d_t = _('Tomorrow')
            else:
                hr = date_time.hour
                tpe = _("AM")
                if date_time.hour > 12:
                    hr = date_time.hour - 12
                    tpe = _("PM")

                minute = str(date_time.minute)+'0'  if date_time.minute==0 else date_time.minute
                d_t = f"{hr}:{minute} {tpe}"

            forecast_time = Gtk.Label(label=f"{d_t}")
            forecast_time.set_css_classes([f'secondary-lighter'])
            forecast_time.set_halign(Gtk.Align.CENTER)
            forecast_content.append(forecast_time)
            forecast_item.append(forecast_content)
            forecast_box.append(forecast_item)
            
            forecast_icon = Gio.Icon.new_for_string(icons.get(data['weather'][0]['icon']))
            forecast_icon = Gtk.Image.new_from_gicon(forecast_icon)
            # forecast_icon = Gtk.Image.new_from_icon_name(icons.get(data['weather'][0]['icon']))
            forecast_icon.set_margin_bottom(10)

            if page_name == 'five_d':
                forecast_condition = Gtk.Label(label=data['weather'][0]['main'].capitalize())
                forecast_condition.set_margin_top(4)
                forecast_condition.set_css_classes(['secondary-light','f-mlg' ,'bold'])
                forecast_content.append(forecast_condition)

                grid = Gtk.Grid()
                grid.set_row_spacing(5)
                grid.set_column_spacing(30)
                grid.set_margin_top(8)
                forecast_content.append(grid)

                forecast_icon.set_pixel_size(86)
                temp_icon_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                temp_icon_box.set_halign(Gtk.Align.CENTER)

                min_temp = Gtk.Label(label=f"{data['main']['temp_max']:.0f}°")
                min_temp.set_css_classes(['bolder','secondary-lighter','f-m'])
                min_temp.set_margin_top(4)
                min_temp.set_halign(Gtk.Align.CENTER)
                temp_icon_box.append(min_temp)
                
                max_temp = Gtk.Label(label=f"{data['main']['temp_min']:.0f}°")
                max_temp.set_css_classes(['bold','secondary-lighter','f-sm'])
                max_temp.set_margin_top(3)
                max_temp.set_halign(Gtk.Align.CENTER)
                temp_icon_box.append(max_temp)
                
                grid.attach(temp_icon_box, 0, 0, 1, 1)
                grid.attach(forecast_icon, 1, 0, 1, 1)

            else:
                forecast_icon.set_margin_top(15)
                forecast_icon.set_pixel_size(70)
                forecast_content.append(forecast_icon)

            grid = Gtk.Grid()
            grid.set_row_spacing(5)
            grid.set_column_spacing(10)
            forecast_content.append(grid)
            grid.set_margin_top(20)

            if page_name == 'five_d':
                grid.set_margin_top(5)

            prec_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            rain_icon = Gtk.Image.new_from_icon_name("weather-showers-scattered-symbolic")
            rain_icon.set_pixel_size(16)
            rain_icon.set_margin_end(5)
            prec_box.append(rain_icon)

            pop = int(data.get('pop')*100) if data.get('pop') else 0
            prec_label = Gtk.Label(label=_("{0}%").format(pop))
            prec_label.set_css_classes(['secondary-light'])
            prec_box.append(prec_label)
            grid.attach(prec_box, 0, 0, 1, 1)

            wind_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            wind_icon = Gtk.Image.new_from_icon_name("weather-windy-symbolic")
            wind_icon.set_pixel_size(16)
            wind_icon.set_css_classes(['secondary'])
            wind_icon.set_margin_end(5)
            wind_box.append(wind_icon)

            wind_label = Gtk.Label(label=_("{0:.1f} {1}").format(data['wind']['speed']*measurements[measurement_type]['speed_mul'],measurements[measurement_type]['speed_unit']))
            wind_label.set_css_classes(['secondary-light'])
            wind_box.append(wind_label)
            grid.attach(wind_box, 0, 1, 1, 1)

            temp_label = Gtk.Label(label=_("{0:.0f}°").format(data['main']['temp']))
            temp_label.set_css_classes(['f-lg','bolder'])
            temp_label.set_margin_top(20)
            if page_name == 'five_d':
                temp_label.set_css_classes(['f-lg2','bolder'])
                temp_label.set_margin_top(12)
            forecast_content.append(temp_label)
