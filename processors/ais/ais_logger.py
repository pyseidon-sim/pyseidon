from components import Velocity
from components.fsm import SpeedStateMachine
from environment import RunInfo
from environment.queries import fetch_vessels
from processors.ais.model.ais_log import AISPositionLogger
from processors.base_processor import BaseProcessor


class AISVesselLogProcessor(BaseProcessor):
    def __init__(self):
        self.logger = AISPositionLogger()

    def _process(self, dt):
        for ent, (pos, _, cs, vel, _, fsm, _) in fetch_vessels(self.world):
            try:
                speed_fsm = self.world.component_for_entity(ent, SpeedStateMachine)
                speed_fsm_state = speed_fsm.current()

                # Update the velocity to match the speed FSM state
                vel = Velocity(speed_fsm.update_input_velocity(vel.velocity))
            except:
                speed_fsm_state = None

            self.logger.add_log(
                ent,
                pos,
                vel,
                cs,
                speed_fsm_state,
                RunInfo.get_instance().simulation_time(),
                state=fsm.current(),
            )
