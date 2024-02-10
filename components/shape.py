from shapely.geometry import Polygon


class Shape:
    def __init__(self, shape_points):
        """Initializes a new shape.

        shape_points must be an array of latlon coordinates, such
        as the one below:

        [
            [10, 10.5],
            [11, 10.7]
        ]
        """
        self.polygon = Polygon(shape_points)

    @property
    def centroid(self):
        """Return the centroid of the shape"""
        return self.polygon.centroid

    def __str__(self):
        return f"<Shape: {self.polygon}>"
