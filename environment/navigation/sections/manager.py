import json
import math

from shapely.geometry import Point, Polygon

from exceptions import NoSectionException

from .section import Section


class SectionManager:
    """Singleton class that handles the creation and retrieval of section in the port"""

    __instance = None

    @staticmethod
    def get_instance():
        if SectionManager.__instance is None:
            SectionManager()

        return SectionManager.__instance

    def __init__(self):
        """Private constructor."""

        if SectionManager.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            SectionManager.__instance = self
            self.sections = []
            self.ocean_section = Section(
                name="ocean", shape=None, is_ocean=True, vessel_speeds=None
            )

    def create_sections(
        self,
        sections_file_path,
        vessel_classes,
        default_vessel_speed={"min": 0.0, "max": 15.0},
    ):
        with open(sections_file_path, "r") as sections_file:
            sections_data = json.loads(sections_file.read())

        sections = []

        for geom in sections_data["features"]:
            sections.append(
                self._create_section(geom, default_vessel_speed, vessel_classes)
            )

        self.sections = sections

    def _create_section(self, section_json, default_vessel_speed, vessel_classes):
        properties = section_json["properties"]

        # Pre-process the speeds dict
        vessel_speeds = self._unpack_vessel_speeds(properties["speed"], vessel_classes)

        return Section(
            name=properties["name"],
            shape=Polygon(section_json["geometry"]["coordinates"][0]),
            vessel_class_speeds=vessel_speeds,
            default_speeds=default_vessel_speed,
        )

    def _unpack_vessel_speeds(self, vessel_speed_dict, vessel_classes):
        vessel_speeds = {}

        for vessel_class in vessel_classes:
            key = vessel_class.value.replace(" ", "_").lower()
            vessel_speeds[vessel_class] = vessel_speed_dict[key]

        return vessel_speeds

    def section_for_point(self, in_point):
        point = Point(in_point[0], in_point[1])

        for section in self.sections:
            if section.shape.contains(point):
                return section

        return self.ocean_section

    def get_section(self, section_name):
        if section_name == self.ocean_section.name:
            return self.ocean_section

        for section in self.sections:
            if section.name == section_name:
                return section

        raise NoSectionException(f"No section with name: {section_name}")

    def clear(self):
        self.sections = []
