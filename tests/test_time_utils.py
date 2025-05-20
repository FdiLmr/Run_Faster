import sys
import os

sys.path.append(os.path.abspath(os.path.join(".")))  # Adjust the path as necessary

import pytest
from utils.time_utils import format_runtime


@pytest.mark.parametrize(
    "input_sec, expected",
    [
        # simple minutes+seconds
        (0, "0:00"),
        (59, "0:59"),
        (60, "1:00"),
        (150, "2:30"),
        # rounding floats
        (150.2, "2:30"),  # rounds down
        (150.5, "2:31"),  # rounds up
        # hours
        (3600, "1:00:00"),
        (3661, "1:01:01"),
        (7325, "2:02:05"),
        # big number
        (10_000, "2:46:40"),
    ],
)
def test_format_runtime_valid(input_sec, expected):
    assert format_runtime(input_sec) == expected


def test_negative_raises():
    with pytest.raises(ValueError):
        format_runtime(-1)


def test_exact_hour_boundary():
    # Makes sure it doesn’t print "60:00" but "1:00:00"
    assert format_runtime(3599.9) == "59:59"  # rounds down
    assert format_runtime(3600.1) == "1:00:00"  # rounds up
