import copy
import json
import random

from shapely.geometry import Polygon

from components import (Course, FrameCounter, LocationInfo, LocationType,
                        Position, Shape, TugInfo, Velocity, VesselPath)
from components.fsm import TugStateMachine
from environment import RunInfo
from log.events.tug import TugEvent
from log.tug import TugEventLogger
from utils import shapes


class TugsInitializer:
    DEFAULT_TUG_SPEED = 10.0

    def __init__(
        self,
        world,
        tugboats_locations_filename,
        tugs_count=20,
        companies_from_data=False,
    ):
        """Initializes a tug initializer.

        The `companies_from_data` flag specifies whether the tugs (from tugs_count) should
        be allocated randomly between the waiting locations or the tugs count and allocations
        (along with tug company member vessel) should be retrieved from the data (in the latter
        case, tugs_count is ignored and the number of tugs is retrieved from the GeoJSON file)
        """
        self.world = world
        self.tugs_count = tugs_count
        self.tugboats_locations_filename = tugboats_locations_filename
        self.tug_company_names = None
        self.companies_from_data = companies_from_data

    def get_tugboat_companies(self):
        return self.tug_company_names

    def create_tugboats(self):
        """Initializes the tugboats randomly in the locations specified by the input filename.

        The file must be in GeoJSON format and contain a list of polygons
        that define the tugs storage locations
        """
        with open(self.tugboats_locations_filename) as geo_file:
            geo_data = json.loads(geo_file.read())

            if self.companies_from_data:
                self._create_tugs_geojson(geo_data)
            else:
                self._create_tugs_random_allocation(geo_data)

    def _create_tugs_geojson(self, geo_data):
        """For each waiting location in the GeoJSON file
        this method retrieves the tug company names and
        the number of tugs per company and adds the to the
        simulation.
        """
        tug_company_names = set()

        for feature in geo_data["features"]:
            location_id = self._create_waiting_location(feature)

            companies = feature["properties"]["companies"]
            tug_per_company = feature["properties"]["tugs_per_company"]

            for i in range(len(companies)):
                tug_company_names.add(companies[i])

                for _ in range(int(tug_per_company[i])):
                    self._create_tugboat(
                        Polygon(feature["geometry"]["coordinates"][0]),
                        companies[i],
                        location_id,
                    )

        self.tug_company_names = list(tug_company_names)

    def _create_tugs_random_allocation(self, geo_data):
        """Create tugboats by allocating them to a single default company."""

        locations_count = len(geo_data["features"])
        tugs_allocation = [0] * locations_count
        self.tug_company_names = ["Company 1"]

        for i in range(self.tugs_count):
            tugs_allocation[random.choice(range(locations_count))] += 1

        for idx, location_data in enumerate(geo_data["features"]):
            location_id = self._create_waiting_location(location_data)

            for _ in range(tugs_allocation[idx]):
                self._create_tugboat(
                    Polygon(location_data["geometry"]["coordinates"][0]),
                    random.choice(self.tug_company_names),
                    location_id,
                )

    def _create_tugboat(self, polygon, company_name, waiting_location_id):
        """Creates a tugboat entity with the required components and adds it to the world."""
        tug = self.world.create_entity()

        self.world.add_component(tug, Position(shapes.random_point_in_polygon(polygon)))

        tug_info = TugInfo(company_name=company_name)
        tug_velocity = Velocity(self.DEFAULT_TUG_SPEED)
        self.world.add_component(tug, tug_velocity)
        self.world.add_component(tug, VesselPath())
        self.world.add_component(tug, FrameCounter())
        self.world.add_component(tug, Course())
        self.world.add_component(tug, tug_info)
        self.world.add_component(
            tug,
            TugStateMachine(
                waiting_location_id=waiting_location_id,
                on_state_change=lambda ev: self._tug_fsm_transition_callback(
                    tug, tug_info, tug_velocity, ev
                ),
            ),
        )

    def _create_waiting_location(self, feature):
        """Creates a tugboat waiting location entity with the required components and adds it to the world."""

        location = self.world.create_entity()

        location_info = LocationInfo(
            id=feature["properties"]["id"],
            name=feature["properties"]["name"],
            location_type=LocationType.TUGBOATS_STORAGE,
        )

        self.world.add_component(
            location, Shape(shape_points=feature["geometry"]["coordinates"][0])
        )
        self.world.add_component(location, location_info)

        return location_info.id

    def _tug_fsm_transition_callback(self, ent, tug_info, vel, event):
        cloned_tug_info = copy.deepcopy(tug_info)

        event = TugEvent(
            f"{event.src} → {event.dst}",
            cloned_tug_info,
            copy.deepcopy(vel),
            RunInfo.get_instance().timestamp(),
        )

        tug_logger = TugEventLogger.get_instance()
        tug_logger.log_event(ent, cloned_tug_info, event)
