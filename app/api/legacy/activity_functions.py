"""
Activity functions - Backward compatibility module.

This module provides backward compatibility by importing all functions
from the new modular running package structure.

The original functionality has been refactored into:
- running.processing.activity_processor: Core activity data processing

For new code, consider importing directly from the specific modules.
"""

# Import all functions from the new modular structure
from running import (
    get_non_run_activity_data,
    get_run_activity_data,
    get_run_hr_pace,
    get_activity_type,
    safe_get,
    calculate_time_in_zones,
    calculate_signal_metrics,
)

# Re-export for backward compatibility
__all__ = [
    "get_non_run_activity_data",
    "get_run_activity_data",
    "get_run_hr_pace",
    "get_activity_type",
    "safe_get",
    "calculate_time_in_zones",
    "calculate_signal_metrics",
]
