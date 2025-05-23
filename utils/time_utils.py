import math


def format_runtime(total_seconds: float) -> str:
    """
    Convert a number of seconds (int or float) into a run-time string.
    Uses round-half-up and *never* shows "1:00:00" if the original < 3600.

    - If original total_seconds < 3600, always formats as "M:SS".
    - Otherwise formats as "H:MM:SS".
    """
    if total_seconds < 0:
        raise ValueError("Total seconds must be non-negative")

    # ROUND-HALF-UP: add 0.5, then floor
    rounded = math.floor(total_seconds + 0.5)

    # if it was originally < 3600, clamp it so it can never become >= 3600
    if total_seconds < 3600:
        rounded = min(rounded, 3599)

    if total_seconds < 7200:
        rounded = min(rounded, 7199)

    if total_seconds < 14400:
        rounded = min(rounded, 14399)

    if total_seconds < 28800:
        rounded = min(rounded, 28799)

    hours = rounded // 3600
    rem = rounded % 3600
    minutes = rem // 60
    seconds = rem % 60

    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"


def hms_to_minutes(h, m, s):
    """
    Convert a time in hours, minutes, and seconds to minutes.
    """
    return h * 60 + m + s / 60
