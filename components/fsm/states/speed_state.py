class SpeedState:
    """Enum-like class that represents a velocity's state in its finite
       state machine graph. A normal enum was not used due to fysom
       compatibility.
    """

    NORMAL = "normal"
    DOUBLE = "double"
    HALF = "half"

    @classmethod
    def get_state_graph(cls):
        speed_events = [
            {
                'name': 'double_speed',
                'src': SpeedState.NORMAL,
                'dst': SpeedState.DOUBLE
            },
            {
                'name': 'halve_speed',
                'src': SpeedState.NORMAL,
                'dst': SpeedState.HALF
            },
            {
                'name': 'return_to_normal',
                'src': [SpeedState.DOUBLE, SpeedState.HALF],
                'dst': SpeedState.NORMAL
            }
        ]

        return {
            'initial': SpeedState.NORMAL,
            'events': speed_events
        }
