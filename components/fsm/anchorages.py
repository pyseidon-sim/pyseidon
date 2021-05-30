from fysom import Fysom

from components.fsm.states import AnchorageState


class AnchorageStateMachine:
    """Keeps track of the state of an anchorage in the port."""

    def __init__(self):
        self.current_vessel_fsms = []
        self.fsm = Fysom(AnchorageState.get_state_graph())

    def occupancy(self):
        return len(self.current_vessel_fsms)

    def current(self):
        return self.fsm.current
    
    def book(self, vessel_fsm):
        assert vessel_fsm is not None, "A vessel state machine is required!"

        self.current_vessel_fsms.append(vessel_fsm)

    def remove_vessel(self, vessel_fsm):
        assert vessel_fsm is not None, "The anchorage can't process a null vessel!"
        assert vessel_fsm in self.current_vessel_fsms, "The anchorage can't process a vessel that isn't at the anchorage!"

        self.current_vessel_fsms.remove(vessel_fsm)
