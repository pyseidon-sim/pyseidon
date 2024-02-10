"""
    The entry point of the example simulation.
    This file initializes all relevant components, connects them together, and then starts the simulation.
"""

import argparse
import csv
import json
import os
import pickle
import random
import signal
import sys
import time
from enum import Enum

import esper
import geoplotlib
import numpy as np
from shapely.geometry import Polygon

from anomalies import TugMalfunctionAnomaly
from components.fsm import NULL_SPEED_MODEL
from environment import RunInfo
from environment.initializers import (AnchoragesInitializer, BerthsInitializer,
                                      PilotsInitializer, TugsInitializer)
from environment.messaging import MessageBroker
from environment.navigation import PathFinder
from environment.navigation.sections import SectionManager
from example.example_model.anchorages import assign_anchorage
from example.example_model.berth_designator import berths_allocation_designator
from example.example_model.berth_service_distribution_factory import \
    BerthServiceDistributionFactory
from example.example_model.tugboat_company_logic import \
    DefaultTugCompanyStrategy
from example.example_model.vessel_class import VesselClass
from example.example_model.vessel_content_type import VesselContentType
from example.example_model.vessel_distribution_factory import \
    VesselDistributionFactory
from example.example_model.vessel_type import VesselType
from layers import SimulationLayer
from log.pilot import PilotEventLogger
from log.tug import TugEventLogger
from log.vessel import VesselEventLogger
from processors.ais import (AISPilotLogProcessor, AISTugLogProcessor,
                            AISVesselLogProcessor, SectionsLogProcessor)
from processors.core import TimerProcessor
from processors.generators import (FixedVesselGeneratorProcessor,
                                   VesselGeneratorProcessor)
from processors.harbourmaster import HarbourMasterProcessor
from processors.harbourmaster.strategies import (DefaultTugStrategy,
                                                 DefaultVesselStrategy)
from processors.pilot import (PilotGoalFormulatorProcessor,
                              PilotMovementProcessor)
from processors.rendering import (AnchorageRenderer, BerthRenderer,
                                  OperationsRenderer, PilotsRenderer,
                                  RendezvousRenderer, TugsRenderer,
                                  VesselRenderer)
from processors.tug import TugGoalFormulatorProcessor, TugMovementProcessor
from processors.vessel import (VesselGoalFormulatorProcessor,
                               VesselMovementProcessor)
from utils.timer import TimerScheduler


def init_parser():
    parser = argparse.ArgumentParser(description="PySeidon - a Maritime Port Simulator")

    parser.add_argument("--out", required=True, help="Output directory", type=str)
    parser.add_argument("--step", default=10, help="Step size (seconds)", type=int)
    parser.add_argument(
        "--max-time", default=None, help="Maximum simulation time", type=int
    )
    parser.add_argument(
        "--verbose", default="y", help="Verbose output? [y/n]", type=str
    )
    parser.add_argument(
        "--graphics",
        default="y",
        help="Display the simulation on-screen? [y/n]",
        type=str,
    )
    parser.add_argument(
        "--cache", default="n", help="Use the traces cache? [y/n]", type=str
    )

    parser.add_argument(
        "--tugs-allocation-data",
        default="n",
        help="Allocate tugs from data or randomly? [y/n]",
        type=str,
    )
    parser.add_argument(
        "--single-tugs-company",
        default="y",
        help="Use a single tugboat company? [y/n]",
        type=str,
    )

    parser.add_argument(
        "--fixed-generation",
        default="n",
        help="Generate all arrivals at the beginning of the simulation or on the fly? [y/n]",
        type=str,
    )

    # Anomalies
    parser.add_argument(
        "--berth-check-prob",
        default=0,
        help="The probability of a berth inspection upon arrival of a vessel (0 <= x <= 1)",
        type=float,
    )
    parser.add_argument(
        "--anomalous-speed",
        default="n",
        help="Whether to add speed anomalies [y/n]",
        type=str,
    )
    parser.add_argument(
        "--tugs-malfunction",
        default="n",
        help="Introduce the tugs breaking down anomaly? [y/n]",
        type=str,
    )
    parser.add_argument(
        "--tugs-break-percentage-idle",
        default=0.00001,
        help="Probability of an idle tug malfunctioning at every iteration.",
        type=float,
    )
    parser.add_argument(
        "--tugs-break-percentage-busy",
        default=0.0002,
        help="Probability of a busy tug malfunctioning at every iteration.",
        type=float,
    )

    parser.add_argument(
        "--seed", default=None, help="Seed for random generators.", type=int
    )

    return parser


