from components import AnchorageInfo, Shape
from components.fsm import AnchorageStateMachine
from components.fsm.states import AnchorageState


class AnchorageList:
    """Class that handles the retrieval of Anchorage entities with different sorting methods. """
    def __init__(self, world=None, data=None):
        if world is None and data is None:
            raise ValueError("Either a world or an array must be given")

        self.index = 0

        if data is None:
            self.world = world
            self.anchorages = world.get_components(AnchorageInfo, AnchorageStateMachine, Shape)
        else:
            self.anchorages = data
    
    def len(self):
        return len(self.anchorages)

    def __iter__(self):
        return self

    def __getitem__(self, index):
        return self.anchorages[index]

    def __next__(self):
        if self.index >= len(self.anchorages):
            raise StopIteration

        anchorage = self.anchorages[self.index]
        self.index += 1

        return anchorage
    
    def filter_by_available(self, available: AnchorageState):
        if available is None:
            raise ValueError("Availability must be non null!")

        available_anchorages = []

        for d, (anchorage_info, fsm, shape) in self.anchorages:
            if fsm.current() == available:
                available_anchorages.append([d, (anchorage_info, fsm, shape)])

        return AnchorageList(data=available_anchorages)

    def get_by_name(self, name):
        if name is None:
            raise ValueError("The anchorage name cannot be None!")

        for d, (anchorage_info, fsm, shape) in self.anchorages:
            if anchorage_info.name == name:
                return [d, (anchorage_info, fsm, shape)]

        return None
