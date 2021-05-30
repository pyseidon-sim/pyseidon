import numpy as np
import pandas as pd

from components import Position, BerthInfo
from components.fsm import BerthStateMachine


class BerthsInitializer():
    """Generates berths world entities from a csv file input."""

    def __init__(self, world, filename, vessel_content_types,
                 berth_service_distribution_factory, berth_randomized_check_prob=0):
        self.world = world
        self.berths_data = pd.read_csv(filename, sep=",")
        self.vessel_content_types = vessel_content_types
        self.berth_service_distribution_factory = berth_service_distribution_factory
        self.berth_randomized_check_prob = berth_randomized_check_prob

    def create_berths(self):
        for _, row in self.berths_data.iterrows():
            self._create_berth(row)

    def _create_berth(self, row):
        """Create a berth as an esper world object"""

        berth = self.world.create_entity()

        position = np.array([
            float(row["lon"]),
            float(row["lat"])
        ])

        berth_info = BerthInfo(
                        row["id"],
                        row["name"],
                        row['max_quay_length'],
                        float(row['max_depth']),
                        self.vessel_content_types(int(row["ship_types"])),
                        allowed_vessel_classes=
                        self.berth_service_distribution_factory.get_allowed_vessel_classes_for_terminal(row["terminal"]),
                        section=row["section"])

        sampler = self.berth_service_distribution_factory.service_time_sampler(row["terminal"])

        self.world.add_component(berth, Position(lonlat=np.array(position)))
        self.world.add_component(berth, berth_info)
        self.world.add_component(berth, BerthStateMachine(sampler, self.berth_randomized_check_prob))
        
        return berth
