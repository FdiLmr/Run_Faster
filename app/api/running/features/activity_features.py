"""
Activity-level feature extraction for running analytics.

This module provides functionality for extracting features from individual
activities, including both running and non-running activities.
"""

from typing import List
import pandas as pd
import logging
from datetime import datetime
from ..processing.activity_processor import (
    get_non_run_activity_data,
    get_run_activity_data,
)
from utils.weather import get_weather_for_activity_id

logger = logging.getLogger(__name__)


def extract_activity_features(
    activities: pd.DataFrame,
    activity: dict,
    zones: List[int],
    activity_type: str,
    athlete_id: str,
    block_id: int,
    week_id: int,
    hr_regressor,
) -> pd.DataFrame:
    """
    Extract features from an activity and add them to the activities DataFrame.

    Args:
        activities: Existing DataFrame of activities
        activity: Activity dictionary from Strava API
        zones: Heart rate zones for the athlete
        activity_type: Type of activity (Run, TrailRun, etc.)
        athlete_id: ID of the athlete
        block_id: ID of the training block
        week_id: ID of the training week
        hr_regressor: Heart rate regression model (optional)

    Returns:
        Updated DataFrame with new activity features
    """
    base_features = {"athlete_id": athlete_id, "block_id": block_id, "week_id": week_id}

    # Get weather data for the activity
    weather_data = {"temperature": None, "humidity": None}
    if activity.get("start_date") and activity.get("start_latlng"):
        weather_data = get_weather_for_activity_id(
            str(activity.get("id", "")), 
            activity["start_date"], 
            activity["start_latlng"]
        )

    try:
        if activity_type not in ["Run", "TrailRun"]:
            # Handle non-run activities
            basic_data = get_non_run_activity_data(activity, zones)
            features = {
                **base_features,
                "activity_type": basic_data[1],
                "activity_id": basic_data[0],
                "elapsed_time": basic_data[2],
                "distance": basic_data[3],
                "mean_hr": basic_data[4],
                "temperature": weather_data.get("temperature"),
                "humidity": weather_data.get("humidity"),
            }
        else:
            # Handle run activities
            run_data = get_run_activity_data(activity, zones, hr_regressor)
            features = {
                **base_features,
                "activity_type": run_data[1],
                "activity_id": run_data[0],
                "elapsed_time": run_data[2],
                "distance": run_data[3],
                "mean_hr": run_data[4],
                "stdev_hr": run_data[5],
                "freq_hr": run_data[6],
                "time_in_z1": run_data[-1][0],
                "time_in_z2": run_data[-1][1],
                "time_in_z3": run_data[-1][2],
                "time_in_z4": run_data[-1][3],
                "time_in_z5": run_data[-1][4],
                "elevation": run_data[7],
                "stdev_elevation": run_data[8],
                "freq_elevation": run_data[9],
                "pace": run_data[10],
                "stdev_pace": run_data[11],
                "freq_pace": run_data[12],
                "cadence": run_data[13],
                "athlete_count": run_data[14],
                "temperature": weather_data.get("temperature"),
                "humidity": weather_data.get("humidity"),
            }

        new_features_df = pd.DataFrame([features]).dropna(axis=1, how="all")
        return pd.concat([activities, new_features_df], ignore_index=True)

    except Exception as e:
        logger.error(
            f"Error extracting features from activity {activity.get('id', 'unknown')}: {e}"
        )
        return activities
