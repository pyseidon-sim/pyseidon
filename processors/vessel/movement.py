from processors.base_movement_processor import BaseMovementProcessor

from environment.queries import fetch_vessels
from exceptions import NoPathException, PathTerminatedException

from components import Position, Course, Velocity
from components.fsm import TugStateMachine, SpeedStateMachine
from components.fsm.states import VesselState, TugState, SpeedState

from processors.utils import knots_to_coords_sec, meters_to_coords_sec
from utils.constants import MIN_VESSEL_SPEED


class VesselMovementProcessor(BaseMovementProcessor):
    """
        Handles the process of updating the position and speed of a
        vessel in the port, whilst communicating it with the HarbourMasterProcessor
    """
    TUGS_DISTANCE_METERS = 200

    def __init__(self, vessel_base_class):
        """Initializes a movement processor

        Arguments:
        vessel_base_class -- the Python base class of vessel classes
        """
        self.vessel_base_class = vessel_base_class

    def _process(self, dt):
        for ent, (pos, _, cs, vel, vessel_path, fsm, vessel_info) in fetch_vessels(self.world):
            state = fsm.current()

            if not pos.is_valid() or state in [VesselState.LEFT, VesselState.TUG_MALFUNCTION]:
                # Skip vessels not yet fully created or departed
                continue

            try:
                # Smooth the vessel's velocity
                self._update_vessel_speed(vessel_info, vessel_path, vel)

                # Update the velocity if a vessel speed state machine is being used
                try:
                    speed_fsm = self.world.component_for_entity(ent, SpeedStateMachine)
                    step_velocity = Velocity(speed_fsm.update_input_velocity(vel.velocity))
                except:
                    step_velocity = vel

                direction = self.update_position(vessel_path, pos, step_velocity, cs, dt)
                velocity = knots_to_coords_sec(step_velocity.velocity)

                # Update tugs position
                if fsm.tugboats is not None:
                    for tug_id in fsm.tugboats:
                        tug_fsm = self.world.component_for_entity(tug_id, TugStateMachine)

                        if not (tug_fsm.current() == TugState.TUGGING_IN or tug_fsm.current() == TugState.TUGGING_OUT):
                            continue

                        tug_pos = self.world.component_for_entity(tug_id, Position)
                        tug_course = self.world.component_for_entity(tug_id, Course)

                        tug_pos.update_position(pos.lonlat + direction * velocity * dt + direction * meters_to_coords_sec(self.TUGS_DISTANCE_METERS))
                        tug_course.course = cs.course
            except (PathTerminatedException, NoPathException):
                pass

    def _update_vessel_speed(self, vessel_info, vessel_path, vel):
        angle = vessel_path.angle()
        vessel_class = self.vessel_base_class.get_vessel_class(
            vessel_info.length,
            vessel_info.actual_draught)

        c1 = 0.00001
        c2 = 10000

        if vessel_path.path is not None and vessel_path.path_idx < len(vessel_path.path['y']):
            speed_limit = vessel_path.get_current_section().speeds_for_class(vessel_class)
            vel.velocity = max(min(
                vel.velocity + (180 - angle) * c1 - (angle * vel.velocity) / c2,
                speed_limit['max']), speed_limit['min'])
        else:
            vel.velocity = vel.velocity + (180 - angle) * c1 - (angle * vel.velocity) / c2
        
        vel.velocity = max(MIN_VESSEL_SPEED, vel.velocity)
