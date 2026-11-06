import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gsk", "4.0")
gi.require_version("Graphene", "1.0")
from gi.repository import Gtk, Gsk, Graphene  # noqa: E402

# Extra space around the image so its corners aren't clipped when rotated
PADDING = 10


class DrawImage:
    """An image file rotated by an angle (e.g. the wind direction arrow).

    The image is loaded with Gtk.Image rather than GdkPixbuf: GdkPixbuf decodes
    SVGs through glycin's sandboxed loaders, which fail in some environments
    (GNOME Builder), while Gtk.Image renders them itself.
    """

    def __init__(self, path: str, angle: float, width: int, height: int, center=(0.5, 0.5)):
        """center is the point of the image, as a share of its width and
        height, that is rotated around and placed in the middle."""
        image = Gtk.Image.new_from_file(path)
        image.set_size_request(width, height)
        image.set_pixel_size(max(width, height))

        fixed = Gtk.Fixed()
        fixed.set_size_request(width + 2 * PADDING, height + 2 * PADDING)
        fixed.put(image, 0, 0)

        # Put the image's center point in the middle of the box, and rotate around it
        transform = (
            Gsk.Transform.new()
            .translate(Graphene.Point().init(PADDING + width / 2, PADDING + height / 2))
            .rotate(angle)
            .translate(Graphene.Point().init(-width * center[0], -height * center[1]))
        )
        fixed.set_child_transform(image, transform)

        self.img_box = Gtk.Box()
        self.img_box.append(fixed)
