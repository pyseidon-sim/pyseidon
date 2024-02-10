from components import BerthInfo, Position
from components.fsm import BerthStateMachine
from components.fsm.states import BerthState


class BerthList:
    """Class that handles the retrieval of Berth entities with different sorting methods."""

    def __init__(self, world=None, data=None):
        if world is None and data is None:
            raise ValueError("Either a world or an array must be given")

        self.index = 0

        if data is None:
            self.world = world
            self.berths = world.get_components(Position, BerthInfo, BerthStateMachine)
        else:
            self.berths = data

    def len(self):
        return len(self.berths)

    def __iter__(self):
        return self

    def __getitem__(self, index):
        return self.berths[index]

    def __next__(self):
        if self.index >= len(self.berths):
            raise StopIteration

        berth = self.berths[self.index]
        self.index += 1

        return berth

    def filter_by_available(self, available: BerthState):
        if available is None:
            raise ValueError("Availability must be non null!")

        available_berths = []

        for d, (pos, berth_info, fsm) in self.berths:
            if fsm.current() == available:
                available_berths.append([d, (pos, berth_info, fsm)])

        return BerthList(data=available_berths)

    def filter_by_vessel_types(self, vessel_types):
        if vessel_types is None:
            raise ValueError("Vessel types must be a list")

        allowed_berths = []

        for d, (pos, berth_info, fsm) in self.berths:
            if berth_info.allowed_vessel_content_type() in vessel_types:
                allowed_berths.append([d, (pos, berth_info, fsm)])

        return BerthList(data=allowed_berths)

    def filter_by_ids(self, ids):
        if ids is None:
            raise ValueError("Ids must be a list")

        if len(ids) == 0:
            return BerthList(data=[])

        out_berths = []

        for d, (pos, berth_info, fsm) in self.berths:
            if berth_info.id in ids:
                out_berths.append([d, (pos, berth_info, fsm)])

        return BerthList(data=out_berths)
