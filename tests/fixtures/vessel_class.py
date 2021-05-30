from enum import Enum


class VesselClass(Enum):
    CLASS_1 = "Class 1"

    @classmethod
    def from_class_code(cls, code):
        mapping = {
            "1": VesselClass.CLASS_1
        }

        assert code in mapping, "Invalid class code!"
        return mapping[code]

    @classmethod
    def from_number(cls, num):
        return [c for c in VesselClass][num]

    @classmethod
    def ordered_vessel_classes(cls):
        return [e for e in VesselClass]

    @classmethod
    def get_vessel_class(cls, length, draught=None):
        return VesselClass.CLASS_1
