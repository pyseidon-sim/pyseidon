import json

import pytest
from shapely.geometry import Point, Polygon

from utils.shapes import random_point_in_polygon

from .constants import MOCK_SPAWN_FILENAME


@pytest.fixture()
def polygon():
    spawn_area_file = open(MOCK_SPAWN_FILENAME, "r")
    spawn_area_json = json.loads(spawn_area_file.read())
    spawn_area_file.close()

    return Polygon(spawn_area_json["features"][0]["geometry"]["coordinates"])


def test_random_point_in_polygon(polygon):
    for _ in range(1000):
        point = random_point_in_polygon(polygon)

        assert polygon.contains(Point(point[0], point[1]))
