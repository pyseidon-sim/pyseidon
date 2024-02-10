from processors.rendering.base_renderer import BaseRenderer
from utils.shapes import geojson_to_points


class RendezvousRenderer(BaseRenderer):
    """Renders rendezvous areas on a Simulation Layer using geoplotlib"""

    def __init__(self, geojson_filename, rendezvous_color=None):
        if rendezvous_color is None:
            # Default color
            rendezvous_color = [26, 188, 156]

        self.rendezvous_areas = geojson_to_points(geojson_filename)
        self.rendezvous_color = rendezvous_color

    def _process(self, dt):
        for point in self.rendezvous_areas:
            self.paint_point(self.painter, point, self.rendezvous_color)
