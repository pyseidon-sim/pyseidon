import json

from shapely.geometry import Polygon, Point

from environment.queries import WaitingLocationList
from environment.messaging.types import TugMessageType

from components import Position, VesselPath, LocationType, FrameCounter
from components.fsm import TugStateMachine, VesselStateMachine


class DefaultTugStrategy():
    """Strategy that handles tugboat requests"""
    RESOURCE_CHECK_FRAME_DELTA = 20

    def __init__(
            self,
            world,
            path_finder,
            deattach_polygon_filename,
            tug_malfunction_anomaly=None):
        self.world = world
        self.path_finder = path_finder
        self.deattach_polygon = self._load_polygon(deattach_polygon_filename)
        self.tug_malfunction_anomaly = tug_malfunction_anomaly

    def handle(self, message, entity_id, tug_info):
        """Handle incoming messages

           Args:

           :param message: message object
           :param entity_id: entity id of the vessel that sent the message
           :param tug_info: the message sender tug info
        """
        return {
            TugMessageType.TUGGING_IN: self.handle_tugging_in,
            TugMessageType.TUGGING_OUT: self.handle_tugging_out,
            TugMessageType.NOT_TUGGING: self.handle_not_tugging
        }[message.message](message, entity_id, tug_info)

    def handle_not_tugging(self, message, entity_id, vessel_info):
        if self._verify_tug_anomaly(entity_id):
            return

    def handle_tugging_in(self, message, entity_id, vessel_info):
        if self._verify_tug_anomaly(entity_id):
            return

    def handle_tugging_out(self, message, entity_id, vessel_info):
        if self._verify_tug_anomaly(entity_id):
            return

        tug_fsm = self.world.component_for_entity(entity_id, TugStateMachine)
        tug_path = self.world.component_for_entity(entity_id, VesselPath)
        tug_position = self.world.component_for_entity(entity_id, Position)
        frame_counter = self.world.component_for_entity(entity_id, FrameCounter)

        # Check if the tugboat should deattach and return to a
        # waiting location. Do this check only every x ticks to speed up the simulation
        if frame_counter.get_count() >= self.RESOURCE_CHECK_FRAME_DELTA:
            # Check if the current tug position is in the specified area to deattach
            if self.in_deattach_location(tug_position):
                # Tugs "de-attach" and go to waiting location
                _, (waiting_location_info, _) = WaitingLocationList(
                    world=self.world).filter_by_location_type(LocationType.TUGBOATS_STORAGE).random_location()
                waiting_location_path = self.path_finder.tugs_current_location_waiting_location_path(
                    tug_position=tug_position.lonlat,
                    waiting_location_id=waiting_location_info.id)

                tug_path.set_path(waiting_location_path)

                vessel_fsm = self.world.component_for_entity(tug_fsm.current_target_vessel_id(), VesselStateMachine)
                vessel_fsm.tugboats = None

                tug_fsm.done_tugging(waiting_location_info.id)

            frame_counter.reset()
        else:
            frame_counter.increase()

    def _verify_tug_anomaly(self, entity_id):
        if self.tug_malfunction_anomaly is not None:
            if self.tug_malfunction_anomaly.check_for_anomaly(entity_id):
                self.tug_malfunction_anomaly.execute_anomaly(entity_id)
                return True

        return False

    def in_deattach_location(self, tug_position):
        return self.deattach_polygon.contains(Point(tug_position.lon(), tug_position.lat()))

    def _load_polygon(self, filename):
        area_file = open(filename, "r")
        area_json = json.loads(area_file.read())
        area_file.close()

        return Polygon(
            area_json["features"][0]["geometry"]["coordinates"][0])
