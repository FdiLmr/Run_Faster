"""
VDOT calculation using Daniels' formula.

This module provides functions for calculating VDOT (VO2 max equivalent)
and predicting marathon times based on running performance data.
"""

import math
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


def calculate_vdot(distance: float, time_minutes: float) -> Tuple[float, float]:
    """
    Calculate VDOT and predicted marathon time using Daniels' formula.

    Args:
        distance: Distance in meters
        time_minutes: Time in minutes

    Returns:
        Tuple of (vdot, predicted_marathon_time_seconds)

    Raises:
        ValueError: If distance or time are invalid
    """
    if distance <= 0 or time_minutes <= 0:
        raise ValueError("Distance and time must be positive values")

    try:
        # Calculate VDOT using Daniels' formula
        c = (
            -4.6
            + 0.182258 * (distance / time_minutes)
            + 0.000104 * (distance / time_minutes) ** 2
        )
        i = (
            0.8
            + 0.1894393 * math.exp(-0.012778 * time_minutes)
            + 0.2989558 * math.exp(-0.1932605 * time_minutes)
        )
        vdot = c / i

        # Calculate marathon prediction (42.2km)
        d = 42200  # Marathon distance in meters
        t = d * 0.004  # Initial time estimate
        n = 0
        e = 1.0

        # Iterative solution for marathon time
        while n < 50 and e > 0.1:
            c = -4.6 + 0.182258 * (d / t) + 0.000104 * (d / t) ** 2
            i = (
                0.8
                + 0.1894393 * math.exp(-0.012778 * t)
                + 0.2989558 * math.exp(-0.1932605 * t)
            )
            e = abs(c - i * vdot)
            dc = -0.182258 * d / t / t - 2 * 0.000104 * d * d / t / t / t
            di = -0.012778 * 0.1894393 * math.exp(
                -0.012778 * t
            ) - 0.1932605 * 0.2989558 * math.exp(-0.1932605 * t)
            dt = (c - i * vdot) / (dc - di * vdot)
            t -= dt
            n += 1

        return vdot, t * 60  # Return VDOT and marathon time in seconds

    except Exception as e:
        logger.error(
            f"Error calculating VDOT for distance {distance}m, time {time_minutes}min: {e}"
        )
        raise
