"""Utility functions for processors"""
import math
import random
import numpy as np
import numpy.linalg as la
from utils.constants import KNOTS_TO_METERS_SEC, METERS_TO_COORDS, TARGET_REACHED_DELTA


def lonlat_array_to_screen(proj, lonlat):
    """Projects a 2-dimensional array to the screen using the given projection"""
    if len(lonlat) != 2:
        raise ValueError("The lonlat argument must be a 2-dimensional vector")

    return proj.lonlat_to_screen(lonlat[0], lonlat[1])


def random_sign():
    """Generates either -1 or 1"""
    return 1 if random.random() < 0.5 else -1


def vector_angle(v1, v2):
    """Returns the angle in radians between vectors 'v1' and 'v2'"""
    cosang = np.dot(v1, v2)
    sinang = la.norm(np.cross(v1, v2))

    return np.arctan2(sinang, cosang)


def convert_course_angle(angle):
    """Converts the course angle (where 0 is the true north) to the angle referenced to the unit circle"""
    degrees_angle = math.degrees(angle)

    if degrees_angle < 180:
        return math.radians(90 - degrees_angle)
    
    return math.radians((360 - degrees_angle) + 90)


def course(direction):
    """Returns the course given a direction vector (target - current)"""
    north = np.array([0, 1])
    angle = -(math.atan2(direction[1], direction[0]) - math.atan2(north[1], north[0]))

    return angle


def smooth_course(direction, prev_course=0, smooth_value=0.2):
    c = course(direction)
    smooth_course = prev_course + smooth_value * (c - prev_course)
    
    return smooth_course


def knots_to_coords_sec(knots):
    # Consult https://www.usna.edu/Users/oceano/pguth/md_help/html/approx_equivalents.htm
    # for the approximation used here
    return (knots * KNOTS_TO_METERS_SEC) * METERS_TO_COORDS


def meters_to_coords_sec(meters):
    return meters * METERS_TO_COORDS


def target_reached(vessel_path, pos):
    target = vessel_path.get_current_destination()
    direction = np.array([pos.lon() - target[0], pos.lat() - target[1]])

    return np.linalg.norm(direction) < TARGET_REACHED_DELTA