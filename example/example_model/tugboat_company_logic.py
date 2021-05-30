import random
from collections import defaultdict

from exceptions import NotEnoughAvailableTugsException

from components import TugInfo, VesselInfo
from components.fsm import TugStateMachine, VesselStateMachine
from components.fsm.states import TugState


class DefaultTugCompanyStrategy:
    __instance = None

    @staticmethod
    def get_instance():
        if DefaultTugCompanyStrategy.__instance is None:
            DefaultTugCompanyStrategy()

        return DefaultTugCompanyStrategy.__instance

    def __init__(self):
        """Private constructor"""
        if DefaultTugCompanyStrategy.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            DefaultTugCompanyStrategy.__instance = self

    def set_world(self, world):
        self.world = world

    def set_tug_companies(self, companies):
        self.tug_companies = companies

    def assign_company_to_vessel(self, vessel_fsm):
        """Method that performs the global tugboat company planning at the start of the simulation.

           Override this method to implement a custom tug company logic.
        """
        return random.choice(self.tug_companies)

    def assign_specific_tugs_to_vessel(self, entity_id):
        """Method that performs specific tugboat allocation for some vessel when it is
           added to the simulation world.

           Override this method to implement custom logic.
        """
        vessel_info = self.world.component_for_entity(entity_id, VesselInfo)
        vessel_fsm = self.world.component_for_entity(entity_id, VesselStateMachine)

        if vessel_info.number_of_tugboats == 0:
            return None

        # Unpack the tug FSM components
        tugs = self._get_tugs()
        available_tug_ids = []

        # Collect all tugs by tug company names and at the same time check if the allocated
        # company has enough available tugs
        tug_companies = self._available_tugs_by_company()

        if len(tug_companies[vessel_fsm.tug_company]) >= vessel_info.number_of_tugboats:
            return tug_companies[vessel_fsm.tug_company][:vessel_info.number_of_tugboats]

        # Since there are not enough available tugs by the allocated
        # company, check other companies as well
        for tug_company in tug_companies.keys():
            if len(tug_companies[tug_company]) >= vessel_info.number_of_tugboats:
                return tug_companies[tug_company][:vessel_info.number_of_tugboats]

        raise NotEnoughAvailableTugsException("Not enough tugs available")

    def _available_tugs_by_company(self):
        tug_companies = defaultdict(list)

        tugs = self._get_tugs()

        for tug_id, (tug_fsm) in tugs:
            if tug_fsm.current() != TugState.IDLE:
                continue

            tug_info = self.world.component_for_entity(tug_id, TugInfo)
            tug_companies[tug_info.company_name].append(tug_id)

        return tug_companies

    def select_tugs(self, entity_id):
        vessel_info = self.world.component_for_entity(entity_id, VesselInfo)

        if vessel_info.number_of_tugboats == 0:
            return None

        available_tug_ids = []
        tugs = self._get_tugs()

        for tug_id, (tug_fsm) in tugs:
            if tug_fsm.current() == TugState.IDLE:
                available_tug_ids.append(tug_id)

            if len(available_tug_ids) == vessel_info.number_of_tugboats:
                return available_tug_ids

        raise NotEnoughAvailableTugsException("Not enough tugs available")

    def _get_tugs(self):
        return [(tug[0], tug[1][0]) for tug in self.world.get_components(TugStateMachine)]
