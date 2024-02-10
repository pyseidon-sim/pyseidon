import esper
import pytest

from components.fsm import VesselStateMachine
from components.fsm.states import BerthState
from environment.initializers import BerthsInitializer
from environment.queries import BerthList, fetch_vessels
from tests.fixtures import berths_sim_world

from .constants import MOCK_BERTHS_COUNT, MOCK_BERTHS_FILENAME
from .fixtures.berth_service_time import MockBerthServiceDistributionFactory
from .fixtures.vessel_ctype import VesselContentType
from .test_ship_generator import vessels_world


def test_fetch_berths(berths_sim_world):
    """
    Verifies that all the berths are fetched correctly
    """
    world, berths_initializer = berths_sim_world
    berths_initializer.create_berths()

    berths = list(BerthList(world=world))
    assert len(berths) == MOCK_BERTHS_COUNT


def test_fetch_available_berths(berths_sim_world):
    """
    Books and frees a set of berths, checking if the correct number
    of available berths is returned
    """
    world, berths_initializer = berths_sim_world
    berths_initializer.create_berths()

    # No berths should be booked at the start of the simulation
    available_query = BerthList(world=world).filter_by_available(BerthState.AVAILABLE)
    assert len(list(available_query)) == len(list(BerthList(world=world)))

    berths = list(BerthList(world=world))

    # Book a single berth and check wheter it's not available anymore
    _, (_, berth_info, fsm) = berths[0]
    # Pass a mock vessel state machine
    fsm.book(VesselStateMachine())

    # There should be 1 less available berth
    query = BerthList(world=world).filter_by_available(BerthState.AVAILABLE)
    available_berths = list(query)
    assert len(berths) == len(available_berths) + 1

    # Make sure the correct berth is missing
    for _, (_, info, _) in available_berths:
        assert info.name != berth_info.name

    # Free the booked berth. This is a 'Private API' call and
    # should be replaced by something nicer if possible
    fsm.fsm.process_boat()
    fsm.fsm.finish_processing()

    query = BerthList(world=world).filter_by_available(BerthState.AVAILABLE)
    assert len(berths) == len(list(query))

    # Test fetching berths by id
    _, target_berth_data = BerthList(world=world)[0]
    _, target_berth_info, _ = target_berth_data

    _, fetched_berth_data = BerthList(world=world).filter_by_ids(
        [target_berth_info.id]
    )[0]
    _, fetched_berth_info, _ = fetched_berth_data

    assert fetched_berth_info.id == target_berth_info.id


def test_fetch_vessels(vessels_world):
    world, generator, time_generator, _ = vessels_world

    # The simulation starts with 0 vessels
    assert len(fetch_vessels(world)) == 0

    # Add a vessel to the simulation
    generator.generate_vessel()
    assert len(fetch_vessels(world)) == 1
