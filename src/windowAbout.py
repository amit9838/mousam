import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw,Gio,GLib

def AboutWindow(parent,*args):
        dialog = Adw.AboutWindow.new()
        dialog.set_application_name(_("Weather"))
        dialog.set_application_icon("io.github.amit9838.weather")
        dialog.set_version("1.0.0")
        dialog.set_developer_name("Amit Chaudhary")
        dialog.set_license_type(Gtk.License(Gtk.License.GPL_3_0))
        dialog.set_comments(_("Beautiful and light weight weather app build using Gtk and python"))
        dialog.set_website("https://github.com/amit9838/weather")
        dialog.set_issue_url("https://github.com/amit9838/weather/issues")
        # dialog.add_credit_section("Contributors", ["name url"])
        dialog.set_copyright(_("Copyright © 2023 Weather Developers"))
        dialog.set_developers(["Amit Chaudhary"])
        # Translators: Please enter your credits here. (format: "Name https://example.com" or "Name <email@example.com>", no quotes)
        dialog.set_translator_credits(_("translator_credits"))
        dialog.set_transient_for(parent)
        dialog.present()
