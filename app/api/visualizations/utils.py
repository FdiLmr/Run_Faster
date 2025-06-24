"""
Utility functions for visualization components.

Contains helper functions for data formatting and conversion.
"""

import math
import datetime


def double_to_hours_minutes(time):
    """
    Convert a decimal time value to hours and minutes format.

    Args:
        time (float): Time in decimal hours (e.g., 1.5 = 1 hour 30 minutes)

    Returns:
        str: Formatted time string (HH:MM:SS)
    """
    hours = int(math.floor(time))
    minutes = int(round(60 * (time - hours), 0))
    return str(datetime.time(hours, minutes, 0, 0))


def format_distance(distance_meters):
    """
    Format distance from meters to a human-readable string.

    Args:
        distance_meters (float): Distance in meters

    Returns:
        str: Formatted distance string
    """
    if distance_meters >= 1000:
        return f"{distance_meters / 1000:.2f} km"
    else:
        return f"{distance_meters:.0f} m"


def format_duration(seconds):
    """
    Format duration from seconds to a human-readable string.

    Args:
        seconds (float): Duration in seconds

    Returns:
        str: Formatted duration string
    """
    if seconds >= 3600:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    elif seconds >= 60:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        return f"{seconds:.0f}s"


def safe_divide(numerator, denominator, default=0.0):
    """
    Safely divide two numbers with fallback for division by zero.

    Args:
        numerator (float): Numerator
        denominator (float): Denominator
        default (float): Default value if division by zero

    Returns:
        float: Result of division or default value
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0):
    """
    Safely convert value to float with fallback.

    Args:
        value: Value to convert
        default (float): Default value if conversion fails

    Returns:
        float: Converted value or default
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
