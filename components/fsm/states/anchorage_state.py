class AnchorageState:
    """Enum-like class that represents an anchorage state in its finite
       state machine graph. A normal enum was not used due to fysom
       compatibility,
    """
    AVAILABLE = "available"

    @classmethod
    def all_states(cls):
        return [
            AnchorageState.AVAILABLE
        ]

    @classmethod
    def get_state_graph(cls):
        return {
            'initial': AnchorageState.AVAILABLE,
            'events': []
        }
