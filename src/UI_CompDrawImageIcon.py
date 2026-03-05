import gi
import math
from gi.repository import Gtk, Gdk, GdkPixbuf

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

class DrawImage:
    def __init__(self, path, angle, width, height):
        self.image_path = path
        self.angle_degrees = angle
        self.width = width
        self.height = height

        # 1. Load and scale the image ONCE during initialization
        try:
            temp_pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.image_path)
            self.pixbuf = temp_pixbuf.scale_simple(self.width, self.height, GdkPixbuf.InterpType.BILINEAR)
        except Exception as e:
            print(f"Error loading image: {e}")
            self.pixbuf = None

        self.drawing_area = Gtk.DrawingArea()
        # Adding a bit of extra space for rotation clipping prevention
        self.drawing_area.set_size_request(self.width + 20, self.height + 20)
        self.drawing_area.set_draw_func(self.on_draw, None)

        self.img_box = Gtk.Box()
        self.img_box.append(self.drawing_area)

    def on_draw(self, widget, cr, width, height, data):
        if not self.pixbuf:
            return

        # 2. Clear background (Transparent)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()

        # 3. Calculate the center of the drawing area for rotation
        center_x = width / 2
        center_y = height / 2

        # 4. Perform the rotation
        # Move to center -> Rotate -> Move back
        cr.translate(center_x, center_y)
        cr.rotate(self.angle_degrees * math.pi / 180)
        cr.translate(-self.width / 2, -self.height / 2)

        # 5. Paint the pre-loaded pixbuf
        Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, 0, 0)
        cr.paint()