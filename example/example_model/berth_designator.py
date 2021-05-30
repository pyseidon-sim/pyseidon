from .vessel_content_type import VesselContentType
from exceptions import NoBerthException


def berths_allocation_designator(vessel_info, con_berths):
    berths = []

    # Filter berths that are eligible by vessel's class and cargo type
    for ent, (pos, berth_info, term_fsm) in con_berths:
        # Does the berth allow this type of vessel cargo?
        if berth_info.allowed_vessel_content_type() != VesselContentType.map_vessel_type_to_vessel_content_type(vessel_info.vessel_type):
            continue

        # Does the berth allow this type of vessel class?
        if vessel_info.vessel_class not in berth_info.allowed_vessel_classes:
            continue

        # Is the berth's quay long enough for the vessel?
        if berth_info.max_quay_length is not None:
            if berth_info.max_quay_length < vessel_info.length:
                continue

        # Is the berth deep enough for the vessel?
        if berth_info.max_depth is not None:
            if berth_info.max_depth < vessel_info.actual_draught:
                continue

        berths.append([ent, (pos, berth_info, term_fsm)])

    if len(berths) == 0:
        raise NoBerthException()

    return berths
