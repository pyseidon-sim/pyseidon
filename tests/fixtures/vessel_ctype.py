from enum import Enum
from .vessel_type import VesselType


class VesselContentType(Enum):
    LIQUID_BULK = 1

    @classmethod
    def map_vessel_type_to_vessel_content_type(cls, vessel_type):
        return {
            VesselType.CHEMICAL_TANKER: VesselContentType.LIQUID_BULK
        }[vessel_type]
