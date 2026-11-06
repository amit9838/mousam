import gi
import cairo

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from .CORE_GTKUtils import safe_set_draw_func, draw_knob  # noqa: E402

HEIGHT = 40
TRACK_HEIGHT = 8
KNOB_RADIUS = 7

# The bar spans US AQI 0 to 350. One colour per AQI band, placed in the middle
# of the band (the bands match WeatherDataManager.classify_aqi), in
# libadwaita's palette.
AQI_SCALE = 350
AQI_BAND_COLORS = [
    (25, (0.20, 0.82, 0.48)),   # Good (0-50), green 3
    (75, (0.96, 0.83, 0.18)),   # Moderate (51-100), yellow 3
    (125, (1.00, 0.47, 0.00)),  # Poor (101-150), orange 3
    (175, (0.88, 0.11, 0.14)),  # Unhealthy (151-200), red 3
    (250, (0.57, 0.25, 0.67)),  # Severe (201-300), purple 3
    (325, (0.65, 0.11, 0.18)),  # Hazardous (301+), red 5
]
STOPS = [(aqi / AQI_SCALE, rgb) for aqi, rgb in AQI_BAND_COLORS]


def color_at(pos: float):
    """The bar's colour at pos (0 to 1), blended between the two nearest stops."""
    if pos <= STOPS[0][0]:
        return STOPS[0][1]
    for (p1, c1), (p2, c2) in zip(STOPS, STOPS[1:]):
        if pos <= p2:
            t = (pos - p1) / (p2 - p1)
            return tuple(a + (b - a) * t for a, b in zip(c1, c2))
    return STOPS[-1][1]


class PollutionBar(Gtk.DrawingArea):
    """The AQI scale, coloured by band, with a knob at the current AQI.

    pos is the AQI as a share of AQI_SCALE, from 0 to 1.
    """

    def __init__(self, pos: float):
        super().__init__()
        self.pos = max(0.0, min(pos, 1.0))
        self.knob_rgb = color_at(self.pos)
        self.set_hexpand(True)
        self.set_size_request(-1, HEIGHT)
        safe_set_draw_func(self, self, "on_draw")

    def on_draw(self, area, cr, width, height, data):
        # Leave room for the knob's ring and shadow at both ends
        start = KNOB_RADIUS + 4
        end = width - KNOB_RADIUS - 4
        y = height / 2

        gradient = cairo.LinearGradient(start, 0, end, 0)
        for stop, rgb in STOPS:
            gradient.add_color_stop_rgb(stop, *rgb)
        cr.set_source(gradient)
        cr.set_line_width(TRACK_HEIGHT)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.move_to(start, y)
        cr.line_to(end, y)
        cr.stroke()

        draw_knob(cr, start + (end - start) * self.pos, y, KNOB_RADIUS, self.knob_rgb)
