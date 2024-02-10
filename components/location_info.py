from enum import Enum


class LocationType(Enum):
    """Enumeration for location types
    To be implemented according to the environment.
    e.g: storage, ...
    """

    TUGBOATS_STORAGE = "tugs-storage"
    PILOTS_STORAGE = "pilots-storage"


class LocationInfo:
    """Contains information for a location in the port"""

    def __init__(self, id, name, location_type: LocationType):
        """Initializes a new LocationInfo

        :param id: location id
        :param name: name of the location.
        :param location_type: location type.
        """
        self.id = id
        self.name = name
        self.type = location_type
