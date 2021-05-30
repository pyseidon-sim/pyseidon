import random

from processors.base_processor import BaseProcessor

from components.fsm.states import VesselState
from components import Velocity, VesselInfo

from environment.queries import fetch_vessels

from exceptions import NoPathException, PathTerminatedException

from environment.messaging.types import VesselMessageType
from environment.messaging import MessageBroker, SimulationMessage

from processors.utils import target_reached


class VesselGoalFormulatorProcessor(BaseProcessor):
    """
        Handles the goal formulation of a vessel, such
        as retrieving the next destination and checking
        if a target is reached. Communicates with the
        HarbourMasterProcessor
    """
    MIN_SPEED_THRESHOLD = 3
    RESOURCE_CHECK_FRAME_DELTA = 20

    def __init__(self, vessel_base_class):
        """Initializes a goal formulator

        Arguments:
        vessel_base_class -- the Python base class of vessel classes
        """
        self.message_broker = MessageBroker.get_instance()
        self.message_per_state = {
            VesselState.INCOMING: VesselMessageType.REQUEST_ARRIVAL_CLEARANCE,
            VesselState.GOING_TO_ANCHORAGE: VesselMessageType.GOING_TO_ANCHORAGE,
            VesselState.WAITING_AT_ANCHORAGE: VesselMessageType.WAITING_AT_ANCHORAGE,
            VesselState.GOING_TO_BERTH: VesselMessageType.DOCKED_AT_TERMINAL,
            VesselState.GOING_TO_TUGS_RENDEZVOUS: VesselMessageType.WAITING_FOR_TUGS_AT_RENDEZVOUS,
            VesselState.GOING_TO_PILOT_RENDEZVOUS: VesselMessageType.WAITING_FOR_PILOT_AT_RENDEZVOUS,
            VesselState.WAITING_FOR_PILOTS_RENDEZVOUS: VesselMessageType.GO_TO_BERTH,
            VesselState.WAITING_FOR_TUGS_RENDEZVOUS: VesselMessageType.GO_TO_BERTH,
            VesselState.WAITING_FOR_TUGS_PILOTS_BERTH: VesselMessageType.DEPART,
            VesselState.WAITING_FOR_DEPARTURE_CLEARANCE: VesselMessageType.REQUEST_DEPARTURE_CLEARANCE,
            VesselState.LEAVING: VesselMessageType.DEPARTED,
            VesselState.TUG_MALFUNCTION: VesselMessageType.FIX_TUG
        }

        # The smaller the number, the more important some state is
        self.state_priorities = {
            VesselState.TUG_MALFUNCTION: 1,
            VesselState.WAITING_FOR_DEPARTURE_CLEARANCE: 2,
            VesselState.WAITING_AT_ANCHORAGE: 3,
            VesselState.GOING_TO_ANCHORAGE: 3,
            VesselState.LEAVING: 4,
            VesselState.WAITING_FOR_TUGS_PILOTS_BERTH: 4,
            VesselState.WAITING_FOR_TUGS_RENDEZVOUS: 4,
            VesselState.WAITING_FOR_PILOTS_RENDEZVOUS: 4,
            VesselState.GOING_TO_PILOT_RENDEZVOUS: 4,
            VesselState.GOING_TO_TUGS_RENDEZVOUS: 4,
            VesselState.GOING_TO_BERTH: 4,
            VesselState.INCOMING: 4,
            VesselState.SERVICING: 4,
            VesselState.SCHEDULED: 4,
            VesselState.LEFT: 5
        }

        # Taken from environment/queries/__init__.py
        self.vessel_fsm_index = 5

        self.vessel_base_class = vessel_base_class

    def _process(self, dt):
        vessels = fetch_vessels(self.world)
        # Sort by state and spawn time (smaller entity id means spawned earlier)
        vessels = sorted(vessels, key=lambda x: (self.state_priorities[x[1][self.vessel_fsm_index].current()], x[0]))

        for ent, (pos, frame_counter, _, vel, vessel_path, vessel_fsm, vessel_info) in vessels:
            current_state = vessel_fsm.current()
            # Do not formulate a goal/advance the path if the vessel's tug has broken down and its waiting for a new one
            if current_state == VesselState.TUG_MALFUNCTION:
                message = self.message_per_state[current_state]
                self._send_harbour_master_message(
                    ent=ent,
                    message=message)

                continue

            # Formulate a goal if none is set
            if not vessel_path.has_current_route() or target_reached(vessel_path, pos):
                self.formulate_goal(ent, vessel_path, vessel_fsm, vel, vessel_info)

            # Special case: if the vessel is going towards the anchorage
            # because there are not enough resources, we check every x
            # ticks if the resources are available to speed up the simulation
            if vessel_fsm.current() == VesselState.GOING_TO_ANCHORAGE:
                if frame_counter.get_count() >= self.RESOURCE_CHECK_FRAME_DELTA:
                    self._send_harbour_master_message(
                        ent=ent,
                        message=self.message_per_state[vessel_fsm.current()])

                    frame_counter.reset()
                else:
                    frame_counter.increase()

    def formulate_goal(self, ent, vessel_path, vessel_fsm, vel, vessel_info):
        """
            Retrieves the next node in path if a path exists, otherwise notifies the
            HM of its current status
        """
        try:
            _ = vessel_path.get_next_destination()

            current_section = vessel_path.get_current_section()
            next_section = vessel_path.get_next_section()

            # Check if we crossed a section
            if current_section.name != next_section.name:
                # We assume a crossing happens when the next node
                # in path belongs to a different section
                self._handle_section_crossing(
                    ent=ent,
                    from_section=current_section,
                    to_section=next_section)
        except (NoPathException, PathTerminatedException) as _:
            current_state = vessel_fsm.current()

            if current_state in self.message_per_state:
                message = self.message_per_state[current_state]

                self._send_harbour_master_message(
                    ent=ent,
                    message=message)
        finally:
            vessel_path.advance_path()

    def _handle_section_crossing(self, ent, from_section, to_section):
        data = {
            "from": from_section,
            "to": to_section
        }

        self._update_vessel_speed(to_section, ent)

        self.message_broker.send_message(
            SimulationMessage(
                sender=f"vessel:{ent}",
                destination="harbour-master",
                message=VesselMessageType.CHANGE_SECTION,
                data=data))

    def _update_vessel_speed(self, target_section, ent):
        velocity = self.world.component_for_entity(ent, Velocity)
        vessel_info = self.world.component_for_entity(ent, VesselInfo)

        vessel_class = self.vessel_base_class.get_vessel_class(
            vessel_info.length,
            vessel_info.actual_draught)

        speed_data = target_section.speeds_for_class(vessel_class)
        max_speed, min_speed = speed_data["max"], speed_data["min"]

        if min_speed < self.MIN_SPEED_THRESHOLD:
            min_speed = max_speed / 2

        new_speed = ((max_speed - min_speed) * random.random()) + min_speed
        velocity.velocity = new_speed

    def _send_harbour_master_message(self, ent, message):
        self.message_broker.send_message(
            SimulationMessage(
                sender=f"vessel:{ent}",
                destination="harbour-master",
                message=message))
