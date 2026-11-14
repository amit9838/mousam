import gi
import math
import cairo
from gettext import gettext as _

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from .CORE_GTKUtils import safe_set_draw_func, theme_rgba, draw_text, text_layout  # noqa: E402

# The sun's height through the day: a wave from midnight (left edge) through
# noon (top, in the middle) to midnight (right edge)
WAVE_HALF_WIDTH = 60
WAVE_AMPLITUDE = 30
WAVE_STEPS = 48  # line pieces for the whole wave
BODY_RADIUS = 6.5
SUN_GLOW_RADIUS = 15
MOON_GLOW_RADIUS = 12
# The day never gets shorter than this share of the 24 hours, nor longer than 1 minus it
MIN_DAY_FRACTION = 0.2
# The light above the horizon: how high it reaches, in pixels, and how strong it is
HORIZON_GLOW_HEIGHT = 11
HORIZON_GLOW_ALPHA = 0.15
# How far the middle of the horizon rises above its ends, in pixels
HORIZON_BEND = 3

# The sun's colour by how high it is, from 0 (on the horizon) to 1 (noon).
# Low down its light crosses the most air, which scatters the blue away, so
# it looks red-orange; it turns golden, then yellow as it climbs. The top
# colour stays a little yellow so the sun still shows on a light background.
SUN_COLOR_STOPS = (
    (0.0, (1.0, 0.38, 0.05)),    # red-orange, on the horizon
    (0.15, (1.0, 0.55, 0.10)),   # orange, golden hour
    (0.35, (1.0, 0.72, 0.18)),   # amber
    (0.65, (0.97, 0.83, 0.25)),  # yellow
    (1.0, (0.97, 0.88, 0.45)),   # pale yellow, noon
)
NIGHT_RGB = (0.55, 0.65, 1.0)
MOON_RGB = (0.92, 0.94, 1.0)


def sun_color(height: float) -> tuple:
    """The sun's colour (r, g, b) at this height, from 0 (horizon) to 1 (noon)."""
    low_height, low_rgb = SUN_COLOR_STOPS[0]
    if height <= low_height:
        return low_rgb
    for high_height, high_rgb in SUN_COLOR_STOPS[1:]:
        if height <= high_height:
            mix = (height - low_height) / (high_height - low_height)
            return tuple(a + (b - a) * mix for a, b in zip(low_rgb, high_rgb))
        low_height, low_rgb = high_height, high_rgb
    return low_rgb


def _wave_point(hours_from_noon: float) -> tuple:
    """Where the sun is at this time, as (x, y) from the centre of the drawing."""
    x = hours_from_noon / 12 * WAVE_HALF_WIDTH
    y = -WAVE_AMPLITUDE * math.cos(math.pi * hours_from_noon / 12)
    return x, y


def _wave_points(hours_from: float, hours_to: float) -> list:
    """The wave between two times, as (x, y) points from the centre."""
    steps = max(1, math.ceil(abs(hours_to - hours_from) / 24 * WAVE_STEPS))
    return [_wave_point(hours_from + (hours_to - hours_from) * i / steps) for i in range(steps + 1)]