def parse_arguments():
    parser = init_parser()

    args = parser.parse_args()

    args.graphics = args.graphics.lower() == "y"
    args.verbose = args.verbose.lower() == "y"
    args.cache = args.cache.lower() == "y"

    args.tugs_allocation_data = args.tugs_allocation_data.lower() == "y"
    args.single_tugs_company = args.single_tugs_company.lower() == "y"

    args.fixed_generation = args.fixed_generation.lower() == "y"

    args.anomalous_speed = args.anomalous_speed.lower() == "y"
    args.tugs_malfunction = args.tugs_malfunction.lower() == "y"

    if args.fixed_generation and args.max_time is None:
        print(
            "For generating vessels at the start of the simulation a max_time is required!"
        )
        sys.exit(-1)

    if args.seed is not None:
        print(f"Using random seed {args.seed}")
        # sets random seed for random and numpy
        random.seed(args.seed)
        np.random.seed(args.seed)

    # Controls the execution state of the simulation when no graphics are used
    os.environ[SIMULATION_STATE_KEY] = SimulationState.RUNNING.value

    # Create the output directory if it does not exist
    if not os.path.exists(args.out):
        os.makedirs(args.out)

    return args


def save_log_to_file(filename, logs):
    with open(filename, "w") as ais_out_file:
        out_lines = logs.header() + logs.logs
        csv_writer = csv.writer(ais_out_file)

        for row in out_lines:
            csv_writer.writerow(row)


# Set-up an handler to log the simulation
# statistics on exit
def on_exit(sig, frame):
    """Set-up an handler to log the simulation statistics on exit."""
    os.environ[SIMULATION_STATE_KEY] = SimulationState.STOPPED.value

    print("-------------------      Vessel Logs     ------------------- ")
    print(vessel_event_logger.log_to_string(colored=True))

    print("Writing log files...")

    vessel_event_logger.log_to_csv(f"{args.out}/vessel_events.csv")
    print("Written the vessel events log to file")

    if pilots_event_logger is not None:
        pilots_event_logger.log_to_csv(f"{args.out}/pilot_events.csv")
        print("Written the pilot events log to file")

    if tug_event_logger is not None:
        tug_event_logger.log_to_csv(f"{args.out}/tug_events.csv")
        print("Written the tug events log to file")

    if vessel_logger_pos is not None:
        save_log_to_file(f"{args.out}/vessel_pos.csv", vessel_logger_pos.logger)
        print("Written the vessel positions log to file")

    if pilot_logger_pos is not None:
        save_log_to_file(f"{args.out}/pilot_pos.csv", pilot_logger_pos.logger)
        print("Written the pilot positions log to file")

    if tug_logger_pos is not None:
        save_log_to_file(f"{args.out}/tug_pos.csv", tug_logger_pos.logger)
        print("Written the tug positions log to file")

    if sections_logger is not None:
        save_log_to_file(f"{args.out}/sections.csv", sections_logger.logger)
        print("Written sections occupancy log to file")

    sys.exit(0)


class SimulationState(Enum):
    RUNNING = "running"
    STOPPED = "stopped"


world = esper.World()

ocean_berth_traces_folder = "example_data/traces/ocean_berth"
ocean_tugs_rv_traces_folder = "example_data/traces/ocean_tugs_rv"
ocean_pilots_rv_traces_folder = "example_data/traces/ocean_pilots_rv"
pilots_rv_berth_traces_folder = "example_data/traces/pilots_rv_berth"
pilots_rv_tugs_rv_traces_folder = "example_data/traces/pilots_rv_tugs_rv"
tugs_rv_berth_traces_folder = "example_data/traces/tugs_rv_berth"
tugs_wl_tugs_rv_traces_folder = "example_data/traces/tugs_wl_tugs_rv"
pilots_wl_pilot_rv_traces_folder = "example_data/traces/pilots_wl_pilots_rv"
pilots_wl_berth_traces_folder = "example_data/traces/pilots_wl_berth"
ocean_tug_wl_traces_folder = "example_data/traces/ocean_tugs_wl"

