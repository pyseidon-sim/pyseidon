import esper
import pytest

from processors.core import TimerProcessor
from utils.timer import TimerScheduler

from tests.constants import MOCK_BERTHS_FILENAME
from environment.initializers import BerthsInitializer
from tests.fixtures.berth_service_time import MockBerthServiceDistributionFactory
from tests.fixtures.vessel_ctype import VesselContentType


def world_and_timer_processor():
    world = esper.World()
    timer_processor = TimerProcessor()

    world.add_processor(timer_processor)

    timer_scheduler = TimerScheduler.get_instance()
    timer_scheduler.world = world

    return world, timer_processor


@pytest.fixture()
def world_and_timer_processor_fixture():
    return world_and_timer_processor()


@pytest.fixture
def berths_sim_world():
    world = esper.World()

    return world, BerthsInitializer(
        world,
        MOCK_BERTHS_FILENAME,
        VesselContentType,
        MockBerthServiceDistributionFactory()
    )
