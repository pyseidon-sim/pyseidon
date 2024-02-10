from enum import Enum

from .vessel_type import VesselType


class VesselContentType(Enum):
    LIQUID_BULK = 1
    CONTAINER = 2
    DRY_BULK = 3
    CHEMICAL = 4
    NOT_PROCESSING = 5

    @classmethod
    def map_vessel_type_to_vessel_content_type(cls, vessel_type):
        return {
            VesselType.BULK_CARRIER: VesselContentType.DRY_BULK,
            VesselType.CHEMICAL_TANKER: VesselContentType.CHEMICAL,
            VesselType.CONTAINER: VesselContentType.CONTAINER,
        }[vessel_type]
