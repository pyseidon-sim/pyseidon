import random
import functools
import numpy as np

from exceptions import NoBerthException, \
    SectionPathUnavailableException, NoAvailablePilotException, \
    NotEnoughAvailableTugsException, NoPathException, PathTerminatedException

from environment.queries import BerthList, WaitingLocationList
from environment.messaging.types import VesselMessageType
from components.fsm.states import BerthState, TugState, PilotState, VesselState

from components import Position, VesselInfo, VesselPath, PilotInfo, Velocity, LocationType
from components.fsm import VesselStateMachine, TugStateMachine, PilotStateMachine, BerthStateMachine

from .constants import VESSEL_ORIGIN_OFFSET


class DefaultVesselStrategy():
    """This class handles incoming vessel messages and decides the next step to be taken"""
    def __init__(
            self,
            world,
            anchorage_designator,
            berth_designator,
            path_finder,
            tug_designator=None):
        """Initialize the vessel strategy

            Args:
                world: the simulation world.
                anchorage_designator: function that returns an anchorage given a entity id and the world
                berth_designator: function that returns a suitable berth given the vessel info and a list of available berths
                path_finder: PathFinder singleton object
                tug_designator: function(vessel_entity_id) that returns tug ids available for the given vessel
                                or raises a NotEnoughAvailableTugsException
        """
        self.world = world
        self.anchorage_designator = anchorage_designator
        self.berth_designator = berth_designator
        self.path_finder = path_finder
        self.tug_designator = tug_designator

    def handle(self, message, entity_id, vessel_info):
        """
            Handle incoming messages

            Args:
                message: message object
                entity_id: entity id of the vessel that generated the message
                vessel_info: the message sender vessel info
        """
        return {
            VesselMessageType.REQUEST_ARRIVAL_CLEARANCE: self.handle_incoming,
            VesselMessageType.REQUEST_DEPARTURE_CLEARANCE: self.handle_departure_clearance,
            VesselMessageType.DEPARTED: self.handle_departed,
            VesselMessageType.DOCKED_AT_TERMINAL: self.handle_docked_at_terminal,
            VesselMessageType.GOING_TO_ANCHORAGE: self.handle_anchored,
            VesselMessageType.WAITING_AT_ANCHORAGE: self.handle_anchored,
            VesselMessageType.DEPART: self.handle_departure,
            VesselMessageType.WAITING_FOR_PILOT_AT_RENDEZVOUS: self.handle_waiting_for_pilots_rendezvous,
            VesselMessageType.WAITING_FOR_TUGS_AT_RENDEZVOUS: self.handle_waiting_for_tugs_rendezvous,
            VesselMessageType.GO_TO_BERTH: self.handle_go_to_berth,
            VesselMessageType.GO_TO_PILOT_RENDEZVOUS: self.handle_go_to_pilot_rendezvous,
            VesselMessageType.GO_TO_TUGS_RENDEZVOUS: self.handle_go_to_tugs_rendezvous,
            VesselMessageType.FIX_TUG: self.handle_fix_tug
        }[message.message](message, entity_id, vessel_info)

    def lock_arrival_resources(self, entity_id, vessel_info):
        position = self.world.component_for_entity(entity_id, Position)
        path = self.world.component_for_entity(entity_id, VesselPath)
        fsm = self.world.component_for_entity(entity_id, VesselStateMachine)

        pilot_id, pilot_fsm = None, None
        tug_ids = None

        try:
            # If the vessel does not need pilots or tugs, redirect it to the berth straight away
            if not vessel_info.pilot_required and (not vessel_info.tugs_required or self.tug_designator is None):
                berth_info, term_fsm, ocean_berth_path = self._select_berth(path, vessel_info, position)

                path.set_path(ocean_berth_path)

                fsm.assign_berth(term_fsm, berth_info.id)
                fsm.go_to_berth()

                self._add_offset_to_vessel_position(position, path)
                return True

            # If the vessel needs pilots but no tugboats, redirect it to a pilot rendezvous and then to berth
            if vessel_info.pilot_required and (not vessel_info.tugs_required or self.tug_designator is None):
                # Verify if a pilot is available for this vessel
                pilot_id, pilot_fsm = self._select_pilot()

                # Select an available berth connected to the designated pilot rendezvous point
                berth_info, ocean_pilot_rv_path, pilot_rv_berth_path, pilot_rv_id = \
                    self._select_berth_pilot_rendezvous(path, vessel_info, position)

                if berth_info is None:
                    raise NoBerthException(f"No available berth for vessel {vessel_info.name}")

                path.set_path(ocean_pilot_rv_path)

                berth_fsm = BerthList(world=self.world).filter_by_ids([berth_info.id])[0][1][2]

                # Lock the paths berth for this vessel
                fsm.assign_berth(berth_fsm, berth_info.id)

                # Assign the pilot to the vessel
                pilot_position = self.world.component_for_entity(pilot_id, Position)
                pilot_path = self.world.component_for_entity(pilot_id, VesselPath)

                _, (location_info, _) = \
                    WaitingLocationList(world=self.world).filter_by_ids([pilot_fsm.waiting_location_id])[0]

                pilot_path.set_path(
                    self.path_finder.pilot_waiting_location_pilot_rendezvous_path(
                        pilot_position=pilot_position.lonlat,
                        rendezvous_id=pilot_rv_id,
                        waiting_location_id=location_info.id))

                pilot_fsm.go_to_rendezvous(entity_id, pilot_rv_id)

                fsm.pilot = pilot_id
                fsm.go_to_pilots_rendezvous(pilot_rv_id, pilot_rv_berth_path)

                self._add_offset_to_vessel_position(position, path)
                
                return True

            # If the vessel needs tugs but no pilot, redirect it to a tug rendezvous and then to berth
            if not vessel_info.pilot_required and vessel_info.tugs_required and self.tug_designator is not None:
                # Verify if tugs are available for this vessel
                tug_ids = self.tug_designator(entity_id)

                # Select an available berth connected to the designed rendezvous point
                berth_info, ocean_tug_rv_path,\
                tug_rv_berth_path, tug_rv_id = self._select_berth_tug_rendezvous(path, vessel_info, position)

                if berth_info is None:
                    raise NoBerthException(f"No available berth for vessel {vessel_info.name}")

                path.set_path(ocean_tug_rv_path)

                berth_fsm = BerthList(world=self.world).filter_by_ids([berth_info.id])[0][1][2]

                # Lock the berth for this vessel
                fsm.assign_berth(berth_fsm, berth_info.id)

                # Assign the tugs to the vessel
                for tug_id in tug_ids:
                    tug_fsm = self.world.component_for_entity(tug_id, TugStateMachine)
                    tug_position = self.world.component_for_entity(tug_id, Position)
                    tug_path = self.world.component_for_entity(tug_id, VesselPath)

                    _, (location_info, _) = WaitingLocationList(world=self.world).filter_by_ids([tug_fsm.waiting_location_id])[0]

                    tug_wl_rv_path = self.path_finder.tugs_waiting_location_rendezvous_path(
                        tug_position=tug_position.lonlat,
                        waiting_location_id=location_info.id,
                        rendezvous_id=tug_rv_id)
                    tug_path.set_path(tug_wl_rv_path)

                    tug_fsm.go_to_rendezvous(entity_id, tug_rv_id)

                fsm.tugboats = tug_ids
                fsm.go_to_tugs_rendezvous(rendezvous_id=tug_rv_id, rendezvous_berth_path=tug_rv_berth_path)
                self._add_offset_to_vessel_position(position, path)

                return True

            # If the vessel needs both tugs and pilots, redirect it to a pilot rendezvous,
            # then to tug rendezvous, and then to berth
            if vessel_info.pilot_required and vessel_info.tugs_required and self.tug_designator is not None:
                # Verify if a pilot is available for this vessel
                pilot_id, pilot_fsm = self._select_pilot()

                # Select an available berth connected to the designated tug rendezvous point and pilot rendezvous point
                berth_info, ocean_pilot_rv_path, pilot_rv_tug_rv_path, tug_rv_berth_path, tug_rv_id, pilot_rv_id = \
                    self._select_berth_tug_rendezvous_pilot_rendezvous(path,
                                                                       vessel_info,
                                                                       position)

                if berth_info is None:
                    raise NoBerthException(f"No available berth for vessel {vessel_info.name}")

                berth_fsm = BerthList(world=self.world).filter_by_ids([berth_info.id])[0][1][2]

                # Assign the pilot to the vessel
                pilot_position = self.world.component_for_entity(pilot_id, Position)
                pilot_path = self.world.component_for_entity(pilot_id, VesselPath)

                _, (pilot_location_info, _) = \
                    WaitingLocationList(world=self.world).filter_by_ids([pilot_fsm.waiting_location_id])[0]

                # Verify if tugs are available for this vessel
                tug_ids = self.tug_designator(entity_id)

                # Assign the tugs to the vessel
                for tug_id in tug_ids:
                    tug_fsm = self.world.component_for_entity(tug_id, TugStateMachine)
                    tug_position = self.world.component_for_entity(tug_id, Position)
                    tug_path = self.world.component_for_entity(tug_id, VesselPath)

                    _, (tug_location_info, _) = \
                    WaitingLocationList(world=self.world).filter_by_ids([tug_fsm.waiting_location_id])[0]

                    tug_wl_rv_path = self.path_finder.tugs_waiting_location_rendezvous_path(
                        tug_position=tug_position.lonlat,
                        waiting_location_id=tug_location_info.id,
                        rendezvous_id=tug_rv_id)
                    tug_path.set_path(tug_wl_rv_path)

                    tug_fsm.go_to_rendezvous(entity_id, tug_rv_id)
                    self._add_offset_to_vessel_position(tug_position, tug_path)

                # Redirect assigned pilot to go to pilot rendezvous
                pilot_path.set_path(
                    self.path_finder.pilot_waiting_location_pilot_rendezvous_path(
                        pilot_position=pilot_position.lonlat,
                        waiting_location_id=pilot_location_info.id,
                        rendezvous_id=pilot_rv_id))

                # Redirect vessel to pilot rendezvous
                path.set_path(ocean_pilot_rv_path)

                # Lock the berth for this vessel
                fsm.assign_berth(berth_fsm, berth_info.id)
                fsm.assign_tugs_rendezvous(tug_rv_id, pilot_rv_tug_rv_path, tug_rv_berth_path)

                pilot_fsm.go_to_rendezvous(entity_id, pilot_rv_id)

                fsm.pilot = pilot_id
                fsm.tugboats = tug_ids
                fsm.go_to_pilots_rendezvous(pilot_rv_id, ocean_pilot_rv_path)

                # The offset is added to make sure the next
                # destination node has a distance != 0
                self._add_offset_to_vessel_position(position, path)
                return True
        except (NoBerthException, SectionPathUnavailableException,
                NoAvailablePilotException, NotEnoughAvailableTugsException) as _:
            fsm.pilot = None
            fsm.tugboats = None

            return False

    def handle_incoming(self, message, entity_id, vessel_info):
        """
            Decides whether a vessel should sail directly to
            meet pilots and tugs at a designated location or wait in an anchorage
        """
        position = self.world.component_for_entity(entity_id, Position)
        path = self.world.component_for_entity(entity_id, VesselPath)

        if self.lock_arrival_resources(entity_id, vessel_info):
            # FIXME: "Spawn" the vessel at the beginning of the arrival path.
            #        This is a temporary solution that should be changed ASAP
            path.path["x"], path.path["y"] = path.path["x"][1:], path.path["y"][1:]
            path.path["point_sections"] = path.path["point_sections"][1:]

            # The offset is added to make sure the next
            # destination node has a distance != 0
            self._add_offset_to_vessel_position(position, path)
        else:
            # If any of the resources are not available, the vessel
            # cannot proceed into the port. Thus, it slows down and
            # proceeds towards the port (anchorage?) slowly
            velocity = self.world.component_for_entity(entity_id, Velocity)
            velocity.velocity = 2

            fsm = self.world.component_for_entity(entity_id, VesselStateMachine)

            anchorage_id, anchorage_fsm = self._select_and_route_to_anchorage(
                entity_id,
                path,
                position)

            position.update_position(np.array(path.get_origin()) + VESSEL_ORIGIN_OFFSET)
            anchorage_fsm.book(fsm)
            fsm.go_to_anchorage(anchorage_id, anchorage_fsm)

    def handle_waiting_for_pilots_rendezvous(self, message, entity_id, vessel_info):
        fsm = self.world.component_for_entity(entity_id, VesselStateMachine)
        fsm.stop_at_pilots_rendezvous()

    def handle_waiting_for_tugs_rendezvous(self, message, entity_id, vessel_info):
        fsm = self.world.component_for_entity(entity_id, VesselStateMachine)
        fsm.stop_at_tugs_rendezvous()

    def handle_go_to_pilot_rendezvous(self, message, entity_id, vessel_info):
        pass

    def handle_go_to_tugs_rendezvous(self, message, entity_id, vessel_info):
        path = self.world.component_for_entity(entity_id, VesselPath)
        fsm = self.world.component_for_entity(entity_id, VesselStateMachine)

        # Check if the pilot is at the rendezvous location, if that's not the case return
        pilot_fsm = self.world.component_for_entity(fsm.pilot, PilotStateMachine)

        if pilot_fsm.current() != PilotState.WAITING_AT_RENDEZVOUS:
            return

        fsm.pilot_boarded = True

        _, (waiting_location_info, _) = WaitingLocationList(
            world=self.world).random_location_by_type(LocationType.PILOTS_STORAGE)

        pilot_position = self.world.component_for_entity(fsm.pilot, Position)
        pilot_path = self.world.component_for_entity(fsm.pilot, VesselPath)

        waiting_location_path = self.path_finder.pilot_rendezvous_pilot_waiting_location_path(
            pilot_position=pilot_position.lonlat,
            rendezvous_id=fsm.pilot_rendezvous_id,
            waiting_location_id=waiting_location_info.id)

        pilot_fsm.deliver_pilot(waiting_location_info.id)
        pilot_path.set_path(waiting_location_path)

        # Set the current path as the previously locked pilot rendezvous -> tug rendezvous path
        path.set_path(fsm.pilots_rendezvous_tug_rendezvous_path)

        fsm.pilots_rendezvous_tug_rendezvous_path = None
        fsm.go_to_tugs_rendezvous()

    def handle_go_to_berth(self, message, entity_id, vessel_info):
        fsm = self.world.component_for_entity(entity_id, VesselStateMachine)
        vessel_info = self.world.component_for_entity(entity_id, VesselInfo)

        if vessel_info.tugs_required and fsm.current() == VesselState.WAITING_FOR_PILOTS_RENDEZVOUS:
            self.handle_go_to_tugs_rendezvous(message, entity_id, vessel_info)
            return

        path = self.world.component_for_entity(entity_id, VesselPath)

        if fsm.current() == VesselState.WAITING_FOR_TUGS_RENDEZVOUS:
            # Redirect vessel from tug rendezvous to berth
            #
            # Check if all tugs are at the rendezvous location, if not,
            # return without proceeding to the berth
            tug_fsms = [self.world.component_for_entity(tug_id, TugStateMachine) for tug_id in fsm.tugboats]

            for tug_fsm in tug_fsms:
                if tug_fsm.current() != TugState.WAITING_AT_RENDEZVOUS:
                    return

            for tug_fsm in tug_fsms:
                tug_fsm.start_tugging_in(fsm.destination_berth_id)

            # Set the current path as the previously locked rendezvous -> berth path
            path.set_path(fsm.tugs_rendezvous_berth_path)
            fsm.tug_rendezvous_berth_path = None
        elif fsm.current() == VesselState.WAITING_FOR_PILOTS_RENDEZVOUS:
            # Redirect vessel from pilot rendezvous to berth
            #
            # Check if the pilot is at the rendezvous location, if not
            # return without proceeding to the berth
            pilot_fsm = self.world.component_for_entity(fsm.pilot, PilotStateMachine)

            if pilot_fsm.current() != PilotState.WAITING_AT_RENDEZVOUS:
                return

            fsm.pilot_boarded = True

            _, (waiting_location_info, _) = WaitingLocationList(
                world=self.world).random_location_by_type(LocationType.PILOTS_STORAGE)

            pilot_position = self.world.component_for_entity(fsm.pilot, Position)
            pilot_path = self.world.component_for_entity(fsm.pilot, VesselPath)

            waiting_location_path = self.path_finder.pilot_rendezvous_pilot_waiting_location_path(
                pilot_position=pilot_position.lonlat,
                rendezvous_id=fsm.pilot_rendezvous_id,
                waiting_location_id=waiting_location_info.id)

            pilot_fsm.deliver_pilot(waiting_location_info.id)
            pilot_path.set_path(waiting_location_path)

            # Set the current path as the previously locked pilot rendezvous -> tug rendezvous path
            path.set_path(fsm.pilot_rendezvous_berth_path)
            fsm.pilot_rendezvous_berth_path = None

        fsm.go_to_berth()

    def handle_anchored(self, message, entity_id, vessel_info):
        path = self.world.component_for_entity(entity_id, VesselPath)
        fsm = self.world.component_for_entity(entity_id, VesselStateMachine)
        position = self.world.component_for_entity(entity_id, Position)
        velocity = self.world.component_for_entity(entity_id, Velocity)

        if not path.has_current_route():
            # When the vessel has no longer a route it means
            # it reached the destination anchorage
            fsm.stop_at_anchorage()
            # Stop the vessel
            velocity.velocity = 0

        if self.lock_arrival_resources(entity_id, vessel_info):
            # The offset is added to make sure the next
            # destination node has a distance != 0
            position.update_position(
                np.array(path.get_origin()) + VESSEL_ORIGIN_OFFSET)

    def handle_docked_at_terminal(self, message, entity_id, vessel_info):
        fsm = self.world.component_for_entity(entity_id, VesselStateMachine)
        vessel_info = self.world.component_for_entity(entity_id, VesselInfo)
        velocity = self.world.component_for_entity(entity_id, Velocity)

        destination_berth_id = fsm.destination_berth_id
        _, (_, berth_info, _) = BerthList(world=self.world).filter_by_ids([destination_berth_id])[0]

        # FIXME: hmm why sometimes destination_berth_fsm is None here? It shouldn't be ever?
        if fsm.destination_berth_fsm is None:
            fsm.destination_berth_fsm = self.world.component_for_entity(destination_berth_id, BerthStateMachine)
            if fsm.destination_berth_fsm.current_vessel_fsm is None:
                fsm.destination_berth_fsm.book(fsm)
            assert fsm.destination_berth_fsm.current_vessel_fsm == fsm, "The booked vessel at the berth must be the same!"

        fsm.servicing(vessel_info)

        # Stop the vessel
        velocity.velocity = 0

        # leave pilot
        if vessel_info.pilot_required:
            fsm.pilot_boarded = False
            fsm.pilot = None

        # Tugs "de-attach" and go to waiting location
        if fsm.tugboats is not None:
            for tug_id in fsm.tugboats:
                tug_fsm = self.world.component_for_entity(tug_id, TugStateMachine)
                tug_path = self.world.component_for_entity(tug_id, VesselPath)
                tug_position = self.world.component_for_entity(tug_id, Position)

                _, (waiting_location_info, _) = \
                    WaitingLocationList(world=self.world).random_location_by_type(LocationType.TUGBOATS_STORAGE)

                waiting_location_path = self.path_finder.tugs_berth_waiting_location_path(
                    tug_position=tug_position.lonlat,
                    berth_info=berth_info,
                    waiting_location_id=waiting_location_info.id)

                tug_path.set_path(waiting_location_path)
                tug_fsm.done_tugging(waiting_location_info.id)
                fsm.tugboats = None

    def handle_departure_clearance(self, message, entity_id, vessel_info):
        try:
            fsm = self.world.component_for_entity(entity_id, VesselStateMachine)

            # If neither pilot nor tugs are required, send the vessel out of the port
            if not vessel_info.pilot_required and (not vessel_info.tugs_required or self.tug_designator is None):
                # Compute a path and send the vessel down that path
                vessel_path = self.world.component_for_entity(entity_id, VesselPath)
                position = self.world.component_for_entity(entity_id, Position)

                spawn_path = self._route_to_spawn(
                    fsm.destination_berth_id,
                    position,
                    vessel_info)

                vessel_path.set_path(spawn_path)

                fsm.leave()
                return

            _, (_, berth_info, _) = BerthList(world=self.world).filter_by_ids([fsm.destination_berth_id])[0]

            # Request a pilot
            if vessel_info.pilot_required and fsm.pilot is None:
                pilot_id, _ = self._select_pilot()

                pilot_fsm = self.world.component_for_entity(pilot_id, PilotStateMachine)
                pilot_path = self.world.component_for_entity(pilot_id, VesselPath)
                pilot_position = self.world.component_for_entity(pilot_id, Position)

                pilot_berth_path = self.path_finder.pilot_waiting_location_berth_path(
                    pilot_position=pilot_position.lonlat,
                    berth_id=berth_info.id,
                    waiting_location_id=pilot_fsm.waiting_location_id)

                pilot_path.set_path(pilot_berth_path)
                pilot_fsm.go_to_berth(entity_id, fsm.destination_berth_id)

                fsm.pilot = pilot_id
                fsm.wait_for_tugs_pilots()

            # Request tugs
            if vessel_info.tugs_required and self.tug_designator is not None and fsm.tugboats is None:
                tug_ids = self.tug_designator(entity_id)

                for tug_id in tug_ids:
                    tug_fsm = self.world.component_for_entity(tug_id, TugStateMachine)
                    tug_path = self.world.component_for_entity(tug_id, VesselPath)
                    tug_position = self.world.component_for_entity(tug_id, Position)

                    tug_berth_path = self.path_finder.tugs_berth_waiting_location_path(
                        tug_position=tug_position.lonlat,
                        berth_info=berth_info,
                        waiting_location_id=tug_fsm.waiting_location_id)
                    tug_berth_path = self.path_finder.reverse_path(tug_berth_path)

                    tug_path.set_path(tug_berth_path)
                    tug_fsm.go_to_berth(entity_id, fsm.destination_berth_id)

                fsm.tugboats = tug_ids
                fsm.wait_for_tugs_pilots()

        except (NoAvailablePilotException, NotEnoughAvailableTugsException) as _:
            pass

    def handle_departure(self, message, entity_id, vessel_info):
        position = self.world.component_for_entity(entity_id, Position)
        path = self.world.component_for_entity(entity_id, VesselPath)
        fsm = self.world.component_for_entity(entity_id, VesselStateMachine)

        # Check if the pilot is at the berth, if not then return
        if vessel_info.pilot_required and not fsm.pilot_boarded:
            pilot_fsm = self.world.component_for_entity(fsm.pilot, PilotStateMachine)

            # If pilot vessel is at the berth, pilot boards and pilot vessel goes back to waiting location
            if pilot_fsm.current() == PilotState.WAITING_AT_BERTH:
                _, (waiting_location_info, _) = WaitingLocationList(
                    world=self.world).random_location_by_type(LocationType.PILOTS_STORAGE)

                pilot_path = self.world.component_for_entity(fsm.pilot, VesselPath)
                pilot_position = self.world.component_for_entity(fsm.pilot, Position)

                waiting_location_path = self.path_finder.berth_pilot_waiting_location_path(
                    pilot_position=pilot_position.lonlat,
                    berth_id=fsm.destination_berth_id,
                    waiting_location_id=waiting_location_info.id)
                # waiting_location_path = self.path_finder.reverse_path(waiting_location_path)

                pilot_fsm.deliver_pilot(waiting_location_info.id)
                # Send the pilot back
                pilot_path.set_path(waiting_location_path)

                fsm.pilot_boarded = True
            else:
                # Wait until pilots are ready to board
                return

        # Check if all tugs are at the berth, if not, return without
        # proceeding out of the port
        if vessel_info.tugs_required:
            if fsm.tugboats:
                tug_fsms = [self.world.component_for_entity(tug_id, TugStateMachine) for tug_id in fsm.tugboats]
            else:
                return

            # Make sure the correct number of tugboats is assigned to the vessel
            if len(fsm.tugboats) != vessel_info.number_of_tugboats:
                return

            for tug_fsm in tug_fsms:
                if tug_fsm.current() != TugState.WAITING_AT_BERTH:
                    return

        spawn_path = self._route_to_spawn(
            fsm.destination_berth_id,
            position,
            vessel_info)

        path.set_path(spawn_path)

        if fsm.tugboats is not None:
            for tug_id in fsm.tugboats:
                tug_fsm = self.world.component_for_entity(tug_id, TugStateMachine)
                tug_fsm.start_tugging_out()

        fsm.leave()

    def handle_departed(self, message, entity_id, vessel_info):
        fsm = self.world.component_for_entity(entity_id, VesselStateMachine)
        vessel_info = self.world.component_for_entity(entity_id, VesselInfo)
        fsm.complete()

        # leave pilot
        if vessel_info.pilot_required:
            pilot_info = self.world.component_for_entity(fsm.pilot, PilotInfo)

            pilot_info.available = True
            fsm.pilot = None

        # Tugs "de-attach" and go to waiting location. If no tugs
        # are attached even if the vessel requires tugboats that means
        # the tugs already de-attached
        if vessel_info.tugs_required and fsm.tugboats is not None:
            for tug_id in fsm.tugboats:
                tug_fsm = self.world.component_for_entity(tug_id, TugStateMachine)
                tug_path = self.world.component_for_entity(tug_id, VesselPath)
                tug_position = self.world.component_for_entity(tug_id, Position)
                
                _, (waiting_location_info, _) = WaitingLocationList(world=self.world).random_location_by_type(LocationType.TUGBOATS_STORAGE)
                waiting_location_path = self.path_finder.tugs_ocean_waiting_location_path(
                    tug_position=tug_position.lonlat,
                    waiting_location_id=waiting_location_info.id)
                
                tug_path.set_path(waiting_location_path)
                tug_fsm.done_tugging(waiting_location_info.id)
                fsm.tugboats = None

        self.world.delete_entity(entity_id)

    def handle_fix_tug(self, message, entity_id, vessel_info):
        fsm = self.world.component_for_entity(entity_id, VesselStateMachine)

        if fsm.tugboats:
            # Check if the newly assigned tug arrived at the location, if not - return
            tug_fsms = [self.world.component_for_entity(tug_id, TugStateMachine) for tug_id in fsm.tugboats]
        else:
            return

        # Check if the vessel has the required amount of tugs
        if vessel_info.number_of_tugboats == len(tug_fsms):
            # ...and check if they are all attached and waiting
            for tug_fsm in tug_fsms:
                if tug_fsm.current() != TugState.WAITING_AT_MALFUNCTION_LOCATION:
                    return

            if fsm.state_before_failure == VesselState.GOING_TO_BERTH:
                fsm.tug_fix_berth()

                for tug_fsm in tug_fsms:
                    tug_fsm.start_tugging_in(fsm.destination_berth_id)
            elif fsm.state_before_failure == VesselState.LEAVING:
                fsm.tug_fix_leaving()

                for tug_fsm in tug_fsms:
                    tug_fsm.start_tugging_out()
            else:
                raise Exception(f"Could not handle a tugboat fix for a vessel that was in state {fsm.state_before_failure} before the failure")
    def _select_pilot(self):
        # Fetch the pilot finite state machine components in the world
        pilots = self.world.get_components(PilotStateMachine)

        for ent, pilot_fsm in pilots:
            # Unpack the pilot info from the list
            pilot_fsm = pilot_fsm[0]

            if pilot_fsm.current() == PilotState.IDLE:
                return ent, pilot_fsm

        raise NoAvailablePilotException("No pilot available")

    def _select_path(self, berths_info, vessel_position, vessel_info):
        for berth_info in berths_info:
            if vessel_position is not None:
                ocean_berth_paths = self.path_finder.ocean_berth_paths(
                    vessel_position=vessel_position.lonlat,
                    berth_id=berth_info.id)
            else:
                ocean_berth_paths = self.path_finder.ocean_berth_paths(
                    berth_id=berth_info.id)

            if len(ocean_berth_paths) > 0:
                path = ocean_berth_paths[0]
                return path, berth_info

        return None, None

    def _add_offset_to_vessel_position(self, position, path):
        # The offset is added to make sure the next
        # destination node has a distance != 0
        position.update_position(
            np.array(path.get_origin()) + VESSEL_ORIGIN_OFFSET)

    def _berths_for_vessel(self, vessel_info):
        available_berths = BerthList(world=self.world).filter_by_available(BerthState.AVAILABLE)
        available_berths = available_berths.filter_by_ids(self.path_finder.ocean_connected_berth_ids())

        berths = self.berth_designator(vessel_info, list(available_berths))

        return [b[1][1] for b in berths]

    def _select_berth(self, vessel_path, vessel_info, vessel_position):
        """
            Selects an available berth that can serve the target vessel
        """
        berths_info = self._berths_for_vessel(vessel_info)
        ocean_berth_path, berth_info = self._select_path(berths_info, vessel_position, vessel_info)

        if ocean_berth_path is None:
            raise NoPathException(f"No ocean -> berth path for vessel {vessel_info}")

        term_fsm = BerthList(world=self.world).filter_by_ids([berth_info.id])[0][1][2]

        return berth_info, term_fsm, ocean_berth_path

    def _select_berth_tug_rendezvous(self, vessel_path, vessel_info, vessel_position):
        """
            Selects an available berth that can serve the target vessel
        """
        berths_info = self._berths_for_vessel(vessel_info)

        for berth_info in berths_info:
            try:
                tug_rv_berth_paths = self.path_finder.tug_rendezvous_berth_paths(
                    final_section=berth_info.section,
                    berth_id=berth_info.id)

                ocean_tug_rv_paths, tug_rendezvous_id = self.path_finder.ocean_tug_rendezvous_paths(
                    vessel_position=vessel_position.lonlat,
                    final_section=berth_info.section)

                if len(tug_rv_berth_paths) != 0 and len(ocean_tug_rv_paths) != 0:
                    return berth_info, random.choice(ocean_tug_rv_paths), random.choice(tug_rv_berth_paths), \
                           tug_rendezvous_id
            except:
                pass

        return None, None, None, None

    def _select_berth_tug_rendezvous_pilot_rendezvous(self, vessel_path, vessel_info, vessel_position):
        """
            Selects an available berth that can serve the target vessel
        """
        berths_info = self._berths_for_vessel(vessel_info)

        for berth_info in berths_info:
            try:
                tug_rv_berth_paths, tug_rv_id = self.path_finder.tug_rendezvous_berth_paths(
                    final_section=berth_info.section,
                    berth_id=berth_info.id)

                ocean_pilot_rv_paths, pilot_rv_id = self.path_finder.ocean_pilot_rendezvous_paths(
                    vessel_position=vessel_position.lonlat,
                    vessel_class=vessel_info.vessel_class)

                pilot_rv_tug_rv_paths = self.path_finder.pilot_rendezvous_tug_rendezvous_paths(
                    pilot_rv_id=pilot_rv_id,
                    tug_rv_id=tug_rv_id)

                if len(tug_rv_berth_paths) != 0 and len(pilot_rv_tug_rv_paths) != 0 \
                        and len(ocean_pilot_rv_paths) != 0:
                    return berth_info, random.choice(ocean_pilot_rv_paths), random.choice(pilot_rv_tug_rv_paths), \
                           random.choice(tug_rv_berth_paths), tug_rv_id, pilot_rv_id
            except:
                pass

        return None, None, None, None, None, None

    def _select_berth_pilot_rendezvous(self, vessel_path, vessel_info, vessel_position):
        """
            Selects an available berth that can serve the target vessel
        """
        berths_info = self._berths_for_vessel(vessel_info)

        for berth_info in berths_info:
            try:
                pilot_rv_berth_paths = self.path_finder.pilot_rendezvous_berth_paths(
                    vessel_class=vessel_info.vessel_class,
                    berth_id=berth_info.id)

                ocean_pilot_rv_paths, pilot_rendezvous_id = self.path_finder.ocean_pilot_rendezvous_paths(
                    vessel_position=vessel_position.lonlat,
                    vessel_class=vessel_info.vessel_class)

                if len(pilot_rv_berth_paths) != 0 and len(ocean_pilot_rv_paths) != 0:
                    return berth_info, random.choice(ocean_pilot_rv_paths), random.choice(pilot_rv_berth_paths),\
                           pilot_rendezvous_id
            except NoPathException as _:
                pass

        return None, None, None, None

    def _select_and_route_to_anchorage(self, ent, vessel_path, pos):
        """
            Selects a suitable anchorage for the target vessel
        """
        selected_anchorage = self.anchorage_designator(self.world, ent)
        _, (anchorage_info, anchorage_fsm, anchorage_shape) = selected_anchorage

        ocean_anchorage_path = self.path_finder.anchorage_path(
            pos.lonlat,
            anchorage_shape.centroid)
        vessel_path.set_path(ocean_anchorage_path)

        return anchorage_info.name, anchorage_fsm

    def _route_to_spawn(self, berth_id, vessel_position, vessel_info):
        """
            Computes a route from a berth to the ocean
        """
        berths = BerthList(world=self.world).filter_by_ids([berth_id])
        berths_info = [b[1][1] for b in berths]

        ocean_berth_path, _ = self._select_path(berths_info, None, vessel_info) 

        return self.path_finder.reverse_path(ocean_berth_path)
