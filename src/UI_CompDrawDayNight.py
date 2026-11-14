import gi
import math
import time
import cairo
from gettext import gettext as _

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk  # noqa: E402

from .CORE_GTKUtils import safe_set_draw_func, theme_rgba, draw_text, text_layout, weak_connect  # noqa: E402
from .configs import DAY_NIGHT_UPDATE_SECONDS, LUNAR_CYCLE_DAYS, NEW_MOON_REFERENCE  # noqa: E402

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
# Twilight, the blue hour just after sunset and before sunrise: a soft blue
# band under the horizon, how deep it reaches, in pixels, and how strong it is
TWILIGHT_DEPTH = 9
TWILIGHT_ALPHA = 0.22
TWILIGHT_RGB = (0.38, 0.48, 0.95)

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
DAY_SECONDS = 24 * 3600


def sun_position(now: float, sunrise: float, sunset: float) -> tuple:
    """Whether the sun is up, and how far along it is (0 to 1).

    By day progress runs from sunrise to sunset, by night from sunset to the
    next sunrise. All are Unix timestamps, so time zones and daylight saving
    changes don't matter. sunrise and sunset are today's; on other days the
    same times are used, a few minutes off at most.
    """
    # Polar night or day (or missing times): no sunrise and sunset to place it by
    day_length = sunset - sunrise
    if day_length <= 0:
        return False, 0.5
    if day_length >= DAY_SECONDS:
        return True, 0.5

    # Move sunrise and sunset by whole days so that now is in the 24 hours
    # starting at sunrise
    days = math.floor((now - sunrise) / DAY_SECONDS)
    sunrise += days * DAY_SECONDS
    sunset += days * DAY_SECONDS
    if now < sunset:
        return True, (now - sunrise) / (sunset - sunrise)
    next_sunrise = sunrise + DAY_SECONDS
    return False, (now - sunset) / (next_sunrise - sunset)


