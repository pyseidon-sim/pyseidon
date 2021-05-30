import math
import pytest
import numpy as np

from processors.utils import vector_angle, course, convert_course_angle


def test_vector_angle():
    north = np.array([0, 1])
    east = np.array([1, 0])

    assert int(math.degrees(vector_angle(north, east))) == 90

    # Test case from https://www.varsitytutors.com/precalculus-help/find-the-measure-of-an-angle-between-two-vectors
    a = np.array([5, 24])
    b = np.array([1, 3])

    assert math.degrees(vector_angle(a, b)) == pytest.approx(6.66, 0.01)


def test_course():
    # Line y = x
    line = np.array([5, 5])

    north = np.array([0, 5])
    south = np.array([0, -5])
    east = np.array([5, 0])
    west = np.array([-5, 0])

    assert math.degrees(course(line)) == 45
    assert math.degrees(course(north)) == 0
    assert math.degrees(course(south)) == 180
    assert math.degrees(course(west)) == -90


def test_convert_course_angle():
    # Course angles, thus the reference vector is [0, 1]
    east = math.radians(90)
    west = math.radians(-90)
    north = math.radians(0)
    south = math.radians(180)
    south_neg = math.radians(-180)
    

    line = math.radians(45)
    negative_line = math.radians(-45)

    assert math.degrees(convert_course_angle(east)) == 0
    assert math.degrees(convert_course_angle(west)) == 180
    assert math.degrees(convert_course_angle(north)) == 90
    assert math.degrees(convert_course_angle(south)) == 270
    assert math.degrees(convert_course_angle(south_neg)) == 270

    assert math.degrees(convert_course_angle(line)) == 45
    assert math.degrees(convert_course_angle(negative_line)) == 135