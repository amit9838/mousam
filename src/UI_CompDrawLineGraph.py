import gi
from gi.repository import Gtk
import cairo
from datetime import datetime
from zoneinfo import ZoneInfo

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

class LineGraph:
    def __init__(self, values, times=None, current_idx=None, color=[0.38, 0.7, 1], tz=None):
        self.values = values
        self.times = times
        self.current_idx = current_idx
        self.color = color
        self.tz = tz if tz else ZoneInfo("UTC")
        self.dw = Gtk.DrawingArea()
        self.dw.set_size_request(260, 120) # Increased height for date labels
        
        from .CORE_GTKUtils import safe_set_draw_func
        safe_set_draw_func(self.dw, self, "draw")

    def draw(self, area, ctx, width, height, data):
        if not self.values or len(self.values) < 2:
            return

        # Padding
        padding_top = 25
        padding_bottom = 15
        padding_left = 10
        padding_right = 10
        
        draw_width = width - padding_left - padding_right
        draw_height = height - padding_top - padding_bottom
        
        # Filter out None values for range calculation
        valid_values = [v for v in self.values if v is not None]
        if not valid_values:
            return

        max_val = max(valid_values)
        min_val = min(valid_values)
        val_range = max_val - min_val if max_val != min_val else 1
        
        num_points = len(self.values)
        step_x = draw_width / (num_points - 1)
        
        def get_coords(i):
            val = self.values[i]
            if val is None:
                val = min_val # Default to min_val for missing data
            x = padding_left + i * step_x
            y = height - padding_bottom - ((val - min_val) / val_range * draw_height)
            return x, y

        # 1. Draw the gradient fill
        ctx.move_to(padding_left, height - padding_bottom)
        for i in range(num_points):
            ctx.line_to(*get_coords(i))
        ctx.line_to(padding_left + draw_width, height - padding_bottom)
        ctx.close_path()
        
        gradient = cairo.LinearGradient(0, padding_top, 0, height - padding_bottom)
        gradient.add_color_stop_rgba(0, *self.color, 0.4)
        gradient.add_color_stop_rgba(1, *self.color, 0.0)
        ctx.set_source(gradient)
        ctx.fill()

        # 2. Draw the main line
        ctx.set_line_width(2.5)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        
        if self.current_idx is not None and 0 <= self.current_idx < num_points - 1:
            # Draw past and current as solid
            ctx.set_source_rgba(*self.color, 1.0)
            ctx.move_to(*get_coords(0))
            for i in range(1, self.current_idx + 1):
                ctx.line_to(*get_coords(i))
            ctx.stroke()
            
            # Draw future as dashed and dimmed
            ctx.set_source_rgba(*self.color, 0.4)
            ctx.set_dash([4.0, 4.0])
            ctx.move_to(*get_coords(self.current_idx))
            for i in range(self.current_idx + 1, num_points):
                ctx.line_to(*get_coords(i))
            ctx.stroke()
            ctx.set_dash([]) # Reset dash
        else:
            ctx.set_source_rgba(*self.color, 1.0)
            ctx.move_to(*get_coords(0))
            for i in range(1, num_points):
                ctx.line_to(*get_coords(i))
            ctx.stroke()

        # 3. Draw current point indicator if provided
        if self.current_idx is not None and 0 <= self.current_idx < num_points:
            curr_x, curr_y = get_coords(self.current_idx)
            
            # Glow effect
            ctx.set_source_rgba(*self.color, 0.3)
            ctx.arc(curr_x, curr_y, 8, 0, 2 * 3.14159)
            ctx.fill()
            
            # Outer circle
            ctx.set_source_rgba(1, 1, 1, 1)
            ctx.set_line_width(2)
            ctx.arc(curr_x, curr_y, 4, 0, 2 * 3.14159)
            ctx.stroke()
            
            # Inner circle
            ctx.set_source_rgba(*self.color, 1)
            ctx.arc(curr_x, curr_y, 3, 0, 2 * 3.14159)
            ctx.fill()

            # 4. Draw labels (Min, Max, Current)
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(10)
            
            # Current value label
            curr_val = self.values[self.current_idx]
            if curr_val is not None:
                ctx.set_source_rgba(1, 1, 1, 0.9)
                text = str(int(curr_val))
                extents = ctx.text_extents(text)
                ctx.move_to(curr_x - extents.width / 2, curr_y - 12)
                ctx.show_text(text)

        # Max label
        ctx.set_font_size(9)
        ctx.set_source_rgba(1, 1, 1, 0.5)
        max_text = f"MAX: {int(max_val)}"
        ctx.move_to(padding_left, 15)
        ctx.show_text(max_text)

        # Min label
        min_text = f"MIN: {int(min_val)}"
        ctx.move_to(padding_left, height - padding_bottom - 4)
        ctx.show_text(min_text)

        # 5. Draw daily time labels and date checkpoints
        if self.times and len(self.times) == num_points:
            ctx.set_font_size(8)
            
            for i, ts in enumerate(self.times):
                dt = datetime.fromtimestamp(ts, tz=self.tz)
                # Draw a label at midnight of each day
                if dt.hour == 0:
                    x, y = get_coords(i)
                    # Small dot on the curve
                    ctx.set_source_rgba(1, 1, 1, 0.8)
                    ctx.arc(x, y, 2.5, 0, 2 * 3.14159)
                    ctx.fill()
                    ctx.set_source_rgba(1, 1, 1, 0.4)
                    date_str = dt.strftime("%d %b")
                    x, _ = get_coords(i)
                    extents = ctx.text_extents(date_str)
                    
                    # Prevent clipping at the edges
                    x_pos = x - extents.width / 2
                    x_pos = max(padding_left, min(x_pos, width - padding_right - extents.width))
                    
                    ctx.move_to(x_pos, height - 2)
                    ctx.show_text(date_str)