class DrawDayNight:
    """The sun or moon on its way through the day, as seen from the ground.

    The wave is the sun's height over 24 hours, centred on noon. The horizon
    crosses it at sunrise and sunset, so it sits lower on long summer days and
    higher on short winter ones. is_day and progress (0 at sunrise / sunset,
    1 at sunset / sunrise) place the sun or moon on it.
    """

    def __init__(self, is_day: bool, progress: float, day_fraction: float, width: int, height: int):
        self.is_day = is_day
        self.status = _("Day") if is_day else _("Night")
        # Translators: the line in the sun's path where the sun rises and sets
        self.horizon_label = _("Horizon")

        # Hours from noon to sunset (and from sunrise to noon). The clamp
        # keeps the horizon off the very top and bottom (polar day and night).
        day_fraction = min(max(day_fraction, MIN_DAY_FRACTION), 1 - MIN_DAY_FRACTION)
        half_day = 12 * day_fraction
        progress = min(max(progress, 0), 1)

        # Everything below is in pixels from the centre, worked out once here
        # so that drawing stays light
        self.horizon_y = _wave_point(half_day)[1]
        self.day_points = _wave_points(-half_day, half_day)
        self.night_points = [_wave_points(-12, -half_day), _wave_points(half_day, 12)]

        # The part of the way already travelled, ending at the sun or moon.
        # Before sunrise the moon is on the left of the wave (after midnight).
        if is_day:
            body_hours = -half_day + progress * 2 * half_day
            self.travelled = [_wave_points(-half_day, body_hours)]
        else:
            body_hours = half_day + progress * (24 - 2 * half_day)
            if body_hours <= 12:
                self.travelled = [_wave_points(half_day, body_hours)]
            else:
                body_hours -= 24
                self.travelled = [_wave_points(half_day, 12), _wave_points(-12, body_hours)]
        self.body = _wave_point(body_hours)

        # How high the sun is, 0 on the horizon to 1 at noon: red-orange low,
        # yellow high
        height_factor = 0
        if is_day:
            noon_height = self.horizon_y + WAVE_AMPLITUDE
            height_factor = min(max((self.horizon_y - self.body[1]) / noon_height, 0), 1)
        self.sun_rgb = sun_color(height_factor)

        # The same colours along today's path: each stop where the path
        # reaches that height (0 at sunrise, 0.5 at noon, 1 at sunset), so the
        # path under the sun has the sun's colour
        horizon_cos = math.cos(math.pi * half_day / 12)
        self.path_stops = []
        for stop_height, rgb in SUN_COLOR_STOPS:
            stop_cos = horizon_cos + stop_height * (1 - horizon_cos)
            stop_hours = 12 / math.pi * math.acos(min(stop_cos, 1))
            offset = stop_hours / (2 * half_day)
            self.path_stops += [(0.5 - offset, rgb), (0.5 + offset, rgb)]

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(width + 20, height + 20)
        # Don't keep a parent container on self: the drawing area keeps self
        # alive (safe_set_draw_func), so self holding its parent would form a
        # cycle Python can't collect, and leak the card on every refresh.
        safe_set_draw_func(self.drawing_area, self, "on_draw")

    def on_draw(self, area, cr, width, height, data):
        cx, cy = width / 2, height / 2 - 6
        left, right = cx - WAVE_HALF_WIDTH - 4, cx + WAVE_HALF_WIDTH + 4
        horizon_y = round(cy + self.horizon_y) + 0.5
        # The horizon bows up HORIZON_BEND in the middle, like the curve of the
        # Earth. Its ends sit a little lower than horizon_y, so it still
        # crosses the wave exactly at sunrise and sunset.
        sunset_x = self.day_points[-1][0]
        half_length = right - cx
        end_y = horizon_y + HORIZON_BEND * (1 - (sunset_x / half_length) ** 2)
        middle_y = end_y - HORIZON_BEND

        # A soft light just above the horizon, the sun's colour by day and the
        # moon's by night, fading upwards and towards the sides
        glow_rgb = self.sun_rgb if self.is_day else NIGHT_RGB
        rise = cairo.LinearGradient(0, end_y, 0, middle_y - HORIZON_GLOW_HEIGHT)
        rise.add_color_stop_rgba(0, *glow_rgb, HORIZON_GLOW_ALPHA)
        rise.add_color_stop_rgba(1, *glow_rgb, 0)
        cr.push_group()
        cr.set_source(rise)
        self._horizon_curve(cr, left, right, end_y, 0)
        self._horizon_curve(cr, right, left, end_y, -HORIZON_GLOW_HEIGHT, start=False)
        cr.close_path()
        cr.fill()
        cr.pop_group_to_source()
        cr.mask(self._side_fade(left, right, 0, 0, 0, 1))

        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)

        # The whole way: day solid, night dotted and fading towards midnight
        cr.set_line_width(2)
        cr.set_source_rgba(*theme_rgba(area, 0.16))
        self._add_line(cr, cx, cy, self.day_points)
        cr.stroke()
        cr.set_dash([1, 4])
        cr.set_source(self._side_fade(left, right, *theme_rgba(area, 0.3)))
        for points in self.night_points:
            self._add_line(cr, cx, cy, points)
        cr.stroke()
        cr.set_dash([])

        # The part of today's (or tonight's) way already travelled
        cr.set_line_width(3)
        if self.is_day:
            sunrise_x, sunset_x = cx + self.day_points[0][0], cx + self.day_points[-1][0]
            gradient = cairo.LinearGradient(sunrise_x, 0, sunset_x, 0)
            for offset, rgb in sorted(self.path_stops):
                gradient.add_color_stop_rgb(offset, *rgb)
            cr.set_source(gradient)
        else:
            cr.set_source_rgba(*NIGHT_RGB, 0.8)
        for points in self.travelled:
            self._add_line(cr, cx, cy, points)
        cr.stroke()

        # Horizon, faded at the ends
        cr.set_line_width(1)
        cr.set_source(self._side_fade(left, right, *theme_rgba(area, 0.35)))
        self._horizon_curve(cr, left, right, end_y, 0)
        cr.stroke()

        body_x, body_y = cx + self.body[0], cy + self.body[1]
        if self.is_day:
            self._draw_sun(cr, body_x, body_y)
        else:
            self._draw_moon(cr, body_x, body_y)

        # "Horizon" under the middle of the line, where the wave is high above
        # it; left out when the horizon is so low it would touch Day / Night
        status_top = cy + WAVE_AMPLITUDE + BODY_RADIUS + 2
        label_top = middle_y + 2
        label_height = text_layout(area, self.horizon_label, "xx-small").get_pixel_size()[1]
        if label_top + label_height < status_top:
            draw_text(area, cr, self.horizon_label, cx, label_top, size="xx-small", alpha=0.45)

        # Day / Night under the wave
        draw_text(area, cr, self.status, cx, status_top, size="x-small", alpha=0.6)

    @staticmethod
    def _horizon_curve(cr, x_from, x_to, end_y, shift, start=True):
        """Add the horizon from x_from to x_to to the path, moved down by shift."""
        # A quadratic curve peaks halfway to its control point; Cairo draws
        # cubic ones, whose control points sit 2/3 of the way to it
        control_y = end_y - 2 * HORIZON_BEND
        pull_y = end_y + shift + 2 / 3 * (control_y - end_y)
        third = (x_to - x_from) / 3
        if start:
            cr.move_to(x_from, end_y + shift)
        else:
            cr.line_to(x_from, end_y + shift)
        cr.curve_to(x_from + third, pull_y, x_to - third, pull_y, x_to, end_y + shift)

    @staticmethod
    def _add_line(cr, cx, cy, points):
        """Add a line through points (from the centre cx, cy) to the path."""
        cr.move_to(cx + points[0][0], cy + points[0][1])
        for x, y in points[1:]:
            cr.line_to(cx + x, cy + y)

    @staticmethod
    def _side_fade(left, right, red, green, blue, alpha):
        """A colour that is clear at left and right and full in the middle."""
        fade = cairo.LinearGradient(left, 0, right, 0)
        fade.add_color_stop_rgba(0, red, green, blue, 0)
        fade.add_color_stop_rgba(0.5, red, green, blue, alpha)
        fade.add_color_stop_rgba(1, red, green, blue, 0)
        return fade

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
