import gi
import cairo
from datetime import datetime
from gettext import gettext as _
from zoneinfo import ZoneInfo

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from .CORE_GTKUtils import safe_set_draw_func, theme_rgba, draw_text, text_layout, draw_knob  # noqa: E402

PAD_X = 6
HEADER_HEIGHT = 26  # Max / Min line, and room for the current value above the curve
FOOTER_HEIGHT = 18  # weekday labels
KNOB_RADIUS = 4


class LineGraph:
    """A line graph of hourly values with a "now" marker (the AQI trend).

    The past is drawn solid and the forecast dashed. Days are split by faint
    lines at midnight (in the city's time zone), labelled with the weekday.
    """

    def __init__(self, values, times=None, current_idx=None, color=(0.38, 0.7, 1), tz=None):
        self.color = tuple(color)
        self.dw = Gtk.DrawingArea()
        self.dw.set_size_request(260, 120)
        safe_set_draw_func(self.dw, self, "draw")

        # Everything that doesn't depend on the widget's size is worked out here,
        # so draw() only scales it.
        self.points = []
        valid = [v for v in values if v is not None] if values else []
        if len(values or []) < 2 or not valid:
            return

        low, high = min(valid), max(valid)
        span = (high - low) or 1
        # Missing values sit on the minimum line
        self.points = [((v if v is not None else low) - low) / span for v in values]
        # Translators: lowest and highest value of the air quality graph
        self.range_text = _("Max {max} · Min {min}").format(max=int(high), min=int(low))

        self.current_idx = None
        self.current_text = None
        if current_idx is not None and 0 <= current_idx < len(values):
            self.current_idx = current_idx
            if values[current_idx] is not None:
                self.current_text = str(int(values[current_idx]))

        # Midnights, as (index, weekday name)
        self.days = []
        if times and len(times) == len(values):
            tz = tz or ZoneInfo("UTC")
            for i, ts in enumerate(times):
                dt = datetime.fromtimestamp(ts, tz=tz)
                if dt.hour == 0:
                    self.days.append((i, dt.strftime("%a")))

    def draw(self, area, ctx, width, height, data):
        if not self.points:
            return

        left, right = PAD_X, width - PAD_X
        top, bottom = HEADER_HEIGHT, height - FOOTER_HEIGHT
        step = (right - left) / (len(self.points) - 1)

        def x_of(i):
            return left + i * step

        def y_of(i):
            return bottom - self.points[i] * (bottom - top)

        # Max / Min, top left
        draw_text(area, ctx, self.range_text, left, 0, size="x-small", alpha=0.6, align=0)

        # Day dividers and weekday labels
        ctx.set_line_width(1)
        for i, name in self.days:
            x = x_of(i)
            ctx.set_source_rgba(*theme_rgba(area, 0.1))
            ctx.move_to(round(x) + 0.5, top - 4)
            ctx.line_to(round(x) + 0.5, bottom)
            ctx.stroke()
            label_width = text_layout(area, name, "x-small").get_pixel_size()[0]
            if x + 4 + label_width <= right:
                draw_text(area, ctx, name, x + 4, bottom + 3, size="x-small", alpha=0.55, align=0)

        # Area under the curve
        ctx.move_to(left, bottom)
        for i in range(len(self.points)):
            ctx.line_to(x_of(i), y_of(i))
        ctx.line_to(right, bottom)
        ctx.close_path()
        gradient = cairo.LinearGradient(0, top, 0, bottom)
        gradient.add_color_stop_rgba(0, *self.color, 0.3)
        gradient.add_color_stop_rgba(1, *self.color, 0.02)
        ctx.set_source(gradient)
        ctx.fill()

        # The line: solid up to now, dashed and lighter for the forecast
        ctx.set_line_width(2.5)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        last = len(self.points) - 1
        now = self.current_idx if self.current_idx is not None else last

        ctx.set_source_rgba(*self.color, 1)
        ctx.move_to(x_of(0), y_of(0))
        for i in range(1, now + 1):
            ctx.line_to(x_of(i), y_of(i))
        ctx.stroke()

        if now < last:
            ctx.set_source_rgba(*self.color, 0.55)
            ctx.set_dash([3, 4])
            ctx.move_to(x_of(now), y_of(now))
            for i in range(now + 1, last + 1):
                ctx.line_to(x_of(i), y_of(i))
            ctx.stroke()
            ctx.set_dash([])

        if self.current_idx is None:
            return

        # Now: a guide down to the axis, the knob and the value above it
        x, y = x_of(now), y_of(now)
        ctx.set_line_width(1)
        ctx.set_source_rgba(*theme_rgba(area, 0.25))
        ctx.move_to(round(x) + 0.5, y)
        ctx.line_to(round(x) + 0.5, bottom)
        ctx.stroke()

        draw_knob(ctx, x, y, KNOB_RADIUS, self.color)

        if self.current_text:
            text_width, text_height = text_layout(area, self.current_text, "small", True).get_pixel_size()
            text_x = max(left + text_width / 2, min(x, right - text_width / 2))
            draw_text(area, ctx, self.current_text, text_x, y - KNOB_RADIUS - 5 - text_height,
                      size="small", bold=True)
