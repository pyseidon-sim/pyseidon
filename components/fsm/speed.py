import random

from fysom import Fysom

from utils.timer import SimulationTimer, TimerScheduler

from .states import SpeedState

# Probabilities for an always normal speed model
NULL_SPEED_MODEL = {"double": 0, "half": 0, "reset": 0}


class SpeedStateMachine:
    """Velocity finite state machine. Used for introducing velocity anomalies."""

    def __init__(
        self, double_p, halve_p, normal_p, transition_chance_interval=7200, factor=2.0
    ):
        self.transition_chance_interval = transition_chance_interval
        self.probabilities = {"double": double_p, "half": halve_p, "reset": normal_p}
        self.factor = factor

        assert (
            sum([double_p, halve_p, normal_p]) <= 1
        ), "Probabilities must sum up to 1!"

        self.fsm = Fysom(SpeedState.get_state_graph())
        self._schedule_transition_timer()

    def current(self):
        return self.fsm.current

    def _timer_callback(self):
        self.random_transition()
        self._schedule_transition_timer()

    def _schedule_transition_timer(self):
        self.timer = SimulationTimer(
            duration=self.transition_chance_interval,
            target_function=self._timer_callback,
        )
        TimerScheduler.get_instance().schedule(self.timer)

    def random_transition(self):
        sample = random.random()

        if self.current() == SpeedState.NORMAL:
            if sample <= self.probabilities["double"]:
                # Double the speed if the sample is in (0, double_p]
                self.fsm.double_speed()
            elif sample <= (self.probabilities["double"] + self.probabilities["half"]):
                # Halve the speed if the sample is in (double_p, halve_p]
                self.fsm.halve_speed()
            else:
                pass
        else:
            # The vessel is in an abornmal state, if the sample is
            # in (0, normal_p] range reset the FSM to the normal state
            if sample <= self.probabilities["reset"]:
                self.fsm.return_to_normal()

    def update_input_velocity(self, velocity):
        if self.current() == SpeedState.DOUBLE:
            return velocity * self.factor
        elif self.current() == SpeedState.HALF:
            return velocity / self.factor

        return velocity
