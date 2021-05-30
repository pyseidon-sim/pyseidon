from environment import RunInfo

from processors.base_processor import BaseProcessor

from environment.queries import fetch_pilots
from processors.ais.model.ais_log import AISPositionLogger


class AISPilotLogProcessor(BaseProcessor):
    def __init__(self):
        self.logger = AISPositionLogger()

    def _process(self, dt):
        for ent, (pos, cs, vel, _, fsm, _) in fetch_pilots(self.world):
            self.logger.add_log(ent, pos, vel, cs, None, RunInfo.get_instance().simulation_time(), state=fsm.current())
