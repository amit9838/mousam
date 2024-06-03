from gi.repository import Gio

class Settings:
    _instance = None
    APP_ID = "io.github.amit9838.mousam"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance.init_settings()
        return cls._instance

    def init_settings(self):
        self.settings = Gio.Settings(self.APP_ID)
        self._settings_map = {
            "added_cities": "added-cities",
            "selected_city": "selected-city",
            "is_using_dynamic_bg": "use-gradient-bg",
            "is_using_inch_for_prec": "use-inch-for-prec",
            "is_using_24h_clock": "use-24h-clock",
            "window_width": "window-width",
            "window_height": "window-height",
            "window_maximized": "window-maximized",
            "unit": "unit",
        }

    @property
    def added_cities(self):
        return self.settings.get_strv(self._settings_map["added_cities"])

    @added_cities.setter
    def added_cities(self, value):
        self.settings.set_strv(self._settings_map["added_cities"], value)

    @property
    def selected_city(self):
        return self.settings.get_string(self._settings_map["selected_city"])

    @selected_city.setter
    def selected_city(self, value):
        self.settings.set_string(self._settings_map["selected_city"], value)

    @property
    def is_using_dynamic_bg(self):
        return self.settings.get_boolean(self._settings_map["is_using_dynamic_bg"])

    @is_using_dynamic_bg.setter
    def is_using_dynamic_bg(self, value):
        self.settings.set_boolean(self._settings_map["is_using_dynamic_bg"], value)

    @property
    def is_using_inch_for_prec(self):
        return self.settings.get_boolean(self._settings_map["is_using_inch_for_prec"])

    @is_using_inch_for_prec.setter
    def is_using_inch_for_prec(self, value):
        self.settings.set_boolean(self._settings_map["is_using_inch_for_prec"], value)

    @property
    def is_using_24h_clock(self):
        return self.settings.get_boolean(self._settings_map["is_using_24h_clock"])

    @is_using_24h_clock.setter
    def is_using_24h_clock(self, value):
        self.settings.set_boolean(self._settings_map["is_using_24h_clock"], value)

    @property
    def window_width(self):
        return self.settings.get_int(self._settings_map["window_width"])

    @window_width.setter
    def window_width(self, value):
        self.settings.set_int(self._settings_map["window_width"], value)

    @property
    def window_height(self):
        return self.settings.get_int(self._settings_map["window_height"])

    @window_height.setter
    def window_height(self, value):
        self.settings.set_int(self._settings_map["window_height"], value)

    @property
    def window_maximized(self):
        return self.settings.get_boolean(self._settings_map["window_maximized"])

    @window_maximized.setter
    def window_maximized(self, value):
        self.settings.set_boolean(self._settings_map["window_maximized"], value)

    @property
    def unit(self):
        return self.settings.get_string(self._settings_map["unit"])

    @unit.setter
    def unit(self, value):
        self.settings.set_string(self._settings_map["unit"], value)

def get_settings():
    return Settings()

settings = get_settings()
