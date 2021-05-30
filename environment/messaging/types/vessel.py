from enum import Enum


class VesselMessageType(Enum):
    """Enumeration of different types of messages a vessel can send."""

    REQUEST_ARRIVAL_CLEARANCE = "request-arrival-clearance"
    REQUEST_DEPARTURE_CLEARANCE = "request-departure-clearance"

    DOCKED_AT_TERMINAL = "docked-at-terminal"
    GOING_TO_ANCHORAGE = "going-to-anchorage"
    WAITING_AT_ANCHORAGE = "waiting-at-anchorage"
    DEPART = "depart"
    WAITING_FOR_TUGS_AT_RENDEZVOUS = "waiting-for-tugs-rv"
    WAITING_FOR_PILOT_AT_RENDEZVOUS = "waiting-for-pilot-rv"
    DEPARTED = "departed"
    GO_TO_BERTH = "go-to-berth"
    GO_TO_TUGS_RENDEZVOUS = "go-to-tugs-rendezvous"
    GO_TO_PILOT_RENDEZVOUS = "go-to-pilot-rendezvous"

    CHANGE_SECTION = "change-section"

    FIX_TUG = "fix-tug"

    def is_section_message(self):
        return self == VesselMessageType.CHANGE_SECTION
