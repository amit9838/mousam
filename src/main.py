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
from .mousam import WeatherMainWindow
from .config import settings

gi.require_version('Adw', '1')
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, Adw, Gdk


class WeatherApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='io.github.amit9838.mousam',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.main_window = None
        self.compact_window = None

        self.set_accels_for_action("win.preferences", ['<primary>comma'])
        self.set_accels_for_action("win.shortcuts", ['<primary>question'])
        
        # Mode switching actions
        self.create_action("show-compact", self._on_show_compact)
        self.create_action("show-normal", self._on_show_normal)
        
        # Centralized auto-refresh
        from .utils import AutoRefreshTimer
        self.auto_refresh = AutoRefreshTimer(self._on_auto_refresh_tick)

    def do_activate(self):
        global css_provider
        CSS_PATH = os.path.dirname(os.path.realpath(__file__)) + "/css/"
        css_provider = Gtk.CssProvider()
        Priority = Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        with open(CSS_PATH+'style.css', 'r') as css_file:
            css = bytes(css_file.read(), 'utf-8')
        css_provider.load_from_data(css,len(css))
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Priority)

        if not self.main_window:
            self.main_window = WeatherMainWindow(application=self)

        if settings.window_maximized:
            self.main_window.maximize()

        self.main_window.present()
        self.auto_refresh.setup()

    def _on_auto_refresh_tick(self):
        from .utils import fetch_all_weather_data_async, show_notification
        
        def on_success():
            show_notification(self)
            # Notify all windows to refresh UI
            if self.main_window:
                self.main_window._on_data_fetch_success(is_auto=True)
            if self.compact_window:
                self.compact_window.update_ui()
                
        fetch_all_weather_data_async(on_success=on_success)

    def _on_show_compact(self, *args):
        if not self.main_window: return
        
        bg_classes = self.main_window.get_css_classes()
        self.main_window.hide()
        
        if not self.compact_window:
            from .UI_CompactWeather import CompactWeatherWindow
            self.compact_window = CompactWeatherWindow(
                self, 
                bg_classes=bg_classes,
                on_back_to_normal=lambda: self.activate_action("show-normal", None)
            )
            self.compact_window.connect("destroy", self._on_compact_destroy)
        else:
            self.compact_window.update_bg(bg_classes)
            self.compact_window.update_ui()
            
        self.compact_window.present()

    def _on_show_normal(self, *args):
        if self.main_window:
            self.main_window.present()
        if self.compact_window:
            self.compact_window.hide()

    def _on_compact_destroy(self, *args):
        # If compact window is closed and main window is hidden, quit the app
        if self.main_window and not self.main_window.get_visible():
            self.main_window.close()

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action."""
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = WeatherApplication()
    return app.run(sys.argv)
