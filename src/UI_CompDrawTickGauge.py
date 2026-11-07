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

# From the middle (best) out to each edge (extreme), the ticks go:
# a little blue, then plain grey, then a little orange. The tints fade in
# and out, so there are no hard steps. Positions are the share of each half
# (0 middle, 1 edge).
GREY_ALPHA = 0.75
BLUE_END = 0.3       # the blue has faded out here
ORANGE_START = 0.65  # the orange starts fading in here
CENTER_RGB = (0.11, 0.44, 0.85)  # GNOME blue 4 (#1c71d8)
CENTER_TINT = 0.4  # how much blue the middle tick gets: 0 grey, 1 full blue
EDGE_RGB = (0.90, 0.38, 0.0)     # GNOME orange 5 (#e66100)
EDGE_TINT = 0.5  # how much orange the edges get: 0 grey, 1 full orange
EDGE_ALPHA = 0.9
POINTER_ALPHA = 0.9


class DrawTickGauge:
    """A horizontal leveler made of vertical ticks, centred on the best value.

    From the middle out, the ticks are a little blue, then grey, then a
    little orange at both edges.
    fill_fr is the position, from 0 (lowest) to 1 (highest); 0.5 is the
    middle. A triangle above the ticks points at it. Used by the pressure card.
    """

    def __init__(self, fill_fr: float):
        self.fill_fr = max(0.0, min(fill_fr, 1.0))
        # Each tick's tint colour, how much of it (0 to 1) and its opacity
        self.ticks = []
        for i in range(TICKS):
            d = abs(i - CENTER) / CENTER  # 0 in the middle, 1 at the edges
            if d < BLUE_END:
                self.ticks.append((CENTER_RGB, CENTER_TINT * (1 - d / BLUE_END), GREY_ALPHA))
            elif d < ORANGE_START:
                self.ticks.append((CENTER_RGB, 0.0, GREY_ALPHA))
            else:
                t = (d - ORANGE_START) / (1 - ORANGE_START)
                alpha = GREY_ALPHA + (EDGE_ALPHA - GREY_ALPHA) * t
                self.ticks.append((EDGE_RGB, EDGE_TINT * t, alpha))

        self.dw = Gtk.DrawingArea()
        self.dw.set_hexpand(True)
        self.dw.set_size_request(-1, HEIGHT)
        safe_set_draw_func(self.dw, self, "draw")

    def draw(self, area, ctx, width, height, data):
        # The ticks span the whole width: the outer ones touch the edges
        tick_width = max(1.5, width / TICKS * TICK_WIDTH_RATIO)
        pitch = (width - tick_width) / (TICKS - 1)
        tick_top = height - TICK_HEIGHT

        grey = theme_rgba(area)
        for i, (tint_rgb, tint, alpha) in enumerate(self.ticks):
            rgb = [g + (c - g) * tint for g, c in zip(grey[:3], tint_rgb)]
            ctx.set_source_rgba(*rgb, grey[3] * alpha)
            ctx.rectangle(i * pitch, tick_top, tick_width, TICK_HEIGHT)
            ctx.fill()

        # A triangle pointing down at the exact value
        x = tick_width / 2 + self.fill_fr * (width - tick_width)
        half = POINTER_HEIGHT * 0.7
        x = max(half, min(x, width - half))  # keep it inside at the edges
        ctx.set_source_rgba(*theme_rgba(area, POINTER_ALPHA))
        ctx.move_to(x - half, 0)
        ctx.line_to(x + half, 0)
        ctx.line_to(x, POINTER_HEIGHT)
        ctx.close_path()
        ctx.fill()
