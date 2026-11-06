import gi
import cairo

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from .CORE_GTKUtils import safe_set_draw_func, theme_rgba  # noqa: E402

BAR_WIDTH = 10
PADDING_Y = 10


class DrawBar:
    """A small vertical bar in a faint track (the hourly precipitation amount).

    value is the share of the day's highest amount, from 0 to 1. Every hour
    shows the track, so dry hours and wet hours read on the same scale.
    """

    def __init__(self, value: float, rgb_color=(0.38, 0.7, 1)):
        self.value = max(0.0, min(value, 1.0))
        self.rgb = tuple(rgb_color)

        self.dw = Gtk.DrawingArea()
        self.dw.set_size_request(50, 60)
        safe_set_draw_func(self.dw, self, "draw")

    def draw(self, area, ctx, width, height, data):
        x = width / 2
        top = PADDING_Y + BAR_WIDTH / 2
        bottom = height - PADDING_Y - BAR_WIDTH / 2

        ctx.set_line_width(BAR_WIDTH)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)

        ctx.set_source_rgba(*theme_rgba(area, 0.08))
        ctx.move_to(x, top)
        ctx.line_to(x, bottom)
        ctx.stroke()

        if self.value <= 0:
            return

        ctx.set_source_rgba(*self.rgb, 0.9)
        ctx.move_to(x, bottom)
        ctx.line_to(x, bottom - (bottom - top) * self.value)
        ctx.stroke()
