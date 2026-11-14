import math

import cairo
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from .CORE_GTKUtils import safe_set_draw_func, theme_rgba  # noqa: E402


def _drop_outline(steps: int = 24) -> tuple:
    """A drop, in unit coordinates: tip at y = -1, bottom at y = 1.

    The bottom is a circle; from its sides two curves rise to a pointed tip.
    Each curve leaves the circle along it (no corner where they meet), and
    starts at the tip slightly apart from the other, so the tip is sharp.
    """
    radius = 0.62
    centre_y = 1 - radius
    side = math.radians(38)  # where the curves leave the circle, above its middle
    tip = (0.0, -1.0)
    join = (radius * math.cos(side), centre_y - radius * math.sin(side))
    # The circle's direction at the join, going round towards the bottom
    along = (math.sin(side), math.cos(side))
    control_tip = (0.10, -0.62)
    control_join = (join[0] - 0.42 * along[0], join[1] - 0.42 * along[1])

    def curve(t: float) -> tuple:
        u = 1 - t
        return tuple(
            u ** 3 * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t ** 3 * p3
            for p0, p1, p2, p3 in zip(tip, control_tip, control_join, join)
        )

    right = [curve(i / steps) for i in range(steps)]
    bottom = [
        (radius * math.cos(a), centre_y + radius * math.sin(a))
        for a in (-side + (math.pi + 2 * side) * i / (2 * steps) for i in range(2 * steps))
    ]
    left = [(-x, y) for x, y in reversed(right)]
    return tuple(right + bottom + left)


DROP_POINTS = _drop_outline()
DROP_HALF_WIDTH = max(x for x, _y in DROP_POINTS)

# The water: light at the top, deep at the bottom
WATER_TOP_RGB = (0.60, 0.85, 1.0)
WATER_BOTTOM_RGB = (0.10, 0.45, 0.95)

# The drops around the main one, in the order they join it: (size, centre x,
# centre y, opacity), sizes and offsets as shares of the main drop's height.
# They are smaller and fainter, as if further away, and lean like rain
# falling in a light wind.
EXTRA_DROPS = (
    (0.58, 0.56, -0.40, 0.75),   # top right, higher up
    (0.55, -0.52, 0.22, 0.70),   # left, lower down
    (0.42, 0.92, -0.05, 0.55),   # far right, the smallest, furthest away
)
EXTRA_DROP_TILT = 12  # degrees
# The clear gap around the main drop, where it covers the ones behind (px)
DROP_GAP = 1.5
PADDING = 1


class DrawRainDrops:
    """One to four drops of rain: the main one in the middle, then one at the
    top right, one on the left, and a smallest one far right.

    The outlines take the widget's colour: give the drawing area a colour
    class (text-rain) so they follow the theme.
    """

    def __init__(self, count: int, height: int):
        count = min(max(count, 1), 1 + len(EXTRA_DROPS))
        self.half = height / 2  # the main drop's half height

        # Each drop as (half height, centre x, centre y, tilt in radians,
        # opacity), from the main drop's centre. Drawn back to front: the
        # faintest (furthest away) first, the main drop last.
        tilt = math.radians(EXTRA_DROP_TILT)
        self.extras = sorted(
            ((size * self.half, dx * height, dy * height, tilt, opacity)
             for size, dx, dy, opacity in EXTRA_DROPS[:count - 1]),
            key=lambda drop: drop[4],
        )

        # The area fits every drop, with the main one centred up and down, so
        # it lines up with the text next to it whatever is around it
        xs, ys = [-DROP_HALF_WIDTH * self.half, DROP_HALF_WIDTH * self.half], [self.half]
        for half, cx, cy, angle, _opacity in self.extras:
            for x, y in DROP_POINTS:
                xs.append(cx + half * (x * math.cos(angle) - y * math.sin(angle)))
                ys.append(cy + half * (x * math.sin(angle) + y * math.cos(angle)))
        reach = max(abs(min(ys)), max(ys))
        self.origin_x = -min(xs) + PADDING
        width = max(xs) - min(xs) + 2 * PADDING
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(math.ceil(width), math.ceil(2 * (reach + PADDING)))
        safe_set_draw_func(self.drawing_area, self, "draw")

    def draw(self, area, cr, width, height, data):
        # Snap the main drop to the pixel grid, so it stays crisp: its tip is a
        # point on the middle line, so that line runs through the middle of a
        # pixel; its top and bottom fall on pixel edges (the height is whole)
        cx, cy = math.floor(self.origin_x) + 0.5, round(height / 2)
        outline = theme_rgba(area, 0.85)

        if self.extras:
            # The drops behind, each faded by its opacity, then a clear gap
            # cut around the main drop so the drops stay apart
            cr.push_group()
            for half, dx, dy, angle, opacity in self.extras:
                cr.push_group()
                self._draw_drop(cr, cx + dx, cy + dy, half, angle, outline)
                cr.pop_group_to_source()
                cr.paint_with_alpha(opacity)
            cr.set_operator(cairo.OPERATOR_CLEAR)
            self._drop_path(cr, cx, cy, self.half, 0)
            cr.set_line_width(2 * DROP_GAP)
            cr.stroke_preserve()
            cr.fill()
            cr.pop_group_to_source()
            cr.paint()

        self._draw_drop(cr, cx, cy, self.half, 0, outline)

    @staticmethod
    def _drop_path(cr, cx, cy, half, angle):
        """Add a drop to the path: centred at cx, cy, half tall, leaning by angle."""
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        for i, (x, y) in enumerate(DROP_POINTS):
            px = cx + half * (x * cos_a - y * sin_a)
            py = cy + half * (x * sin_a + y * cos_a)
            (cr.line_to if i else cr.move_to)(px, py)
        cr.close_path()

    @classmethod
    def _draw_drop(cls, cr, cx, cy, half, angle, outline):
        """One full drop: water, a glint of light, and its outline."""
        line_width = max(1.0, half / 8)
        cr.save()
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cls._drop_path(cr, cx, cy, half, angle)
        drop = cr.copy_path()
        cr.clip()

        # The water, along the drop (it leans with it)
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        water = cairo.LinearGradient(cx + half * sin_a, cy - half * cos_a, cx - half * sin_a, cy + half * cos_a)
        water.add_color_stop_rgb(0, *WATER_TOP_RGB)
        water.add_color_stop_rgb(1, *WATER_BOTTOM_RGB)
        cr.set_source(water)
        cr.paint()

        # A small curved glint on the round part, like light on water
        glint_x = cx - half * 0.38 * sin_a
        glint_y = cy + half * 0.38 * cos_a
        cr.set_source_rgba(1, 1, 1, 0.55)
        cr.set_line_width(line_width * 1.1)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.arc(glint_x, glint_y, half * DROP_HALF_WIDTH * 0.55,
               math.radians(195) + angle, math.radians(235) + angle)
        cr.stroke()

        # The outline, inside the edge (a double width line, clipped to the
        # drop), so it stays crisp and doesn't make the drop look bigger
        cr.append_path(drop)
        cr.set_line_width(line_width * 2)
        cr.set_source_rgba(*outline)
        cr.stroke()
        cr.restore()
