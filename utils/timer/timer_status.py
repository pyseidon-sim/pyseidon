from enum import Enum


class TimerStatus(Enum):
    FIRED = "fired"
    IN_PROGRESS = "in_progress"
    INVALIDATED = "invalidated"
