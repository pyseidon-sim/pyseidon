import numpy as np

from processors.base_processor import BaseProcessor
from processors.utils import knots_to_coords_sec, smooth_course


class BaseMovementProcessor(BaseProcessor):
    def update_position(self, vessel_path, pos, vel, course, dt):
        # Calculate direction
        target = vessel_path.get_current_destination()
        direction = np.array([target[0] - pos.lon(), target[1] - pos.lat()])

        direction = direction / np.linalg.norm(direction)
        velocity = knots_to_coords_sec(vel.velocity)

        # Move the vessel
        pos.update_position(pos.lonlat + direction * velocity * dt)

        course.prev_course = course.course
        course.course = smooth_course(direction, course.course)

        return direction
