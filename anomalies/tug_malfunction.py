import random
import copy

from anomalies import BaseVesselAnomaly

from components import VesselPath, Position
from components.fsm import VesselStateMachine, TugStateMachine
from components.fsm.states import TugState, VesselState

from environment.queries import WaitingLocationList
from components.location_info import LocationType

from utils.timer import SimulationTimer, TimerScheduler

from exceptions import NotEnoughAvailableTugsException, NoPathException
from environment.queries import berth_info_by_id

from shapely.geometry import Point


class TugMalfunctionAnomaly(BaseVesselAnomaly):
    """Class that defines the logic of a tug malfunction anomaly."""

    def __init__(self,
                 world,
                 path_finder,
                 break_percentage_idle,
                 break_percentage_busy,
                 tug_designator,
                 deattach_location_polygon,
                 broken_tug_time_sampler=None,
                 default_malfunction_duration=18000):
        """
            Input:
                :param world: Esper world object
                :param path_finder: reference to a PathFinder singleton object
                :param break_percentage_idle: probability of the tugboats malfunctioning
                    in an idle state (must be 0 <= x <= 1)
                :param break_percentage_busy: probability of the tugboats malfunctioning
                    in a busy state (must be 0 <= x <= 1)
                :param tug_designator: a function that uses some logic to pick and return
                    a list of tugboat ids
                :param deattach_location_polygon: a shapely.geometry Polygon object that
                    defines an area where the tugboats should deattach from the tugged vessel
                :param broken_tug_time_sampler: a function that samples a time in seconds for which
                    the tugboat should be broken for
                :param default_malfunction_duration: an amount of time in seconds for which the
                    tugboat should be broken for
        """

        self.world = world
        self.path_finder = path_finder
        self.break_percentage_idle = break_percentage_idle
        self.break_percentage_busy = break_percentage_busy
        self.tug_designator = tug_designator
        self.broken_tug_time_sampler = broken_tug_time_sampler
        self.default_malfunction_duration = default_malfunction_duration
        self.deattach_location_polygon = deattach_location_polygon

    def check_for_anomaly(self, entity_id):
        """Performs a check whether the tug is supposed to malfunction.

            Check if at this moment in time the tug malfunctions.
            This is decided by generating a random number between 0 and 1
            and checking against the fixed probabilities of malfunction.
        """
        tug_fsm = self.world.component_for_entity(entity_id, TugStateMachine)
        state = tug_fsm.current()

        if state not in TugState.breakable_states():
            return False

        if state in TugState.busy_states():
            if random.random() <= self.break_percentage_busy:
                return True
        else:
            if random.random() <= self.break_percentage_idle:
                return True

        return False

    def execute_anomaly(self, entity_id):
        """Executes the tugboat malfunction anomaly.

            Simulate a tugboat malfunction. Schedule an amount of time
            this tug will be unavailable. Remove this tug from the assigned tugboats
            of the vessel being tugged and assign a new tugboat. This tugboat enters a
            state TugState.BROKEN.
        """
        tug_fsm = self.world.component_for_entity(entity_id, TugStateMachine)
        tug_path = self.world.component_for_entity(entity_id, VesselPath)
        tug_position = self.world.component_for_entity(entity_id, Position)

        # Schedule an amount of time for which the tug will be broken down.
        # After fixing the tug will autonomously move back to a waiting location
        complete_processing_timer = SimulationTimer(
            duration=self._get_malfunction_duration(),
            target_function=self._redirect_fixed_tug_to_waiting_location,
            tug_fsm=tug_fsm,
            tug_path=tug_path,
            tug_position=tug_position)

        TimerScheduler.get_instance().schedule(complete_processing_timer)

        # If the tug was booked/operating find a replacement
        vessel_id = tug_fsm.current_target_vessel_id()
        vessel_path = None

        if vessel_id:
            vessel_fsm = self.world.component_for_entity(vessel_id, VesselStateMachine)

            if vessel_fsm.current() == VesselState.LEAVING:
                # Used to retain the same spawn path to return to the waiting location
                vessel_path = copy.deepcopy(self.world.component_for_entity(vessel_id, VesselPath).path)

            self._replace_tug(vessel_id, tug_fsm, entity_id)

        tug_fsm.break_down(previous_vessel_path=vessel_path)

    def _replace_tug(self, vessel_id, tug_fsm, tug_id):
        """Replaces a malfunctioned tugboat with a new one.

            Remove the tugboat from the vessel being tugged,
            stop the vessel and other tugboats as they cannot carry on,
            try to assign a new tugboat that will take over the
            assignment of the broken tugboat.

            Input:
                :param vessel_id: vessel entity id
                :param tug_fsm: tugboat finite state machine object
                :param tug_id: tugboat entity id
        """

        # Retrieve the fsm of the vessel being tugged
        vessel_fsm = self.world.component_for_entity(vessel_id, VesselStateMachine)
        tug_rv_id = self._get_rendezvous_id(tug_fsm, vessel_fsm)
        tug_pos = self.world.component_for_entity(tug_id, Position)

        # Detach the old tugboat and stop the vessel if it's currently being tugged
        vessel_fsm.tugboats.remove(tug_id)
        if vessel_fsm.current() in [VesselState.GOING_TO_BERTH, VesselState.LEAVING]:
            vessel_fsm.tug_malfunction()

        # Update all other tugging tugboats statuses to waiting at malfunction location
        for tug_id in vessel_fsm.tugboats:
            tug_fsm = self.world.component_for_entity(tug_id, TugStateMachine)

            if tug_fsm.current() in [TugState.TUGGING_IN, TugState.TUGGING_OUT]:
                tug_fsm.wait_at_malfunction_location()

        self._assign_new_tug(vessel_id, vessel_fsm, tug_fsm.destination_berth_id, tug_rv_id, tug_pos)

    def _get_rendezvous_id(self, tug_fsm, vessel_fsm):
        if tug_fsm.destination_rendezvous_id is not None:
            return tug_fsm.destination_rendezvous_id

        return vessel_fsm.tugs_rendezvous_id

    def _get_malfunction_duration(self):
        if self.broken_tug_time_sampler:
            return self.broken_tug_time_sampler()
        else:
            return self.default_malfunction_duration

    def _assign_new_tug(self, vessel_id, vessel_fsm, berth_id, old_tug_rendezvous_id, old_tug_pos):
        """Assigns a new tug to a vessel.

            A function that tries assigning a new tugboat to a vessel whose tugboat
            has broken down. If it succeeds in finding a replacement, it tells the new
            tug to go to the place where the malfunctioning tug has broken down or
            go to a tug rendezvous location if it has not yet reached it and started tugging a vessel.

            Input:
                :param vessel_id: vessel entity id
                :param vessel_fsm: vessel finite state machine object
                :param berth_id: berth entity id
                :param old_tug_rendezvous_id: the entity id of a tugboat which has malfunctioned
                :param old_tug_pos: the position object of a tugboat which has malfunctioned
        """

        # Check for new tugboats, if they are not available at the moment,
        # schedule a timer and check again in the designated time (greatly reduces amount of computations)
        try:
            potential_tugs = self.tug_designator(vessel_id)
        except NotEnoughAvailableTugsException:
            self._schedule_assignment_timer(vessel_id, vessel_fsm, berth_id, old_tug_rendezvous_id, old_tug_pos)
            return

        assigned = False
        for new_tug_entity_id in potential_tugs:
            try:
                new_tug_fsm = self.world.component_for_entity(new_tug_entity_id, TugStateMachine)
                new_tug_position = self.world.component_for
                new_tug_path = self.world.component_for_entity(new_tug_entity_id, VesselPath)

                vessel_pos = self.world.component_for_entity(vessel_id, Position)
                

                if vessel_fsm.state_before_failure == VesselState.GOING_TO_BERTH:
                    # FIXME: In theory, tug_fsm.destination_berth_id (berth_id) == vessel_fsm.destination_berth_id.
                    #  In practice that is not the case, and putting berth_id breaks it
                    berth_id = vessel_fsm.destination_berth_id
                    berth_info = berth_info_by_id(self.world, berth_id)

                    tug_wl_destination_path = self.path_finder.tugs_berth_waiting_location_path(
                        tug_position=None,
                        berth_info=berth_info,
                        waiting_location_id=new_tug_fsm.waiting_location_id)

                    # Stop the trace at the vessel's new position
                    self.path_finder.trim_trace_to_current_position(
                        vessel_position=vessel_pos.lonlat,
                        trace=tug_wl_destination_path)

                    tug_wl_destination_path = self.path_finder.reverse_path(tug_wl_destination_path)
                    self.path_finder.prefix_path(new_tug_position.lonlat, tug_wl_destination_path)

                    new_tug_fsm.go_to_malfunction_location(vessel_id, berth_id)
                elif vessel_fsm.state_before_failure == VesselState.LEAVING:
                    berth_info = berth_info_by_id(self.world, berth_id)

                    if self.deattach_location_polygon.contains(Point(old_tug_pos.lon(), old_tug_pos.lat())):
                        # The vessel is already in the deattach location, don't schedule a new tug
                        return
                    else:
                        # The vessel is moving out, schedule a new vessel go to the
                        # berth and use the spawn path from there
                        tug_wl_destination_path = self.path_finder.tugs_berth_waiting_location_path(
                            tug_position=None,
                            berth_info=berth_info,
                            waiting_location_id=new_tug_fsm.waiting_location_id)
                        tug_wl_destination_path = self.path_finder.reverse_path(tug_wl_destination_path)
                        
                        # Copy the spawn path of the vessel and cut it up to the vessel's position
                        vessel_spawn_path = copy.deepcopy(self.world.component_for_entity(vessel_id, VesselPath).path)
                        vessel_spawn_path = self.path_finder.reverse_path(vessel_spawn_path)

                        self.path_finder.trim_trace_to_current_position(
                            vessel_position=vessel_pos.lonlat,
                            trace=vessel_spawn_path)

                        vessel_spawn_path = self.path_finder.reverse_path(vessel_spawn_path)

                        tug_wl_destination_path = self.path_finder.merge_paths(tug_wl_destination_path, vessel_spawn_path)
                        
                        new_tug_fsm.go_to_malfunction_location(vessel_id, berth_id)
                elif vessel_fsm.state_before_failure == VesselState.WAITING_FOR_TUGS_PILOTS_BERTH:
                    berth_info = berth_info_by_id(self.world, berth_id)

                    # TODO: Should we choose the same RV - berth path as the vessel?
                    tug_wl_destination_path = self.path_finder.tugs_berth_waiting_location_path(
                        tug_position=None,
                        berth_info=berth_info,
                        waiting_location_id=new_tug_fsm.waiting_location_id)

                    tug_wl_destination_path = self.path_finder.reverse_path(tug_wl_destination_path)
                    self.path_finder.prefix_path(new_tug_position.lonlat, tug_wl_destination_path)

                    new_tug_fsm.go_to_berth(vessel_id, berth_id)
                else:
                    tug_wl_destination_path = self.path_finder.tugs_waiting_location_rendezvous_path(
                        tug_position=new_tug_position.lonlat,
                        waiting_location_id=new_tug_fsm.waiting_location_id,
                        rendezvous_id=old_tug_rendezvous_id)

                    new_tug_fsm.go_to_rendezvous(vessel_id, old_tug_rendezvous_id)
                
                if vessel_fsm.tugboats is None:
                    vessel_fsm.tugboats = []
                vessel_fsm.tugboats.append(new_tug_entity_id)
                new_tug_path.set_path(tug_wl_destination_path)

                assigned = True
                break
            except NoPathException:
                # Schedule a timer here as well
                continue

        if not assigned:
            self._schedule_assignment_timer(vessel_id, vessel_fsm, berth_id, old_tug_rendezvous_id, old_tug_pos)

    def _schedule_assignment_timer(self, vessel_id, vessel_fsm, berth_id, old_tug_rendezvous_id, old_tug_pos):
        """Schedule a timer for self._assign_new_tug method.

            Schedule a timer that will try assigning a new tugboat to a vessel after
            1800 simulation seconds (30 simulation minutes). This is done to reduce
            the computations.
        """

        tug_assignment_timer = SimulationTimer(
            duration=1800,
            target_function=self._assign_new_tug,
            vessel_id=vessel_id,
            vessel_fsm=vessel_fsm,
            berth_id=berth_id,
            old_tug_rendezvous_id=old_tug_rendezvous_id,
            old_tug_pos=old_tug_pos)

        TimerScheduler.get_instance().schedule(tug_assignment_timer)

    def _redirect_fixed_tug_to_waiting_location(self, tug_fsm, tug_path, tug_position):
        """Orders the now fixed tug to go to the waiting location and await new assignments."""

        # If a vessel has not been assigned destination vessel id, it has broken down in the waiting location
        if tug_fsm.state_before_failure == TugState.IDLE:
            tug_fsm.get_fixed_idle()
            return

        # If the destination path exists, the tug has broken down whilst on an assignment
        if tug_fsm.state_before_failure in [TugState.TUGGING_IN, TugState.GOING_TO_BERTH]:
            berth_info = berth_info_by_id(self.world, tug_fsm.destination_berth_id)

            tug_wl_destination_path, waiting_location_id = self._find_berth_waiting_location_path(tug_position, berth_info)

            if tug_wl_destination_path is None:
                raise Exception(f"No path from berth {tug_fsm.destination_berth_id} to any tugboat waiting location")
            else:
                tug_fsm.waiting_location_id = waiting_location_id
        elif tug_fsm.state_before_failure in [TugState.GOING_TO_RENDEZVOUS, TugState.GOING_TO_WAITING_LOCATION]:
            tug_wl_destination_path = self.path_finder.tugs_waiting_location_rendezvous_path(
                tug_position=None,
                waiting_location_id=tug_fsm.waiting_location_id,
                rendezvous_id=tug_fsm.destination_rendezvous_id)

            tug_wl_destination_path = self.path_finder.reverse_path(tug_wl_destination_path)
        elif tug_fsm.state_before_failure in [TugState.TUGGING_OUT]:
            # Create a path to the old berth from the current position
            old_outgoing_path = copy.deepcopy(tug_fsm.previous_vessel_path)
            old_outgoing_path = self.path_finder.reverse_path(old_outgoing_path)
            
            # Find a berth -> waiting location path
            berth_info = berth_info_by_id(self.world, tug_fsm.destination_berth_id)
            berth_wl_path, waiting_location_id = self._find_berth_waiting_location_path(tug_position, berth_info)

            if berth_wl_path is None:
                raise Exception(f"No path from berth {tug_fsm.destination_berth_id} to any tugboat waiting location")
            else:
                tug_wl_destination_path = self.path_finder.merge_paths(old_outgoing_path, berth_wl_path)
                tug_fsm.waiting_location_id = waiting_location_id
        else:
            raise Exception(f"Tug fsm was in an unhandled state: {tug_fsm.state_before_failure}")

        tug_wl_destination_path = self.path_finder.trim_trace_to_current_position(
            vessel_position=tug_position.lonlat,
            trace=tug_wl_destination_path)

        tug_path.set_path(tug_wl_destination_path)

        # Redirect the tug to its waiting location
        tug_fsm.get_fixed_busy()

    def _find_berth_waiting_location_path(self, tug_position, berth_info):
        # Extract the waiting location IDs
        tug_waiting_locations = WaitingLocationList(world=self.world).filter_by_location_type(LocationType.TUGBOATS_STORAGE)
        tug_waiting_locations = [location[1][0].id for location in list(tug_waiting_locations)]

        # Redirect the tug to the first connected waiting location
        for waiting_location_id in tug_waiting_locations:
            try:
                tug_wl_destination_path = self.path_finder.tugs_berth_waiting_location_path(
                    tug_position=tug_position.lonlat,
                    berth_info=berth_info,
                    waiting_location_id=waiting_location_id)
                
                return tug_wl_destination_path, waiting_location_id
            except NoPathException:
                continue

        return None, None
