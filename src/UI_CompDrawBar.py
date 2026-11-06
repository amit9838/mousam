import gi
import cairo

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from .CORE_GTKUtils import safe_set_draw_func, theme_rgba  # noqa: E402

# Space kept free above and below the track
PADDING_Y = 6

# The triangle pointing at the current level
POINTER_WIDTH = 8
POINTER_HEIGHT = 10
POINTER_GAP = 3  # between its tip and the track


class DrawLevelBar:
    """A vertical gauge: a pill-shaped track filled from the bottom, and a pointer at the level.

    Used by the humidity, pressure and UV index cards.
    """

    def __init__(
        self,
        fill_fr: float = 0.5,
        rounded_cap: bool = True,
        width: int = 40,
        height: int = 90,
        line_w: int = 18,
        rgb_color=(0.38, 0.7, 1),
    ):
        self.fill_fr = max(0.0, min(fill_fr, 1.0))
        self.cap = cairo.LINE_CAP_ROUND if rounded_cap else cairo.LINE_CAP_BUTT
        self.line_w = line_w
        self.rgb = tuple(rgb_color)  # (r, g, b), each 0 to 1

        # The cards centre their labels ("100", "0") over this area, so the
        # space on the right is part of the area, not a margin: the track,
        # drawn in the middle, then lines up with the labels.
        self.dw = Gtk.DrawingArea()
        self.dw.set_size_request(width + 10, height)
        safe_set_draw_func(self.dw, self, "draw")

    def draw(self, area, ctx, width, height, data):
        x = width / 2
        # With round caps the stroke reaches half a line width past its ends
        inset = self.line_w / 2 if self.cap == cairo.LINE_CAP_ROUND else 0
        top = PADDING_Y + inset
        bottom = height - PADDING_Y - inset

        ctx.set_line_width(self.line_w)
        ctx.set_line_cap(self.cap)

        # Track
        ctx.set_source_rgba(*theme_rgba(area, 0.12))
        ctx.move_to(x, top)
        ctx.line_to(x, bottom)
        ctx.stroke()

        level = bottom - (bottom - top) * self.fill_fr

        # Fill, a little lighter at the bottom. A tiny level still shows as a dot.
        if self.fill_fr > 0:
            gradient = cairo.LinearGradient(0, bottom + inset, 0, level - inset)
            gradient.add_color_stop_rgba(0, *self.rgb, 0.7)
            gradient.add_color_stop_rgba(1, *self.rgb, 1)
            ctx.set_source(gradient)
            ctx.move_to(x, bottom)
            ctx.line_to(x, level)
            ctx.stroke()

        # Pointer at the level, left of the track. Drawn at 0 and 100 % too,
        # so an empty or a full bar still shows where the value is.
        tip_x = x - self.line_w / 2 - POINTER_GAP
        ctx.move_to(tip_x, level)
        ctx.line_to(tip_x - POINTER_WIDTH, level - POINTER_HEIGHT / 2)
        ctx.line_to(tip_x - POINTER_WIDTH, level + POINTER_HEIGHT / 2)
        ctx.close_path()
        ctx.set_source_rgba(*self.rgb, 1)
        # A thin stroke over the fill softens the corners
        ctx.set_line_width(1.5)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.fill_preserve()
        ctx.stroke()
