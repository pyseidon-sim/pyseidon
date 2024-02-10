import numpy as np
import pytest

from components import Velocity


def test_create():
    # FIXME old velocity models
    # A position must be expressed as 2-valued numpy array
    with pytest.raises(TypeError):
        position = Velocity([4, 10])

    with pytest.raises(TypeError):
        position = Velocity(np.array([4]))

    position = Velocity(4)
