from fysom import Fysom

from .states import TugState


class TugStateMachine:
    """Keeps track of the state of a tugboat in the port."""

    def __init__(self, waiting_location_id, on_state_change=None):
        """Initializes a new TugStateMachine

        :param on_state_change: function to execute when the state changes (optional).
        """
        self.destination_vessel_id = None
        self.waiting_location_id = waiting_location_id
        self.destination_berth_id = None
        self.destination_rendezvous_id = None
        self.state_before_failure = None
        self.previous_vessel_path = None

        self.fsm = Fysom(TugState.get_state_graph())

        if on_state_change is not None:
            self.fsm.onchangestate = on_state_change

    def current(self):
        return self.fsm.current

    def current_target_vessel_id(self):
        return self.destination_vessel_id

    def go_to_rendezvous(self, vessel_id, rendezvous_id):
        assert (
            self.destination_vessel_id is None
        ), "The tugboat already has an assigned vessel!"
        assert (
            self.destination_rendezvous_id is None
        ), "The tugboat already has an assigned rendezvous!"
        assert vessel_id is not None, "The vessel id must not be None!"
        assert rendezvous_id is not None, "The rendezvous id must not be None!"

        self.destination_vessel_id = vessel_id
        self.destination_rendezvous_id = rendezvous_id
        # self.waiting_location_id = None
        self.fsm.go_to_rendezvous()

    def wait_at_rendezvous(self):
        self.fsm.wait_at_rendezvous()

    def go_to_malfunction_location(self, vessel_id, berth_id):
        assert (
            self.destination_vessel_id is None
        ), "The tugboat already has an assigned vessel!"

        assert vessel_id is not None, "The vessel id must not be none!"
        assert berth_id is not None, "The berth id must not be none!"

        self.destination_vessel_id = vessel_id
        self.destination_berth_id = berth_id

        self.fsm.go_to_malfunction_location()

    def wait_at_malfunction_location(self):
        self.fsm.wait_at_malfunction_location()

    def go_to_berth(self, vessel_id, berth_id):
        assert (
            self.destination_vessel_id is None
        ), "The tugboat already has an assigned vessel!"
        assert (
            self.destination_berth_id is None
        ), "The tugboat already has an assigned berth!"

        assert vessel_id is not None, "The vessel id must exist!"
        assert berth_id is not None, "The berth id must exist!"

        self.destination_vessel_id = vessel_id
        self.destination_berth_id = berth_id

        self.fsm.go_to_berth()

    def wait_at_berth(self):
        self.fsm.wait_at_berth()

    def start_tugging_in(self, berth_id):
        assert berth_id is not None, "The berth id must exist!"

        self.destination_berth_id = berth_id
        self.fsm.start_tugging_in()

    def start_tugging_out(self):
        self.fsm.start_tugging_out()

    def done_tugging(self, waiting_location_id):
        self.waiting_location_id = waiting_location_id
        self.destination_vessel_id = None
        self.destination_berth_id = None
        self.destination_rendezvous_id = None

        self.fsm.done_tugging()

    def arrived_at_waiting_location(self):
        self.fsm.arrived_at_waiting_location()

        self.destination_vessel_id = None
        self.destination_rendezvous_id = None
        self.destination_berth_id = None

    def break_down(self, previous_vessel_path=None):
        self.previous_vessel_path = previous_vessel_path
        self.state_before_failure = self.current()

        self.fsm.break_down()

    def get_fixed_busy(self):
        self.state_before_failure = None
        self.previous_vessel_path = None

        self.fsm.get_fixed_busy()

    def get_fixed_idle(self):
        self.state_before_failure = None
        self.previous_vessel_path = None

        self.fsm.get_fixed_idle()
