from gi.repository import Gio

def get_measurement_type():
        settings = Gio.Settings.new("io.github.amit9838.mousam")
        return settings.get_string("measure-type")
