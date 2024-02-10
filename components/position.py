import numpy as np


class Position:
    """Entity position component"""

    # The length of the vessel position's history
    TRACE_LENGTH = 100

    def __init__(self, lonlat=None):
        self._history = {"lon": [], "lat": []}

        self._lonlat = lonlat

        if self._lonlat is None:
            return

        if not self.is_valid():
            raise ValueError("The position must be a 2-valued numpy array")

        self._save_to_history(lonlat)

    @property
    def lonlat(self):
        """Returns the position in [lon, lat] format"""

        return self._lonlat

    def is_valid(self):
        """Check if the position of the current instance is in valid format"""
        # Force numpy arrays usage because of the graphics framework
        return type(self._lonlat) == np.ndarray and len(self._lonlat) == 2

    def update_position(self, lonlat):
        """Update the position of this component

        :param lonlat: numpy array of the form [lon, lat] where lon and lat are numeric values.
        """
        self._lonlat = lonlat
        self._save_to_history(lonlat)

        # Keep only the last n positions
        self._history["lon"] = self._history["lon"][-self.TRACE_LENGTH :]
        self._history["lat"] = self._history["lat"][-self.TRACE_LENGTH :]

    def _save_to_history(self, lonlat):
        self._history["lon"].append(lonlat[0])
        self._history["lat"].append(lonlat[1])

    def history(self):
        """Return an array with previous position of the entity"""
        return self._history

    def lon(self):
        """Return the longitude"""
        return self._lonlat[0]

    def lat(self):
        """Return the latitude"""
        return self._lonlat[1]

    def __str__(self):
        return f"<Position: {self._lonlat}>"
