from components import Course, PilotInfo, Position
from processors.rendering.base_renderer import BaseRenderer
from processors.utils import convert_course_angle, lonlat_array_to_screen


class PilotsRenderer(BaseRenderer):
    """Renders pilots on a Simulation Layer using geoplotlib"""

    PILOT_COLOR = [143, 95, 183]

    def _process(self, dt):
        self.painter.set_color(self.PILOT_COLOR)

        for _, (pos, course, _) in self.world.get_components(
            Position, Course, PilotInfo
        ):
            if not pos.is_valid():
                # Skip pilots not yet fully created
                continue

            x, y = lonlat_array_to_screen(self.proj, pos.lonlat)
            self.paint_vessel(self.painter, x, y, convert_course_angle(course.course))
