import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from .CORE_GTKUtils import safe_set_draw_func, theme_rgba  # noqa: E402

TICKS = 35
HEIGHT = 22
TICK_WIDTH_RATIO = 0.5  # tick width as a share of the space between ticks

# Default colour of the filled ticks: the app's blue, (r, g, b) from 0 to 1
FILLED_RGB = (0.38, 0.7, 1)
# Unfilled ticks use the same grey as the tracks of the other gauges
EMPTY_ALPHA = 0.12


class DrawTickGauge:
    """A horizontal gauge made of vertical ticks, filled from the left.

    fill_fr is the level, from 0 to 1. Used by the pressure card.
    """

    def __init__(self, fill_fr: float, rgb_color=FILLED_RGB):
        fill_fr = max(0.0, min(fill_fr, 1.0))
        self.filled = round(fill_fr * TICKS)
        self.filled_rgba = (*rgb_color, 1)

        self.dw = Gtk.DrawingArea()
        self.dw.set_hexpand(True)
        self.dw.set_size_request(-1, HEIGHT)
        safe_set_draw_func(self.dw, self, "draw")

    def draw(self, area, ctx, width, height, data):
        empty_rgba = theme_rgba(area, EMPTY_ALPHA)

        # The ticks span the whole width: the outer ones touch the edges
        tick_width = max(1.5, width / TICKS * TICK_WIDTH_RATIO)
        pitch = (width - tick_width) / (TICKS - 1)

        for i in range(TICKS):
            ctx.set_source_rgba(*(self.filled_rgba if i < self.filled else empty_rgba))
            ctx.rectangle(i * pitch, 0, tick_width, height)
            ctx.fill()
