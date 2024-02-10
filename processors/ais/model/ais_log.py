class AISPositionLogger:
    """Class that is used to log AIS-like simulator output data."""

    def __init__(self):
        self.logs = []

    def add_log(self, ent, pos, vel, course, speed_fsm_state, timestamp, state=None):
        self.logs.append(
            [
                ent,
                pos.lonlat[0],
                pos.lonlat[1],
                vel.velocity,
                course.course,
                speed_fsm_state,
                timestamp,
                state,
            ]
        )

    def header(self):
        return [
            [
                "entity",
                "lon",
                "lat",
                "velocity",
                "course",
                "speed_fsm_state",
                "timestamp",
                "state",
            ]
        ]

    def clear(self):
        self.logs = []
