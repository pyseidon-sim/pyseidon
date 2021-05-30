from enum import Enum


class TugMessageType(Enum):
    """Enumeration of different types of messages a tug can send."""

    TUGGING_OUT = "tugging_out"
    TUGGING_IN = "tugging_in"
    NOT_TUGGING = "not_tugging"
