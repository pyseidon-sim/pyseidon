from environment.queries import fetch_pilots
from components.fsm.states import PilotState
from processors.base_processor import BaseProcessor
from exceptions import NoPathException, PathTerminatedException
from processors.utils import target_reached


class PilotGoalFormulatorProcessor(BaseProcessor):
    def _process(self, dt):
        for ent, (pos, _, vel, pilot_path, pilot_fsm, _) in fetch_pilots(self.world):
            # Formulate a goal if none is set
            if not pilot_path.has_current_route() or target_reached(pilot_path, pos):
                self.formulate_goal(ent, pilot_path, pilot_fsm, vel)

    def formulate_goal(self, ent, pilot_path, fsm, vel):
        """
            Retrieves the next node in path if a path exists, otherwise notifies the
            HM of its current status
        """
        try:
            _ = pilot_path.get_next_destination()
        except (NoPathException, PathTerminatedException) as _:
            current_state = fsm.current()

            if current_state == PilotState.GOING_TO_RENDEZVOUS:
                fsm.arrive_at_rendezvous()
            elif current_state == PilotState.GOING_TO_WAITING_LOCATION:
                fsm.arrive_at_waiting_location()
            elif current_state == PilotState.GOING_TO_BERTH:
                fsm.arrive_at_berth()
        finally:
            pilot_path.advance_path()
