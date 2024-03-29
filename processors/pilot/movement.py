from environment.queries import fetch_pilots
from exceptions import NoPathException, PathTerminatedException
from processors.base_movement_processor import BaseMovementProcessor


class PilotMovementProcessor(BaseMovementProcessor):
    def _process(self, dt):
        for _, (pos, cs, vel, vessel_path, _, _) in fetch_pilots(self.world):
            try:
                self.update_position(vessel_path, pos, vel, cs, dt)
            except (PathTerminatedException, NoPathException) as _:
                pass
