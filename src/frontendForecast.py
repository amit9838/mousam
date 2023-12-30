import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk,Gio
from gettext import gettext as _

from datetime import datetime,timedelta
from .constants import icons

from .frontendUiDrawImageIcon import DrawImage
image_path = "/home/amit/Drive-D/weather/src/frontend/ui/arrowA.png"  # Replace with the path to your image file
angle = 120


class Forecast(Gtk.Grid):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_hexpand(True)
        # self.set_margin_start(10)
        # self.set_size_request(350, 300)

        self.set_margin_top(20)
        self.set_margin_bottom(5)
        self.set_margin_start(10)
        self.set_margin_end(5)
        self.set_css_classes(['view','card','custom_card'])
        self.paint_ui()

    def paint_ui(self):

        tab_box = Gtk.Box(orientation=Gtk .Orientation.VERTICAL,hexpand=True,halign=Gtk.Align.CENTER)
        self.attach(tab_box,0,0,1,1)

        style_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        style_buttons_box.add_css_class('linked')
        style_buttons_box.set_margin_start(2)
        style_buttons_box.set_valign(Gtk.Align.CENTER)
        
        tomorrow_btn = Gtk.ToggleButton.new_with_label(_('Tomorrow'))
        tomorrow_btn.set_css_classes(['pilal','btn_sm'])
        tomorrow_btn.do_clicked(tomorrow_btn)
        style_buttons_box.append(tomorrow_btn)
        tomorrow_btn.connect('clicked',self._on_tomorrow_forecast_btn_clicked)

        weekly_btn = Gtk.ToggleButton.new_with_label(_('Weekly'))
        weekly_btn.set_css_classes(['pilla','btn_sm'])
        weekly_btn.set_group(tomorrow_btn)
        style_buttons_box.append(weekly_btn)
        weekly_btn.connect('clicked',self._on_weekly_btn_forecast_btn_clicked)

        self.forecast_stack = Gtk.Stack.new()
        self.forecast_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.attach(self.forecast_stack,0,1,1,1)

        tab_box.append(style_buttons_box)
        self.page_stacks('tomorrow')


    def _on_tomorrow_forecast_btn_clicked(self,widget):
        page_name = 'tomorrow'
        if self.forecast_stack.get_child_by_name(page_name):
            self.forecast_stack.set_visible_child_name(page_name)
            return
        self.page_stacks('tomorrow')

    def _on_weekly_btn_forecast_btn_clicked(self,widget):
        page_name = 'weekly'
        if self.forecast_stack.get_child_by_name(page_name):
            self.forecast_stack.set_visible_child_name(page_name)
            return
        self.page_stacks('weekly')

        # ---------- Create page stack --------------
    def page_stacks(self,page_name):
        from .weatherData import daily_forecast_data as daily_data
        from .weatherData import hourly_forecast_data as hourly_data

        #Forecast cards scrolled window

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=0,margin_bottom=0)
        self.forecast_stack.add_named(box,page_name)
        self.forecast_stack.set_visible_child_name(page_name)

        scrolled_window = Gtk.ScrolledWindow()
        box.append(scrolled_window)

        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        # scrolled_window.set_min_content_height(190)
        scrolled_window.set_size_request(350, 560)

        print("adding page",page_name)
        scrolled_window.set_margin_bottom(8)
        scrolled_window.set_margin_top(8)
        scrolled_window.set_kinetic_scrolling(True)

        #Forecast cards container
        forecast_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=0,margin_bottom=0)
        scrolled_window.set_child(forecast_container)

        date_time = [d_t for d_t in hourly_data.time.get("data") if int(datetime.fromtimestamp(d_t).strftime(r"%d")) == datetime.today().date().day]

        items = date_time

        if page_name == 'weekly':
            items = daily_data.time.get("data")

        for i,item in enumerate(items):
            
            forecast_item_grid = Gtk.Grid(hexpand=True,margin_start=0,margin_end=0,margin_top=5)
            forecast_item_grid.set_css_classes(['bg_light_grey','custom_card_forecast_item'])

            forecast_container.append(forecast_item_grid)
            date_time = datetime.fromtimestamp(item)
            
            d_t =  date_time.strftime("%I:%M %p")
            
            if page_name == 'weekly':
                d_t = date_time.strftime("%A")
                
                if date_time.date().day == datetime.today().date().day:
                    d_t = _('Today')
                elif date_time.date().day == (datetime.today()+timedelta(days=1)).date().day:
                    d_t = _('Tomorrow')
            
            label_day_time = Gtk.Label(label=d_t,halign=Gtk.Align.START)
            label_day_time.set_hexpand(True)
            label_day_time.set_css_classes(['text-3'])
            forecast_item_grid.attach(label_day_time,0,0,1,1)

            # icon = Gtk.Label(label="☁︎")
            icon = DrawImage(image_path,0,26,26)
            forecast_item_grid.attach(icon.img_box,1,0,1,1)
            
            # Max temp label ======
            temp_max_label = hourly_data.temperature_2m.get("data")[i]
            if page_name == 'weekly':
                temp_max_label = daily_data.temperature_2m_max.get("data")[i]
            
            temp_max = Gtk.Label(label=f"{temp_max_label:.0f} / ")
            temp_max.set_margin_start(10)
            temp_max.set_css_classes(['text-3','bold-2'])
            forecast_item_grid.attach(temp_max,2,0,1,1)
            
            #Min temp label ======
            temp_min_label = hourly_data.temperature_2m.get("data")[i]
            if page_name == 'weekly':
                temp_min_label = daily_data.temperature_2m_min.get("data")[i]

            temp_min = Gtk.Label(label=f"{temp_min_label:.0f}")
            temp_min.set_css_classes(['light-4'])
            temp_min.set_margin_top(5)
            forecast_item_grid.attach(temp_min,3,0,1,1)
