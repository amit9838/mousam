
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk
import cairo 

class PollutionBar(Gtk.DrawingArea):
    def __init__(self,pos):
        super(PollutionBar, self).__init__()
        width = self.get_allocated_width()
        height = 40
        self.set_hexpand(True)
        self.slider_pos = pos  # Initial position of the slider
        self.set_draw_func(self.on_draw,None)
        self.set_size_request(width,height)

    def on_draw(self, area, cr, h, w, data):
        width = self.get_width()
        height = 40

        gradient = cairo.LinearGradient(0, 0, 400, 0)
        # Add color stops to the gradient (position, R, G, B, A)
        gradient.add_color_stop_rgba(0, 0, 1, 0, 1)  # Green
        gradient.add_color_stop_rgba(0.3, 1, 1, 0, 1)  # Yellow
        gradient.add_color_stop_rgba(0.6, 1, 1, 0, 1)  # Yellow
        gradient.add_color_stop_rgba(1, 1, 0, 0, 1)  # Red
        cr.set_source(gradient)

        # cr.set_source_rgba(0.8, 0.8, 0.8, 1)
        cr.set_line_width(6)
        cr.move_to(10, height / 2)
        cr.line_to(width - 10, height / 2)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.stroke()

        # Draw the circular slider
        slider_x = 10 + (width - 20) * self.slider_pos
        slider_y = height / 2
        cr.set_source_rgba(.9, 0.9, 0.9, 1)
        cr.arc(slider_x, slider_y, 6, 0, 2 * 3.14159)
        cr.fill()
        cr.arc(slider_x, slider_y, 7, 0, 2 * 3.14159)
        cr.set_line_width(4)
        cr.set_source_rgba(0.4, 0.4, 0.4, .7)
        cr.stroke()
