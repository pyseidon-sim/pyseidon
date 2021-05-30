import csv
from colored import fg, attr

from datetime import datetime
from log.events.pilot import PilotEvent

from environment import RunInfo


class PilotEventLogger:
    __instance = None

    @staticmethod
    def get_instance():
        if PilotEventLogger.__instance is None:
            PilotEventLogger()

        return PilotEventLogger.__instance 

    def __init__(self):
        """Private constructor."""
        if PilotEventLogger.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            PilotEventLogger.__instance = self
            
            self._verbose = False
            self.pilot_logs = {}

    @property
    def verbose(self):
        return self._verbose

    @verbose.setter
    def verbose(self, verbose):
        self._verbose = verbose

    def log_event(self, ent, pilot_info, event: PilotEvent):
        if str(ent) not in self.pilot_logs:
            self.pilot_logs[str(ent)] = {
                "name": f"Pilot {ent}",
                "events": []
            }

        self.pilot_logs[str(ent)]["events"].append(event)

        if self.verbose:
            self._print_event(ent, pilot_info, event)

    def _print_event(self, ent, pilot_info, event):
        out_name = f"Pilot {ent}"

        if len(out_name) < 32:
            out_name = out_name + " " * (32 - len(out_name))

        event_log = event.to_log_string(
            RunInfo.get_instance().start_timestamp(),
            colored=True)

        formatted_date = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        event_string = f"[{formatted_date} : Pilots] "
        event_string += f"{fg(45)}{out_name}{attr(0)}\t{event_log}"

        print(event_string)

    def log_to_csv(self, out_filename):
        """Exports the logged events as a csv file."""
        with open(out_filename, "w") as out_file:
            csv_writer = csv.writer(
                out_file,
                delimiter=";",
                quoting=csv.QUOTE_MINIMAL)

            # Add header
            csv_writer.writerow(["pilot_id"] + PilotEvent.csv_header())

            for ent in self.pilot_logs.keys():
                events = self.pilot_logs[ent]["events"]

                for e in events:
                    csv_writer.writerow(
                        [ent] + e.to_list(RunInfo.get_instance().start_timestamp()))
