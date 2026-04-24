import gi
from gi.repository import Gtk, Adw
from gettext import gettext as _

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')


def show_about_window(parent_window: Gtk.Window = None) -> None:
    """Present the app's about dialog."""
    about = Adw.AboutDialog(
        application_name="Mousam",
        application_icon="io.github.amit9838.mousam",
        version="1.5.0",
        comments=_("Weather at a glance"),
        developer_name="Amit Chaudhary",
        developers=["Amit Chaudhary"],
        copyright=_("Copyright © 2024 Mousam Developers"),
        license_type=Gtk.License.GPL_3_0,
        website="https://amit9838.github.io/mousam/",
        issue_url="https://github.com/amit9838/mousam/issues",
        translator_credits=_("translator-credits"),
    )


    about.present()