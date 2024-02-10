import math

import numpy as np

from processors.base_processor import BaseProcessor


class BaseRenderer(BaseProcessor):
    """Abstract class for a renderer processor"""

    VESSEL_TRIANGLE_SIZE = 10

    def update_drawing_context(self, proj, painter):
        self.proj = proj
        self.painter = painter

    def update_mouse(self, mouse_x, mouse_y):
        self.mouse_x = mouse_x
        self.mouse_y = mouse_y

    def mouse_hovers(self, x, y, sensitivity=15):
        hovers_x = abs(x - self.mouse_x) < sensitivity
        hovers_y = abs(y - self.mouse_y) < sensitivity

        return hovers_x and hovers_y

    def paint_polygon(self, painter, shape, color):
        x, y = [], []

        coords = shape.exterior.coords.xy

        for point in zip(coords[0], coords[1]):
            # Transform the points in two x, y arrays
            conv_point = np.array(point)
            p_x, p_y = self.proj.lonlat_to_screen(conv_point[0], conv_point[1])

            x.append(p_x)
            y.append(p_y)

        self.painter.set_color(color)
        self.painter.poly(x, y)
        self.painter.linestrip(x, y, width=2.0, closed=True)

    def paint_point(self, painter, point, color, radius=3.0):
        conv_point = np.array([point.x, point.y])
        p_x, p_y = self.proj.lonlat_to_screen(conv_point[0], conv_point[1])

        self.painter.set_color(color)
        self.painter.circle_filled(p_x, p_y, radius)

    def paint_vessel(self, painter, x, y, course):
        painter.triangle(
            [
                # Upper vertex of the triangle
                x + math.cos(course) * self.VESSEL_TRIANGLE_SIZE,
                y + math.sin(course) * self.VESSEL_TRIANGLE_SIZE,
                # Lower right vertex of the triangle
                x + math.cos(course - 90) * self.VESSEL_TRIANGLE_SIZE / 2,
                y + math.sin(course - 90) * self.VESSEL_TRIANGLE_SIZE / 2,
                # Upper left vertex of the triangle
                x + math.cos(course + 90) * self.VESSEL_TRIANGLE_SIZE / 2,
                y + math.sin(course + 90) * self.VESSEL_TRIANGLE_SIZE / 2,
            ]
        )
