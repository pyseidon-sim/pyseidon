from collections import defaultdict

import numpy as np

from components import AnchorageInfo, TugInfo
from components.fsm.anchorages import AnchorageStateMachine
from components.fsm.berth import BerthStateMachine
from components.fsm.pilot import PilotStateMachine
from components.fsm.states import BerthState, PilotState, TugState
from components.fsm.tug import TugStateMachine
from processors.rendering.base_renderer import BaseRenderer
from processors.utils import lonlat_array_to_screen


class OperationsRenderer(BaseRenderer):
    """Renders berth, anchorage and tugboats occupancy labels."""

    def __init__(self, tug_companies=None):
        self.tug_companies = tug_companies

    # Holds the message displayed at the top left corner.
    # The `message` field contains a message split in
    # x lines (one line per array element)
    hover = {"ent": -1, "message": ["Hover over a vessel or berth to see details"]}

    operational = {"message": [""]}

    def _process(self, dt):
        self.painter.set_color([0, 0, 0])

        self._render_hover_message(self.proj, self.painter)

        self._update_operations_message()
        self._render_operations_message(self.proj, self.painter)

    def _render_hover_message(self, proj, painter):
        top_left_corner = np.array([proj.bbox().west, proj.bbox().north])
        tl_x, tl_y = lonlat_array_to_screen(proj, top_left_corner)

        for i, message in enumerate(OperationsRenderer.hover["message"]):
            painter.labels(
                [tl_x + 5],
                [tl_y - (25 * i)],
                [message],
                font_size=14,
                anchor_x="left",
                anchor_y="top",
            )

    def _update_operations_message(self):
        occupied_berths, num_berths = self._get_busy_berths_count()
        occupied_pilots, num_pilots = self._get_busy_pilots_count()

        anchorages_statuses = self._get_anchorage_occupancy_messages()

        OperationsRenderer.operational["message"] = []
        OperationsRenderer.operational["message"].append("Anchorage occupancy: ")
        OperationsRenderer.operational["message"].extend(anchorages_statuses)

        OperationsRenderer.operational["message"].append(
            f"Berth occupancy: {occupied_berths}/{num_berths}"
        )
        OperationsRenderer.operational["message"].append(
            f"Pilot vessel occupancy: {occupied_pilots}/{num_pilots}"
        )

        if self.tug_companies is not None:
            info = self._get_busy_tugs_count_by_company()

            for company in self.tug_companies:
                OperationsRenderer.operational["message"].append(
                    f"{company} "
                    f"tugboat occupancy: "
                    f"{info[company]['busy']}/{info[company]['num']}"
                )
        else:
            occupied_tugs, num_tugs = self._get_busy_tugs_count()
            OperationsRenderer.operational["message"].append(
                f"Tugboat occupancy: {occupied_tugs}/{num_tugs}"
            )

        # Reverse the messages to anchorages are rendered first
        # (rendering is bottom to top for operational statistics)
        OperationsRenderer.operational["message"].reverse()

    def _get_anchorage_occupancy_messages(self):
        anchorages = self.world.get_components(AnchorageInfo)
        anchorages_statuses = []

        for id, anchorage in anchorages:
            anchorage_fsm = self.world.component_for_entity(id, AnchorageStateMachine)
            anchorages_statuses.append(
                f"{anchorage[0].name}: {anchorage_fsm.occupancy()}"
            )

        return anchorages_statuses

    def _get_busy_berths_count(self):
        berths = self.world.get_components(BerthStateMachine)
        occupied_berths = 0

        for id, berth in berths:
            berth_fsm = berth[0]

            if (
                berth_fsm.current() == BerthState.SERVING_VESSEL
                or berth_fsm.current() == BerthState.WAITING_FOR_VESSEL
            ):
                occupied_berths += 1

        return occupied_berths, len(berths)

    def _get_busy_pilots_count(self):
        pilots = self.world.get_components(PilotStateMachine)
        occupied_pilots = 0

        for id, pilot in pilots:
            pilot_fsm = pilot[0]

            if pilot_fsm.current() in PilotState.busy_states():
                occupied_pilots += 1

        return occupied_pilots, len(pilots)

    def _get_busy_tugs_count(self):
        tugs = self.world.get_components(TugStateMachine)
        occupied_tugs = 0

        for id, tug in tugs:
            tug_fsm = tug[0]

            if tug_fsm.current() in TugState.busy_states():
                occupied_tugs += 1

        return occupied_tugs, len(tugs)

    def _get_busy_tugs_count_by_company(self):
        info = defaultdict(lambda: defaultdict(int))

        tugs = self.world.get_components(TugStateMachine)

        for id, tug in tugs:
            tug_fsm = tug[0]

            tug_info = self.world.component_for_entity(id, TugInfo)

            if tug_fsm.current() in TugState.busy_states():
                info[tug_info.company_name]["busy"] += 1

            info[tug_info.company_name]["num"] += 1

        return info

    def _render_operations_message(self, proj, painter):
        bottom_left_corner = np.array([proj.bbox().west, proj.bbox().south])
        bl_x, bl_y = lonlat_array_to_screen(proj, bottom_left_corner)

        for i, message in enumerate(OperationsRenderer.operational["message"]):
            painter.labels(
                [bl_x + 5],
                [bl_y + (25 * i)],
                [message],
                font_size=14,
                anchor_x="left",
                anchor_y="bottom",
            )
