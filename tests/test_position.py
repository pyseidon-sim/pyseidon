import numpy as np
import pytest

from components import Position


def test_create():
    # A position must be expressed as 2-valued numpy array
    with pytest.raises(ValueError):
        position = Position([4, 10])

    with pytest.raises(ValueError):
        position = Position(np.array([4]))

    position = Position(np.array([4, 10]))

    assert position.lon() == 4
    assert position.lat() == 10
