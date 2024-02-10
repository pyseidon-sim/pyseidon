import csv
from datetime import datetime

from colored import attr, fg

from environment import RunInfo
from log.events.vessel import VesselEvent


class VesselEventLogger:
    __instance = None

    @staticmethod
    def get_instance():
        if VesselEventLogger.__instance is None:
            VesselEventLogger()

        return VesselEventLogger.__instance

    def __init__(self):
        """Private constructor."""
        if VesselEventLogger.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            VesselEventLogger.__instance = self

            self._verbose = False
            self.vessel_logs = {}

    @property
    def verbose(self):
        return self._verbose

    @verbose.setter
    def verbose(self, verbose):
        self._verbose = verbose

    def log_event(self, ent, vessel_info, event: VesselEvent):
        if str(ent) not in self.vessel_logs:
            self.vessel_logs[str(ent)] = {"name": vessel_info.name, "events": []}

        self.vessel_logs[str(ent)]["events"].append(event)

        if self.verbose:
            self._print_event(ent, vessel_info, event)

    def _print_event(self, ent, vessel_info, event):
        out_name = f"{vessel_info.name} ({ent})"

        if len(out_name) < 32:
            out_name = out_name + " " * (32 - len(out_name))

        event_log = event.to_log_string(
            RunInfo.get_instance().start_timestamp(), colored=True
        )

        formatted_date = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        event_string = f"[{formatted_date} : Vessels] "
        event_string += f"{fg(45)}{out_name}{attr(0)}\t{event_log}"

        print(event_string)

    def log_to_string(self, colored=False):
        """Write out the logged files to a string."""

        out_string = ""

        for vessel_id in self.vessel_logs.keys():
            vessel_data = self.vessel_logs[vessel_id]
            vessel_info = self.vessel_logs[vessel_id]["events"][0].vessel_info

            if colored:
                out_string = f"{out_string}{fg(45)}{vessel_data['name']}{attr(0)} ({vessel_id}):\n"
                out_string = f"{out_string}{fg(47)}Tugs: {vessel_info.number_of_tugboats} | Pilots {vessel_info.pilot_required}{attr(0)}\n"
            else:
                out_string = f"{out_string}{vessel_data['name']} ({vessel_id}):\n"
                out_string = f"{out_string}Tugs: {vessel_info.number_of_tugboats} | Pilots {vessel_info.pilot_required}\n"

            for event in vessel_data["events"]:
                event_log = event.to_log_string(
                    RunInfo.get_instance().start_timestamp(), colored=colored
                )
                out_string = f"{out_string}  - {event_log}\n"

            out_string = f"{out_string}\n"

        return out_string

    def log_to_csv(self, out_filename):
        """Exports the logged events as a csv file."""

        with open(out_filename, "w") as out_file:
            csv_writer = csv.writer(out_file, delimiter=";", quoting=csv.QUOTE_MINIMAL)

            # Add header
            csv_writer.writerow(["vessel_id"] + VesselEvent.csv_header())

            for ent in self.vessel_logs.keys():
                events = self.vessel_logs[ent]["events"]

                for e in events:
                    csv_writer.writerow(
                        [ent] + e.to_list(RunInfo.get_instance().start_timestamp())
                    )
