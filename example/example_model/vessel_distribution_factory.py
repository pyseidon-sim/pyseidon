import numpy as np

from components import VesselInfo
from .vessel_type import VesselType
from .vessel_class import VesselClass
SECONDS_IN_HOUR = 60 * 60


class VesselDistributionFactory:
    def __init__(self):
        self._inter_arrival_means = self._build_vessel_inter_arrival_mean_dict()
        self._vessel_properties = self._build_vessel_info_dict()

    def vessel_info_sampler(self, vessel_type):
        return lambda: self._vessel_properties[vessel_type]

    def inter_arrival_time_sampler(self, vessel_type):
        return lambda: np.random.exponential(
            scale=self._inter_arrival_means[vessel_type]) * SECONDS_IN_HOUR

    def _build_vessel_inter_arrival_mean_dict(self):
        return {
            VesselType.BULK_CARRIER: 12,
            VesselType.CHEMICAL_TANKER: 7,
            VesselType.CONTAINER: 5
        }

    def _build_vessel_info_dict(self):
        info_per_vessel = {}

        # These metrics could be sampled from some distribution to introduce variability
        info_per_vessel[VesselType.BULK_CARRIER] = VesselInfo(
            length=200,
            width=30,
            max_draught=15,
            actual_draught=15,
            vessel_type=VesselType.BULK_CARRIER,
            vessel_class=VesselClass.get_vessel_class(200),
            pilot_required=True,
            number_of_tugboats=1)

        info_per_vessel[VesselType.CHEMICAL_TANKER] = VesselInfo(
            length=125,
            width=20,
            max_draught=8,
            actual_draught=8,
            vessel_type=VesselType.CHEMICAL_TANKER,
            vessel_class=VesselClass.get_vessel_class(125),
            pilot_required=True,
            number_of_tugboats=0)

        info_per_vessel[VesselType.CONTAINER] = VesselInfo(
            length=180,
            width=25,
            max_draught=10,
            actual_draught=10,
            vessel_type=VesselType.CONTAINER,
            vessel_class=VesselClass.get_vessel_class(180),
            pilot_required=True,
            number_of_tugboats=0)

        return info_per_vessel
