import random

from fysom import Fysom

from utils.timer import SimulationTimer, TimerScheduler

from .states import BerthState


class BerthStateMachine:
    """Keeps track of the state of a berth in the port."""

    def __init__(self, service_time_sampler, random_check_prob=0):
        """
        Initializes a new BerthStateMachine

        :param service_time_sampler: function to sample time from
        """
        self.current_vessel_fsm = None
        self.fsm = Fysom(BerthState.get_state_graph())
        self.service_time_sampler = service_time_sampler
        self.current_berth_timer_id = None
        self.random_check_prob = random_check_prob

    def current(self):
        return self.fsm.current

    def book(self, vessel_fsm):
        assert vessel_fsm is not None, "A vessel state machine is required!"
        assert (
            self.current_vessel_fsm is None
        ), "The berth is already booked by a vessel!"

        self.current_vessel_fsm = vessel_fsm
        self.fsm.book()

    def process_boat(self, vessel_info):
        assert (
            not self.current_vessel_fsm is None
        ), "The berth can't process a null vessel!"

        self.fsm.process_boat()
        self._schedule_processing(
            self.service_time_sampler(vessel_info), self.current_vessel_fsm
        )

    def _schedule_processing(self, seconds, vessel_fsm):
        """.Schedules a timer that completes the vessel processing."""
        # Anomaly: increase the service time so as to simulate e.g. a randomized check
        if random.random() < self.random_check_prob:
            # Increase by 5 hours
            seconds += 18000

        complete_processing_timer = SimulationTimer(
            duration=seconds, target_function=self.finish_processing
        )

        TimerScheduler.get_instance().schedule(complete_processing_timer)

    def finish_processing(self):
        self.current_vessel_fsm.done_servicing()
        self.current_vessel_fsm = None
        self.fsm.finish_processing()
