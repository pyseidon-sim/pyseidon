import pytest
import esper

from environment.queries import AnchorageList
from .constants import MOCK_ANCHORAGES_COUNT, MOCK_ANCHORAGES_FILENAME
from environment.initializers import AnchoragesInitializer


@pytest.fixture
def create_anchorages_initializer():
    world = esper.World()
    return world, AnchoragesInitializer(world, MOCK_ANCHORAGES_FILENAME)

def test_create_anchorages(create_anchorages_initializer):
    world, initializer = create_anchorages_initializer
    initializer.create_anchorages()

    # Check that all anchorages were created and added to the world
    anchorages = list(AnchorageList(world=world))
    assert len(anchorages) == MOCK_ANCHORAGES_COUNT
