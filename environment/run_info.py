class RunInfo:
    """Singleton containing information of the simulation run."""

    __instance = None

    @staticmethod
    def get_instance():
        if RunInfo.__instance == None:
            RunInfo()

        return RunInfo.__instance

    def __init__(self):
        """Private constructor."""

        if RunInfo.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            RunInfo.__instance = self

            self.simulation_start_time = None
            self.simulation_end_time = None
            self.simulation_timestamp = None
            self.step_size_seconds = 0

    def set_simulation_start_time(self, simulation_start_time):
        """Set the simulation start time

        :param simulation_start_time: start time of the simulation.
        """
        self.simulation_start_time = simulation_start_time
        self.simulation_timestamp = simulation_start_time

    def set_simulation_end_time(self, simulation_end_time):
        self.simulation_end_time = simulation_end_time

    def set_simulation_step_size(self, step_size):
        assert step_size > 0, "Delta time should be positive"

        self.step_size_seconds = step_size

    def set_simulation_time(self, time):
        self.simulation_timestamp = time

    def update_time(self):
        assert self.simulation_timestamp is not None, "Simulation time not set up"
        self.set_simulation_time(self.simulation_timestamp + self.step_size_seconds)

    def start_timestamp(self):
        assert (
            self.simulation_start_time is not None
        ), "Simulation start time not set up"
        return self.simulation_start_time

    def end_timestamp(self):
        return self.simulation_end_time

    def timestamp(self):
        """Return how long the simulation has been running for
        :return: runtime of the simulation as timestamp
        """
        assert self.simulation_timestamp is not None, "Simulation time not set up"
        return self.simulation_timestamp

    def simulation_time(self):
        """Return the current time of the simulation
        :return: current time of the simulation
        """
        assert self.simulation_timestamp is not None, "Simulation time not set up"
        assert (
            self.simulation_start_time is not None
        ), "Simulation start time not set up"

        return self.simulation_timestamp - self.simulation_start_time
