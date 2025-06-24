"""
Running functions - Backward compatibility module.

This module provides backward compatibility by importing all functions
from the new modular running package structure.

The original functionality has been refactored into:
- running.calculations: VDOT, PB detection, outlier analysis
- running.features: Activity and week feature extraction
- running.regressors: Pace-HR regression models
- running.processing: Activity data processing

For new code, consider importing directly from the specific modules.
"""

# Import all functions from the new modular structure
from running import (
    # Calculations
    calculate_vdot,
    get_pbs,
    get_run_outliers,
    # Features
    extract_activity_features,
    extract_week_features,
    calculate_week_stats,
    # Regressors
    build_pace_to_hr_regressor,
)

# Re-export for backward compatibility
__all__ = [
    "calculate_vdot",
    "get_pbs",
    "get_run_outliers",
    "extract_activity_features",
    "extract_week_features",
    "calculate_week_stats",
    "build_pace_to_hr_regressor",
]
