import copy
import json
import random

from shapely.geometry import Polygon

from components import (Course, LocationInfo, LocationType, PilotInfo,
                        Position, Shape, Velocity, VesselPath)
from components.fsm import PilotStateMachine
from environment import RunInfo
from log.events.pilot import PilotEvent
from log.pilot import PilotEventLogger
from utils import shapes


class PilotsInitializer:
    """Generates pilot world entities from a csv file input."""

    DEFAULT_PILOT_SPEED = 10.0

    def __init__(self, world, pilots_locations_filename, num=20):
        self.world = world
        self.pilots_locations_filename = pilots_locations_filename
        self.pilot_num = num

    def create_pilots(self):
        """Initializes the pilots randomly in the locations
        specified by the input filename. The file must be
        in GeoJSON format and contain a list of polygons
        that define the pilots waiting locations.
        """
        with open(self.pilots_locations_filename) as geo_file:
            geo_data = json.loads(geo_file.read())

            self._create_pilots_geojson(geo_data)

    def _create_pilots_geojson(self, geo_data):
        """For each waiting location in the GeoJSON file
        this method retrieves the pilot company names and
        the number of pilots per company and adds the to the
        simulation.
        """
        pilot_company_names = set()

        for feature in geo_data["features"]:
            location_id = self._create_waiting_location(feature)

            companies = feature["properties"]["companies"]
            pilots_per_company = feature["properties"]["pilots_per_company"]

            for i in range(len(companies)):
                pilot_company_names.add(companies[i])

                for _ in range(int(pilots_per_company[i])):
                    self._create_pilot(
                        Polygon(feature["geometry"]["coordinates"][0]),
                        companies[i],
                        location_id,
                    )

        self.pilot_company_names = list(pilot_company_names)

    def _create_pilots_random_allocation(self, geo_data):
        """Assigning one company to all pilot entities and randomly allocating them."""

        locations_count = len(geo_data["features"])
        pilots_allocation = [0] * locations_count
        self.pilot_company_names = ["Company 1"]

        for _ in range(self.pilot_num):
            pilots_allocation[random.choice(range(locations_count))] += 1

        for idx, location_data in enumerate(geo_data["features"]):
            location_id = self._create_waiting_location(location_data)

            for _ in range(pilots_allocation[idx]):
                self._create_pilot(
                    Polygon(location_data["geometry"]["coordinates"][0]),
                    random.choice(self.pilot_company_names),
                    location_id,
                )

    def _pilot_fsm_transition_callback(self, ent, pilot_info, vel, event):
        pilot_info_clone = copy.deepcopy(pilot_info)

        event = PilotEvent(
            f"{event.src} → {event.dst}",
            pilot_info_clone,
            copy.deepcopy(vel),
            RunInfo.get_instance().timestamp(),
        )

        pilot_logger = PilotEventLogger.get_instance()
        pilot_logger.log_event(ent, pilot_info_clone, event)

    def _create_pilot(self, polygon, company_name, waiting_location_id):
        """Creates a pilot entity with the required components and adds it to the esper world."""
        pilot = self.world.create_entity()

        pilot_velocity = Velocity(self.DEFAULT_PILOT_SPEED)
        pilot_info = PilotInfo(company_name=company_name)
        pilot_fsm = PilotStateMachine(
            waiting_location_id=waiting_location_id,
            on_state_change=lambda ev: self._pilot_fsm_transition_callback(
                pilot, pilot_info, pilot_velocity, ev
            ),
        )

        self.world.add_component(
            pilot, Position(shapes.random_point_in_polygon(polygon))
        )

        self.world.add_component(pilot, pilot_velocity)
        self.world.add_component(pilot, VesselPath())
        self.world.add_component(pilot, Course())
        self.world.add_component(pilot, pilot_info)
        self.world.add_component(pilot, pilot_fsm)

    def _create_waiting_location(self, feature):
        """Creates a pilot waiting location entity with the required components and adds it to the world."""

        location = self.world.create_entity()

        location_info = LocationInfo(
            id=feature["properties"]["id"],
            name=feature["properties"]["name"],
            location_type=LocationType.PILOTS_STORAGE,
        )

        self.world.add_component(
            location, Shape(shape_points=feature["geometry"]["coordinates"][0])
        )
        self.world.add_component(location, location_info)

        return location_info.id
