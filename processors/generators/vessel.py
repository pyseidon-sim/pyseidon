import copy
import json
import random

from shapely.geometry import Polygon

from components import Course, FrameCounter, Position, Velocity, VesselPath
from components.fsm import (NULL_SPEED_MODEL, SpeedStateMachine,
                            VesselStateMachine)
from environment import RunInfo
from log.events.vessel import VesselEvent
from processors.base_processor import BaseProcessor
from utils.shapes import random_point_in_polygon
from utils.timer import SimulationTimer, TimerScheduler


class VesselGeneratorProcessor(BaseProcessor):
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
        vessel_logger=None,
        default_speed_knots=15,
        speed_model_probabilities=NULL_SPEED_MODEL,
        anomalous_vessels_percent=0,
    ):
        """
        :param world: Esper world object
        :param inter_arrival_time_sampler: a function that samples an inter-arrival time for vessels
        :param vessel_info_sampler: a function that samples vessel_info
        :param spawn_area_filename: the name of a geojson file that denotes a spawn area for vessels
        :param vessel_logger: VesselEventLogger singleton that is logging events about vessels
        :param default_speed_knots: The default velocity of a vessel in knots
        :param speed_model_probabilities: The Markov Model depicting state of vessels velocities
         (used for generating velocity anomalies)
        :param anomalous_vessels_percent: the percentage of all vessels having the anomalous velocity
        markov model attached
        """
        assert world is not None, "A world is required!"
        assert (
            inter_arrival_time_sampler is not None
        ), "An inter-arrival distribution is required!"
        assert vessel_info_sampler is not None, "A vessel info sampler is required!"
        assert (
            type(speed_model_probabilities) == dict
        ), "No probabilities for the speed model were provided!"

        self.world = world
        self.vessel_info_sampler = vessel_info_sampler
        self.inter_arrival_time_sampler = inter_arrival_time_sampler
        self._load_spawn_area(spawn_area_filename)
        self.vessel_logger = vessel_logger
        self.default_speed_knots = default_speed_knots
        self.speed_model_probabilities = speed_model_probabilities
        self.anomalous_vessels_percent = anomalous_vessels_percent

        self._create_vessel_generation_timer()

    def _load_spawn_area(self, spawn_area_filename):
        spawn_area_file = open(spawn_area_filename, "r")
        spawn_area_json = json.loads(spawn_area_file.read())
        spawn_area_file.close()

        self.spawn_area = Polygon(
            spawn_area_json["features"][0]["geometry"]["coordinates"]
        )

    def _process(self, dt):
        if self.generation_timer.completed():
            self._create_vessel_generation_timer()

    def _create_vessel_generation_timer(self):
        """Create a timer at the end of which a new vessel will be generated."""

        inter_arrival_time = self.inter_arrival_time_sampler()

        self.generation_timer = SimulationTimer(
            duration=inter_arrival_time, target_function=self.generate_vessel
        )
        TimerScheduler.get_instance().schedule(self.generation_timer)

    def generate_vessel(self):
        """Initialize the vessel and its components and add them to the world."""

        # FIXME: This should be dependent on the vessel type
        vessel_velocity = self.default_speed_knots

        vessel = self.world.create_entity()

        spawn_point = random_point_in_polygon(self.spawn_area)
        vessel_info = self.vessel_info_sampler()
        velocity = Velocity(velocity=vessel_velocity)

        self.world.add_component(vessel, Position(lonlat=spawn_point))
        self.world.add_component(vessel, FrameCounter())
        self.world.add_component(vessel, Course())
        self.world.add_component(vessel, velocity)
        self.world.add_component(vessel, vessel_info)
        self.world.add_component(vessel, VesselPath())

        if random.random() <= self.anomalous_vessels_percent:
            # Add a markov model for creating speed anomalies
            speed_fsm = SpeedStateMachine(
                double_p=self.speed_model_probabilities["double"],
                halve_p=self.speed_model_probabilities["half"],
                normal_p=self.speed_model_probabilities["reset"],
            )

            self.world.add_component(vessel, speed_fsm)

        vessel_state_machine = VesselStateMachine()
        vessel_state_machine.generate()
        vessel_state_machine.fsm.onchangestate = lambda x: self._log_vessel_event(
            vessel, vessel_info, vessel_state_machine, velocity, f"{x.src} → {x.dst}"
        )

        self.world.add_component(vessel, vessel_state_machine)

    def _log_vessel_event(self, ent, vessel_info, fsm, velocity, event_type):
        if self.vessel_logger is None:
            return

        event = VesselEvent(
            event_type,
            copy.deepcopy(vessel_info),
            copy.deepcopy(velocity),
            copy.deepcopy(fsm.pilot),
            copy.deepcopy(fsm.tugboats),
            fsm.destination_berth_id,
            fsm.destination_anchorage_id,
            RunInfo.get_instance().timestamp(),
        )

        self.vessel_logger.log_event(ent, vessel_info, event)
