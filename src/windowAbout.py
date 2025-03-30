import gi
from gi.repository import Gtk, Adw
from gettext import gettext as _, pgettext as C_

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')


"""Present the app's about dialog."""
def AboutWindow(*args):
    about_window = Adw.AboutDialog(
        application_icon="io.github.amit9838.mousam",
        application_name="Mousam",
        comments = _("Weather at a glance"),
        developer_name="Amit Chaudhary",
        developers= ["Amit Chaudhary"],
        issue_url="https://github.com/amit9838/mousam/issues",
        version="1.4.0",
        website="https://amit9838.github.io/mousam/",
        copyright=_("Copyright © 2024 Mousam Developers"),
        license_type=Gtk.License(Gtk.License.GPL_3_0),
        translator_credits=_("translator-credits"),
    )
    
    about_window.present()