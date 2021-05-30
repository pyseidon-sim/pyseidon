from processors.base_processor import BaseProcessor
from environment.queries import fetch_timers


class TimerProcessor(BaseProcessor):
    """This processor advances the simulation timers"""
    def _process(self, dt):
        for ent, (timer, ) in fetch_timers(self.world):
            timer.update(dt)

            if timer.completed():
                self.world.delete_entity(ent)
