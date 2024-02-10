import numpy as np
import pytest
from scipy import stats

from components import VesselInfo
from processors.generators import VesselGeneratorProcessor
from utils.timer.timer_status import TimerStatus

from .constants import MOCK_SPAWN_FILENAME
from .fixtures import world_and_timer_processor


@pytest.fixture()
def vessels_world():
    world, time_processor = world_and_timer_processor()
    distribution_lambda = lambda: np.random.normal(loc=100, scale=5)

    vessel_generator = VesselGeneratorProcessor(
        world,
        distribution_lambda,
        lambda: VesselInfo(length=10, width=5, actual_draught=10, max_draught=12),
        MOCK_SPAWN_FILENAME,
    )
    world.add_processor(vessel_generator)

    yield world, vessel_generator, time_processor, distribution_lambda


def test_process(vessels_world):
    _, generator, _, _ = vessels_world

    # Stop the initial timer
    generator.generation_timer.invalidate()
    generator.process(10)

    assert generator.generation_timer.status == TimerStatus.IN_PROGRESS


def test_distribution(vessels_world):
    world, generator, timer_processor, dist_func = vessels_world

    samples = 1000
    alpha = 0.05
    t_critical = 1.96

    normal_samples = [dist_func() for _ in range(samples)]
    sampled_inter_arrival_times = []

    generator.generation_timer.invalidate()

    for _ in range(samples):
        generator.process(1)
        generator.generation_timer.status == TimerStatus.IN_PROGRESS

        sampled_inter_arrival_times.append(generator.generation_timer.duration)
        generator.process(generator.generation_timer.duration)
        timer_processor.process(generator.generation_timer.duration + 1)

    assert len(world.get_components(VesselInfo)) == samples
    assert len(normal_samples) == len(sampled_inter_arrival_times)

    t_stat, p_value = stats.ttest_ind(normal_samples, sampled_inter_arrival_times)

    assert p_value > alpha
    assert t_stat < t_critical
