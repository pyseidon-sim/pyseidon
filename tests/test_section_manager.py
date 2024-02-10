import pytest

from environment.navigation.sections import SectionManager
from example.example_model.vessel_class import VesselClass
from exceptions import NoSectionException

from .constants import MOCK_SECTIONS_FILENAME


@pytest.fixture
def section_manager():
    manager = SectionManager.get_instance()

    manager.clear()
    manager.create_sections(MOCK_SECTIONS_FILENAME, VesselClass)

    return manager


def test_point_in_section(section_manager):
    ocean_point = [3.4941673278808594, 51.45529052633677]

    # The point does not belong to any section, thus
    # its 'section' should be the ocean (a.k.a. no section)
    assert section_manager.section_for_point(ocean_point).name == "ocean"

    test_section_1_point = [3.544635772705078, 51.430895644580175]

    assert section_manager.section_for_point(test_section_1_point).name == "section_1"


def test_get_section(section_manager):
    # Fetch an existing section
    existing_name = "section_1"
    existing = section_manager.get_section(existing_name)

    assert existing is not None
    assert existing.name == existing_name

    # Try fetching a non-existing section (this)
    # should result in an exception being raised
    with pytest.raises(NoSectionException):
        section_manager.get_section("section_3")

    # Try fetching the ocean 'section'
    ocean = section_manager.get_section("ocean")

    assert ocean is not None
    assert ocean.name == "ocean"
