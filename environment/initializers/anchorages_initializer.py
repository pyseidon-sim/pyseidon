import geojson

from components import AnchorageInfo, Shape
from components.fsm import AnchorageStateMachine


class AnchoragesInitializer():
    """Generates anchorages entities from a geojson file input."""

    def __init__(self, world, filename):
        self.world = world
        geo_file = open(filename, "r")
        self.anchorage_data = geojson.loads(geo_file.read())
        geo_file.close()

    def create_anchorages(self):
        for row in self.anchorage_data["features"]:
            self._create_anchorage(row)

    def _create_anchorage(self, row):
        """Create an anchorage as esper world entity"""

        anchorage = self.world.create_entity()

        properties = row["properties"]

        anchorage_info = AnchorageInfo(
            properties["id"],
            properties["name"],
            float(properties["max_draught"]),
            properties["use"])

        self.world.add_component(anchorage, Shape(shape_points=row["geometry"]["coordinates"]))
        self.world.add_component(anchorage, anchorage_info)
        self.world.add_component(anchorage, AnchorageStateMachine())
        
        return anchorage
