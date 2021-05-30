from environment.queries import fetch_tugs
from components.fsm.states import TugState
from processors.base_movement_processor import BaseMovementProcessor

from exceptions import NoPathException, PathTerminatedException


class TugMovementProcessor(BaseMovementProcessor):
    def _process(self, dt):
        for _, (pos, _, cs, vel, vessel_path, fsm, _) in fetch_tugs(self.world):
            if fsm.current() in [TugState.BROKEN, TugState.TUGGING_IN, TugState.TUGGING_OUT]:
                continue

            try:
                self.update_position(vessel_path, pos, vel, cs, dt)
            except (PathTerminatedException, NoPathException):
                pass
