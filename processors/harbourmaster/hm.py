import copy

from components import TugInfo, Velocity, VesselInfo
from components.fsm import VesselStateMachine
from environment import RunInfo
from environment.messaging import MessageBroker
from environment.messaging.types import TugMessageType, VesselMessageType
from environment.navigation import PathFinder
from log.vessel import VesselEvent
from processors.base_processor import BaseProcessor


class HarbourMasterProcessor(BaseProcessor):
    """Class that simulates the behaviour of the Harbour Master in a port.
    Receives requests from vessels and handles different situations.
    """

    def __init__(self, world, vessel_strategy, tug_strategy=None, logger=None):
        """Initializes a HarbourMasterProcessor

        :param world: Esper simulation world.
        :param vessel_strategy: VesselStrategy instance that send and handles requests with the harbour master
        :param tug_strategy: TugStrategy instance that handles tug requests
        :param logger: event logger to which sections events will be logged
        """
        self.world = world
        self.message_broker = MessageBroker.get_instance()
        self.path_finder = PathFinder.get_instance()
        self.logger = logger

        self.vessel_strategy = vessel_strategy
        self.tug_strategy = tug_strategy

        # Register the handlers for messages from different senders
        self.messsage_handlers = {
            VesselMessageType: self._handle_vessel_message,
            TugMessageType: self._handle_tug_message,
        }

    def _process(self, dt):
        pending_messages = self.message_broker.get_messages("harbour-master")

        for message in pending_messages:
            entity_id = message.sender_entity_id

            self.messsage_handlers[type(message.message)](message, entity_id)
            self.message_broker.remove_message(
                message_id=message.id, destination_queue="harbour-master"
            )

    def _handle_vessel_message(self, message, entity_id):
        if message.message.is_section_message():
            vessel_info = self.world.component_for_entity(entity_id, VesselInfo)
            self._handle_section_crossing(message, entity_id, vessel_info)
        else:
            vessel_info = self.world.component_for_entity(entity_id, VesselInfo)
            self.vessel_strategy.handle(message, entity_id, vessel_info)

    def _handle_tug_message(self, message, entity_id):
        assert self.tug_strategy is not None, (
            "It seems you have tugboats in the simulation but you have not defined "
            "a tugboat strategy. Please define it and pass it into this object."
        )

        tug_info = self.world.component_for_entity(entity_id, TugInfo)
        self.tug_strategy.handle(message, entity_id, tug_info)

    def _handle_section_crossing(self, message, entity_id, vessel_info):
        self._log_section_event(message, entity_id, vessel_info)

    def _log_section_event(self, message, entity_id, vessel_info):
        if self.logger is None:
            return

        from_section, to_section = message.data["from"], message.data["to"]
        fsm = self.world.component_for_entity(entity_id, VesselStateMachine)
        velocity = self.world.component_for_entity(entity_id, Velocity)

        event = VesselEvent(
            f"{message.message.value} ({from_section.name} → {to_section.name})",
            copy.deepcopy(vessel_info),
            copy.deepcopy(velocity),
            copy.deepcopy(fsm.pilot),
            copy.deepcopy(fsm.tugboats),
            fsm.destination_berth_id,
            fsm.destination_anchorage_id,
            RunInfo.get_instance().timestamp(),
        )

        self.logger.log_event(entity_id, vessel_info, event)
