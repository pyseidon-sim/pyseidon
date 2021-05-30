import pytest
import numpy as np

from components import VesselPath
from environment.navigation.sections import Section
from exceptions import PathTerminatedException, NoPathException


@pytest.fixture()
def vessel_path():
    section_shape = [
        [10, 10],
        [15, 10],
        [15, 5],
        [10, 5],
        [10, 10]
    ]

    section_a = Section(
        name="A",
        shape=section_shape)
    section_b = Section(
        name="B",
        shape=section_shape)

    # Path with sections AAABB
    point_sections = [section_a] * 3 + [section_b] * 2

    path = VesselPath()
    path.set_path({
        "x": [5, 10, 15, 20, 25],
        "y": [5, 10, 15, 20, 25],
        "point_sections": point_sections,
        "crossed_sections": set(point_sections)
    })

    return path


def test_advance(vessel_path):
    path_idx = 0

    try:
        while True:
            path_idx = path_idx + 1

            vessel_path.advance_path()
            next_node = vessel_path.get_current_destination()
            next_section = vessel_path.get_current_section()

            assert len(next_node) == 2

            assert next_section.name == vessel_path.path["point_sections"][path_idx].name
            assert next_node[0] == vessel_path.path["x"][path_idx]
            assert next_node[1] == vessel_path.path["x"][path_idx]
    except PathTerminatedException as _:
        pass


def test_get_current_destination(vessel_path):
    # An exception should be raised if no path was generated
    empty_path = VesselPath()
    with pytest.raises(NoPathException):
        empty_path.get_current_destination()

    current_destination = vessel_path.get_current_destination()

    # The current destination must be a 2 elements numpy array
    assert type(current_destination) == np.ndarray
    assert len(current_destination) == 2


def test_has_current_route(vessel_path):
    empty_path = VesselPath()

    # No path was generated, so no route should exist
    assert not empty_path.has_current_route()
    
    # The fixture vessel path was initialized with a route
    assert vessel_path.has_current_route()

    try:
        # Exhaust the path, and check at every step that a route still exists
        while True:
            vessel_path.advance_path()
            _ = vessel_path.get_current_destination()

            assert vessel_path.has_current_route()
    except PathTerminatedException as _:
        # We reached the end of the path, so no route should exist now
        assert not vessel_path.has_current_route()
