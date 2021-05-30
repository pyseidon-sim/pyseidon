import numpy as np
from haversine import haversine
from math import acos, degrees

from exceptions import NoPathException, PathTerminatedException


class VesselPath:
    """Contains information on the path of a vessel"""

    def __init__(self):
        self.path_idx = 0
        self.path = None

    def get_path_node_id(self):
        return self.path_idx

    def advance_path(self):
        self.path_idx += 1

    def get_next_destination(self):
        """Returns the current destination node in the path"""
        if self.path is None:
            raise NoPathException("The path is none")

        try:
            return np.array([
                self.path["x"][self.path_idx + 1],
                self.path["y"][self.path_idx + 1]
            ])
        except Exception as _:
            raise PathTerminatedException("Path terminated")

    def get_current_destination(self):
        """Returns the current destination node in the path"""
        if self.path is None:
            raise NoPathException("The path is none")

        try:
            return np.array([
                self.path["x"][self.path_idx],
                self.path["y"][self.path_idx]
            ])
        except Exception as _:
            raise PathTerminatedException("Path terminated")

    def get_next_section(self):
        """Get the next section in the current path. if the target was reached
           raises a NoPathException
        """
        if self.path is None:
            raise NoPathException("The path is none")

        try:
            return self.path["point_sections"][self.path_idx + 1]
        except Exception as _:
            raise PathTerminatedException("Path terminated")

    def get_current_section(self):
        """Returns the current section in the path"""
        if self.path is None:
            raise NoPathException("The path is none")

        try:
            return self.path["point_sections"][self.path_idx]
        except Exception as _:
            raise NoPathException("Path terminated")

    def get_crossed_sections(self):
        """Returns an array of sections crossed by this path"""
        if self.path is None:
            raise NoPathException("The path is none")

        return self.path["crossed_sections"]

    def has_current_route(self):
        # If no path is set there is no current route
        if self.path is None:
            return False
        
        # Check if there is a valid destination in the path, if
        # that is not the case an exception will be raised
        try:
            self.get_current_destination()
        except Exception as _:
            return False

        return True
    
    def get_origin(self):
        if self.path is None:
            raise NoPathException("The path is none")

        return [
            self.path["x"][0],
            self.path["y"][0]
        ]

    def set_path(self, path):
        if path is None:
            raise NoPathException("The path is none")

        self.path = path
        self.path_idx = 0

    def angle(self, window=1):
        """
            Returns the positive angle in degrees of the boat compared to the 'window' previous point.
            If the boat turns left or right the angle will be 90.
        """
        current = self.path_idx

        if (current - 1) < window or (current + window - 1) >= len(self.path["y"]):
            return 0
        else:
            prev = (self.path['y'][current - window - 1], self.path['x'][current - window - 1])
            cur = (self.path['y'][current - 1], self.path['x'][current - 1])
            nex = (self.path['y'][current + window - 1], self.path['x'][current + window - 1])

            d_B = abs(haversine(cur, prev))
            d_A = abs(haversine(cur, nex))
            d_C = abs(haversine(nex, prev))

            if d_B == 0 or d_A == 0:
                return 0

        return 180 - degrees(acos(round((d_A * d_A + d_B * d_B - d_C * d_C) / (2.0 * d_A * d_B), 5)))