berths_filename = "example_data/berths.csv"
terminal_service_times_filename = "example_data/terminal-service-times.csv"
anchorages_filename = "example_data/anchorages.geojson"
spawn_area_filename = "example_data/spawn.geojson"
sections_filename = "example_data/sections.geojson"

tugs_waiting_locations_filename = "example_data/tugs/waiting_locations.geojson"
pilots_waiting_location_filename = "example_data/pilots/waiting_locations.geojson"
tugs_rendezvous_filename = "example_data/tugs/rendezvous_locations.geojson"
pilots_rendezvous_filename = "example_data/pilots/rendezvous_locations.geojson"
tugs_deattach_location_filename = "example_data/tugs/deattach_location.geojson"

SIMULATION_STATE_KEY = "SIMULATION_STATE"

args = parse_arguments()

# Initialize the message broker
MessageBroker.get_instance()

# Initialize the timer scheduler
timer_creator = TimerScheduler.get_instance()
timer_creator.world = world

# Initialize the simulation clock
world_run_info = RunInfo.get_instance()
world_run_info.set_simulation_start_time(time.time())
world_run_info.set_simulation_end_time(args.max_time)
world_run_info.set_simulation_step_size(args.step)

# Add Sections to the simulation
sections_manager = SectionManager.get_instance()
sections_manager.create_sections(sections_filename, VesselClass)

# Initialize the path finder. If a pickled version
# of the path finder exists it will be loaded to save
# time during startup
if os.path.isfile("example/path_finder.pickle") and args.cache:
    print("Using precomputed path finder")
    path_finder = pickle.load(open("example/path_finder.pickle", "rb"))
else:
    path_finder = PathFinder.get_instance()
    path_finder.load_traces(
        ocean_berth_traces_folder,
        ocean_tugs_rv_traces_folder,
        ocean_pilots_rv_traces_folder,
        pilots_rv_berth_traces_folder,
        tugs_rv_berth_traces_folder,
        pilots_rv_tugs_rv_traces_folder,
        tugs_wl_tugs_rv_traces_folder,
        pilots_wl_pilot_rv_traces_folder,
        pilots_wl_berth_traces_folder,
        ocean_tug_wl_traces_folder,
        ocean_spawn_ids=[1],
    )

    path_finder.load_tugs_rendezvous_locations(tugs_rendezvous_filename)
    path_finder.load_pilots_rendezvous_locations(
        pilots_rendezvous_filename, VesselClass.from_class_code
    )

    pickle.dump(path_finder, open("example/path_finder.pickle", "wb"))

# Initialize loggers
vessel_event_logger = VesselEventLogger.get_instance()
vessel_event_logger.verbose = args.verbose

pilots_event_logger = PilotEventLogger.get_instance()
pilots_event_logger.verbose = args.verbose

tug_event_logger = TugEventLogger.get_instance()
tug_event_logger.verbose = args.verbose

# Add the AIS and section occupancy loggers to the simulation
vessel_logger_pos = AISVesselLogProcessor()
pilot_logger_pos = AISPilotLogProcessor()
tug_logger_pos = AISTugLogProcessor()

sections_logger = SectionsLogProcessor()

world.add_processor(vessel_logger_pos)
world.add_processor(pilot_logger_pos)
world.add_processor(tug_logger_pos)
world.add_processor(sections_logger)

# Create Esper processors for the simulation
vessel_goal_formulator = VesselGoalFormulatorProcessor(VesselClass)
vessel_movement_processor = VesselMovementProcessor(VesselClass)
tug_movement_processor = TugMovementProcessor()
pilot_movement_processor = PilotMovementProcessor()

