import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Pango  # noqa: E402

from .settings import settings  # noqa: E402
from .CORE_Icons import condition, bg_css, create_weather_icon  # noqa: E402
from .CORE_Helpers import (  # noqa: E402
    check_internet_connection,
    get_selected_city_name,
    get_timezone_from_selected_city,
)
from gettext import gettext as _  # noqa: E402

# Space between the content and the window edge
MARGIN = 25
# Smallest size, used by the loading and error pages
MIN_WIDTH, MIN_HEIGHT = 280, 220
# Longer city names are ellipsized
CITY_MAX_CHARS = 14

WIND_DIRECTIONS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
]


def wind_direction_name(degrees: Optional[float]) -> str:
    """Compass point (N, NNE, …) for a wind direction in degrees."""
    if degrees is None:
        return "--"
    return WIND_DIRECTIONS[int((degrees + 11.25) / 22.5) % 16]


def _label(text: str, css_classes: list, halign: Gtk.Align = Gtk.Align.START) -> Gtk.Label:
    label = Gtk.Label(label=text, halign=halign)
    for css_class in css_classes:
        label.add_css_class(css_class)
    return label


class CompactWeather(Gtk.Overlay):
    """The compact view: city, condition, temperature and a few details.

    Pages live in a Gtk.Stack (loader, error, content) so the window sizes
    itself to the visible page. The overlay only holds the hover button that
    goes back to the normal window.
    """

    def __init__(self, on_back_clicked, **kwargs):
        super().__init__(**kwargs)
        self.on_back_clicked = on_back_clicked
        self._clock_timeout_id = None
        self._rendered_weather = None  # current_weather the content was built from

        self.set_size_request(MIN_WIDTH, MIN_HEIGHT)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.set_child(self.stack)
        self._setup_back_button()

        # notify::is-ready is emitted from the fetch worker threads
        from .CORE_weatherData import weather_manager
        self._ready_handler_id = weather_manager.connect(
            "notify::is-ready", lambda *_: GLib.idle_add(self._show_data_if_new)
        )
        self.connect("destroy", self._on_destroy)

        self.refresh()

    # ---------- Data ----------

    def refresh(self) -> None:
        """Show the current data, or fetch it if there is none yet."""
        from .CORE_weatherData import weather_manager
        if weather_manager.is_ready:
            self._show_data_if_new()
            return

        if not check_internet_connection(force=True):
            self._show_error(_("No Internet"))
            return

        self._show_page("loader")
        from .CORE_Networking import fetch_all_weather_data_async
        fetch_all_weather_data_async(on_error=self._show_error)

    def _show_data_if_new(self) -> bool:
        """Build the content once per fetch, however often is-ready fires."""
        from .CORE_weatherData import weather_manager
        if weather_manager.is_ready and weather_manager.current_weather is not self._rendered_weather:
            self._build_content()
        return GLib.SOURCE_REMOVE

    # ---------- Pages ----------

    def _show_page(self, name: str) -> None:
        if self.stack.get_child_by_name(name) is None:
            if name == "loader":
                spinner = Adw.Spinner(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)
                spinner.set_size_request(32, 32)
                self.stack.add_named(spinner, "loader")
            elif name == "error":
                icon = Gtk.Image(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, pixel_size=64, opacity=0.5)
                # Click the icon to retry
                click = Gtk.GestureClick()
                click.connect("pressed", lambda *_: self.refresh())
                icon.add_controller(click)
                self.stack.add_named(icon, "error")
        self.stack.set_visible_child_name(name)

    def _show_error(self, message: str) -> bool:
        self._show_page("error")
        icon = self.stack.get_child_by_name("error")
        is_net_error = str(message) == _("No Internet")
        icon.set_from_icon_name("network-error-symbolic" if is_net_error else "computer-fail-symbolic")
        icon.set_tooltip_text(str(message))
        return GLib.SOURCE_REMOVE

    def _build_content(self) -> None:
        from .CORE_weatherData import weather_manager
        data = weather_manager.current_weather
        aq_data = weather_manager.air_pollution
        self._rendered_weather = data

        weather_code = str(data.weathercode.data if data.weathercode.data is not None else 0)
        is_night = data.is_day.data == 0
        # On the first build the view isn't in the window yet, so wait a tick
        GLib.idle_add(self._apply_background, weather_code + ("n" if is_night else ""))

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.set_margin_top(MARGIN)
        content.set_margin_bottom(MARGIN)
        content.set_margin_start(MARGIN)
        content.set_margin_end(MARGIN)
        content.append(self._build_header(data, weather_code, is_night))
        content.append(self._build_body(data, aq_data))

        old = self.stack.get_child_by_name("content")
        if old is not None:
            self.stack.remove(old)
        self.stack.add_named(content, "content")
        self.stack.set_visible_child_name("content")

    def _build_header(self, data, weather_code: str, is_night: bool) -> Gtk.Box:
        """City and condition on the left, the weather icon on the right."""
        header = Gtk.Box(spacing=12)

        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        city = _label(get_selected_city_name(), ["text-3xl", "font-bold", "opacity-90"])
        city.set_ellipsize(Pango.EllipsizeMode.END)
        city.set_max_width_chars(CITY_MAX_CHARS)
        city.set_xalign(0)
        text.append(city)
        text.append(_label(condition.get(weather_code, condition["0"]), ["text-xl"]))
        header.append(text)

        icon = create_weather_icon(weather_code + ("n" if is_night else ""), settings.icon_theme, 70)
        icon.set_halign(Gtk.Align.END)
        icon.set_valign(Gtk.Align.CENTER)
        header.append(icon)
        return header

    def _build_body(self, data, aq_data) -> Gtk.Box:
        """The temperature on the left, date, time and details on the right.

        A Gtk.Box, not a Gtk.Grid: a grid row lines up its children's text
        baselines, which pushes the details down and leaves a gap below them.
        """
        body = Gtk.Box(spacing=12)

        temp = data.temperature_2m.data
        lbl_temp = _label(f"{temp:.0f}°" if temp is not None else "--°", ["compact-temp"])
        lbl_temp.set_valign(Gtk.Align.START)
        lbl_temp.set_margin_top(25)
        body.append(lbl_temp)

        details = Gtk.Grid(column_spacing=8, hexpand=True, halign=Gtk.Align.END, valign=Gtk.Align.START)
        details.set_margin_top(15)

        self.lbl_time = _label("", ["compact-detail-value", "compact-time-value"], Gtk.Align.END)
        self.lbl_time.set_margin_bottom(5)
        details.attach(self.lbl_time, 0, 0, 2, 1)
        self._start_clock()

        wind = data.windspeed_10m
        wind_str = f"{wind.data} {wind.unit}" if wind.data is not None else "--"
        hum = data.relativehumidity_2m.data
        pres = data.surface_pressure
        aqi = aq_data.current_us_aqi if aq_data and aq_data.current_us_aqi is not None else "--"
        rows = [
            (_("Wind"), f"{wind_str} • {wind_direction_name(data.winddirection_10m.data)}"),
            (_("Hum."), f"{hum} %" if hum is not None else "-- %"),
            (_("Pres."), f"{pres.data:.1f} {pres.unit}" if pres.data is not None else "--"),
            (_("AQI"), str(aqi)),
        ]
        for row, (name, value) in enumerate(rows, start=1):
            details.attach(_label(name, ["compact-detail-label"]), 0, row, 1, 1)
            details.attach(_label(value, ["compact-detail-value"], Gtk.Align.END), 1, row, 1, 1)

        body.append(details)
        return body

    def _apply_background(self, code: str) -> bool:
        """Put the condition's background on the window (dynamic backgrounds)."""
        root = self.get_root()
        css_class = bg_css.get(code, "")
        if settings.is_using_dynamic_bg and root is not None and css_class:
            for cls in set(root.get_css_classes()) & set(bg_css.values()):
                root.remove_css_class(cls)
            root.add_css_class(css_class)
        return GLib.SOURCE_REMOVE

    # ---------- Clock ----------

    def _start_clock(self) -> None:
        self._stop_clock()
        self._timezone = ZoneInfo(get_timezone_from_selected_city())
        self._update_clock()
        self._clock_timeout_id = GLib.timeout_add_seconds(1, self._update_clock)

    def _update_clock(self) -> bool:
        now = datetime.datetime.now(self._timezone)
        time_format = "%H:%M" if settings.is_using_24h_clock else "%I:%M %p"
        self.lbl_time.set_label(f"{now.strftime('%d %B')} • {now.strftime(time_format)}")
        return GLib.SOURCE_CONTINUE

    def _stop_clock(self) -> None:
        if self._clock_timeout_id:
            GLib.source_remove(self._clock_timeout_id)
            self._clock_timeout_id = None

    # ---------- Back button ----------

    def _setup_back_button(self) -> None:
        self.btn_back = Gtk.Button(icon_name="view-fullscreen-symbolic", visible=False)
        self.btn_back.add_css_class("flat")
        self.btn_back.add_css_class("circular")
        self.btn_back.set_halign(Gtk.Align.END)
        self.btn_back.set_valign(Gtk.Align.START)
        self.btn_back.set_margin_top(5)
        self.btn_back.set_margin_end(5)
        self.btn_back.connect("clicked", self._on_back_clicked)
        self.add_overlay(self.btn_back)

        # Show the button only while the pointer is over the window
        motion = Gtk.EventControllerMotion()
        motion.connect("enter", lambda *_: self.btn_back.set_visible(True))
        motion.connect("leave", lambda *_: self.btn_back.set_visible(False))
        self.add_controller(motion)

    def _on_back_clicked(self, _button) -> None:
        if self.on_back_clicked:
            self.on_back_clicked()

    def _on_destroy(self, *_args) -> None:
        self._stop_clock()
        from .CORE_weatherData import weather_manager
        weather_manager.disconnect(self._ready_handler_id)


