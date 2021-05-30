import pytest

from utils.timer import SimulationTimer
from utils.timer.timer_status import TimerStatus

TIMER_DURATION = 10


class MockClass:
    """Simple one method mock class to test the timer's invocation"""
    def __init__(self):
        self.called = False

    def call_me(self):
        self.called = True


@pytest.fixture
def mock_class():
    return MockClass()


def test_firing(mock_class):
    # Create a new timer and advance it until it fires
    timer = SimulationTimer(
                    duration=TIMER_DURATION,
                    target_function=mock_class.call_me)

    timer.update(TIMER_DURATION + 1)

    # Verify that the timer fired
    assert timer.status == TimerStatus.FIRED
    assert mock_class.called


def test_invalidated(mock_class):
    # Create a new timer, invalidate and advance it 
    # until it should(n't) fires
    timer = SimulationTimer(
                    duration=TIMER_DURATION,
                    target_function=mock_class.call_me)
    timer.invalidate()

    assert timer.status == TimerStatus.INVALIDATED

    # Check if the timer would still fire even if invalidated
    timer.update(TIMER_DURATION + 1)

    # Verify that the timer did not fire
    assert timer.status == TimerStatus.INVALIDATED
    assert not mock_class.called


def test_update(mock_class):
    """
        Tests whether the timer internal clock is updated
        and it fires as expected
    """
    timer = SimulationTimer(
                    duration=TIMER_DURATION,
                    target_function=mock_class.call_me)

    elapsed_seconds = 0
    for i in range(TIMER_DURATION + 1):
        assert timer.status == TimerStatus.IN_PROGRESS
        assert not mock_class.called
        assert timer.elapsed_seconds == elapsed_seconds
        assert not timer.completed()
        
        timer.update(1)
        elapsed_seconds += 1

    # Now the timer should have fired
    assert timer.status == TimerStatus.FIRED
    assert mock_class.called
    assert timer.completed()


def test_init(mock_class):
    """Tests whether the duration and target_function arguments are validated correctly"""
    with pytest.raises(ValueError):
        # No params
        SimulationTimer()
    
    with pytest.raises(ValueError):
        # No target_function
        SimulationTimer(duration=10, target_function=None)
    
    with pytest.raises(ValueError):
        # Negative duration
        SimulationTimer(duration=-10, target_function=mock_class.call_me)
    
    with pytest.raises(ValueError):
        # Null duration
        SimulationTimer(duration=None, target_function=mock_class.call_me)