timer_processor = TimerProcessor()

# Create berth service time generator
berth_service_distribution_factory = BerthServiceDistributionFactory(
    terminal_service_times_filename
)

# Add berths to the simulation
berths_generator = BerthsInitializer(
    world,
    berths_filename,
    VesselContentType,
    berth_service_distribution_factory,
    berth_randomized_check_prob=args.berth_check_prob,
)

berths_generator.create_berths()

# Add tugs to the simulation
tugs_generator = TugsInitializer(
    world,
    tugs_waiting_locations_filename,
    tugs_count=3,
    companies_from_data=args.tugs_allocation_data,
)
tugs_generator.create_tugboats()

# Add pilots to the simulation
pilots_generator = PilotsInitializer(world, pilots_waiting_location_filename)
pilots_generator.create_pilots()

# Add anchorages to the simulation
anchorages_generator = AnchoragesInitializer(world, anchorages_filename)
anchorages_generator.create_anchorages()

# Define tugboat logic and set the tugboat companies (single vs multiple)
tugboat_logic = DefaultTugCompanyStrategy.get_instance()
tugboat_logic.set_world(world)
tugboat_logic.set_tug_companies(tugs_generator.get_tugboat_companies())

if args.single_tugs_company:
    # Strategy with one tug company
    tug_designator = tugboat_logic.select_tugs
else:
    # Strategy with different tug companies
    tug_designator = tugboat_logic.assign_specific_tugs_to_vessel

vessel_strategy = DefaultVesselStrategy(
    world=world,
    anchorage_designator=assign_anchorage,
    berth_designator=berths_allocation_designator,
    path_finder=path_finder,
    tug_designator=tug_designator,
)

if args.tugs_malfunction:
    deattach_polygon = Polygon(
        json.loads(open(tugs_deattach_location_filename).read())["features"][0][
            "geometry"
        ]["coordinates"][0]
    )
    tug_malfunction_anomaly = TugMalfunctionAnomaly(
        world,
        path_finder,
        args.tugs_break_percentage_idle,
        args.tugs_break_percentage_busy,
        tug_designator,
        deattach_polygon,
    )
else:
    tug_malfunction_anomaly = None

tug_strategy = DefaultTugStrategy(
    world=world,
    path_finder=path_finder,
    deattach_polygon_filename=tugs_deattach_location_filename,
    tug_malfunction_anomaly=tug_malfunction_anomaly,
)

hm_processor = HarbourMasterProcessor(
    world=world,
    vessel_strategy=vessel_strategy,
    tug_strategy=tug_strategy,
    logger=vessel_event_logger,
)

# Define the probabilities of the speed anomalies Markov model
if args.anomalous_speed:
    speed_transition_p = {"double": 0.1, "half": 0.1, "reset": 0.8}

    anomalous_vessel_percent = 0.2
else:
    anomalous_vessel_percent = 0
    speed_transition_p = NULL_SPEED_MODEL

# Create vessel generators for each vessel type
vessel_distribution_factory = VesselDistributionFactory()

for vessel_type in VesselType:
    if args.max_time is not None:
        vessel_generator = FixedVesselGeneratorProcessor(
            world=world,
            inter_arrival_time_sampler=vessel_distribution_factory.inter_arrival_time_sampler(
                vessel_type
            ),
            vessel_info_sampler=vessel_distribution_factory.vessel_info_sampler(
                vessel_type
            ),
            spawn_area_filename=spawn_area_filename,
            run_info=world_run_info,
            vessel_logger=vessel_event_logger,
        )
    else:
        vessel_generator = VesselGeneratorProcessor(
            world=world,
            inter_arrival_time_sampler=vessel_distribution_factory.inter_arrival_time_sampler(
                vessel_type
            ),
            vessel_info_sampler=vessel_distribution_factory.vessel_info_sampler(
                vessel_type
            ),
            spawn_area_filename=spawn_area_filename,
            vessel_logger=vessel_event_logger,
        )

    world.add_processor(vessel_generator)

tug_goal_formulator = TugGoalFormulatorProcessor()
pilot_goal_formulator = PilotGoalFormulatorProcessor()

