from components import VesselInfo
from components.fsm.states import AnchorageState

from environment.queries import AnchorageList


def assign_anchorage(world, ent):
    """Function that supplies the logic of how an anchorage is chosen.

       This specific function simply looks at the draught of the vessel and assigns an anchorage
       based on that (the logic is arbitrary).

       Arguments:
       :param world: esper simulation world
       :param ent: vessel simulation world entity ID to assign the anchorage to

       Returns:
       the name of the anchorage this vessel will be routed to
    """
    # Retrieve the vessel information to check the draught of this vessel
    vessel_info = world.component_for_entity(ent, VesselInfo)
    draught = vessel_info.max_draught

    # Retrieve the anchorages from the simulation and filter by those that are available
    available_anchorages = AnchorageList(world=world).filter_by_available(AnchorageState.AVAILABLE)

    # This is arbitrary logic
    if draught > 10:
        anchorage_name = "2"
    else:
        anchorage_name = "1"

    target_anchorage = available_anchorages.get_by_name(anchorage_name)

    return target_anchorage
