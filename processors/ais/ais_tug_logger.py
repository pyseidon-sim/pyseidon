from environment import RunInfo
from environment.queries import fetch_tugs
from processors.ais.model.ais_log import AISPositionLogger
from processors.base_processor import BaseProcessor


class AISTugLogProcessor(BaseProcessor):
    def __init__(self):
        self.logger = AISPositionLogger()

    def _process(self, dt):
        for ent, (pos, _, cs, vel, _, fsm, _) in fetch_tugs(self.world):
            self.logger.add_log(
                ent,
                pos,
                vel,
                cs,
                None,
                RunInfo.get_instance().simulation_time(),
                state=fsm.current(),
            )
