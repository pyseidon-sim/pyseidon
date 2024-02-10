from environment import RunInfo
from environment.navigation.sections import SectionManager
from processors.ais.model import SectionLogger
from processors.base_processor import BaseProcessor


class SectionsLogProcessor(BaseProcessor):
    def __init__(self):
        self.logger = SectionLogger()

    def _process(self, dt):
        for section in SectionManager.get_instance().sections:
            self.logger.add_log(section, RunInfo.get_instance().simulation_time())
