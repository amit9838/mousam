from datetime import datetime, timedelta
import gi
from gi.repository import Gtk
from gettext import gettext as _
from .constants import icons

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')


class Forecast(Gtk.Grid):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_margin_top(20)
        self.set_margin_bottom(5)
        self.set_margin_start(10)
        self.set_margin_end(5)
        self.set_css_classes(['view', 'card', 'custom_card'])
        self.paint_ui()

    def paint_ui(self):

        # ======== Tab Box ==========
        tab_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                          hexpand=True, halign=Gtk.Align.CENTER)
        self.attach(tab_box, 0, 0, 1, 1)

        style_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        style_buttons_box.add_css_class('linked')
        style_buttons_box.set_margin_start(2)
        style_buttons_box.set_valign(Gtk.Align.CENTER)

        tomorrow_btn = Gtk.ToggleButton.new_with_label(_('Tomorrow'))
        tomorrow_btn.set_css_classes(['pill', 'btn_sm'])
        tomorrow_btn.do_clicked(tomorrow_btn)
        style_buttons_box.append(tomorrow_btn)
        tomorrow_btn.connect('clicked', self._on_tomorrow_forecast_btn_clicked)

        weekly_btn = Gtk.ToggleButton.new_with_label(_('Weekly'))
        weekly_btn.set_css_classes(['pill', 'btn_sm'])
        weekly_btn.set_group(tomorrow_btn)
        style_buttons_box.append(weekly_btn)
        weekly_btn.connect('clicked', self._on_weekly_btn_forecast_btn_clicked)

        # =========== Forecast Page Stack ============
        self.forecast_stack = Gtk.Stack.new()
        self.forecast_stack.set_transition_type(
            Gtk.StackTransitionType.CROSSFADE)
        self.attach(self.forecast_stack, 0, 1, 1, 1)

        tab_box.append(style_buttons_box)
        self.page_stacks('tomorrow')

    # ============= Button Click Methods ==============
    def _on_tomorrow_forecast_btn_clicked(self, widget):
        page_name = 'tomorrow'
        if self.forecast_stack.get_child_by_name(page_name):
            self.forecast_stack.set_visible_child_name(page_name)
            return
        self.page_stacks('tomorrow')

    def _on_weekly_btn_forecast_btn_clicked(self, widget):
        page_name = 'weekly'
        if self.forecast_stack.get_child_by_name(page_name):
            self.forecast_stack.set_visible_child_name(page_name)
            return
        self.page_stacks('weekly')

        # ============ Add items to Stack [Tomorrow/Week] =============
    def page_stacks(self, page_name):
        from .weatherData import daily_forecast_data as daily_data
        from .weatherData import hourly_forecast_data as hourly_data

        # Create box and add it stack
        box = Gtk.Box(margin_top=0, margin_bottom=0)
        self.forecast_stack.add_named(box, page_name)
        self.forecast_stack.set_visible_child_name(page_name)

        # Create scrolled window , add it to stack-box
        scrolled_window = Gtk.ScrolledWindow(margin_top=8,margin_bottom=8)
        scrolled_window.set_policy(
            Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_size_request(300, 550)
        scrolled_window.set_kinetic_scrolling(True)
        box.append(scrolled_window)

        # Forecast card container
        forecast_container = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, margin_top=0, margin_bottom=0)
        scrolled_window.set_child(forecast_container)

        # Get Tomorrow's data from hourly forecast
        tomorrow_date_time_list = [d_t for d_t in hourly_data.time.get("data") if int(
            datetime.fromtimestamp(d_t).strftime(r"%d")) == (datetime.today() + timedelta(days=1)).date().day]
        items = tomorrow_date_time_list

        # Get weekly date_time list from daily_data
        if page_name == 'weekly':
            items = daily_data.time.get("data")

        # Add weather items in the stack-box
        for i, item in enumerate(items):
            
            forecast_item_grid = Gtk.Grid(hexpand=True,margin_top=6)
            forecast_item_grid.set_css_classes(
                ['bg_light_grey', 'custom_card_forecast_item'])

            forecast_container.append(forecast_item_grid)

            # Add Date-time Label [dafault : tomorrow]
            date_time = datetime.fromtimestamp(item)
            d_t = date_time.strftime("%I:%M %p")
            weather_code = hourly_data.weathercode.get("data")[i]

            if page_name == 'weekly':
                d_t = date_time.strftime("%A")
                weather_code = daily_data.weathercode.get("data")[i]
                if date_time.date().day == datetime.today().date().day:
                    d_t = _('Today')
                elif date_time.date().day == (datetime.today()+timedelta(days=1)).date().day:
                    d_t = _('Tomorrow')

            # Add d_t Label
            label_day_time = Gtk.Label(label=d_t, halign=Gtk.Align.START)
            label_day_time.set_css_classes(['text-4', 'bold-2'])
            forecast_item_grid.attach(label_day_time, 0, 0, 1, 1)

            # Condition Icon
            # if it is night
            condition_icon = icons[str(weather_code)]
            if hourly_data.is_day.get("data")[i] == 0:
                    condition_icon = icons[str(weather_code)+'n'] 

            icon_main = Gtk.Image().new_from_file(condition_icon)
            icon_main.set_halign(Gtk.Align.END)
            icon_main.set_hexpand(True)
            icon_main.set_pixel_size(50)
            icon_main.set_margin_end(60)
            forecast_item_grid.attach(icon_main, 1, 0, 1, 1)

            # Temp label grid
            temp_label_grid = Gtk.Grid(valign=Gtk.Align.CENTER)
            forecast_item_grid.attach(temp_label_grid, 2, 0, 1, 1)
            
            # Max temp label ======
            temp_max_text = hourly_data.temperature_2m.get("data")[i]
            if page_name == 'weekly':
                temp_max_text = daily_data.temperature_2m_max.get("data")[i]

            temp_max = Gtk.Label(label=f"{temp_max_text:.0f}° ", margin_start=10,)
            temp_max.set_css_classes(['text-3', 'bold-2'])
            temp_label_grid.attach(temp_max, 0, 0, 1, 1)

            # Min temp label ======
            temp_min_text = hourly_data.temperature_2m.get("data")[i]
            if page_name == 'weekly':
                temp_min_text = daily_data.temperature_2m_min.get("data")[i]

            temp_min = Gtk.Label(label=f" {temp_min_text:.0f}°", margin_top=5)
            temp_min.set_css_classes(['light-4'])
            temp_label_grid.attach(temp_min, 0, 1, 1, 1)
