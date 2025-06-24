"""
Constants used throughout the analytics package.
"""

import os

# Minimum activities required per training block
MIN_ACTIVITIES_PER_BLOCK = 3

# Activity type groupings for analysis
OTHER_ACTIVITIES = {
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,
    29,
    30,
    31,
    33,
    34,
}
WALK_HIKE_ACTIVITIES = {4, 5}

# Activity type mappings
ACTIVITY_TYPES = {
    "rides": 1,
    "runs": 2,
    "swims": 3,
    "walks_hikes": WALK_HIKE_ACTIVITIES,
    "alpine_ski": 6,
    "workout": 32,
    "yoga": 34,
    "crossfit": 10,
    "other": OTHER_ACTIVITIES,
}

# Heart rate zone count
HR_ZONES_COUNT = 5

# Default heart rate zones (based on max HR of 190)
DEFAULT_MAX_HR = 190
DEFAULT_HR_ZONES = [
    round(DEFAULT_MAX_HR * 0.6),  # Zone 1
    round(DEFAULT_MAX_HR * 0.7),  # Zone 2
    round(DEFAULT_MAX_HR * 0.8),  # Zone 3
    round(DEFAULT_MAX_HR * 0.9),  # Zone 4
]

# File paths
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

# Database tables that should be stored as strings only
STRING_ONLY_TABLES = {"metadata_athletes", "metadata_blocks"}

# Metric mappings for training analysis
TRAINING_METRIC_MAPPING = {
    "run_distance": "f_run_total_distance",
    "run_time": "f_run_total_elapsed_time",
    "mean_hr": "f_run_mean_hr",
}

# Weekly metrics for relative calculations
WEEKLY_METRICS = [
    ("run_distance", "f_run_total_distance"),
    ("non_run_distance", "f_non_run_total_distance"),
    ("run_time", "f_run_total_elapsed_time"),
    ("non_run_time", "f_non_run_total_elapsed_time"),
    ("run_elevation", "f_mean_elevation"),
    ("athlete_count", "f_athlete_count"),
]

# Outlier types for analysis
OUTLIER_TYPES = ["distance", "intense", "varying"]
