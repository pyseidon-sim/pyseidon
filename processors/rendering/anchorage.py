import numpy as np

from environment.queries import AnchorageList
from processors.rendering.base_renderer import BaseRenderer


class AnchorageRenderer(BaseRenderer):
    """Renders anchorages on a Simulation Layer using geoplotlib's package"""

    ANCHORAGE_COLOR = [52, 152, 219, 137]
    ANCHORAGE_LABEL_COLOR = [0, 0, 0, 255]

    def _process(self, dt):
        for _, [anchorage_info, anchorage_fsm, anchorage_shape] in AnchorageList(
            world=self.world
        ):
            self.paint_polygon(
                self.painter, anchorage_shape.polygon, self.ANCHORAGE_COLOR
            )

            center = np.array(anchorage_shape.centroid)
            x, y = self.proj.lonlat_to_screen(center[0], center[1])

            if self.mouse_hovers(x, y):
                self._show_label(x, y, self.mouse_x, self.mouse_y, anchorage_info.name)

    def _show_label(self, x, y, mouse_x, mouse_y, name):
        self.painter.set_color(self.ANCHORAGE_LABEL_COLOR)
        self.painter.labels(
            [x], [y], [str(name)], font_size=14, anchor_x="left", anchor_y="top"
        )
