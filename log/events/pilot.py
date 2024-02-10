from datetime import datetime

from colored import attr, fg


class PilotEvent:
    def __init__(self, event_type, pilot_info, velocity, timestamp):
        if timestamp is None:
            raise ValueError("The timestamp cannot be null!")

        self.pilot_info = pilot_info
        self.velocity = velocity
        self.event_type = event_type
        self.timestamp = timestamp

    @property
    def date(self):
        return datetime.fromtimestamp(self.timestamp)

    def __repr__(self):
        return f"<Tug Event: {self.event_type} | {self.date}>"

    def to_log_string(self, simulation_start_timestamp, colored=False):
        event_type = self.event_type.upper()
        sim_time = self.date - datetime.fromtimestamp(simulation_start_timestamp)

        out_string = ""

        if colored:
            out_string = f"{fg(178)}{event_type}{attr(0)} @ {sim_time}"
        else:
            out_string = f"{event_type}, {sim_time}"

        return out_string

    def to_list(self, simulation_start_timestamp):
        event_type = self.event_type.upper()
        sim_time = self.date - datetime.fromtimestamp(simulation_start_timestamp)

        return [
            self.timestamp,
            sim_time.total_seconds(),
            self.pilot_info.length,
            self.pilot_info.width,
            self.pilot_info.max_draught,
            self.pilot_info.actual_draught,
            self.velocity.velocity,
            event_type,
        ]

    @classmethod
    def csv_header(cls):
        return [
            "timestamp",
            "simulation_timestamp",
            "length",
            "width",
            "max_draught",
            "actual_draught",
            "speed",
            "event",
        ]
