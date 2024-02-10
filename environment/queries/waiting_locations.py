import random

from shapely.geometry import Point

from components import LocationInfo, Shape


class WaitingLocationList:
    """Class that handles the retrieval of waiting location entities with different sorting methods."""

    def __init__(self, world=None, data=None):
        if world is None and data is None:
            raise ValueError("Either a world or an array must be given")

        self.index = 0

        if data is None:
            self.world = world
            self.locations = world.get_components(LocationInfo, Shape)
        else:
            self.locations = data

    def len(self):
        return len(self.locations)

    def __iter__(self):
        return self

    def __getitem__(self, index):
        return self.locations[index]

    def __next__(self):
        if self.index >= len(self.locations):
            raise StopIteration

        location = self.locations[self.index]
        self.index += 1

        return location

    def filter_by_ids(self, ids):
        if ids is None:
            raise ValueError("Ids must be a list")

        if len(ids) == 0:
            return WaitingLocationList(data=[])

        out_locations = []

        for d, (location_info, shape) in self.locations:
            if location_info.id in ids:
                out_locations.append([d, (location_info, shape)])

        return WaitingLocationList(data=out_locations)

    def filter_by_location_type(self, location_type):
        if location_type is None:
            raise ValueError("Location type must exist")

        out_locations = []

        for d, (location_info, shape) in self.locations:
            if location_info.type == location_type:
                out_locations.append([d, (location_info, shape)])

        return WaitingLocationList(data=out_locations)

    def random_location(self):
        return random.choice(self.locations)

    def random_location_by_type(self, location_type):
        locations_filtered = self.filter_by_location_type(location_type)
        return random.choice(locations_filtered.locations)

    def by_point(self, point: list):
        """Returns the waiting location that contains the given point, given as a lonlat array."""
        geo_point = Point(point[0], point[1])

        for d, (location_info, shape) in self.locations:
            if shape.polygon.contains(geo_point):
                return [d, (location_info, shape)]

        return None
