class TugState:
    """Enum-like class that represents a tugboat's state in its finite
    state machine graph. A normal enum was not used due to fysom
    compatibility
    """

    IDLE = "idle"
    GOING_TO_RENDEZVOUS = "going_to_rendezvous"
    WAITING_AT_RENDEZVOUS = "waiting_at_rendezvous"
    WAITING_AT_BERTH = "waiting_at_berth"
    TUGGING_IN = "tugging_in"
    TUGGING_OUT = "tugging_out"
    GOING_TO_WAITING_LOCATION = "going_to_waiting_location"
    GOING_TO_BERTH = "going_to_berth"
    BROKEN = "broken"
    REPLACING_MALFUNCTIONING_TUG = "replacing_malfunctioning_tug"
    WAITING_AT_MALFUNCTION_LOCATION = "waiting_at_malfunction_location"

    @classmethod
    def all_states(cls):
        return [
            TugState.IDLE,
            TugState.GOING_TO_RENDEZVOUS,
            TugState.WAITING_AT_RENDEZVOUS,
            TugState.WAITING_AT_BERTH,
            TugState.TUGGING_IN,
            TugState.TUGGING_OUT,
            TugState.GOING_TO_WAITING_LOCATION,
            TugState.GOING_TO_BERTH,
            TugState.BROKEN,
            TugState.REPLACING_MALFUNCTIONING_TUG,
            TugState.WAITING_AT_MALFUNCTION_LOCATION,
        ]

    @classmethod
    def breakable_states(cls):
        return [
            TugState.IDLE,
            TugState.GOING_TO_RENDEZVOUS,
            TugState.TUGGING_IN,
            TugState.TUGGING_OUT,
            TugState.GOING_TO_BERTH,
        ]

    @classmethod
    def busy_states(cls):
        return [
            TugState.GOING_TO_RENDEZVOUS,
            TugState.GOING_TO_BERTH,
            TugState.TUGGING_IN,
            TugState.TUGGING_OUT,
            TugState.WAITING_AT_BERTH,
            TugState.WAITING_AT_RENDEZVOUS,
            TugState.BROKEN,
            TugState.GOING_TO_WAITING_LOCATION,
            TugState.REPLACING_MALFUNCTIONING_TUG,
            TugState.WAITING_AT_MALFUNCTION_LOCATION,
        ]

    @classmethod
    def get_state_graph(cls):
        tug_events = [
            {
                "name": "go_to_rendezvous",
                "src": [TugState.IDLE, TugState.GOING_TO_WAITING_LOCATION],
                "dst": TugState.GOING_TO_RENDEZVOUS,
            },
            {
                "name": "wait_at_rendezvous",
                "src": TugState.GOING_TO_RENDEZVOUS,
                "dst": TugState.WAITING_AT_RENDEZVOUS,
            },
            {
                "name": "go_to_berth",
                "src": [TugState.IDLE, TugState.GOING_TO_WAITING_LOCATION],
                "dst": TugState.GOING_TO_BERTH,
            },
            {
                "name": "wait_at_berth",
                "src": TugState.GOING_TO_BERTH,
                "dst": TugState.WAITING_AT_BERTH,
            },
            {
                "name": "start_tugging_in",
                "src": [
                    TugState.WAITING_AT_RENDEZVOUS,
                    TugState.WAITING_AT_BERTH,
                    TugState.WAITING_AT_MALFUNCTION_LOCATION,
                ],
                "dst": TugState.TUGGING_IN,
            },
            {
                "name": "start_tugging_out",
                "src": [
                    TugState.WAITING_AT_RENDEZVOUS,
                    TugState.WAITING_AT_BERTH,
                    TugState.WAITING_AT_MALFUNCTION_LOCATION,
                ],
                "dst": TugState.TUGGING_OUT,
            },
            {
                "name": "done_tugging",
                "src": [TugState.TUGGING_IN, TugState.TUGGING_OUT],
                "dst": TugState.GOING_TO_WAITING_LOCATION,
            },
            {
                "name": "arrived_at_waiting_location",
                "src": TugState.GOING_TO_WAITING_LOCATION,
                "dst": TugState.IDLE,
            },
            {
                "name": "break_down",
                "src": [
                    TugState.GOING_TO_BERTH,
                    TugState.GOING_TO_WAITING_LOCATION,
                    TugState.GOING_TO_RENDEZVOUS,
                    TugState.TUGGING_IN,
                    TugState.TUGGING_OUT,
                    TugState.IDLE,
                    TugState.WAITING_AT_RENDEZVOUS,
                    TugState.WAITING_AT_BERTH,
                    TugState.WAITING_AT_BERTH,
                ],
                "dst": TugState.BROKEN,
            },
            {
                "name": "get_fixed_busy",
                "src": TugState.BROKEN,
                "dst": TugState.GOING_TO_WAITING_LOCATION,
            },
            {"name": "get_fixed_idle", "src": TugState.BROKEN, "dst": TugState.IDLE},
            {
                "name": "go_to_malfunction_location",
                "src": TugState.IDLE,
                "dst": TugState.REPLACING_MALFUNCTIONING_TUG,
            },
            {
                "name": "wait_at_malfunction_location",
                "src": [
                    TugState.REPLACING_MALFUNCTIONING_TUG,
                    TugState.TUGGING_IN,
                    TugState.TUGGING_OUT,
                ],
                "dst": TugState.WAITING_AT_MALFUNCTION_LOCATION,
            },
        ]

        return {"initial": TugState.IDLE, "events": tug_events}
