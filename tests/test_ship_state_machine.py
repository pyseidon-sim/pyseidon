import pytest

from components.fsm import BerthStateMachine, VesselStateMachine
from components.fsm.states import BerthState, VesselState

from .constants import SECONDS_IN_DAY
from .fixtures import world_and_timer_processor_fixture


@pytest.fixture()
def vessel_fsm():
    return VesselStateMachine()


@pytest.fixture()
def berth_fsm():
    return BerthStateMachine(lambda _: 100)


def test_flow(vessel_fsm, berth_fsm, world_and_timer_processor_fixture):
    # Unpack the world and timer processor
    world, timer_processor = world_and_timer_processor_fixture

    # A vessel appears as a scheduled vessel
    assert vessel_fsm.current() == VesselState.SCHEDULED
    vessel_fsm.generate()

    assert vessel_fsm.current() == VesselState.INCOMING

    vessel_fsm.assign_berth(berth_fsm, 1)

    # A vessel is then routed to a berth, this should result in the berth
    # being booked and in the vessel heading to the berth
    vessel_fsm.go_to_berth()

    assert vessel_fsm.current() == VesselState.GOING_TO_BERTH
    assert berth_fsm.current() == BerthState.WAITING_FOR_VESSEL

    # The vessel arrives at the berth and it is processed
    vessel_fsm.servicing(None)

    assert vessel_fsm.current() == VesselState.SERVICING
    assert berth_fsm.current() == BerthState.SERVING_VESSEL

    # Wait to make sure the timer fired
    timer_processor._process(SECONDS_IN_DAY)

    # The vessel should have finished processing and the berth
    # should be free
    print(vessel_fsm.current())
    assert vessel_fsm.current() == VesselState.WAITING_FOR_DEPARTURE_CLEARANCE
    assert berth_fsm.current() == BerthState.AVAILABLE

    # Make the vessel leave and complete the visit
    vessel_fsm.leave()
    assert vessel_fsm.current() == VesselState.LEAVING

    vessel_fsm.complete()
    assert vessel_fsm.current() == VesselState.LEFT
