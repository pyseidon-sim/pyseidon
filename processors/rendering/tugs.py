from processors.utils import lonlat_array_to_screen, convert_course_angle
from components import Position, TugInfo, Course
from components.fsm import TugStateMachine
from components.fsm.states import TugState
from processors.rendering.base_renderer import BaseRenderer


class TugsRenderer(BaseRenderer):
    """Renders tugboats on a Simulation Layer using geoplotlib"""
    TUG_COLOR = [255, 204, 0]
    BROKEN_COLOR = [231, 76, 60]
    CIRCLE_RADIUS = 3.0

    def _process(self, dt):
        self.painter.set_color(self.TUG_COLOR)
        
        for tug, (pos, course, _, fsm) in self.world.get_components(Position, Course, TugInfo, TugStateMachine):
            if not pos.is_valid():
                # Skip vessels not yet fully created
                continue

            x, y = lonlat_array_to_screen(self.proj, pos.lonlat)
            self.paint_vessel(self.painter, x, y, convert_course_angle(course.course))

            if fsm.current() == TugState.BROKEN:
                # TODO: circle should be on top of triangle
                self.painter.set_color(self.BROKEN_COLOR)
                self.painter.circle_filled(x, y, self.CIRCLE_RADIUS)
                self.painter.set_color(self.TUG_COLOR)
