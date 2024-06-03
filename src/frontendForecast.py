from datetime import datetime, timedelta
import gi
from gi.repository import Gtk
from gettext import gettext as _, pgettext as C_
from .constants import icons
from .config import settings

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
        if settings.is_using_dynamic_bg:
            self.add_css_class("transparent_5")
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
        tomorrow_btn.set_size_request(100,20)
        tomorrow_btn.set_css_classes(['btn_sm'])
        tomorrow_btn.do_clicked(tomorrow_btn)
        style_buttons_box.append(tomorrow_btn)
        tomorrow_btn.connect('clicked', self._on_tomorrow_forecast_btn_clicked)

        weekly_btn = Gtk.ToggleButton.new_with_label(_('Weekly'))
        weekly_btn.set_size_request(100,20)
        weekly_btn.set_css_classes(['btn_sm'])
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
        scrolled_window.set_size_request(300, 535)
        scrolled_window.set_kinetic_scrolling(True)
        box.append(scrolled_window)

        # Forecast card container
        forecast_container = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, margin_top=0, margin_bottom=0)
        scrolled_window.set_child(forecast_container)

        items_range = 7
        idx_offset = 0

        if page_name != 'weekly':
            items_range = 24
            idx_offset = self.get_idx_offset(hourly_data)

        # -------- Plot items -------
        for idx in range(items_range):     
            forecast_item_grid = Gtk.Grid(hexpand=True,margin_top=6)
            forecast_item_grid.set_css_classes(
                ['bg_light_grey', 'custom_card_forecast_item'])
            forecast_container.append(forecast_item_grid)


            ts = hourly_data.time.get('data')[idx+idx_offset]
            date_time = datetime.fromtimestamp(ts)
            dt_label = date_time.strftime("%I:%M %p")
            
            if settings.is_using_24h_clock:
                dt_label = date_time.strftime("%H:%M")

            temp_max_text = hourly_data.temperature_2m.get("data")[idx+idx_offset]
            temp_min_text = 0
            weather_code = hourly_data.weathercode.get("data")[idx+idx_offset]

            if page_name == 'weekly':
                ts = daily_data.time.get("data")[idx+idx_offset]
                date_time = datetime.fromtimestamp(ts)
                dt_label = date_time.strftime("%A")
                temp_min_text = daily_data.temperature_2m_min.get("data")[idx+idx_offset]
                temp_max_text = daily_data.temperature_2m_max.get("data")[idx+idx_offset]
                weather_code = daily_data.weathercode.get("data")[idx+idx_offset]

                if date_time.date().day == datetime.today().date().day:
                    dt_label = _('Today')
                elif date_time.date().day == (datetime.today()+timedelta(days=1)).date().day:
                    dt_label = _('Tomorrow')

            # Add dt_label Label
            label_box = Gtk.Box()
            label_box.set_size_request(80, 68)
            label_day_time = Gtk.Label(label=dt_label, halign=Gtk.Align.START)
            label_day_time.set_css_classes(['text-4', 'bold-2','light-2'])
            label_box.append(label_day_time)
            forecast_item_grid.attach(label_box, 0, 0, 1, 1)

            # Condition Icon (if night)
            if hourly_data.is_day.get("data")[idx+idx_offset] == 0:
                    weather_code = str(weather_code)+"n"

            # Condition icon =====
            condition_icon = Gtk.Image().new_from_file(icons[str(weather_code)])
            condition_icon.set_halign(Gtk.Align.CENTER)
            condition_icon.set_hexpand(True)
            condition_icon.set_pixel_size(50)
            forecast_item_grid.attach(condition_icon, 1, 0, 1, 1)

            forecast_cond_grid = Gtk.Grid(valign=Gtk.Align.CENTER,margin_end = 20)
            forecast_item_grid.attach(forecast_cond_grid, 2, 0, 1, 1)

            # Temp label grid =====
            temp_label_grid = Gtk.Grid(valign=Gtk.Align.CENTER)
            forecast_item_grid.attach(temp_label_grid, 3, 0, 1, 1)

            # Max temp label ======
            temp_max = Gtk.Label(label=f"{temp_max_text:.0f}° ", margin_start=10,)
            temp_max.set_css_classes(['text-3', 'bold-2'])
            temp_label_grid.attach(temp_max, 1, 0, 1, 1)

            # Min temp label ======
            if page_name == 'weekly':
                temp_min = Gtk.Label(label=f" {temp_min_text:.0f}°", margin_top=5)
                temp_min.set_css_classes(['light-4'])
                temp_label_grid.attach(temp_min, 1, 1, 1, 1)


    # ============ get timestamp of upcomming 12:00 AM ====================
    def get_upcomming_12am(self):
        # Get current date and time
        current_time = datetime.now()

        # Set time to 12:00 AM
        upcoming_12am = current_time.replace(hour=0, minute=0, second=0, microsecond=0)

        # If the current time is already past 12:00 AM, get the timestamp for the next day
        if current_time >= upcoming_12am:
            upcoming_12am += timedelta(days=1)

        # Convert to timestamp
        return upcoming_12am.timestamp()

    # =========== Return index offset from hourly forecast to get tomorrow's weather condition ====================
    def get_idx_offset(self,hourly_data):
        idx_off = 0
        upcomming_12am = self.get_upcomming_12am()
        for t in hourly_data.time.get("data"):
            if t > upcomming_12am:
                return idx_off
            idx_off+=1