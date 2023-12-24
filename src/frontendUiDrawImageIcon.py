import gi
import math
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk,Gdk,GdkPixbuf

class DrawImage():
    def __init__(self,path,angle,width,height):
        
        self.image_path = path  # Replace with the path to your image file
        self.angle_degrees = angle  # Specify the rotation angle in degrees
        self.width = width
        self.height = height

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(self.width+14 ,self.height+14)
        self.drawing_area.set_css_classes(['drawing-padding'])
        self.drawing_area.set_draw_func(self.on_draw, None)

        self.img_box = Gtk.Box()
        self.img_box.append(self.drawing_area)

    def on_draw(self, widget, cr, width, height, data):
        # Clear the drawing area
        cr.set_source_rgba(0, 1, 1, 0)
        cr.rectangle(0, 0, width, height)
        cr.fill()

        # Load the image
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.image_path)
        pixbuf = pixbuf.scale_simple(self.width,self.height,GdkPixbuf.InterpType(2))

        # Calculate the rotation point
        rotation_x = (width-width*.1) / 2
        rotation_y = (height-height*.1) / 2

        # Rotate the image around its center
        cr.translate(rotation_x, rotation_y)
        cr.rotate(self.angle_degrees * math.pi / 180)
        cr.translate(-rotation_x, -rotation_y)

        # Paint the rotated image
        Gdk.cairo_set_source_pixbuf(cr, pixbuf, 1, 1)
        cr.paint()

