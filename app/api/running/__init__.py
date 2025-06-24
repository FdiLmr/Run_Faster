"""
Running analytics package for Strava data processing.

This package provides functionality for:
- Activity data extraction and processing
- Personal best (PB) detection and VDOT calculations
- Training block and week analysis
- Heart rate zone analysis
- Statistical outlier detection
"""

# Core calculations
from .calculations.vdot import calculate_vdot
from .calculations.personal_bests import get_pbs
from .calculations.outliers import get_run_outliers

# Feature extraction
from .features.activity_features import extract_activity_features
from .features.week_features import extract_week_features, calculate_week_stats

# Regressors
from .regressors.pace_hr import build_pace_to_hr_regressor

# Activity processing
from .processing.activity_processor import (
    get_non_run_activity_data,
    get_run_activity_data,
    get_run_hr_pace,
    get_activity_type,
    safe_get,
    calculate_time_in_zones,
    calculate_signal_metrics,
)

# Search and filtering
from .processing.search_functions import (
    get_activity,
    is_valid_activity,
    get_block,
    get_weeks,
)

__all__ = [
    # Calculations
    "calculate_vdot",
    "get_pbs",
    "get_run_outliers",
    # Features
    "extract_activity_features",
    "extract_week_features",
    "calculate_week_stats",
    # Regressors
    "build_pace_to_hr_regressor",
    # Activity processing
    "get_non_run_activity_data",
    "get_run_activity_data",
    "get_run_hr_pace",
    "get_activity_type",
    "safe_get",
    "calculate_time_in_zones",
    "calculate_signal_metrics",
    # Search functions
    "get_activity",
    "is_valid_activity",
    "get_block",
    "get_weeks",
]
