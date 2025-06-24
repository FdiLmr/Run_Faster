"""
Metrics calculation functionality for athlete analytics.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Union
from scipy.stats import linregress
from .constants import (
    ACTIVITY_TYPES,
    TRAINING_METRIC_MAPPING,
    WEEKLY_METRICS,
    OUTLIER_TYPES,
    HR_ZONES_COUNT,
)

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Handles calculation of various training and performance metrics."""

    def calculate_activity_proportions(
        self, activities_df: pd.DataFrame, activity_type: Union[int, List[int]]
    ) -> float:
        """Calculate proportion of activities of given type(s)."""
        if isinstance(activity_type, int):
            mask = activities_df["activity_type"] == activity_type
        else:
            mask = activities_df["activity_type"].isin(activity_type)

        try:
            return round(len(activities_df[mask]) / len(activities_df), 2)
        except ZeroDivisionError:
            return 0.0

    def calculate_relative_proportion(
        self, block_prop: float, total_prop: float
    ) -> Optional[float]:
        """Calculate relative proportion, handling division by zero."""
        try:
            return round(block_prop / total_prop, 2) if total_prop > 0 else None
        except Exception:
            return None

    def get_activity_type_metrics(
        self, block_activities: pd.DataFrame, all_activities: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate proportions for different activity types."""
        metrics = {}

        for activity_name, activity_type in ACTIVITY_TYPES.items():
            if activity_name == "runs":  # Skip runs as they're handled separately
                continue

            block_prop = self.calculate_activity_proportions(
                block_activities, activity_type
            )
            total_prop = self.calculate_activity_proportions(
                all_activities, activity_type
            )
            rel_prop = self.calculate_relative_proportion(block_prop, total_prop)

            metrics.update(
                {
                    f"f_proportion_{activity_name}": block_prop,
                    f"proportion_{activity_name}": total_prop,
                    f"r_proportion_{activity_name}": rel_prop,
                }
            )

        return metrics

    def get_outlier_metrics(
        self,
        features_activities: pd.DataFrame,
        all_athlete_activities: pd.DataFrame,
        block_id: str,
        athlete_id: str,
        block_activities: pd.DataFrame,
    ) -> Dict[str, float]:
        """Calculate metrics for outlier activities."""
        from running_functions import get_run_outliers

        # Get outliers for block and overall
        f_outliers = get_run_outliers(features_activities, block_id, athlete_id)
        total_outliers = get_run_outliers(all_athlete_activities, "0", athlete_id)
        total_activities = len(all_athlete_activities)

        metrics = {}

        for i, outlier_type in enumerate(OUTLIER_TYPES):
            # Calculate block proportions
            f_prop = round(len(f_outliers[i]) / len(block_activities), 2)
            total_prop = round(len(total_outliers[i]) / total_activities, 2)
            rel_prop = self.calculate_relative_proportion(f_prop, total_prop)

            metrics.update(
                {
                    f"f_proportion_{outlier_type}_activities": f_prop,
                    f"proportion_{outlier_type}_activities": total_prop,
                    f"r_proportion_{outlier_type}_activities": rel_prop,
                }
            )

        return metrics

    def calculate_training_metrics(
        self, block_weeks: pd.DataFrame, athlete_weeks: pd.DataFrame
    ) -> Dict:
        """Calculate training metrics for a block."""
        metrics = {}

        # Calculate ramp rates
        for metric, column_name in TRAINING_METRIC_MAPPING.items():
            if column_name in block_weeks.columns:
                values = list(block_weeks[column_name][:-2])
                if values:
                    slope, *_ = linregress(range(len(values)), values)
                    metrics[f"f_slope_{metric}_before_taper"] = slope

                    mean_value = block_weeks[column_name][:-2].mean()
                    mean_taper = block_weeks[column_name][-2:].mean()
                    metrics[f"f_taper_factor_{metric}"] = (
                        mean_taper / mean_value if mean_value else 0
                    )

        # Calculate relative metrics
        for metric_name, col_name in WEEKLY_METRICS:
            if col_name in block_weeks.columns:
                block_mean = block_weeks[col_name].mean()
                athlete_mean = (
                    athlete_weeks[col_name].mean()
                    if col_name in athlete_weeks.columns
                    else np.nan
                )
                metrics[f"f_avg_weekly_{metric_name}"] = block_mean
                if not np.isnan(athlete_mean) and athlete_mean != 0:
                    metrics[f"r_avg_weekly_{metric_name}"] = block_mean / athlete_mean
                else:
                    metrics[f"r_avg_weekly_{metric_name}"] = np.nan
            else:
                # Set default values for missing columns
                metrics[f"f_avg_weekly_{metric_name}"] = np.nan
                metrics[f"r_avg_weekly_{metric_name}"] = np.nan

        # Calculate heart rate zones
        for zone in range(1, HR_ZONES_COUNT + 1):
            # For runs
            zone_col = f"f_time_in_z{zone}_runs"
            if zone_col in block_weeks.columns:
                block_mean = block_weeks[zone_col].mean()
                athlete_mean = (
                    np.nanmean(athlete_weeks[zone_col])
                    if zone_col in athlete_weeks.columns
                    else np.nan
                )
                metrics[f"f_avg_{zone_col}"] = block_mean
                if not np.isnan(athlete_mean) and athlete_mean != 0:
                    metrics[f"r_avg_{zone_col}"] = block_mean / athlete_mean
                else:
                    metrics[f"r_avg_{zone_col}"] = np.nan

            # For non-runs
            non_run_zone_col = f"f_time_in_z{zone}_non_runs"
            if non_run_zone_col in block_weeks.columns:
                block_mean = block_weeks[non_run_zone_col].mean()
                athlete_mean = (
                    np.nanmean(athlete_weeks[non_run_zone_col])
                    if non_run_zone_col in athlete_weeks.columns
                    else np.nan
                )
                metrics[f"f_avg_{non_run_zone_col}"] = block_mean
                if not np.isnan(athlete_mean) and athlete_mean != 0:
                    metrics[f"r_avg_{non_run_zone_col}"] = block_mean / athlete_mean
                else:
                    metrics[f"r_avg_{non_run_zone_col}"] = np.nan

        return metrics

    def calculate_block_metrics(
        self,
        block_weeks: pd.DataFrame,
        athlete_weeks: pd.DataFrame,
        features_activities: pd.DataFrame,
        all_athlete_activities: pd.DataFrame,
        block_id: str,
        athlete_id: str,
    ) -> Dict:
        """Calculate all block-level metrics."""
        metrics = {}

        # Check if we have sufficient data
        if block_weeks.empty or "f_total_runs" not in block_weeks.columns:
            return metrics

        # Check for required columns and use correct names
        run_distance_col = "f_run_total_distance"

        # Skip blocks without sufficient data
        if block_weeks["f_total_runs"].mean() == 0 or (
            run_distance_col in block_weeks.columns
            and block_weeks[run_distance_col][:-2].mean() == 0
        ):
            return metrics

        # Get base training metrics
        metrics.update(self.calculate_training_metrics(block_weeks, athlete_weeks))

        # Get activity type proportions
        block_activities = features_activities[
            features_activities["block_id"] == block_id
        ]
        metrics.update(
            self.get_activity_type_metrics(block_activities, all_athlete_activities)
        )

        # Get outlier metrics
        metrics.update(
            self.get_outlier_metrics(
                features_activities,
                all_athlete_activities,
                block_id,
                athlete_id,
                block_activities,
            )
        )

        return metrics