def moon_phase(now: float) -> float:
    """The moon's phase at this Unix timestamp: 0 new, 0.25 first quarter,
    0.5 full, 0.75 last quarter. Accurate to about a day."""
    return ((now - NEW_MOON_REFERENCE) / DAY_SECONDS / LUNAR_CYCLE_DAYS) % 1


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
    higher on short winter ones. sunrise and sunset are today's, as Unix
    timestamps. While shown, the sun or moon moves every
    DAY_NIGHT_UPDATE_SECONDS. southern mirrors the moon's phase, as it looks
    from the southern hemisphere.
    """

    def __init__(self, sunrise: float, sunset: float, southern: bool, width: int, height: int):
        self.sunrise = sunrise
        self.sunset = sunset
        self.southern = southern
        # Translators: the line in the sun's path where the sun rises and sets
        self.horizon_label = _("Horizon")

        # Hours from noon to sunset (and from sunrise to noon). The clamp
        # keeps the horizon off the very top and bottom (polar day and night).
        day_fraction = (sunset - sunrise) / DAY_SECONDS
        day_fraction = min(max(day_fraction, MIN_DAY_FRACTION), 1 - MIN_DAY_FRACTION)
        self.half_day = 12 * day_fraction

        # Everything below is in pixels from the centre, worked out once here
        # (or once per move) so that drawing stays light
        self.horizon_y = _wave_point(self.half_day)[1]
        self.day_points = _wave_points(-self.half_day, self.half_day)
        self.night_points = [_wave_points(-12, -self.half_day), _wave_points(self.half_day, 12)]

        # The sun's colours along today's path: each stop where the path
        # reaches that height (0 at sunrise, 0.5 at noon, 1 at sunset), so the
        # path under the sun has the sun's colour
        horizon_cos = math.cos(math.pi * self.half_day / 12)
        self.path_stops = []
        for stop_height, rgb in SUN_COLOR_STOPS:
            stop_cos = horizon_cos + stop_height * (1 - horizon_cos)
            stop_hours = 12 / math.pi * math.acos(min(stop_cos, 1))
            offset = stop_hours / (2 * self.half_day)
            self.path_stops += [(0.5 - offset, rgb), (0.5 + offset, rgb)]
        self.path_stops.sort()

        self._update_id = 0
        self._move_to_now()

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(width + 20, height + 20)
        # Don't keep a parent container on self: the drawing area keeps self
        # alive (safe_set_draw_func), so self holding its parent would form a
        # cycle Python can't collect, and leak the card on every refresh.
        safe_set_draw_func(self.drawing_area, self, "on_draw")
        # Move only while shown: the timer stops when the card goes
        weak_connect(self.drawing_area, "map", self._start_updates)
        weak_connect(self.drawing_area, "unmap", self._stop_updates)

    # ---------- Moving with the time ----------

    def _start_updates(self, *_args) -> None:
        self._stop_updates()
        self._on_update()
        self._update_id = GLib.timeout_add_seconds(DAY_NIGHT_UPDATE_SECONDS, self._on_update)

    def _stop_updates(self, *_args) -> None:
        if self._update_id:
            GLib.source_remove(self._update_id)
            self._update_id = 0

    def _on_update(self) -> bool:
        self._move_to_now()
        self.drawing_area.queue_draw()
        return GLib.SOURCE_CONTINUE

    def _move_to_now(self) -> None:
        """Place the sun or moon for the current time."""
        now = time.time()
        is_day, progress = sun_position(now, self.sunrise, self.sunset)
        progress = min(max(progress, 0), 1)
        half_day = self.half_day
        self.is_day = is_day
        self.status = _("Day") if is_day else _("Night")

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

        # The moon's lit part, as points from its centre. Its outer edge is a
        # half circle; the terminator (where light meets shadow) is a half
        # ellipse, as wide as cos(phase) of the radius: on the lit side for a
        # crescent, on the dark side for a gibbous moon.
        phase = moon_phase(now)
        self.moon_light = (1 - math.cos(2 * math.pi * phase)) / 2
        # In the north the waxing moon is lit on the right, in the south on the left
        side = 1 if (phase < 0.5) != self.southern else -1
        terminator = math.cos(2 * math.pi * phase)
        steps = 16
        edge = [(-math.pi / 2 + math.pi * i / steps) for i in range(steps + 1)]
        self.moon_lit_points = (
            [(side * BODY_RADIUS * math.cos(a), BODY_RADIUS * math.sin(a)) for a in edge]
            + [(side * terminator * BODY_RADIUS * math.cos(a), BODY_RADIUS * math.sin(a)) for a in reversed(edge)]
        )

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

        # Twilight: a soft blue band just under the horizon, where the sun is
        # only a little below it, fading downwards and towards the sides
        dusk = cairo.LinearGradient(0, middle_y, 0, end_y + TWILIGHT_DEPTH)
        dusk.add_color_stop_rgba(0, *TWILIGHT_RGB, TWILIGHT_ALPHA)
        dusk.add_color_stop_rgba(1, *TWILIGHT_RGB, 0)
        cr.push_group()
        cr.set_source(dusk)
        self._horizon_curve(cr, left, right, end_y, 0)
        self._horizon_curve(cr, right, left, end_y, TWILIGHT_DEPTH, start=False)
        cr.close_path()
        cr.fill()
        cr.pop_group_to_source()
        cr.mask(self._side_fade(left, right, 0, 0, 0, 1))

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
            for offset, rgb in self.path_stops:
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
        # The glow is stronger the more of the moon is lit
        glow = cairo.RadialGradient(x, y, BODY_RADIUS * 0.5, x, y, MOON_GLOW_RADIUS)
        glow.add_color_stop_rgba(0, *NIGHT_RGB, 0.15 + 0.3 * self.moon_light)
        glow.add_color_stop_rgba(1, *NIGHT_RGB, 0)
        cr.set_source(glow)
        cr.arc(x, y, MOON_GLOW_RADIUS, 0, 2 * math.pi)
        cr.fill()

        # The dark part stays faintly visible, so a new moon still shows
        cr.set_source_rgba(*NIGHT_RGB, 0.35)
        cr.arc(x, y, BODY_RADIUS, 0, 2 * math.pi)
        cr.fill()

        # The lit part, for today's phase
        cr.set_source_rgb(*MOON_RGB)
        self._add_line(cr, x, y, self.moon_lit_points)
        cr.close_path()
        cr.fill()

        # A thin rim, so a full moon still shows on a light background
        cr.set_line_width(1)
        cr.set_source_rgba(*NIGHT_RGB, 0.7)
        cr.arc(x, y, BODY_RADIUS - 0.5, 0, 2 * math.pi)
        cr.stroke()
