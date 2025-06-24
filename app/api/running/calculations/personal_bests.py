"""
Personal best detection and analysis.

This module provides functionality for detecting significant personal bests
from activity data and calculating performance improvements over time.
"""

import datetime
from typing import List
import logging
from .vdot import calculate_vdot

logger = logging.getLogger(__name__)

# Constants for PB calculations
PB_CONSTANTS = {
    "MIN_DISTANCE": 4900,
    "MAX_DISTANCE": 45000,
    "MIN_VDOT_INCREASE": 0.1,
    "MIN_DAYS_BETWEEN_PB": 7,
}


def get_pbs(activities: List[dict]) -> List[List]:
    """
    Get a chronological list of significant personal bests (PBs) for target distance categories.

    For each activity that is a Run or Trail Run with a 'best_efforts' list, we check each effort
    whose name is in our target categories. If an effort's predicted marathon time
    (computed via Daniels' formula) is lower than the current best for that category, we record that
    effort as a new PB (and update the current best) without discarding previous PBs.

    Args:
        activities: List of activity dictionaries from Strava API

    Returns:
        List[List]: Each sublist contains:
            [vdot, predicted marathon time (in hours), pb_date, activity_id, distance_category].
    """
    significant_pbs = []
    # Maintain current best predicted marathon time for each category.
    current_best = {}
    target_categories = {
        "400m",
        "Half Mile",
        "1K",
        "1 Mile",
        "2 Miles",
        "5K",
        "10K",
        "15K",
        "10 Miles",
        "20K",
        "Half Marathon",
        "30K",
        "Marathon",
    }
    default_best = 10 * 60 * 60  # 10 hours in seconds

    # Initialize current best for each target category.
    for cat in target_categories:
        current_best[cat] = default_best

    logger.info(
        "Starting get_pbs computation to record PB history with detailed logging."
    )

    for activity in activities:
        if not isinstance(activity, dict):
            logger.debug("Skipping non-dictionary activity.")
            continue

        activity_type = activity.get("type")
        if activity_type not in ["Run", "Trail Run"]:
            continue

        if "best_efforts" not in activity:
            continue

        if activity.get("id") == 9009284547:
            # Skip known problematic activity
            continue

        # Parse the activity's start_date to use as pb_date.
        try:
            pb_date = datetime.datetime.strptime(
                activity.get("start_date")[:10], "%Y-%m-%d"
            )
        except Exception as e:
            logger.warning(
                f"Error parsing start_date for activity id {activity.get('id')}: {e}"
            )
            pb_date = None

        for effort in activity.get("best_efforts", []):
            effort_name = effort.get("name")
            if effort_name not in target_categories:
                continue

            try:
                elapsed = float(effort.get("elapsed_time"))
                distance = float(effort.get("distance", 0))
            except Exception as e:
                logger.warning(
                    f"Error parsing elapsed_time or distance for effort '{effort_name}' in activity id {activity.get('id')}: {e}"
                )
                continue

            if not (
                PB_CONSTANTS["MIN_DISTANCE"] <= distance <= PB_CONSTANTS["MAX_DISTANCE"]
            ):
                continue

            try:
                vdot, marathon_pred_secs = calculate_vdot(
                    distance=distance, time_minutes=elapsed / 60
                )
            except Exception as e:
                logger.warning(
                    f"Error calculating vdot for effort '{effort_name}' in activity id {activity.get('id')}: {e}"
                )
                continue

            # If the effort beats the current best, record it as a new PB.
            if marathon_pred_secs < current_best[effort_name]:
                logger.info(
                    f"New PB for {effort_name} found in activity id {activity.get('id')}: "
                    f"predicted marathon time {marathon_pred_secs/3600:.2f}h (previous best: "
                    f"{current_best[effort_name]/3600:.2f}h), vdot {vdot:.2f}."
                )
                significant_pbs.append(
                    [
                        vdot,
                        marathon_pred_secs / 3600,  # Convert seconds to hours.
                        pb_date,
                        activity.get("id"),
                        effort_name,
                    ]
                )
                # Update current best so that later efforts must be even better.
                current_best[effort_name] = marathon_pred_secs

    logger.info("Completed get_pbs computation; returning PB history.")
    return significant_pbs
