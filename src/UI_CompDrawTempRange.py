import gi
import cairo

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from .CORE_GTKUtils import safe_set_draw_func, theme_rgba  # noqa: E402

BAR_HEIGHT = 6
LOW_RGB = (0.38, 0.7, 1)    # the blue used across the drawings
HIGH_RGB = (0.93, 0.63, 0.32)  # warm orange


class DrawTempRange:
    """A day's low-to-high temperature range on a scale shared by the whole week.

    A faint pill-shaped track spans the week's lowest to highest temperature;
    the day's range is filled over it, from blue at the low end to orange at
    the high end. Used by the weekly forecast.
    """

    def __init__(self, low: float, high: float, week_min: float, week_max: float):
        span = week_max - week_min
        if span > 0:
            self.start_fr = (low - week_min) / span
            self.end_fr = (high - week_min) / span
        else:
            self.start_fr, self.end_fr = 0.0, 1.0
        self.start_fr = max(0.0, min(self.start_fr, 1.0))
        self.end_fr = max(self.start_fr, min(self.end_fr, 1.0))

        self.dw = Gtk.DrawingArea()
        self.dw.set_size_request(56, 20)
        self.dw.set_valign(Gtk.Align.CENTER)
        safe_set_draw_func(self.dw, self, "draw")

    def draw(self, area, ctx, width, height, data):
        y = height / 2
        # Round caps reach half the line width past each end
        left = BAR_HEIGHT / 2
        right = width - BAR_HEIGHT / 2
        length = right - left

        ctx.set_line_width(BAR_HEIGHT)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)

        # Track
        ctx.set_source_rgba(*theme_rgba(area, 0.1))
        ctx.move_to(left, y)
        ctx.line_to(right, y)
        ctx.stroke()

        # The day's range. A day with no range still shows as a dot.
        start = left + length * self.start_fr
        end = left + length * self.end_fr
        gradient = cairo.LinearGradient(start, 0, max(end, start + 1), 0)
        gradient.add_color_stop_rgb(0, *LOW_RGB)
        gradient.add_color_stop_rgb(1, *HIGH_RGB)
        ctx.set_source(gradient)
        ctx.move_to(start, y)
        ctx.line_to(end, y)
        ctx.stroke()
