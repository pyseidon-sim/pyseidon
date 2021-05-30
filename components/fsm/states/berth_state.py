class BerthState:
    """Enum-like class that represents a berth's state in its finite
       state machine graph. A normal enum was not used due to fysom
       compatibility.
    """
    AVAILABLE = "available"
    WAITING_FOR_VESSEL = "waiting_for_vessel"
    SERVING_VESSEL = "serving_vessel"

    @classmethod
    def all_states(cls):
        return [
            BerthState.AVAILABLE,
            BerthState.WAITING_FOR_VESSEL,
            BerthState.SERVING_VESSEL
        ]

    @classmethod
    def get_state_graph(cls):
        berth_events = [
            {'name': 'book', 'src': BerthState.AVAILABLE, 'dst': BerthState.WAITING_FOR_VESSEL},
            {'name': 'process_boat', 'src': BerthState.WAITING_FOR_VESSEL, 'dst': BerthState.SERVING_VESSEL},
            {'name': 'finish_processing', 'src': BerthState.SERVING_VESSEL, 'dst': BerthState.AVAILABLE}
        ]

        return {
            'initial': BerthState.AVAILABLE,
            'events': berth_events
        }