class CompactWeatherWindow(Adw.ApplicationWindow):
    def __init__(self, app, bg_classes=None, on_back_to_normal=None, **kwargs):
        super().__init__(application=app, **kwargs)
        self.on_back_to_normal = on_back_to_normal
        self.set_title(_("Mousam Compact"))
        # Not resizable: the window takes the size of its content
        self.set_resizable(False)
        self.connect("destroy", self._on_window_destroy)

        self.compact_view = CompactWeather(on_back_clicked=self._on_back)
        handle = Gtk.WindowHandle(child=self.compact_view)
        self.set_content(handle)

        self.update_bg(bg_classes)

    def update_bg(self, bg_classes) -> None:
        """Use the main window's weather background (dynamic backgrounds)."""
        if not settings.is_using_dynamic_bg:
            return
        self.add_css_class("bg-dark-overlay")
        valid_bgs = set(bg_css.values())
        for cls in set(self.get_css_classes()) & valid_bgs:
            self.remove_css_class(cls)
        for cls in bg_classes or []:
            if cls in valid_bgs:
                self.add_css_class(cls)

    def update_ui(self) -> None:
        self.compact_view.refresh()

    def _on_back(self) -> None:
        app = self.get_application()
        if app:
            app.activate_action("show-normal", None)

    def _on_window_destroy(self, *_args) -> None:
        app = self.get_application()
        if app and hasattr(app, "compact_window"):
            app.compact_window = None
