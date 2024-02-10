from components import (BerthInfo, Course, Position, Velocity, VesselInfo,
                        VesselPath)
from components.fsm import VesselStateMachine
from components.fsm.states import VesselState
from environment.queries import berth_info_by_id
from exceptions import NoPathException, PathTerminatedException
from processors.rendering.base_renderer import BaseRenderer
from processors.rendering.operations import OperationsRenderer
from processors.rendering.pilots import PilotsRenderer
from processors.utils import convert_course_angle, lonlat_array_to_screen


class VesselRenderer(BaseRenderer):
    """Renders vessels on a Simulation Layer using geoplotlib"""

    VESSEL_COLOR = [52, 152, 219]
    PILOT_COLOR = PilotsRenderer.PILOT_COLOR
    CIRCLE_RADIUS = 3

    def _process(self, dt):
        self.painter.set_color(self.VESSEL_COLOR)

        for vessel, (pos, course, vessel_info, fsm) in self.world.get_components(
            Position, Course, VesselInfo, VesselStateMachine
        ):
            if not pos.is_valid():
                # Skip vessels not yet fully created
                continue

            x, y = lonlat_array_to_screen(self.proj, pos.lonlat)

            if vessel == OperationsRenderer.hover["ent"]:
                # Update the top-left message box for the currently tracked vessel entity
                self._update_vessel_message_box(vessel)

            self.paint_vessel(self.painter, x, y, convert_course_angle(course.course))
            self._paint_pilot_on_vessel(self.painter, x, y, fsm)
            self._paint_on_mouse_hover(
                self.painter,
                x,
                y,
                self.mouse_x,
                self.mouse_y,
                vessel,
                vessel_info,
                pos,
                fsm,
            )

    def _paint_on_mouse_hover(
        self, painter, x, y, mouse_x, mouse_y, ent, vessel_info, pos, fsm
    ):
        if self.mouse_hovers(x, y):
            # Show mmsi on mouse hover
            painter.labels(
                [x],
                [y],
                [f"{vessel_info.name} ({ent})"],
                font_size=14,
                anchor_x="left",
                anchor_y="top",
            )

            OperationsRenderer.hover["ent"] = ent
            self._update_vessel_message_box(ent)

            history = pos.history()
            trace = lonlat_array_to_screen(self.proj, [history["lon"], history["lat"]])
            self._draw_vessel_trace(trace, self.painter)

    def _paint_pilot_on_vessel(self, painter, x, y, fsm):
        if fsm.pilot_boarded:
            painter.set_color(self.PILOT_COLOR)
            painter.circle_filled(x, y, self.CIRCLE_RADIUS)
            painter.set_color(self.VESSEL_COLOR)

    def _update_vessel_message_box(self, ent):
        fsm = self.world.component_for_entity(ent, VesselStateMachine)
        pos = self.world.component_for_entity(ent, Position)
        velocity = self.world.component_for_entity(ent, Velocity)
        vessel_info = self.world.component_for_entity(ent, VesselInfo)
        vessel_path = self.world.component_for_entity(ent, VesselPath)

        destination_id = ""

        if fsm.current() == VesselState.GOING_TO_BERTH:
            destination_id = fsm.destination_berth_id
        elif fsm.current() == VesselState.GOING_TO_PILOT_RENDEZVOUS:
            destination_id = fsm.pilot_rendezvous_id
        elif fsm.current() == VesselState.GOING_TO_TUGS_RENDEZVOUS:
            destination_id = fsm.tugs_rendezvous_id
        elif fsm.current() == VesselState.GOING_TO_ANCHORAGE:
            destination_id = fsm.destination_anchorage_id

        pilot_text = "yes" if vessel_info.pilot_required else "no"
        section_name = self._get_vessel_section_name(fsm, vessel_path).replace("_", " ")

        OperationsRenderer.hover["message"] = [
            f"{vessel_info.name} ({ent})",
            f"content type: {vessel_info.vessel_type.value}",
            f"vessel class: {vessel_info.vessel_class.value}",
            f"position: {pos.lonlat}",
            f"velocity: {velocity.velocity}",
            f"angle: {vessel_path.angle()}",
            f"section: {section_name}",
            f'state: {fsm.current().replace("_", " ")} {destination_id}',
            f"tugs needed: {vessel_info.number_of_tugboats}",
            f"pilot needed: {pilot_text}, boarded: {fsm.pilot_boarded}",
            f"destination berth: {fsm.destination_berth_id}",
        ]

    def _get_vessel_section_name(self, fsm, vessel_path):
        if fsm.current() == VesselState.SERVICING:
            berth_info = berth_info_by_id(self.world, fsm.destination_berth_id)
            return f"section {berth_info.section}"
        else:
            try:
                return vessel_path.get_current_section().name
            except (NoPathException, PathTerminatedException) as _:
                return ""

    def _draw_vessel_trace(self, trace, painter):
        painter.lines([trace[0][:-1]], [trace[1][:-1]], [trace[0][1:]], [trace[1][1:]])
