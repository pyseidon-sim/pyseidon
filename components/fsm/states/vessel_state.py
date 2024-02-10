class VesselState:
    """Enum-like class that represents a vessel's state in its finite
    state machine graph. A normal enum was not used due to fysom
    compatibility.
    """

    SCHEDULED = "scheduled"
    INCOMING = "incoming"
    GOING_TO_BERTH = "going_to_berth"
    GOING_TO_ANCHORAGE = "going_to_anchorage"
    GOING_TO_PILOT_RENDEZVOUS = "going_to_pilot_rendezvous"
    GOING_TO_TUGS_RENDEZVOUS = "going_to_tugs_rendezvous"
    WAITING_FOR_DEPARTURE_CLEARANCE = "waiting_for_departure_clearance"
    WAITING_FOR_TUGS_PILOTS_BERTH = "waiting_for_tugs_pilots_berth"
    WAITING_AT_ANCHORAGE = "waiting_at_anchorage"
    WAITING_FOR_TUGS_RENDEZVOUS = "waiting_for_tugs_rendezvous"
    TUG_MALFUNCTION = "tug_malfunction"
    WAITING_FOR_PILOTS_RENDEZVOUS = "waiting_for_pilots_rendezvous"
    SERVICING = "servicing"
    LEAVING = "leaving"
    LEFT = "left"

    @classmethod
    def all_states(cls):
        return [
            VesselState.SCHEDULED,
            VesselState.INCOMING,
            VesselState.GOING_TO_BERTH,
            VesselState.GOING_TO_ANCHORAGE,
            VesselState.GOING_TO_PILOT_RENDEZVOUS,
            VesselState.GOING_TO_TUGS_RENDEZVOUS,
            VesselState.WAITING_FOR_DEPARTURE_CLEARANCE,
            VesselState.WAITING_FOR_TUGS_PILOTS_BERTH,
            VesselState.WAITING_AT_ANCHORAGE,
            VesselState.WAITING_FOR_TUGS_RENDEZVOUS,
            VesselState.WAITING_FOR_PILOTS_RENDEZVOUS,
            VesselState.SERVICING,
            VesselState.LEAVING,
            VesselState.LEFT,
            VesselState.TUG_MALFUNCTION,
        ]

    @classmethod
    def get_state_graph(cls):
        vessel_events = [
            {
                "name": "generate",
                "src": VesselState.SCHEDULED,
                "dst": VesselState.INCOMING,
            },
            {
                "name": "go_to_berth",
                "src": [
                    VesselState.WAITING_FOR_PILOTS_RENDEZVOUS,
                    VesselState.WAITING_FOR_TUGS_RENDEZVOUS,
                    VesselState.INCOMING,
                    VesselState.WAITING_AT_ANCHORAGE,
                    VesselState.GOING_TO_ANCHORAGE,
                ],
                "dst": VesselState.GOING_TO_BERTH,
            },
            {
                "name": "go_to_anchorage",
                "src": VesselState.INCOMING,
                "dst": VesselState.GOING_TO_ANCHORAGE,
            },
            {
                "name": "go_to_pilots_rendezvous",
                "src": [
                    VesselState.INCOMING,
                    VesselState.WAITING_AT_ANCHORAGE,
                    VesselState.GOING_TO_ANCHORAGE,
                ],
                "dst": VesselState.GOING_TO_PILOT_RENDEZVOUS,
            },
            {
                "name": "go_to_tugs_rendezvous",
                "src": [
                    VesselState.INCOMING,
                    VesselState.WAITING_AT_ANCHORAGE,
                    VesselState.WAITING_FOR_PILOTS_RENDEZVOUS,
                ],
                "dst": VesselState.GOING_TO_TUGS_RENDEZVOUS,
            },
            {
                "name": "wait_for_tugs_pilots",
                "src": [
                    VesselState.WAITING_FOR_DEPARTURE_CLEARANCE,
                    VesselState.WAITING_FOR_TUGS_PILOTS_BERTH,
                ],
                "dst": VesselState.WAITING_FOR_TUGS_PILOTS_BERTH,
            },
            {
                "name": "stop_at_anchorage",
                "src": [
                    VesselState.GOING_TO_ANCHORAGE,
                    VesselState.WAITING_AT_ANCHORAGE,
                ],
                "dst": VesselState.WAITING_AT_ANCHORAGE,
            },
            {
                "name": "stop_at_pilots_rendezvous",
                "src": VesselState.GOING_TO_PILOT_RENDEZVOUS,
                "dst": VesselState.WAITING_FOR_PILOTS_RENDEZVOUS,
            },
            {
                "name": "stop_at_tugs_rendezvous",
                "src": VesselState.GOING_TO_TUGS_RENDEZVOUS,
                "dst": VesselState.WAITING_FOR_TUGS_RENDEZVOUS,
            },
            {
                "name": "servicing",
                "src": VesselState.GOING_TO_BERTH,
                "dst": VesselState.SERVICING,
            },
            {
                "name": "done_servicing",
                "src": VesselState.SERVICING,
                "dst": VesselState.WAITING_FOR_DEPARTURE_CLEARANCE,
            },
            {
                "name": "leave",
                "src": [
                    VesselState.WAITING_FOR_TUGS_PILOTS_BERTH,
                    VesselState.WAITING_FOR_DEPARTURE_CLEARANCE,
                ],
                "dst": VesselState.LEAVING,
            },
            {"name": "complete", "src": VesselState.LEAVING, "dst": VesselState.LEFT},
            {
                "name": "tug_malfunction",
                "src": [VesselState.LEAVING, VesselState.GOING_TO_BERTH],
                "dst": VesselState.TUG_MALFUNCTION,
            },
            {
                "name": "tug_fix_berth",
                "src": VesselState.TUG_MALFUNCTION,
                "dst": VesselState.GOING_TO_BERTH,
            },
            {
                "name": "tug_fix_leaving",
                "src": VesselState.TUG_MALFUNCTION,
                "dst": VesselState.LEAVING,
            },
        ]

        return {
            "initial": VesselState.SCHEDULED,
            "final": VesselState.LEFT,
            "events": vessel_events,
        }
