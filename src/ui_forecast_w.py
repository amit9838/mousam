import gi
import datetime
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk,Gio

# from backend.curr_weather import fetch_weather
from .constants import icons


def forecast_weather(middle_row,f_data):

        scrolled_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scrolled_container.set_size_request(800,200)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)  # Enable automatic scrolling
        scrolled_window.set_min_content_height(190)
        scrolled_window.set_margin_bottom(8)
        scrolled_window.set_margin_top(8)
        scrolled_window.set_kinetic_scrolling(True)
        scrolled_window.set_halign(Gtk.Align.CENTER)
        scrolled_container.append(scrolled_window)
        scrolled_window.set_size_request(800,190)
        middle_row.append(scrolled_container)

        forecast_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        forecast_box.set_css_classes(['forecast_box'])

        scrolled_window.set_child(forecast_box)

        # f_data = [{'dt': 1685491200, 'main': {'temp': 24.2, 'feels_like': 24.76, 'temp_min': 24.2, 'temp_max': 26.51, 'pressure': 1007, 'sea_level': 1007, 'grnd_level': 982, 'humidity': 80, 'temp_kf': -2.31}, 'weather': [{'id': 803, 'main': 'Clouds', 'description': 'broken clouds', 'icon': '04d'}], 'clouds': {'all': 61}, 'wind': {'speed': 3.41, 'deg': 274, 'gust': 4.37}, 'visibility': 10000, 'pop': 0.62, 'sys': {'pod': 'd'}, 'dt_txt': '2023-05-31 00:00:00'},
        #         {'dt': 1685566800, 'main': {'temp': 29.55, 'feels_like': 29.18, 'temp_min': 29.55, 'temp_max': 29.55, 'pressure': 1005, 'sea_level': 1005, 'grnd_level': 981, 'humidity': 40, 'temp_kf': 0}, 'weather': [{'id': 800, 'main': 'Clear', 'description': 'clear sky', 'icon': '01n'}], 'clouds': {'all': 0}, 'wind': {'speed': 4.36, 'deg': 345, 'gust': 7.02}, 'visibility': 10000, 'pop': 0, 'sys': {'pod': 'n'}, 'dt_txt': '2023-05-31 21:00:00'}]

        for data in f_data.get('list'):
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
            # forecast_content.set_vexpand(True)

            # date_time = data.get('dt_txt')
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
            forecast_icon.set_from_icon_name(icons.get(data['weather'][0]['icon']))  # Set the icon name and size
            # icon.set_hexpand(True)
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
            rain_icon.set_from_icon_name("weather-showers-scattered-symbolic")  # Set the icon name and size
            rain_icon.set_css_classes(['secondary'])
            rain_icon.set_pixel_size(16)
            rain_icon.set_margin_end(5)
            prec_box.append(rain_icon)

            pop = int(data.get('pop')*100) if data.get('pop') else 0
            prec_label = Gtk.Label(label=_("{0}%").format(pop))
            prec_label.set_css_classes(['secondary-light'])
            prec_box.append(prec_label)
            grid.attach(prec_box, 0, 0, 1, 1)

            wind_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            # weather-windy-symbolic
            wind_icon = Gtk.Image()
            wind_icon.set_from_icon_name("weather-windy-symbolic")  # Set the icon name and size
            # icon.set_hexpand(True)
            wind_icon.set_pixel_size(16)
            wind_icon.set_css_classes(['secondary'])
            wind_icon.set_margin_end(5)
            wind_box.append(wind_icon)


            wind_label = Gtk.Label(label=_("{0:.1f} km/h").format(data['wind']['speed']*1.609344))
            wind_label.set_css_classes(['secondary-light'])
            wind_box.append(wind_label)
            grid.attach(wind_box, 0, 1, 1, 1)

            temp_label = Gtk.Label(label=_("{0:.0f}°").format(data['main']['temp']))
            temp_label.set_css_classes(['forecast_temp_label'])
            temp_label.set_margin_top(10)
            forecast_content.append(temp_label)
