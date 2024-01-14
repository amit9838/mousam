import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk
import cairo


class DrawBar:
    def __init__(self,value, rgb_color=[0.38, 0.7, 1]):
        
        self.ht = 45
        self.dw = Gtk.DrawingArea()
        self.dw.set_size_request(50, self.ht+20)
        self.dw.set_draw_func(self.draw, None)
        self.value = self.ht*value
        self.rgb = rgb_color


        
    def draw(self, area, ctx, h, w, data):

        if self.value == 0:
            return
        
        x_offset = 25
        y_offset=10

        self.value = self.value
        ctx.set_source_rgba(*self.rgb, 0.8)
        ctx.set_line_width(15)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)

        x,y2 = x_offset,self.ht - self.value + y_offset
        ctx.move_to(x, y2)
        ctx.rel_line_to(0, self.ht-y2+y_offset)
        ctx.stroke()


