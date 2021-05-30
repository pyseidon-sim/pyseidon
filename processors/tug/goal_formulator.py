from environment.queries import fetch_tugs
from environment.messaging.types import TugMessageType
from environment.messaging import MessageBroker, SimulationMessage

from components.fsm.states import TugState

from processors.base_processor import BaseProcessor

from exceptions import NoPathException, PathTerminatedException

from processors.utils import target_reached


class TugGoalFormulatorProcessor(BaseProcessor):
    RESOURCE_CHECK_FRAME_DELTA = 20

    def __init__(self):
        self.message_broker = MessageBroker.get_instance()
        self.message_per_state = {
            TugState.IDLE: TugMessageType.NOT_TUGGING,
            TugState.GOING_TO_BERTH: TugMessageType.NOT_TUGGING,
            TugState.GOING_TO_RENDEZVOUS: TugMessageType.NOT_TUGGING,
            TugState.WAITING_AT_RENDEZVOUS: TugMessageType.NOT_TUGGING,
            TugState.WAITING_AT_BERTH: TugMessageType.NOT_TUGGING,
            # If this is uncommented, then the tug can also break down on its way to waiting location
            # But I've noticed this introduces additional bugs
            # TugState.GOING_TO_WAITING_LOCATION: TugMessageType.NOT_TUGGING,
            TugState.TUGGING_IN: TugMessageType.TUGGING_IN,
            TugState.TUGGING_OUT: TugMessageType.TUGGING_OUT
        }

    def _process(self, dt):
        for ent, (pos, frame_counter, _, vel, vessel_path, vessel_fsm, _) in fetch_tugs(self.world):
            # Formulate a goal if none is set
            if not vessel_path.has_current_route() or target_reached(vessel_path, pos):
                self.formulate_goal(ent, vessel_path, vessel_fsm, vel)

            state = vessel_fsm.current()

            if state in self.message_per_state:
                self._send_harbour_master_message(
                    ent=ent,
                    message=self.message_per_state[state])

    def formulate_goal(self, ent, vessel_path, fsm, vel):
        """
            Retrieves the next node in path if a path exists, otherwise notifies the
            HM of its current status
        """
        try:
            _ = vessel_path.get_next_destination()
        except (NoPathException, PathTerminatedException) as _:
            current_state = fsm.current()

            if current_state == TugState.GOING_TO_RENDEZVOUS:
                fsm.wait_at_rendezvous()
            elif current_state == TugState.GOING_TO_WAITING_LOCATION:
                fsm.arrived_at_waiting_location()
            elif current_state == TugState.GOING_TO_BERTH:
                fsm.wait_at_berth()
            elif current_state == TugState.REPLACING_MALFUNCTIONING_TUG:
                fsm.wait_at_malfunction_location()
        finally:
            vessel_path.advance_path()

    def _send_harbour_master_message(self, ent, message):
        self.message_broker.send_message(
            SimulationMessage(
                sender=f"tug:{ent}",
                destination="harbour-master",
                message=message))
