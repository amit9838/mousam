import gi
import math
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk
import cairo
from datetime import datetime
import time
from .utils import get_cords, get_tz_offset_by_cord,get_my_tz_offset_from_utc

my_tz_offset = get_my_tz_offset_from_utc()

class DrawDayNight:
    def __init__(self,angle,width,height):
        
        self.angle_degrees = angle  # Specify the rotation angle in degrees
        self.width = width
        self.height = height

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(self.width+20,self.height+20)
        self.drawing_area.set_css_classes(['drawing-padding'])
        # self.drawing_area.connect("draw", self.on_draw)
        self.drawing_area.set_draw_func(self.on_draw, None)

        self.img_box = Gtk.Box()
        self.img_box.append(self.drawing_area)

    def on_draw(self, widget, cr, width, height, data):
         # Create a Cairo surface
        context = cr
        outer_radius = 50

        num_rays = 8
        sun_angle = self.angle_degrees  #Degree
        sun_radius = 8
        ray_length = 6

        # Set line width for the outer circle
        context.set_line_width(2)

        # Set fill color for the disk
        context.set_source_rgba(1.0, 0.0, 0.0, 1.0)  # Red

        # Define the center and radius of the outer circle
        center_x, center_y = width // 2, height // 2

        # Define the center and radius of the disk (inner circle)
        context.set_source_rgba(.8, .8, .8, .9)  # Red

        # Create Upper half of circle (Day)
        context.arc(center_x, center_y, outer_radius, 3.14, 2 * 3.14159)  # Full circle (0 to 2π)
        context.stroke()

        # Create Lower half of circle (Night)
        dash_length = 5
        gap_length = 5
        context.set_dash([dash_length, gap_length])
        context.set_source_rgba(0.5, 0.5, 0.5, .7)  # Red
        context.arc(center_x, center_y, outer_radius, 0, 1 * 3.14159)  # Full circle (0 to 2π)
        context.stroke()

        # Midnight Mark
        context.set_dash([1, 0])
        context.set_source_rgba(0.5, 0.5, 0.5, .7) 
        context.move_to(center_x,center_y+outer_radius/1.2)
        context.line_to(center_x,center_y+outer_radius)
        context.stroke()


        # Clock
        context.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        context.set_font_size(13)
        context.set_source_rgba(0.7, 0.7, 0.7, 1.0)  # Black

        tz_offset_from_curr_tz = get_tz_offset_by_cord(*get_cords())

        now = time.time() + my_tz_offset + tz_offset_from_curr_tz
        formatted_date_time = datetime.fromtimestamp(now).strftime("%I:%M %p")
        text = formatted_date_time

        # Calculate the position for text placement
        text_x = center_x - 30
        text_y = center_y + 15

        # Move the text cursor to the calculated position
        context.move_to(text_x, text_y)

        # Display the text along the circular path
        context.show_text(text)

        context.set_font_size(13)

        # Horizon text
        text = "Horizon"
        # Calculate the position for text placement
        text_x = center_x + outer_radius*1.3
        text_y = center_y -10
        # Move the text cursor to the calculated position
        context.move_to(text_x, text_y)

        # Display the text along the circular path
        context.show_text(text)



        text2 = "Midnight"
        # Calculate the position for text placement
        text_x = center_x - 30
        text_y = center_y + outer_radius*1.3
        # Move the text cursor to the calculated position
        context.move_to(text_x, text_y)

        # Display the text along the circular path
        context.show_text(text2)




        # Choose sun color
        if sun_angle>=180 and sun_angle<=360:
            yellow = abs(1.2-(1-(sun_angle-170)/90))
            if sun_angle > 270:
                upper_limit = abs(1.2-(1-(360-170)/90))
                lower_limit = abs(1.2-(1-(180-170)/90))
                yellow = upper_limit - yellow + lower_limit
            context.set_source_rgba(1, yellow, 0, 1.5)  # Red
        else:
            context.set_source_rgba(.9, 0.9, 0.9, 1.0)  # Red

        # Convert to radian
        sun_angle_rad = math.radians(sun_angle)  # Angle at which the disk is positioned (in radians)

        # # Calculate the position of the disk on the outer circle
        disk_x = center_x + outer_radius * math.cos(sun_angle_rad)
        disk_y = center_y + outer_radius * math.sin(sun_angle_rad)

        # Sun
        center_x,center_y = disk_x,disk_y
        context.arc(center_x, center_y, sun_radius, 0, 2 * math.pi)
        context.fill()

        # Create sun rays
        if sun_angle>=180 and sun_angle<=360:
            for i in range(num_rays):
                angle = i * (2 * math.pi / num_rays)
                x1 = center_x + (sun_radius + 2) * math.cos(angle)
                y1 = center_y + (sun_radius + 2) * math.sin(angle)
                x2 = center_x + (sun_radius + ray_length) * math.cos(angle)
                y2 = center_y + (sun_radius + ray_length) * math.sin(angle)
                context.move_to(x1, y1)
                context.line_to(x2, y2)
                context.stroke()

        # Horizon Line
        context.set_line_width(1)
        context.set_source_rgba(.8, .8, 0.8, 1)  # Red
        context.set_line_cap(cairo.LINE_CAP_ROUND)
        context.move_to(width/6,height//2)
        context.line_to(width,height//2)
        dash_length = 12
        gap_length = 5
        context.set_dash([dash_length, gap_length])
        context.stroke()

