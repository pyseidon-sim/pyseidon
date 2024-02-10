import copy
import json
import math
import os
import random
from collections import defaultdict

import geojson
import numpy as np
from shapely.geometry import Point

from environment.navigation.sections import SectionManager
from exceptions import NoPathException


class PathFinder:
    """Singleton class that handles path finding in the port."""

    __instance = None

    @staticmethod
    def get_instance():
        if PathFinder.__instance is None:
            PathFinder()

        return PathFinder.__instance

    def __init__(self):
        """Private constructor."""

        if PathFinder.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            PathFinder.__instance = self
            self.sections_manager = SectionManager.get_instance()

    def load_traces(
        self,
        ocean_berth_folder,
        ocean_tugs_folder=None,
        ocean_pilots_folder=None,
        pilots_rv_berth_traces_folder=None,
        tugs_rv_berth_traces_folder=None,
        pilots_rv_tugs_rv_traces_folder=None,
        tugs_wl_tugs_rv_traces_folder=None,
        pilots_wl_pilots_rv_traces_folder=None,
        pilots_wl_berth_traces_folder=None,
        ocean_tug_wl_traces_folder=None,
        ocean_spawn_ids: list = None,
    ):
        """Replaces the known traces with the ones loaded
        from all GeoJSON files in a given folder. Each
        file might contain multiple traces.
        """
        assert (
            ocean_spawn_ids is not None and len(ocean_spawn_ids) > 0
        ), "No ocean spawn IDs provided!"
        self.ocean_spawn_ids = ocean_spawn_ids

        if ocean_tugs_folder is not None:
            rendezvous_dict, rendezvous = self._extract_traces_from_file(
                ocean_tugs_folder
            )
            self.tugs_rv, self.ocean_tugs_rv_traces = list(rendezvous), rendezvous_dict

        if ocean_pilots_folder is not None:
            rendezvous_dict, rendezvous = self._extract_traces_from_file(
                ocean_pilots_folder
            )
            self.pilots_rv, self.ocean_pilots_rv_traces = (
                list(rendezvous),
                rendezvous_dict,
            )

        if pilots_rv_berth_traces_folder is not None:
            self.pilots_rv_berth_traces, _ = self._extract_traces_from_file(
                pilots_rv_berth_traces_folder
            )

        if tugs_rv_berth_traces_folder is not None:
            self.tugs_rv_berth_traces, _ = self._extract_traces_from_file(
                tugs_rv_berth_traces_folder
            )

        if pilots_rv_tugs_rv_traces_folder is not None:
            self.pilots_rv_tugs_rv_traces, _ = self._extract_traces_from_file(
                pilots_rv_tugs_rv_traces_folder
            )

        if tugs_wl_tugs_rv_traces_folder is not None:
            self.tugs_wl_tugs_rv_traces, _ = self._extract_traces_from_file(
                tugs_wl_tugs_rv_traces_folder
            )

        if pilots_wl_pilots_rv_traces_folder is not None:
            self.pilots_wl_pilot_rv_traces_dict, _ = self._extract_traces_from_file(
                pilots_wl_pilots_rv_traces_folder
            )

        if pilots_wl_berth_traces_folder is not None:
            self.pilots_wl_berth_traces_dict, _ = self._extract_traces_from_file(
                pilots_wl_berth_traces_folder
            )

        if ocean_tug_wl_traces_folder is not None:
            self.ocean_tug_wl_traces, _ = self._extract_traces_from_file(
                ocean_tug_wl_traces_folder
            )

        assert os.path.isdir(
            ocean_berth_folder
        ), f"Ocean -> Berth Traces folder {ocean_berth_folder} does not exist"
        assert (
            len(os.listdir(ocean_berth_folder)) > 0
        ), f"No traces data in {ocean_berth_folder}"

        traces_dict, berths = self._extract_traces_from_file(ocean_berth_folder)

        self.berths = list(berths)
        self.berth_traces = traces_dict

    def _get_trace_dict(self, path_json):
        x, y = [], []
        point_sections = []
        waypoints = path_json["geometry"]["coordinates"]

        for w in waypoints:
            x.append(w[0])
            y.append(w[1])

            point_sections.append(self.sections_manager.section_for_point(w))

        # Extract the unique sections that this path crosses
        crossed_sections = set(point_sections)
        # Remove the non-section entries (e.g. Ocean, open-sea)
        crossed_sections.discard(None)

        return {
            "x": x,
            "y": y,
            "point_sections": point_sections,
            "crossed_sections": crossed_sections,
        }

    def _extract_traces_from_file(self, traces_folder, origin_name="ocean"):
        assert os.path.isdir(traces_folder), f"{traces_folder} does not exist"
        assert len(os.listdir(traces_folder)) > 0, f"No traces data in {traces_folder}"

        traces_files = os.listdir(traces_folder)
        traces_dict = {}
        destinations = set()

        for file in traces_files:
            trace_data = self._get_geojson_data(f"{traces_folder}/{file}")

            for feature in trace_data["features"]:
                origin = feature["properties"]["origin"]
                destination = feature["properties"]["destination"]

                if origin_name in origin:
                    destinations.add(destination)

                trace_id = f"{origin}-{destination}"
                trace_dict = self._get_trace_dict(feature)

                if trace_id in traces_dict:
                    # Append to the list of the ocean-berth:id traces if other
                    # traces for that route exist
                    traces_dict[f"{origin}-{destination}"].append(trace_dict)
                else:
                    traces_dict[f"{origin}-{destination}"] = [trace_dict]

        return traces_dict, destinations

    def load_tugs_rendezvous_locations(self, path):
        tugs_rendezvous_mapping = {}
        tugs_rendezvous_locations = {}

        # Define final section mapping to the rendezvous locations
        for feature in self._get_geojson_data(path)["features"]:
            point = feature["geometry"]["coordinates"]
            # vessel_final_destination is the final section destination of the vessel
            # depending on this final section a certain rendezvous point is assigned
            for final_destination in feature["properties"]["vessel_final_destination"]:
                tugs_rendezvous_mapping[str(final_destination)] = [
                    point,
                    feature["properties"]["id"],
                ]

            tugs_rendezvous_locations[feature["properties"]["id"]] = point

        self.tugs_rendezvous_mapping = tugs_rendezvous_mapping
        self.tugs_rendezvous_locations = tugs_rendezvous_locations

    def load_pilots_rendezvous_locations(self, path, vessel_class_map):
        pilots_arrival_rendezvous_mapping = defaultdict(list)
        pilots_departure_rendezvous_mapping = defaultdict(list)

        try:
            for feature in self._get_geojson_data(path)["features"]:
                properties = feature["properties"]
                rendezvous_id = properties["id"]

                # Import the vessel class <--> rendezvous mapping
                if properties["usage"] == "arrival":
                    for vessel_class in properties["vessel_class"]:
                        pilots_arrival_rendezvous_mapping[
                            vessel_class_map(vessel_class)
                        ].append(rendezvous_id)
                else:
                    for vessel_class in properties["vessel_class"]:
                        pilots_departure_rendezvous_mapping[
                            vessel_class_map(vessel_class)
                        ].append(rendezvous_id)
        except Exception as e:
            raise Exception(f"File {path} has invalid data: {e}")

        self.pilots_arrival_rendezvous_mapping = pilots_arrival_rendezvous_mapping
        self.pilots_departure_rendezvous_mapping = pilots_departure_rendezvous_mapping

    def ocean_connected_berth_ids(self):
        """Returns the ids of berths for which at least one ocean -> berth path is available"""
        self._ensure_data_available()
        return [int(berth.split(":")[1]) for berth in self.berths]

    def ocean_tug_rendezvous_paths(self, vessel_position=None, final_section=None):
        """Computes a path from the ocean to a tug rendezvous.

        If the vessel position is specified the position will
        be connected to the first node of the path.
        """
        assert (
            final_section is not None
        ), "The final section of vessel path is required!"

        rendezvous_info = self.tugs_rendezvous_mapping[str(final_section)]
        rendezvous_id = rendezvous_info[1]

        ocean_id = random.choice(self.ocean_spawn_ids)

        trace_ids = self._ocean_tug_rendezvous_trace_ids(ocean_id, rendezvous_id)
        paths = []

        for trace_id in trace_ids:
            if trace_id in self.ocean_tugs_rv_traces:
                paths.extend(self.ocean_tugs_rv_traces[trace_id])

        if len(paths) == 0:
            raise NoPathException(f"There does not exist a {trace_id} trace")

        # Create a copy of the original path
        paths = [copy.deepcopy(p) for p in paths]

        # Add the vessel position as the origin. This creates an additional
        # straight line between the vessel position and the path origin
        if vessel_position is not None:
            for path in paths:
                self.prefix_path(vessel_position, path)

        return paths, rendezvous_id

    def ocean_pilot_rendezvous_paths(self, vessel_position=None, vessel_class=None):
        """Computes a path from the ocean to a pilot rendezvous.

        If the vessel position is specified the position will
        be connected to the first node of the path.
        """
        assert vessel_class is not None, "The vessel class is required!"

        ocean_id = random.choice(self.ocean_spawn_ids)

        rendezvous_id = random.choice(
            self.pilots_arrival_rendezvous_mapping[vessel_class]
        )

        trace_ids = self._ocean_pilot_rendezvous_trace_ids(ocean_id, rendezvous_id)
        paths = []

        for trace_id in trace_ids:
            if trace_id in self.ocean_pilots_rv_traces:
                paths.extend(self.ocean_pilots_rv_traces[trace_id])

        if len(paths) == 0:
            raise NoPathException(f"There does not exist a {trace_id} trace")

        # Create a copy of the original path
        paths = [copy.deepcopy(p) for p in paths]

        # Add the vessel position as the origin. This creates an additional
        # straight line between the vessel position and the path origin
        if vessel_position is not None:
            for path in paths:
                self.prefix_path(vessel_position, path)

        return paths, rendezvous_id

    def tug_rendezvous_berth_paths(
        self, vessel_position=None, final_section=None, berth_id=None
    ):
        """Computes a path from the tug rendezvous to berth.

        If the vessel position is specified the position
        will be connected to the first node of the path.
        """
        assert (
            final_section is not None
        ), "The final section of vessel path is required!"
        assert berth_id is not None, "A berth_id is required!"

        rendezvous_info = self.tugs_rendezvous_mapping[str(final_section)]
        rendezvous_id = rendezvous_info[1]

        trace_ids = self._tug_rendezvous_berth_trace_ids(rendezvous_id, berth_id)
        paths = []

        for trace_id in trace_ids:
            if trace_id in self.tugs_rv_berth_traces:
                paths.extend(self.tugs_rv_berth_traces[trace_id])

        if len(paths) == 0:
            raise NoPathException(
                f"There does not exist a tug rendezvous {rendezvous_id} -> berth {berth_id} trace"
            )

        # Create a copy of the original paths
        paths = [copy.deepcopy(p) for p in paths]

        # Add the vessel position as the origin. This creates an additional
        # straight line between the vessel position and the path origin
        if vessel_position is not None:
            for path in paths:
                self.prefix_path(vessel_position, path)

        return paths, rendezvous_id

    def tug_rendezvous_id_for_berth(self, berth_info):
        if self.tugs_rendezvous_mapping[str(berth_info.section)] is not None:
            return self.tugs_rendezvous_mapping[str(berth_info.section)][1]

        return None

    def pilot_rendezvous_berth_paths(
        self, vessel_position=None, vessel_class=None, berth_id=None
    ):
        """Computes a path from the pilot rendezvous to berth.

        If the vessel position is specified the position will
        be connected to the first node of the path.
        """
        assert vessel_class is not None, "The vessel class is required!"
        assert berth_id is not None, "A berth_id is required!"

        rendezvous_id = random.choice(
            self.pilots_arrival_rendezvous_mapping[vessel_class]
        )

        trace_ids = self._pilot_rendezvous_berth_trace_ids(rendezvous_id, berth_id)
        paths = []

        for trace_id in trace_ids:
            if trace_id in self.pilots_rv_berth_traces:
                paths.extend(self.pilots_rv_berth_traces[trace_id])

        if len(paths) == 0:
            raise NoPathException(
                f"There does not exist a pilot rendezvous -> {berth_id} trace"
            )

        # Create a copy of the original paths
        paths = [copy.deepcopy(p) for p in paths]

        # Add the vessel position as the origin. This creates an additional
        # straight line between the vessel position and the path origin
        if vessel_position is not None:
            for path in paths:
                self.prefix_path(vessel_position, path)

        return paths

    def ocean_berth_paths(self, vessel_position=None, berth_id=None):
        """Computes a path from the ocean to a berth.

        If the vessel position is specified the position
        will be connected to the first node of the path.
        """
        assert berth_id is not None, "A berth id is required!"

        trace_ids = []

        # FIXME: fix this as now it sort of means that vessels coming
        #        from specific places go to specific berths
        for ocean_id in self.ocean_spawn_ids:
            trace_id = self._ocean_id_berth_trace_ids(ocean_id, berth_id)
            trace_ids.extend(trace_id)

        paths = []

        for trace_id in trace_ids:
            if trace_id in self.berth_traces:
                paths = self.berth_traces[trace_id]

                # FIXME: Unclear (this checks if it's a berth -> ocean path)
                if trace_id == trace_ids[1]:
                    reversed_paths = []

                    for p in paths:
                        reversed_paths.append(self.reverse_path(p))

                    paths = reversed_paths

                break

        if len(paths) == 0:
            raise ValueError(f"There does not exist a {trace_id} trace")

        # Create a copy of the original path
        paths = [copy.deepcopy(p) for p in paths]

        # Add the vessel position as the origin. This creates an additional
        # straight line between the vessel position and the path origin
        if vessel_position is not None:
            for path in paths:
                self.prefix_path(vessel_position, path)

        return paths

    def pilot_rendezvous_tug_rendezvous_paths(self, pilot_rv_id, tug_rv_id):
        """Computes a path from the ocean to a tug rendezvous.

        If the vessel position is specified the position will
        be connected to the first node of the path.
        """
        assert pilot_rv_id is not None, "Pilot rendezvous id is required!"
        assert tug_rv_id is not None, "Tug rendezvous id is required!"

        trace_ids = self._pilot_rendezvous_tug_rendezvous_trace_ids(
            pilot_rv_id, tug_rv_id
        )
        paths = []

        for trace_id in trace_ids:
            if trace_id in self.pilots_rv_tugs_rv_traces:
                paths.extend(self.pilots_rv_tugs_rv_traces[trace_id])

        if len(paths) == 0:
            raise NoPathException(f"There does not exist a {trace_id} trace")

        # Create a copy of the original path
        paths = [copy.deepcopy(p) for p in paths]

        return paths

    def prefix_path(self, point: list, path):
        """Prefix a given path with a point"""
        path["x"] = [point[0]] + path["x"]
        path["y"] = [point[1]] + path["y"]

        path["point_sections"] = [self.sections_manager.ocean_section] + path[
            "point_sections"
        ]

    def anchorage_path(self, vessel_position: list, anchorage_center: Point):
        # FIXME: this generates a straight mock path
        return {
            "x": [vessel_position[0], anchorage_center.x],
            "y": [vessel_position[1], anchorage_center.y],
            # FIXME: The second section should be anchorage x?
            "point_sections": [self.sections_manager.ocean_section] * 2,
        }

    def tugs_ocean_waiting_location_path(self, tug_position: list, waiting_location_id):
        trace = random.choice(
            self.ocean_tug_wl_traces[
                f"ocean-tug_waiting_location:{waiting_location_id}"
            ]
        )
        trace = copy.deepcopy(trace)

        if tug_position is not None:
            self.prefix_path(tug_position, trace)

        return trace

    def tugs_current_location_waiting_location_path(
        self, tug_position: list, waiting_location_id
    ):
        paths = []

        for ocean_id in self.ocean_spawn_ids:
            trace_id = f"ocean:{ocean_id}-tug_waiting_location:{waiting_location_id}"
            if trace_id in self.ocean_tug_wl_traces:
                paths.extend(self.ocean_tug_wl_traces[trace_id])

        try:
            trace = random.choice(paths)
        except KeyError:
            raise NoPathException(
                f"There does not exist an ocean -> tug waiting location {waiting_location_id} trace"
            )

        trace = copy.deepcopy(trace)

        trace = self.trim_trace_to_current_position(tug_position, trace)

        self.prefix_path(tug_position, trace)

        return trace

    def tugs_waiting_location_rendezvous_path(
        self, tug_position: list, waiting_location_id, rendezvous_id
    ):
        try:
            trace = random.choice(
                self.tugs_wl_tugs_rv_traces[
                    f"tug_waiting_location:{waiting_location_id}-tug_rendezvous:{rendezvous_id}"
                ]
            )
        except KeyError:
            raise NoPathException(
                f"There does not exist a waiting location {waiting_location_id} -> rendezvous {rendezvous_id} trace"
            )

        trace = copy.deepcopy(trace)

        if tug_position is not None:
            self.prefix_path(tug_position, trace)

        return trace

    def tugs_berth_waiting_location_path(
        self, tug_position: list, berth_info, waiting_location_id
    ):
        rendezvous_id = self.tug_rendezvous_id_for_berth(berth_info)

        rendezvous_wl_path = self.reverse_path(
            self.tugs_waiting_location_rendezvous_path(
                None, waiting_location_id, rendezvous_id
            )
        )

        berth_rendezvous_paths, _ = self.tug_rendezvous_berth_paths(
            final_section=berth_info.section, berth_id=berth_info.id
        )
        berth_rendezvous_path = random.choice(berth_rendezvous_paths)
        berth_rendezvous_path = self.reverse_path(berth_rendezvous_path)

        return self.merge_paths(berth_rendezvous_path, rendezvous_wl_path)

    def pilot_rendezvous_pilot_waiting_location_path(
        self, pilot_position: list, rendezvous_id, waiting_location_id
    ):
        trace = random.choice(
            self.pilots_wl_pilot_rv_traces_dict[
                f"pilot_waiting_location:{waiting_location_id}-pilot_rendezvous:{rendezvous_id}"
            ]
        )
        trace = copy.deepcopy(trace)

        trace = self.reverse_path(trace)

        if pilot_position is not None:
            self.prefix_path(pilot_position, trace)

        return trace

    def pilot_waiting_location_pilot_rendezvous_path(
        self, pilot_position: list, rendezvous_id, waiting_location_id
    ):
        trace = random.choice(
            self.pilots_wl_pilot_rv_traces_dict[
                f"pilot_waiting_location:{waiting_location_id}-pilot_rendezvous:{rendezvous_id}"
            ]
        )
        trace = copy.deepcopy(trace)

        if pilot_position is not None:
            self.prefix_path(pilot_position, trace)

        return trace

    def pilot_waiting_location_berth_path(
        self, pilot_position: list, berth_id, waiting_location_id
    ):
        trace = random.choice(
            self.pilots_wl_berth_traces_dict[
                f"pilot_waiting_location:{waiting_location_id}-berth:{berth_id}"
            ]
        )
        trace = copy.deepcopy(trace)

        if pilot_position is not None:
            self.prefix_path(pilot_position, trace)

        return trace

    def berth_pilot_waiting_location_path(
        self, pilot_position: list, berth_id, waiting_location_id
    ):
        trace = random.choice(
            self.pilots_wl_berth_traces_dict[
                f"pilot_waiting_location:{waiting_location_id}-berth:{berth_id}"
            ]
        )
        trace = copy.deepcopy(trace)

        trace = self.reverse_path(trace)

        if pilot_position is not None:
            self.prefix_path(pilot_position, trace)

        return trace

    def merge_paths(self, a, b):
        return {
            "x": a["x"] + b["x"],
            "y": a["y"] + b["y"],
            "point_sections": a["point_sections"] + b["point_sections"],
        }

    def reverse_path(self, path):
        temp_path = copy.deepcopy(path)

        temp_path["x"] = list(reversed(temp_path["x"]))
        temp_path["y"] = list(reversed(temp_path["y"]))
        temp_path["point_sections"] = list(reversed(temp_path["point_sections"]))

        return temp_path

    def _ocean_berth_trace_ids(self, berth_id):
        return [f"ocean-berth:{berth_id}", f"berth:{berth_id}-ocean"]

    def _ocean_id_berth_trace_ids(self, ocean_id, berth_id):
        return [
            f"ocean:{ocean_id}-berth:{berth_id}",
            f"berth:{berth_id}-ocean:{ocean_id}",
        ]

    def _ocean_tug_rendezvous_trace_ids(self, ocean_id, rendezvous_id):
        return [f"ocean:{ocean_id}-tug_rendezvous:{rendezvous_id}"]

    def _ocean_pilot_rendezvous_trace_ids(self, ocean_id, rendezvous_id):
        return [f"ocean:{ocean_id}-pilot_rendezvous:{rendezvous_id}"]

    def _pilot_rendezvous_tug_rendezvous_trace_ids(self, pilot_rv_id, tug_rv_id):
        return [f"pilot_rendezvous:{pilot_rv_id}-tug_rendezvous:{tug_rv_id}"]

    def _pilot_rendezvous_berth_trace_ids(self, pilot_rv_id, berth_id):
        return [f"pilot_rendezvous:{pilot_rv_id}-berth:{berth_id}"]

    def _tug_rendezvous_berth_trace_ids(self, rendezvous_id, berth_id):
        return [f"tug_rendezvous:{rendezvous_id}-berth:{berth_id}"]

    def _get_geojson_data(self, path):
        geo_file = open(path, "r")
        trace_data = None

        try:
            trace_data = geojson.loads(geo_file.read())
        except Exception as e:
            raise Exception(f"File {path} has invalid data: {e}")

        geo_file.close()

        return trace_data

    def _ensure_data_available(self):
        if self.berths is None or self.berth_traces is None:
            raise Exception("No traces data was loaded!")

    def clear(self):
        """Removes all traces and berths data"""
        self.berths = None
        self.berth_traces = None

        self.tugs_rv = None
        self.ocean_tugs_rv_traces = None

        self.pilots_rv = None
        self.ocean_pilots_rv_traces = None

        self.pilots_rv_berth_traces = None
        self.tugs_rv_berth_traces = None
        self.pilots_rv_tugs_rv_traces = None
        self.tugs_wl_tugs_rv_traces = None
        self.pilots_wl_pilot_rv_traces_dict = None
        self.pilots_wl_berth_traces_dict = None
        self.ocean_tug_wl_traces = None

        self.ocean_spawn_ids = None

    def trim_trace_to_current_position(self, vessel_position, trace):
        distances = []

        xs = trace["x"]
        ys = trace["y"]

        # Compute euclidean distance to each point
        for x, y in zip(xs, ys):
            distance = math.sqrt(
                math.pow(vessel_position[0] - x, 2)
                + math.pow(vessel_position[1] - y, 2)
            )
            distances.append(distance)

        # Return min distance id
        idx = np.where(distances == np.amin(distances))[0][0]

        trace["x"] = trace["x"][idx:]
        trace["y"] = trace["y"][idx:]
        trace["point_sections"] = trace["point_sections"][idx:]

        return trace

    def path_to_geojson(self, path, output_filename):
        out_coords = []

        for x, y in zip(path["x"], path["y"]):
            out_coords.append([x, y])

        with open(output_filename, "w") as out_file:
            output_json = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "LineString", "coordinates": out_coords},
                        "properties": {},
                    }
                ],
            }

            out_file.write(json.dumps(output_json))
