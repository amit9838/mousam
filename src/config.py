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

    @property
    def added_cities(self):
        return self.settings.get_strv("added-cities")

    @added_cities.setter
    def added_cities(self, value):
        self.settings.set_strv("added-cities", value)

    @property
    def selected_city(self):
        return self.settings.get_string("selected-city")

    @selected_city.setter
    def selected_city(self, value):
        self.settings.set_string("selected-city", value)

    @property
    def is_using_dynamic_bg(self):
        return self.settings.get_boolean("use-gradient-bg")

    @is_using_dynamic_bg.setter
    def is_using_dynamic_bg(self, value):
        self.settings.set_boolean("use-gradient-bg", value)

    @property
    def is_using_inch_for_prec(self):
        return self.settings.get_boolean("use-inch-for-prec")

    @is_using_inch_for_prec.setter
    def is_using_inch_for_prec(self, value):
        self.settings.set_boolean("use-inch-for-prec", value)

    @property
    def is_using_24h_clock(self):
        return self.settings.get_boolean("use-24h-clock")

    @is_using_24h_clock.setter
    def is_using_24h_clock(self, value):
        self.settings.set_boolean("use-24h-clock", value)

    @property
    def window_width(self):
        return self.settings.get_int("window-width")

    @window_width.setter
    def window_width(self, value):
        self.settings.set_int("window-width", value)

    @property
    def window_height(self):
        return self.settings.get_int("window-height")

    @window_height.setter
    def window_height(self, value):
        self.settings.set_int("window-height", value)

    @property
    def window_maximized(self):
        return self.settings.get_boolean("window-maximized")

    @window_maximized.setter
    def window_maximized(self, value):
        self.settings.set_boolean("window-maximized", value)

    @property
    def unit(self):
        return self.settings.get_string("unit")

    @unit.setter
    def unit(self, value):
        self.settings.set_string("unit", value)


def get_settings():
    return Settings()


settings = get_settings()
