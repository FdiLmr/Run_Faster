"""
Data processing modules for running analytics.

This package contains:
- Activity data processing and extraction
- Search and filtering functions for activities
"""

from .activity_processor import (
    get_non_run_activity_data,
    get_run_activity_data,
    get_run_hr_pace,
    get_activity_type,
    safe_get,
    calculate_time_in_zones,
    calculate_signal_metrics,
)
from .search_functions import get_activity, is_valid_activity, get_block, get_weeks

__all__ = [
    "get_non_run_activity_data",
    "get_run_activity_data",
    "get_run_hr_pace",
    "get_activity_type",
    "safe_get",
    "calculate_time_in_zones",
    "calculate_signal_metrics",
    "get_activity",
    "is_valid_activity",
    "get_block",
    "get_weeks",
]
