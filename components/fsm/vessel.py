from fysom import Fysom
from .states import VesselState


class VesselStateMachine:
    """Keeps track of the state of a vessel in the port."""

    def __init__(self, on_state_change=None):
        """Initializes a new VesselStateMachine.

            :param on_state_change: function to execute when the state changes (optional).
        """
        self.destination_anchorage_id = None
        self.destination_anchorage_fsm = None
        self.destination_berth_id = None
        self.destination_berth_fsm = None
        self.tugs_rendezvous_id = None
        self.pilot_rendezvous_id = None
        self.pilot = None
        self.tugboats = None
        self.tug_company = None
        self.pilot_boarded = False
        self.fsm = Fysom(VesselState.get_state_graph())

        # Used to keep the state the vessel was in before a malfunction (e.g. broken tug)
        self.state_before_failure = None

        if on_state_change is not None:
            self.fsm.onchangestate = on_state_change

    def current(self):
        return self.fsm.current

    def generate(self):
        self.fsm.generate()

    def assign_berth(self, berth_fsm, berth_id):
        assert self.destination_berth_fsm is None, "The vessel already had an assigned berth!"

        assert berth_id is not None, "The berth id must not be None!"
        assert berth_fsm is not None, "The berth fsm must not be None!"

        self.destination_berth_id = berth_id
        self.destination_berth_fsm = berth_fsm
        self.destination_berth_fsm.book(self)

    def go_to_berth(self):
        if self.destination_anchorage_fsm is not None:
            self.destination_anchorage_fsm.remove_vessel(self)
            self.destination_anchorage_fsm = None

        self.pilot_rendezvous_id = None
        # self.tugs_rendezvous_id = None

        self.fsm.go_to_berth()

    def assign_tugs_rendezvous(self, rendezvous_id, pilot_rv_tug_rv_path, tug_rv_berth_path):
        assert self.tugs_rendezvous_id is None, "The vessel already has a rendezvous area assigned!"
        assert pilot_rv_tug_rv_path is not None, "A pilot rendezvous -> tug rendezvous path is required"
        assert tug_rv_berth_path is not None, "A tug rendezvous -> berth path is required"

        self.tugs_rendezvous_id = rendezvous_id
        self.pilots_rendezvous_tug_rendezvous_path = pilot_rv_tug_rv_path
        self.tugs_rendezvous_berth_path = tug_rv_berth_path

    def go_to_tugs_rendezvous(self, rendezvous_id=None, rendezvous_berth_path=None):
        """Transitions the FSM in the GO_TO_TUG_RENDEZVOUS state.

            The tug rendezvous id (and path) can either be set via assign_tugs_rendezvous
            or by this method, but not both!
        """
        missing_rv = self.tugs_rendezvous_id is None and rendezvous_id is None
        missing_path = self.tugs_rendezvous_berth_path is None and rendezvous_berth_path is None

        assert not missing_rv, "No tugs rendezvous was set or passed as an argument!"
        assert not missing_path, "No tugs rendezvous path was set or passed as an argument!"

        double_rv = self.tugs_rendezvous_id is not None and rendezvous_id is not None
        double_path = self.tugs_rendezvous_berth_path is not None and rendezvous_berth_path is not None

        assert not double_rv, "A tug rendezvous was already set!"
        assert not double_path, "A tug rendezvous path was already set!"

        self.fsm.go_to_tugs_rendezvous()

        if self.tugs_rendezvous_id is None:
            self.tugs_rendezvous_id = rendezvous_id

        if self.tugs_rendezvous_berth_path is None:
            self.tugs_rendezvous_berth_path = rendezvous_berth_path

    def go_to_pilots_rendezvous(self, rendezvous_id, rendezvous_berth_path):
        assert self.pilot_rendezvous_id is None, "The vessel already has a rendezvous area assigned!"
        assert rendezvous_berth_path is not None, "An ocean -> pilot rendezvous path is required"

        self.fsm.go_to_pilots_rendezvous()

        self.pilot_rendezvous_id = rendezvous_id
        self.pilot_rendezvous_berth_path = rendezvous_berth_path

    def stop_at_tugs_rendezvous(self):
        self.fsm.stop_at_tugs_rendezvous()

    def stop_at_pilots_rendezvous(self):
        self.fsm.stop_at_pilots_rendezvous()

    def servicing(self, vessel_info):
        assert self.destination_berth_fsm is not None, "The vessel does not have a booked berth!"

        self.fsm.servicing()
        self.pilot_boarded = False
        self.destination_berth_fsm.process_boat(vessel_info)

    def done_servicing(self):
        self.destination_berth_fsm = None

        self.fsm.done_servicing()        

    def wait_for_tugs_pilots(self):
        self.fsm.wait_for_tugs_pilots()
    
    def go_to_anchorage(self, anchorage_id, anchorage_fsm):
        self.fsm.go_to_anchorage()
        self.destination_anchorage_id = anchorage_id
        self.destination_anchorage_fsm = anchorage_fsm

    def stop_at_anchorage(self):
        self.fsm.stop_at_anchorage()

    def leave(self):
        # self.destination_berth_id = None
        self.destination_berth_fsm = None

        self.fsm.leave()

    def complete(self):
        self.fsm.complete()

    def tug_malfunction(self):
        self.state_before_failure = self.current()

        self.fsm.tug_malfunction()

    def tug_fix_berth(self):
        self.state_before_failure = None

        self.fsm.tug_fix_berth()

    def tug_fix_leaving(self):
        self.state_before_failure = None

        self.fsm.tug_fix_leaving()
