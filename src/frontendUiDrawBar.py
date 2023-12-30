import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk
import cairo


class DrawLevelBar:
    def __init__(
        self,
        fill_fr: float = .5,
        rounded_cap=False,
        width=40,
        height=70,
        line_w=20,
        rgb_color=[0.38, 0.7, 1],
    ):
        self.dw = Gtk.DrawingArea()
        self.dw.set_size_request(width, height)
        self.dw.set_draw_func(self.draw, None)
        self.rounded_cap = rounded_cap
        self.line_w = line_w
        self.height = height
        self.width = 50
        self.margin_left = abs(width - line_w)
        self.fill_fr = 1 - fill_fr
        self.rgb = rgb_color  # [r,g,b] (between 0 to 1)


    def draw(self, area, ctx, h, w, data):
        x,y1 = (self.width)/2,10
        x,y2 = (self.width)/2,self.height-10

        filled = self.fill_fr
        # filled = 1-filled
        
        lev = y1+(y2-y1)*filled
        ctx.set_source_rgba(*self.rgb, 0.4)

        # Set the line width
        ctx.set_line_width(20)

        # Move to the starting point
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(x, y1)
        # Line to the ending point
        ctx.line_to(x, y2)
        # Stroke the line with the gradient
        ctx.stroke()


        ctx.set_source_rgba(*self.rgb, 1)
        ctx.move_to(x,lev)
        ctx.rel_line_to(0,0)
        ctx.stroke()

        # Draw a triangle using move_to and line_to
        ctx.move_to(x-15, lev)
        ctx.rel_line_to(-10, -6)  # Draw the first side
        ctx.rel_line_to(0,12)  # Draw the second side
        ctx.close_path()          # Close the path to complete the triangle

        ctx.fill()
