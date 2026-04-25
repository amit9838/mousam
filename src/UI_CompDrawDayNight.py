import gi
import math

from gi.repository import Gtk
import cairo
from datetime import datetime
from gettext import gettext as _, pgettext as C_

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")


class DrawDayNight:
    def __init__(self, angle, time_str, width, height):
        self.angle_degrees = angle
        self.time_str = time_str
        self.width = width
        self.height = height

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(self.width + 20, self.height + 20)
        self.drawing_area.set_css_classes(["drawing-padding"])
        from .CORE_GTKUtils import safe_set_draw_func
        safe_set_draw_func(self.drawing_area, self, "on_draw")

        self.img_box = Gtk.Box()
        self.img_box.append(self.drawing_area)

    def on_draw(self, widget, cr, width, height, data):
        context = cr
        outer_radius = 40
        center_x, center_y = width // 2, height // 2
        sun_angle = self.angle_degrees
        sun_radius = 7
        ray_length = 5
        num_rays = 10

        # 1. Background Stars (for the Night half)
        # We use a fixed seed for consistent star positions
        import random
        random.seed(42)
        for i in range(15):
            sx = random.uniform(center_x - outer_radius, center_x + outer_radius)
            sy = random.uniform(center_y + 5, center_y + outer_radius + 5)
            # Only draw if inside the bottom arc
            dist = math.sqrt((sx - center_x)**2 + (sy - center_y)**2)
            if dist < outer_radius - 2:
                opacity = random.uniform(0.1, 0.4)
                context.set_source_rgba(1, 1, 1, opacity)
                context.arc(sx, sy, 0.7, 0, 2 * math.pi)
                context.fill()

        # 2. Arcs with Gradients
        context.set_line_width(2.5)
        context.set_line_cap(cairo.LINE_CAP_ROUND)

        is_day = (180 <= sun_angle <= 360)
        day_arc_opacity = 1.0 if is_day else 0.2

        # Day Arc (Upper) - Warm Gradient
        day_grad = cairo.LinearGradient(center_x - outer_radius, 0, center_x + outer_radius, 0)
        day_grad.add_color_stop_rgba(0.0, 1.0, 0.4, 0.2, 0.7 * day_arc_opacity) # Sunrise
        day_grad.add_color_stop_rgba(0.5, 1.0, 0.9, 0.3, 0.9 * day_arc_opacity) # Noon
        day_grad.add_color_stop_rgba(1.0, 1.0, 0.4, 0.2, 0.7 * day_arc_opacity) # Sunset
        
        context.set_source(day_grad)
        context.arc(center_x, center_y, outer_radius, math.pi, 2 * math.pi)
        context.stroke()

        # Night Arc (Lower) - Deep Blue Dash
        context.set_source_rgba(0.4, 0.5, 0.8, 0.3)
        context.set_dash([3, 5])
        context.arc(center_x, center_y, outer_radius, 0, math.pi)
        context.stroke()
        context.set_dash([]) # Reset dash

        # 3. Horizon Line (Subtle)
        context.set_line_width(1.5)
        context.set_source_rgba(1, 1, 1, 0.15)
        context.move_to(center_x - outer_radius - 10, center_y)
        context.line_to(center_x + outer_radius + 10, center_y)
        context.stroke()

        # 4. Celestial Body (Sun/Moon)
        sun_angle_rad = math.radians(sun_angle)
        disk_x = center_x + outer_radius * math.cos(sun_angle_rad)
        disk_y = center_y + outer_radius * math.sin(sun_angle_rad)

        if 180 <= sun_angle <= 360:
            # SUN DESIGN
            # Dynamic color based on height (sine of angle)
            # 0 at horizon (180/360), 1 at zenith (270)
            h_factor = abs(math.sin(math.radians(sun_angle)))
            
            # Interpolate: Horizon (1, 0.5, 0.2) -> Zenith (1, 1, 0.8)
            r = 1.0
            g = 0.5 + (0.5 * h_factor)
            b = 0.2 + (0.6 * h_factor)
            dynamic_sun_color = (r, g, b)

            # Radial Glow
            glow = cairo.RadialGradient(disk_x, disk_y, 2, disk_x, disk_y, sun_radius + 10)
            glow.add_color_stop_rgba(0, *dynamic_sun_color, 0.6)
            glow.add_color_stop_rgba(1, dynamic_sun_color[0], dynamic_sun_color[1]*0.5, 0, 0)
            context.set_source(glow)
            context.arc(disk_x, disk_y, sun_radius + 10, 0, 2 * math.pi)
            context.fill()

            # Core
            context.set_source_rgba(*dynamic_sun_color, 1)
            context.arc(disk_x, disk_y, sun_radius, 0, 2 * math.pi)
            context.fill()

            # Rays
            context.set_line_width(1.5)
            context.set_source_rgba(*dynamic_sun_color, 0.8)
            for i in range(num_rays):
                angle = i * (2 * math.pi / num_rays)
                x1 = disk_x + (sun_radius + 3) * math.cos(angle)
                y1 = disk_y + (sun_radius + 3) * math.sin(angle)
                x2 = disk_x + (sun_radius + ray_length + 2) * math.cos(angle)
                y2 = disk_y + (sun_radius + ray_length + 2) * math.sin(angle)
                context.move_to(x1, y1)
                context.line_to(x2, y2)
                context.stroke()
        else:
            # MOON DESIGN
            # Radial Glow
            glow = cairo.RadialGradient(disk_x, disk_y, 2, disk_x, disk_y, sun_radius + 6)
            glow.add_color_stop_rgba(0, 0.8, 0.9, 1.0, 0.5)
            glow.add_color_stop_rgba(1, 0.4, 0.5, 1.0, 0)
            context.set_source(glow)
            context.arc(disk_x, disk_y, sun_radius + 6, 0, 2 * math.pi)
            context.fill()

            # Core
            context.set_source_rgba(0.9, 0.9, 1, 1)
            context.arc(disk_x, disk_y, sun_radius - 1, 0, 2 * math.pi)
            context.fill()

        # 5. Typography
        formatted_time = self.time_str

        # Time Label (Centered)
        # context.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        context.set_font_size(12)
        context.set_source_rgba(1, 1, 1, 0.85)
        
        extents = context.text_extents(formatted_time)
        context.move_to(center_x - extents.width / 2, center_y + 15)
        context.show_text(formatted_time)

        # Day/Night Status
        status_text = _("Day") if (180 <= sun_angle <= 360) else _("Night")
        context.set_font_size(10)
        context.set_source_rgba(1, 1, 1, 0.5)
        extents = context.text_extents(status_text)
        context.move_to(center_x - extents.width / 2, center_y + outer_radius + 12)
        context.show_text(status_text)
