from processors.rendering.base_renderer import BaseRenderer
from processors.rendering.operations import OperationsRenderer
from processors.utils import lonlat_array_to_screen

from environment.queries import BerthList
from components import BerthInfo


class BerthRenderer(BaseRenderer):
    """Renders berths on a Simulation Layer using geoplotlib's package"""
    CIRCLE_RADIUS = 3

    def _process(self, dt):
        for ent, (pos, berth_info, _) in BerthList(world=self.world):
            self.painter.set_color(berth_info.get_color())
            x, y = lonlat_array_to_screen(self.proj, pos.lonlat)
            self._paint_berth(self.painter, x, y)
            self._paint_on_mouse_hover(self.painter, x, y, self.mouse_x, self.mouse_y, ent, berth_info.name)
            if ent == OperationsRenderer.hover['ent']:
                # Update the top-left message box for the currently tracked vessel entity
                self._update_vessel_message_box(ent)

    def _update_vessel_message_box(self, ent):
        info = self.world.component_for_entity(ent, BerthInfo)
        OperationsRenderer.hover['message'] = [
                f'{info.name} ({ent}) | id: {info.id}',
                f'max_quay_length: {info.max_quay_length}',
                f'max_depth: {info.max_depth}',
                f'allowed content type: {info.allowed_vessel_content_type().name}']

    def _paint_berth(self, painter, x, y):
        painter.circle_filled(x, y, self.CIRCLE_RADIUS)

    def _paint_on_mouse_hover(self, painter, x, y, mouse_x, mouse_y, ent, name):
        if self.mouse_hovers(x, y):
            # Show name on mouse hover
            painter.labels(
                        [x],
                        [y],
                        [str(name)],
                        font_size=14,
                        anchor_x='left',
                        anchor_y='top')
            OperationsRenderer.hover['ent'] = ent
            self._update_vessel_message_box(ent)