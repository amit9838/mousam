# main.py
#
# Copyright 2024 Amit
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import sys
import gi

gi.require_version('Adw', '1')
gi.require_version('Gtk', '4.0')

from gi.repository import Gtk, Gio, Adw, Gdk
from .mousam import WeatherMainWindow

class WeatherApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='io.github.amit9838.mousam',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.settings = Gio.Settings(schema_id="io.github.amit9838.mousam")
        self.main_window = None

    def do_activate(self):
        win = self.props.active_window
        global css_provider
        CSS_PATH = os.path.dirname(os.path.realpath(__file__)) + "/css/"
        css_provider = Gtk.CssProvider()
        Priority = Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        with open(CSS_PATH+'style.css', 'r') as css_file:
            css = bytes(css_file.read(), 'utf-8')
        css_provider.load_from_data(css,len(css))
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Priority)

        launch_maximized = self.settings.get_boolean("launch-maximized")

        if not win:
            win = WeatherMainWindow(application=self)

        if launch_maximized:
            win.maximize()

        win.present()

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = WeatherApplication()
    return app.run(sys.argv)
