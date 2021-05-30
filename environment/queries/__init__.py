"""
    This module contains several utility functions to fetch entities
    from the simulation world
"""
from components.fsm import VesselStateMachine, TugStateMachine, \
    PilotStateMachine
from components import Position, Velocity, VesselPath, \
    Course, VesselInfo, TugInfo, PilotInfo, FrameCounter
from utils.timer import SimulationTimer

from .berth_list import BerthList
from .anchorage_list import AnchorageList
from .waiting_locations import WaitingLocationList


def fetch_timers(world):
    return world.get_components(SimulationTimer)


def fetch_vessels(world):
    return world.get_components(Position, FrameCounter, Course, Velocity, VesselPath, VesselStateMachine, VesselInfo)


def fetch_tugs(world):
    return world.get_components(Position, FrameCounter, Course, Velocity, VesselPath, TugStateMachine, TugInfo)


def fetch_pilots(world):
    return world.get_components(Position, Course, Velocity, VesselPath, PilotStateMachine, PilotInfo)


def berth_info_by_id(world, berth_id):
    _, berth_components = list(BerthList(world=world).filter_by_ids([berth_id]))[0]

    return berth_components[1]
