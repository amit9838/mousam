import math

import cairo
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from .CORE_GTKUtils import safe_set_draw_func, theme_rgba  # noqa: E402

TICKS = 35  # odd, so one tick sits exactly in the middle
CENTER = TICKS // 2
TICK_WIDTH_RATIO = 0.5  # tick width as a share of the space between ticks

POINTER_HEIGHT = 6  # the triangle above the ticks
POINTER_GAP = 3     # between the triangle and the ticks
TICK_HEIGHT = 14
HEIGHT = POINTER_HEIGHT + POINTER_GAP + TICK_HEIGHT

# The ticks are the theme's grey. Around the current value they get
# gradually brighter, peaking at the value, with a soft glow behind them.
GREY_ALPHA = 0.25   # ticks far from the value
PEAK_ALPHA = 0.8    # the tick at the value
SPREAD = 1.5        # how many ticks the brightening reaches out on each side
GLOW_ALPHA = 0.12   # the glow at its centre; it fades out to nothing
GLOW_WIDTH = 2.5    # the glow's reach on each side, in ticks
POINTER_ALPHA = 0.9


class DrawTickGauge:
    """A horizontal leveler made of vertical ticks, centred on the best value.

    The ticks are grey, and get gradually brighter around the current value,
    with a soft glow behind it. fill_fr is the position, from 0 (lowest) to
    1 (highest); 0.5 is the middle. A triangle above the ticks points at it.
    Used by the pressure card.
    """

    def __init__(self, fill_fr: float):
        self.fill_fr = max(0.0, min(fill_fr, 1.0))
        # Each tick's opacity: a bell curve around the value
        value_tick = self.fill_fr * (TICKS - 1)
        self.alphas = [
            GREY_ALPHA + (PEAK_ALPHA - GREY_ALPHA) * math.exp(-0.5 * ((i - value_tick) / SPREAD) ** 2)
            for i in range(TICKS)
        ]

        self.dw = Gtk.DrawingArea()
        self.dw.set_hexpand(True)
        self.dw.set_size_request(-1, HEIGHT)
        safe_set_draw_func(self.dw, self, "draw")

    def draw(self, area, ctx, width, height, data):
        # The ticks span the whole width: the outer ones touch the edges
        tick_width = max(1.5, width / TICKS * TICK_WIDTH_RATIO)
        pitch = (width - tick_width) / (TICKS - 1)
        tick_top = height - TICK_HEIGHT

        x = tick_width / 2 + self.fill_fr * (width - tick_width)
        r, g, b, a = theme_rgba(area)

        # The glow: a soft oval behind the ticks at the value, fading out
        ctx.save()
        ctx.translate(x, tick_top + TICK_HEIGHT / 2)
        ctx.scale(GLOW_WIDTH * pitch, TICK_HEIGHT)
        glow = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
        glow.add_color_stop_rgba(0, r, g, b, a * GLOW_ALPHA)
        glow.add_color_stop_rgba(1, r, g, b, 0)
        ctx.set_source(glow)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()

        for i, alpha in enumerate(self.alphas):
            ctx.set_source_rgba(r, g, b, a * alpha)
            ctx.rectangle(i * pitch, tick_top, tick_width, TICK_HEIGHT)
            ctx.fill()

        # A triangle pointing down at the exact value
        half = POINTER_HEIGHT * 0.7
        x = max(half, min(x, width - half))  # keep it inside at the edges
        ctx.set_source_rgba(*theme_rgba(area, POINTER_ALPHA))
        ctx.move_to(x - half, 0)
        ctx.line_to(x + half, 0)
        ctx.line_to(x, POINTER_HEIGHT)
        ctx.close_path()
        ctx.fill()
