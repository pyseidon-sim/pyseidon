import numpy as np
import pandas as pd

from .vessel_class import VesselClass


class BerthServiceDistributionFactory:
    def __init__(self, service_time_filename):
        self.service_data = pd.read_csv(service_time_filename, sep=",", index_col=False)
        self._build_terminal_service_times_dict()

    def _build_terminal_service_times_dict(self):
        service_dict = {}

        # Convert class columns data type from string to int
        mapping = {}
        for column in self.service_data.columns:
            if "class" in column:
                mapping[column] = "int32"

        self.service_data = self.service_data.fillna("0").replace(" ", "0")
        self.service_data = self.service_data.astype(mapping)

        # The second value in the service dictionary is the standard deviation
        # and it is arbitrary
        for _, row in self.service_data.iterrows():
            service_dict[row["terminal"]] = {
                VesselClass.CLASS_1: (row["class 1"], row["class 1"] / 4),
                VesselClass.CLASS_2: (row["class 2"], row["class 2"] / 4),
            }

        self.terminal_service_times = service_dict

    def get_allowed_vessel_classes_for_terminal(self, terminal_name):
        allowed_classes = []

        for key, value in self.terminal_service_times[terminal_name].items():
            if value[0] > 0:
                allowed_classes.append(key)

        return allowed_classes

    def service_time_sampler(self, terminal_name):
        return lambda vessel_info: abs(
            np.random.normal(
                loc=self.terminal_service_times[terminal_name][
                    vessel_info.vessel_class
                ][0],
                scale=self.terminal_service_times[terminal_name][
                    vessel_info.vessel_class
                ][1],
            )
        )
