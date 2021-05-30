from datetime import datetime
from colored import fg, attr


class VesselEvent:
    def __init__(self, event_type, vessel_info, velocity, pilot, tug, berth, anchorage, timestamp):
        if timestamp is None:
            raise ValueError("The timestamp cannot be null!")

        self.vessel_info = vessel_info
        self.velocity = velocity
        self.pilot = pilot
        self.tug = tug
        self.berth = berth
        self.anchorage = anchorage
        self.event_type = event_type
        self.timestamp = timestamp

    @property
    def date(self):
        return datetime.fromtimestamp(self.timestamp)

    def __repr__(self):
        return f"<Vessel Event: {self.event_type} | {self.date}>"

    def to_log_string(self, simulation_start_timestamp, colored=False):
        event_type = self.event_type.upper()
        sim_time = self.date - datetime.fromtimestamp(simulation_start_timestamp)

        out_string = ""

        if colored:
            out_string = f"{fg(178)}{event_type}{attr(0)} @ {sim_time}"
        else:
            out_string = f"{event_type}, {sim_time}"

        if self.pilot is not None:
            out_string = f"{out_string} | Pilot: {self.pilot}"

        if self.berth is not None:
            out_string = f"{out_string} | Berth: {self.berth}"

        if self.anchorage is not None:
            out_string = f"{out_string} | Anchorage: {self.anchorage}"

        return out_string

    def to_list(self, simulation_start_timestamp):
        event_type = self.event_type.upper()
        sim_time = self.date - datetime.fromtimestamp(simulation_start_timestamp)

        return [
            self.timestamp,
            sim_time.total_seconds(),
            self.vessel_info.length,
            self.vessel_info.width,
            self.vessel_info.max_draught,
            self.vessel_info.actual_draught,
            self.vessel_info.vessel_class.value,
            self.vessel_info.vessel_type.value,
            self.velocity.velocity,
            self.vessel_info.pilot_required,
            self.vessel_info.number_of_tugboats,
            self.pilot,
            self.tug,
            self.berth,
            self.anchorage,
            event_type
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
            "vessel_class",
            "vessel_content_type",
            "speed",
            "pilot_required",
            "number_of_tugboats",
            "pilot_id",
            "tug_id",
            "berth_id",
            "anchorage_id",
            "event"
        ]