world.add_processor(vessel_goal_formulator)
world.add_processor(tug_goal_formulator)
world.add_processor(pilot_goal_formulator)
world.add_processor(vessel_movement_processor)
world.add_processor(tug_movement_processor)
world.add_processor(pilot_movement_processor)
world.add_processor(timer_processor)
world.add_processor(hm_processor)

signal.signal(signal.SIGINT, on_exit)


if args.graphics:
    # Specify a bounding box which will show the area at the start of
    # the simulation (so roughly the area of the simulated port)
    # NW corner (lat, lon), SE corner (lat, lon)
    bounding_box = [51.4133, 3.9214, 51.2305, 4.4090]
    # Specify colors in RGB for tugs and pilots rendezvous locations
    tugs_rv_color = [231, 76, 60]
    pilots_rv_color = [120, 55, 173]

    # Initialize renderers and add them to the world
    berths_renderer = BerthRenderer()
    vessel_renderer = VesselRenderer()
    anchorages_renderer = AnchorageRenderer()
    tugs_renderer = TugsRenderer()
    pilots_renderer = PilotsRenderer()
    tugs_rendezvous_renderer = RendezvousRenderer(
        tugs_rendezvous_filename, tugs_rv_color
    )
    pilots_rendezvous_renderer = RendezvousRenderer(
        pilots_rendezvous_filename, pilots_rv_color
    )

    if args.max_time is not None:
        # If max time for the simulation is specified, then split the tugboat companies in the operations graphics
        operations_renderer = OperationsRenderer(
            tug_companies=tugs_generator.get_tugboat_companies()
        )
    else:
        operations_renderer = OperationsRenderer()

    world.add_processor(berths_renderer)
    world.add_processor(vessel_renderer)
    world.add_processor(anchorages_renderer)
    world.add_processor(tugs_renderer)
    world.add_processor(pilots_renderer)
    world.add_processor(tugs_rendezvous_renderer)
    world.add_processor(pilots_rendezvous_renderer)
    world.add_processor(operations_renderer)

    simulation_layer = SimulationLayer(
        world, bounding_box=bounding_box, max_time=args.max_time
    )

    simulation_layer.add_renderer(berths_renderer)
    simulation_layer.add_renderer(vessel_renderer)
    simulation_layer.add_renderer(anchorages_renderer)
    simulation_layer.add_renderer(tugs_renderer)
    simulation_layer.add_renderer(pilots_renderer)
    simulation_layer.add_renderer(tugs_rendezvous_renderer)
    simulation_layer.add_renderer(pilots_rendezvous_renderer)
    simulation_layer.add_renderer(operations_renderer)

    # If your area of interest on the map is outdated, consider playing around
    # with the tile providers. For more info:
    # https://github.com/andrea-cuttone/geoplotlib/wiki/User-Guide#tiles-providers.
    # For example, Port of Antwerp is outdated with the default geoplotlib 'positron' tiles_provider,
    # that's why we are changing it here
    geoplotlib.tiles_provider(
        {
            "url": lambda zoom, xtile, ytile: "http://a.tile.stamen.com/terrain/%d/%d/%d.png"
            % (zoom, xtile, ytile),
            "tiles_dir": "mytiles",
            "attribution": "Map tiles by Stamen Design, under CC BY 3.0. Data @ OpenStreetMap contributors",
        }
    )
    geoplotlib.add_layer(simulation_layer)
    geoplotlib.show()

    # Save the log files if not done already
    if os.environ[SIMULATION_STATE_KEY] != SimulationState.STOPPED.value:
        on_exit(None, None)
else:
    # Run the simulation headless
    current_time = 0

    while os.environ[SIMULATION_STATE_KEY] == SimulationState.RUNNING.value:
        # If max_time was specified kill the simulation after running it
        # for max_time seconds, otherwise run the simulation indefinitely
        if args.max_time is not None and current_time > args.max_time:
            # Write log files and exit
            on_exit(None, None)

        world.process(args.step)
        current_time += args.step
        world_run_info.update_time()
