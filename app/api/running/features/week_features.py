"""
Week-level feature extraction and aggregation for running analytics.

This module provides functionality for extracting and aggregating features
from weekly training data, including running and non-running activities.
"""

from typing import List, Dict
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def calculate_week_stats(df: pd.DataFrame, columns: List[str]) -> Dict[str, float]:
    """
    Calculate basic statistics for a set of columns in a DataFrame.

    Args:
        df: DataFrame containing the data
        columns: List of column names to calculate stats for

    Returns:
        Dictionary with calculated statistics
    """
    stats = {}
    for col in columns:
        if col in df.columns:
            series = df[col]
            if not series.empty:
                stats.update(
                    {
                        f"total_{col}": series.sum(),
                        f"avg_{col}": series.mean(),
                        f"stdev_{col}": series.std(),
                    }
                )
        else:
            # Set default values for missing columns
            stats.update({f"total_{col}": 0.0, f"avg_{col}": 0.0, f"stdev_{col}": 0.0})
    return stats


def extract_week_features(
    week_runs: pd.DataFrame,
    week_non_runs: pd.DataFrame,
    athlete_id: str,
    block_id: int,
    week_id: int,
    total_runs: int,
) -> Dict:
    """
    Extract features from a week of training data.

    Args:
        week_runs: DataFrame of running activities for the week
        week_non_runs: DataFrame of non-running activities for the week
        athlete_id: ID of the athlete
        block_id: ID of the training block
        week_id: ID of the training week
        total_runs: Total number of runs in the week

    Returns:
        Dictionary of extracted week features
    """
    features = {
        "athlete_id": athlete_id,
        "block_id": block_id,
        "week_id": week_id,
        "f_total_runs": total_runs,
    }

    # Calculate run statistics
    run_stats = calculate_week_stats(week_runs, ["distance", "elapsed_time"])
    features.update({f"f_run_{k}": v for k, v in run_stats.items()})

    # Calculate non-run statistics
    non_run_stats = calculate_week_stats(week_non_runs, ["distance", "elapsed_time"])
    features.update({f"f_non_run_{k}": v for k, v in non_run_stats.items()})

    # Calculate heart rate zones for runs and non-runs
    for activity_type in ["runs", "non_runs"]:
        df = week_runs if activity_type == "runs" else week_non_runs
        for zone in range(1, 6):
            zone_col = f"time_in_z{zone}"
            # Only calculate mean if the column exists, otherwise use 0
            if zone_col in df.columns and not df[zone_col].empty:
                features[f"f_time_in_z{zone}_{activity_type}"] = df[zone_col].mean()
            else:
                features[f"f_time_in_z{zone}_{activity_type}"] = 0.0

    # Count non-run activity types
    if not week_non_runs.empty and "activity_type" in week_non_runs.columns:
        activity_counts = week_non_runs["activity_type"].value_counts()
        for activity_type, count in activity_counts.items():
            features[f"f_activity_type_{int(activity_type)}"] = count

    # Calculate running-specific metrics safely
    run_metrics = {
        "run_mean_hr": ("mean_hr", "mean"),
        "run_stdev_hr": ("stdev_hr", "mean"),
        "run_freq_hr": ("freq_hr", "mean"),
        "elevation": ("elevation", ["sum", "mean"]),
        "stdev_elevation": ("stdev_elevation", "mean"),
        "freq_elevation": ("freq_elevation", "mean"),
        "pace": ("pace", "mean"),
        "stdev_pace": ("stdev_pace", "mean"),
        "freq_pace": ("freq_pace", "mean"),
        "cadence": ("cadence", "mean"),
        "athlete_count": ("athlete_count", "mean"),
    }

    # Add non-run metrics
    non_run_metrics = {
        "non_run_mean_hr": ("mean_hr", "mean"),
        "non_run_stdev_hr": ("stdev_hr", "mean"),
        "non_run_freq_hr": ("freq_hr", "mean"),
    }

    # Process run metrics
    for metric, (col, aggs) in run_metrics.items():
        if col in week_runs.columns and not week_runs[col].empty:
            try:
                if isinstance(aggs, list):
                    for agg in aggs:
                        features[f"f_{agg}_{metric}"] = week_runs[col].agg(agg)
                else:
                    features[f"f_{metric}"] = week_runs[col].agg(aggs)
            except Exception as e:
                logger.warning(f"Could not calculate {metric}: {e}")
                # Set default values if calculation fails
                if isinstance(aggs, list):
                    for agg in aggs:
                        features[f"f_{agg}_{metric}"] = 0.0
                else:
                    features[f"f_{metric}"] = 0.0
        else:
            # Set default values for missing columns
            if isinstance(aggs, list):
                for agg in aggs:
                    features[f"f_{agg}_{metric}"] = 0.0
            else:
                features[f"f_{metric}"] = 0.0

    # Process non-run metrics
    for metric, (col, aggs) in non_run_metrics.items():
        if col in week_non_runs.columns and not week_non_runs[col].empty:
            try:
                features[f"f_{metric}"] = week_non_runs[col].agg(aggs)
            except Exception as e:
                logger.warning(f"Could not calculate non-run {metric}: {e}")
                features[f"f_{metric}"] = 0.0
        else:
            features[f"f_{metric}"] = 0.0

    return features
