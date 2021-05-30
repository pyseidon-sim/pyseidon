import numbers


class Velocity:
    """Contains information on the 1D velocity of an entity"""
    def __init__(self, velocity: float):
        self._validate_velocity(velocity)
        self._velocity = velocity
    
    @property
    def velocity(self):
        return self._velocity

    @velocity.setter
    def velocity(self, velocity):
        self._validate_velocity(velocity)
        self._velocity = velocity

    def _validate_velocity(self, velocity):
        """Check if the velocity of the current instance is in valid format"""
        if not isinstance(velocity, numbers.Number):
            raise TypeError("The velocity must be a number!")

    def __str__(self):
        return f"<Velocity: {self._velocity}>"
