from utils import is_number

from .timer_status import TimerStatus


class SimulationTimer:
    """Timer class that accepts a time interval in seconds
    and calls the target function when the elapsed seconds
    surpass the timer's duration.

    The time progression must be updated by the user by calling
    the update(dt) method

    If the target function has arguments, the corresponding
    arguments can be passed in via kwargs. Note that the argument
    names must match exactly as in the target function signature.
    """

    def __init__(self, duration=None, target_function=None, **kwargs):
        self._validate_init(duration, target_function)

        self.duration = duration
        self._elapsed_seconds = 0
        self._status = TimerStatus.IN_PROGRESS
        self.target_function = target_function
        self.arg_dict = kwargs

    def _validate_init(self, duration, target_function):
        if duration is None or not is_number(duration):
            raise ValueError("A float timer duration is required!")
        elif duration < 0:
            raise ValueError("A timer can't have a negative duration!")

        if target_function is None or not callable(target_function):
            raise ValueError("No fireable function was given!")

    def update(self, dt):
        """Advances the timer by the number of seconds in the dt parameter."""
        self._elapsed_seconds += dt

        if self._elapsed_seconds > self.duration and not self.completed():
            self._fire()

    def completed(self):
        """Returns whether the timer has been fired."""
        return (
            self._status == TimerStatus.FIRED or self._status == TimerStatus.INVALIDATED
        )

    @property
    def status(self):
        return self._status

    @property
    def elapsed_seconds(self):
        return self._elapsed_seconds

    def invalidate(self):
        self._status = TimerStatus.INVALIDATED

    def _fire(self):
        self._status = TimerStatus.FIRED
        self.target_function(**self.arg_dict)
