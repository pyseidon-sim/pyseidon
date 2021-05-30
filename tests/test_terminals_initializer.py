import pytest
import esper

from .fixtures.vessel_ctype import VesselContentType
from environment.queries import BerthList
from .constants import MOCK_BERTHS_FILENAME, MOCK_BERTHS_COUNT
from environment.initializers import BerthsInitializer
from components import Position, BerthInfo
from components.fsm import BerthStateMachine
from .fixtures.berth_service_time import MockBerthServiceDistributionFactory

from tests.fixtures import berths_sim_world


def test_create_berths(berths_sim_world):
    world, initializer = berths_sim_world
    initializer.create_berths()

    # Check that all 169 berths were created and added to the world
    berths = list(BerthList(world=world))
    assert len(berths) == MOCK_BERTHS_COUNT

def test_create_berth(berths_sim_world):
    world, initializer = berths_sim_world
    berths_data = initializer.berths_data

    # Retrieve the first row in the data frame, which should be:
    # name                      'Berth 1'
    # lat                       51.82033
    # lon                        3.86652
    # description                       
    # type                          quay
    # id                               1
    # max_quay_length                200
    # max_depth                     3.65
    # vessel_types                     1
    brielselaan = berths_data.iloc[0]
    berth_entity = initializer._create_berth(brielselaan)

    # There should be a single entity with the berth components set
    assert len(list(BerthList(world=world))) == 1

    assert world.has_component(berth_entity, Position)
    assert world.has_component(berth_entity, BerthStateMachine)
    assert world.has_component(berth_entity, BerthInfo)

    entity, (pos, berth_info, fsm) = BerthList(world=world)[0]

    # Verify that the position and berth info components were initialized correctly
    assert pos.lon() == pytest.approx(3.86652, 10e-5)
    assert pos.lat() == pytest.approx(51.82033, 10e-5)

    assert berth_info.name == "Berth 1"
    assert berth_info.max_quay_length == 200
    assert berth_info.max_depth == 3.65
    assert berth_info.allowed_vessel_content_type() == VesselContentType.LIQUID_BULK
