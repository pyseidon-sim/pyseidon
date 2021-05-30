class PilotState:
    """Enum-like class that represents a pilot's state in its finite
       state machine graph. A normal enum was not used due to fysom
       compatibility.
    """
    IDLE = "idle"
    WAITING_AT_RENDEZVOUS = "waiting_at_rendezvous"
    GOING_TO_RENDEZVOUS = "going_to_rendezvous"
    GOING_TO_BERTH = "going_to_berth"
    WAITING_AT_BERTH = "waiting_at_berth"
    GOING_TO_WAITING_LOCATION = "GOING_TO_WAITING_LOCATION"

    @classmethod
    def all_states(cls):
        return [
            PilotState.IDLE,
            PilotState.WAITING_AT_RENDEZVOUS,
            PilotState.GOING_TO_RENDEZVOUS,
            PilotState.GOING_TO_BERTH,
            PilotState.WAITING_AT_BERTH,
            PilotState.GOING_TO_WAITING_LOCATION
        ]

    @classmethod
    def busy_states(cls):
        return [
            PilotState.GOING_TO_RENDEZVOUS,
            PilotState.GOING_TO_BERTH,
            PilotState.WAITING_AT_RENDEZVOUS,
            PilotState.WAITING_AT_BERTH,
            PilotState.GOING_TO_WAITING_LOCATION
        ]

    @classmethod
    def get_state_graph(cls):
        pilot_events = [
            {
                'name': 'go_to_rendezvous',
                'src': PilotState.IDLE,
                'dst': PilotState.GOING_TO_RENDEZVOUS
            },
            {
                'name': 'go_to_berth',
                'src': PilotState.IDLE,
                'dst': PilotState.GOING_TO_BERTH
            },
            {
                'name': 'arrive_at_rendezvous',
                'src': PilotState.GOING_TO_RENDEZVOUS,
                'dst': PilotState.WAITING_AT_RENDEZVOUS
            },
            {
                'name': 'arrive_at_berth',
                'src': PilotState.GOING_TO_BERTH,
                'dst': PilotState.WAITING_AT_BERTH
            },
            {
                'name': 'deliver_pilot',
                'src': [PilotState.WAITING_AT_RENDEZVOUS, PilotState.WAITING_AT_BERTH],
                'dst': PilotState.GOING_TO_WAITING_LOCATION
            },
            {
                'name': 'arrive_at_waiting_location',
                'src': PilotState.GOING_TO_WAITING_LOCATION,
                'dst': PilotState.IDLE
            }
        ]

        return {
            'initial': PilotState.IDLE,
            'events': pilot_events
        }
