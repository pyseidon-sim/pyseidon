import csv
from datetime import datetime

from colored import attr, fg

from environment import RunInfo
from log.events.tug import TugEvent


class TugEventLogger:
    __instance = None

    @staticmethod
    def get_instance():
        if TugEventLogger.__instance is None:
            TugEventLogger()

        return TugEventLogger.__instance

    def __init__(self):
        """Private constructor."""
        if TugEventLogger.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            TugEventLogger.__instance = self

            self._verbose = False
            self.tug_logs = {}

    @property
    def verbose(self):
        return self._verbose

    @verbose.setter
    def verbose(self, verbose):
        self._verbose = verbose

    def log_event(self, ent, tug_info, event: TugEvent):
        if str(ent) not in self.tug_logs:
            self.tug_logs[str(ent)] = {"name": f"Tug {ent}", "events": []}

        self.tug_logs[str(ent)]["events"].append(event)

        if self.verbose:
            self._print_event(ent, tug_info, event)

    def _print_event(self, ent, pilot_info, event):
        out_name = f"Tug {ent}"

        if len(out_name) < 32:
            out_name = out_name + " " * (32 - len(out_name))

        event_log = event.to_log_string(
            RunInfo.get_instance().start_timestamp(), colored=True
        )

        formatted_date = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        event_string = f"[{formatted_date} : Tugs] "
        event_string += f"{fg(45)}{out_name}{attr(0)}\t\t{event_log}"

        print(event_string)

    def log_to_csv(self, out_filename):
        """Exports the logged events as a csv file."""
        with open(out_filename, "w") as out_file:
            csv_writer = csv.writer(out_file, delimiter=";", quoting=csv.QUOTE_MINIMAL)

            # Add header
            csv_writer.writerow(["tug_id"] + TugEvent.csv_header())

            for ent in self.tug_logs.keys():
                events = self.tug_logs[ent]["events"]

                for e in events:
                    csv_writer.writerow(
                        [ent] + e.to_list(RunInfo.get_instance().start_timestamp())
                    )
