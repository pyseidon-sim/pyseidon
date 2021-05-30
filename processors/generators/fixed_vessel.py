import random

from collections import namedtuple

from components.fsm import VesselStateMachine, SpeedStateMachine, NULL_SPEED_MODEL
from components import Position, Course, Velocity, VesselPath, FrameCounter
from utils.shapes import random_point_in_polygon

from processors.generators import VesselGeneratorProcessor


class FixedVesselGeneratorProcessor(VesselGeneratorProcessor):
    """
        Generates vessels based on an inter-arrival time and vessel
        properties generators, to be supplied as functions.
    """
    def __init__(
            self,
            world,
            inter_arrival_time_sampler,
            vessel_info_sampler,
            spawn_area_filename,
            run_info,
            tug_company_designator=None,
            vessel_logger=None,
            default_speed_knots=15,
            speed_model_probabilities=NULL_SPEED_MODEL,
            anomalous_vessels_percent=0):
        """
            :param world: Esper world object
            :param inter_arrival_time_sampler: a function that samples an inter-arrival time for vessels
            :param vessel_info_sampler: a function that samples vessel_info
            :param spawn_area_filename: the name of a geojson file that denotes a spawn area for vessels
            :param run_info: RunInfo singleton object that gives access to the simulation clock
            :param tug_company_designator: a function that assigns tugboats based on some logic
            :param vessel_logger: VesselEventLogger singleton that is logging events about vessels
            :param default_speed_knots: The default velocity of a vessel in knots
            :param speed_model_probabilities: The Markov Model depicting state of vessels velocities
             (used for generating velocity anomalies)
            :param anomalous_vessels_percent: the percentage of vessels with the anomalous speed model
        """
        assert world is not None, "A world is required!"
        assert inter_arrival_time_sampler is not None, "An inter-arrival distribution is required!"
        assert vessel_info_sampler is not None, "A vessel info sampler is required!"

        self.world = world
        self.vessel_info_sampler = vessel_info_sampler
        self.inter_arrival_time_sampler = inter_arrival_time_sampler
        self._load_spawn_area(spawn_area_filename)
        self.vessel_logger = vessel_logger
        self.default_speed_knots = default_speed_knots
        self.run_info = run_info
        self.tug_company_designator = tug_company_designator
        self.speed_model_probabilities = speed_model_probabilities
        self.anomalous_vessels_percent = anomalous_vessels_percent

        self.scheduled_vessels = self._generate_vessels_for_fixed_interval(run_info.end_timestamp())

    def _process(self, dt):
        generated_count = 0

        for vessel in self.scheduled_vessels:
            if vessel.time <= self.run_info.simulation_time():
                generated_count += 1
                self.initialize_vessel(vessel.vessel_info, vessel.fsm, vessel.speed_fsm)
            else:
                # Vessels are sorted in ascending time order so
                # when the time limit is crossed no more vessels
                # will be generated
                break

        # Remove vessels that have been generated from the list
        for _ in range(generated_count):
            self.scheduled_vessels.pop(0)

    def _generate_vessels_for_fixed_interval(self, end_time):
        """Generates vessels arrivals from time 0 up to end_time."""
        current_time = 0
        vessels = []

        GeneratedVessel = namedtuple('GeneratedVessel', ['time', 'vessel_info', 'fsm', 'speed_fsm'])

        while current_time < end_time:
            inter_arrival_time = self.inter_arrival_time_sampler()
            current_time += inter_arrival_time

            vessel_info = self.vessel_info_sampler()
            vessel_state_machine = VesselStateMachine()

            if random.random() <= self.anomalous_vessels_percent:
                # Add a markov model for creating speed anomalies
                speed_state_machine = SpeedStateMachine(
                    double_p=self.speed_model_probabilities["double"],
                    halve_p=self.speed_model_probabilities["half"],
                    normal_p=self.speed_model_probabilities["reset"])
            else:
                speed_state_machine = None

            if self.tug_company_designator is not None:
                vessel_state_machine.tug_company = self.tug_company_designator(vessel_state_machine)

            vessels.append(GeneratedVessel(
                time=current_time,
                vessel_info=vessel_info,
                fsm=vessel_state_machine,
                speed_fsm=speed_state_machine))

        return vessels

    def initialize_vessel(self, vessel_info, vessel_state_machine, speed_fsm):
        """Initialize the vessel and its components and adds them to the world."""

        # FIXME: This should be dependent on the vessel type
        vessel_velocity = self.default_speed_knots
        velocity = Velocity(velocity=vessel_velocity)

        spawn_point = random_point_in_polygon(self.spawn_area)
        vessel = self.world.create_entity()

        self.world.add_component(vessel, Course())
        self.world.add_component(vessel, FrameCounter())
        self.world.add_component(vessel, Position(lonlat=spawn_point))
        self.world.add_component(vessel, velocity)

        if speed_fsm is not None:
            self.world.add_component(vessel, speed_fsm)

        vessel_state_machine.generate()
        vessel_state_machine.fsm.onchangestate = lambda x: self._log_vessel_event(
            vessel,
            vessel_info,
            vessel_state_machine,
            velocity,
            f"{x.src} → {x.dst}")

        self.world.add_component(vessel, vessel_info)
        self.world.add_component(vessel, VesselPath())

        self.world.add_component(
            vessel,
            vessel_state_machine)
