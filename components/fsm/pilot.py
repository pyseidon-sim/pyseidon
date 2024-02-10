from fysom import Fysom

from .states import PilotState


class PilotStateMachine:
    """Keeps track of the state of a pilot vessel in the port."""

    def __init__(self, waiting_location_id, on_state_change=None):
        """
        Initializes a new PilotStateMachine

        :param on_state_change: function to execute when the state changes (optional).
        """
        self.destination_vessel_id = None
        self.berth_id = None
        self.rendezvous_id = None
        self.waiting_location_id = waiting_location_id
        self.fsm = Fysom(PilotState.get_state_graph())

        if on_state_change is not None:
            self.fsm.onchangestate = on_state_change

    def current(self):
        return self.fsm.current

    def booked_vessel_id(self):
        return self.destination_vessel_id

    def go_to_rendezvous(self, vessel_id, rendezvous_id):
        assert (
            self.destination_vessel_id is None
        ), "The pilot already has an assigned vessel!"
        assert rendezvous_id is not None, "A pilot rendezvous id is needed!"

        self.destination_vessel_id = vessel_id
        self.rendezvous_id = rendezvous_id
        self.waiting_location_id = None

        self.fsm.go_to_rendezvous()

    def arrive_at_rendezvous(self):
        self.fsm.arrive_at_rendezvous()

    def go_to_berth(self, vessel_id, berth_id):
        assert (
            self.destination_vessel_id is None
        ), "The pilot already has an assigned vessel!"
        assert berth_id is not None, "A berth id is needed!"

        self.destination_vessel_id = vessel_id
        self.berth_id = berth_id
        self.waiting_location_id = None

        self.fsm.go_to_berth()

    def arrive_at_berth(self):
        self.fsm.arrive_at_berth()

    def deliver_pilot(self, waiting_location_id):
        assert (
            self.waiting_location_id is None
        ), "The pilot already has an assigned waiting location!"
        assert waiting_location_id is not None, "A pilot waiting location id is needed!"

        self.waiting_location_id = waiting_location_id
        self.destination_vessel_id = None
        self.rendezvous_id = None
        self.berth_id = None

        self.fsm.deliver_pilot()

    def arrive_at_waiting_location(self):
        self.fsm.arrive_at_waiting_location()
