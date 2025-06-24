"""
Statistical outlier detection for running activities.

This module provides functionality for identifying distance, intensity,
and interval outliers in training data to help analyze training patterns.
"""

from typing import Tuple
import numpy as np
import pandas as pd
from scipy import stats
import logging

logger = logging.getLogger(__name__)


def get_run_outliers(
    all_activities: pd.DataFrame, block_id: int, athlete_id: str
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Identify distance, intensity, and interval outliers in running activities.

    Args:
        all_activities: DataFrame containing all athlete activities
        block_id: ID of the training block to analyze
        athlete_id: ID of the athlete

    Returns:
        Tuple of (distance_outliers, intensity_outliers, interval_outliers) DataFrames
    """
    runs = all_activities[all_activities["activity_type"] == 2]
    block_activities = runs[runs["block_id"] == block_id]
    athlete_activities = runs[runs["athlete_id"] == athlete_id]

    # Initialize empty DataFrames
    distance_outliers = pd.DataFrame()
    intensity_outliers = pd.DataFrame()
    interval_outliers = pd.DataFrame()

    try:
        # Distance outliers
        if not athlete_activities.empty and "distance" in athlete_activities.columns:
            athlete_mean_distance = athlete_activities["distance"].mean()
            distance_outliers = athlete_activities[
                (np.abs(stats.zscore(athlete_activities["distance"])) >= 1.2)
                & (athlete_activities["distance"] >= athlete_mean_distance)
                & (athlete_activities["block_id"] == block_id)
            ]

        # Intensity outliers
        intensity_outliers = pd.DataFrame()

        # Heart rate based intensity
        if not athlete_activities.empty and "mean_hr" in athlete_activities.columns:
            if athlete_activities["mean_hr"].sum() != 0:
                hr_activities = athlete_activities[
                    athlete_activities["mean_hr"].notna()
                ]
                if not hr_activities.empty:
                    athlete_mean_hr = hr_activities["mean_hr"].mean()
                    athlete_mean_distance = athlete_activities["distance"].mean()
                    hr_outliers = hr_activities[
                        (np.abs(stats.zscore(hr_activities["mean_hr"])) >= 1.2)
                        & (hr_activities["distance"] >= athlete_mean_distance)
                        & (hr_activities["mean_hr"] >= athlete_mean_hr)
                        & (hr_activities["block_id"] == block_id)
                    ]
                    intensity_outliers = pd.concat([intensity_outliers, hr_outliers])

        # Pace based intensity
        if not athlete_activities.empty and "pace" in athlete_activities.columns:
            if athlete_activities["pace"].sum() != 0:
                pace_activities = athlete_activities[athlete_activities["pace"].notna()]
                if not pace_activities.empty:
                    athlete_mean_pace = pace_activities["pace"].mean()
                    pace_outliers = pace_activities[
                        (np.abs(stats.zscore(pace_activities["pace"])) >= 1.5)
                        & (pace_activities["distance"] >= 1000)
                        & (pace_activities["pace"] >= athlete_mean_pace)
                        & (pace_activities["block_id"] == block_id)
                    ]
                    intensity_outliers = pd.concat([intensity_outliers, pace_outliers])

        # Interval outliers
        if not athlete_activities.empty and "stdev_hr" in athlete_activities.columns:
            if not athlete_activities["stdev_hr"].isna().all():
                stdev_hr_threshold = athlete_activities["stdev_hr"].mean()
                interval_outliers = block_activities[
                    (block_activities["stdev_hr"].notna())
                    & (block_activities["distance"] >= 1000)
                    & (block_activities["stdev_hr"] >= stdev_hr_threshold)
                ]

    except Exception as e:
        logger.error(
            f"Error identifying outliers for athlete {athlete_id}, block {block_id}: {e}"
        )

    return (
        (
            distance_outliers.drop_duplicates()
            if not distance_outliers.empty
            else pd.DataFrame()
        ),
        (
            intensity_outliers.drop_duplicates()
            if not intensity_outliers.empty
            else pd.DataFrame()
        ),
        (
            interval_outliers.drop_duplicates()
            if not interval_outliers.empty
            else pd.DataFrame()
        ),
    )
