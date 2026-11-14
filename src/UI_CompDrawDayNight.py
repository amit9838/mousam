import gi
import math
import cairo
from gettext import gettext as _

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from .CORE_GTKUtils import safe_set_draw_func, theme_rgba, draw_text  # noqa: E402

ORBIT_RADIUS = 38
BODY_RADIUS = 6.5
SUN_GLOW_RADIUS = 15
MOON_GLOW_RADIUS = 12

SUNRISE_RGB = (1.0, 0.47, 0.0)   # orange 3
NOON_RGB = (0.96, 0.83, 0.18)    # yellow 3
NIGHT_RGB = (0.55, 0.65, 1.0)
MOON_RGB = (0.92, 0.94, 1.0)


class DrawDayNight:
    """The sun or moon on its way round a circle: day above the horizon, night below.

    angle is in degrees on the circle: 180 → 360 is sunrise → sunset through
    the top, 0 → 180 is sunset → sunrise through the bottom.
    """

    def __init__(self, angle: float, width: int, height: int):
        self.angle = angle
        self.is_day = 180 <= angle <= 360
        self.status = _("Day") if self.is_day else _("Night")

        # 0 on the horizon, 1 at the top: the sun is orange low and yellow high
        height_factor = abs(math.sin(math.radians(self.angle))) if self.is_day else 0
        self.sun_rgb = tuple(a + (b - a) * height_factor for a, b in zip(SUNRISE_RGB, NOON_RGB))

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(width + 20, height + 20)
        # Don't keep a parent container on self: the drawing area keeps self
        # alive (safe_set_draw_func), so self holding its parent would form a
        # cycle Python can't collect, and leak the card on every refresh.
        safe_set_draw_func(self.drawing_area, self, "on_draw")

    def on_draw(self, area, cr, width, height, data):
        cx, cy = width / 2, height / 2 - 6
        r = ORBIT_RADIUS
        rad = math.radians(self.angle)
        body_x, body_y = cx + r * math.cos(rad), cy + r * math.sin(rad)

        cr.set_line_cap(cairo.LINE_CAP_ROUND)

        # The orbit: day half solid, night half dotted
        cr.set_line_width(2)
        cr.set_source_rgba(*theme_rgba(area, 0.16))
        cr.arc(cx, cy, r, math.pi, 2 * math.pi)
        cr.stroke()
        cr.set_dash([1, 4])
        cr.set_source_rgba(*theme_rgba(area, 0.22))
        cr.arc(cx, cy, r, 0, math.pi)
        cr.stroke()
        cr.set_dash([])

        # The part of today's (or tonight's) path already travelled
        cr.set_line_width(3)
        if self.is_day:
            gradient = cairo.LinearGradient(cx - r, 0, cx + r, 0)
            gradient.add_color_stop_rgb(0, *SUNRISE_RGB)
            gradient.add_color_stop_rgb(0.5, *NOON_RGB)
            gradient.add_color_stop_rgb(1, *SUNRISE_RGB)
            cr.set_source(gradient)
            cr.arc(cx, cy, r, math.pi, rad)
        else:
            cr.set_source_rgba(*NIGHT_RGB, 0.8)
            cr.arc(cx, cy, r, 0, rad)
        cr.stroke()

        # Horizon
        cr.set_line_width(1)
        cr.set_source_rgba(*theme_rgba(area, 0.25))
        cr.move_to(cx - r - 12, round(cy) + 0.5)
        cr.line_to(cx + r + 12, round(cy) + 0.5)
        cr.stroke()

        if self.is_day:
            self._draw_sun(cr, body_x, body_y)
        else:
            self._draw_moon(cr, body_x, body_y)

        # Day / Night under the circle
        draw_text(area, cr, self.status, cx, cy + r + BODY_RADIUS + 2, size="x-small", alpha=0.6)

    def _draw_sun(self, cr, x, y):
        glow = cairo.RadialGradient(x, y, BODY_RADIUS * 0.5, x, y, SUN_GLOW_RADIUS)
        glow.add_color_stop_rgba(0, *self.sun_rgb, 0.55)
        glow.add_color_stop_rgba(1, *self.sun_rgb, 0)
        cr.set_source(glow)
        cr.arc(x, y, SUN_GLOW_RADIUS, 0, 2 * math.pi)
        cr.fill()

        cr.set_source_rgb(*self.sun_rgb)
        cr.arc(x, y, BODY_RADIUS, 0, 2 * math.pi)
        cr.fill()

    def _draw_moon(self, cr, x, y):
        glow = cairo.RadialGradient(x, y, BODY_RADIUS * 0.5, x, y, MOON_GLOW_RADIUS)
        glow.add_color_stop_rgba(0, *NIGHT_RGB, 0.45)
        glow.add_color_stop_rgba(1, *NIGHT_RGB, 0)
        cr.set_source(glow)
        cr.arc(x, y, MOON_GLOW_RADIUS, 0, 2 * math.pi)
        cr.fill()

        # A crescent: a disc with an offset disc cut out of it
        cr.push_group()
        cr.set_source_rgb(*MOON_RGB)
        cr.arc(x, y, BODY_RADIUS, 0, 2 * math.pi)
        cr.fill()
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.arc(x + BODY_RADIUS * 0.55, y - BODY_RADIUS * 0.35, BODY_RADIUS * 0.85, 0, 2 * math.pi)
        cr.fill()
        cr.pop_group_to_source()
        cr.paint()
