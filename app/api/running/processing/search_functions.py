"""
Search and filtering functions for activities.

This module provides functionality for finding, filtering, and organizing
activities by date, type, and other criteria.
"""

from datetime import datetime, timedelta
import math
from itertools import dropwhile
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


def get_activity(activities: List[Dict], activity_id: int) -> Optional[Dict]:
    """Find an activity by its ID in a list of activities."""
    try:
        return next(
            (activity for activity in activities if int(activity["id"]) == activity_id),
            None,
        )
    except Exception as e:
        logger.error(f"Error finding activity {activity_id}: {e}")
        return None


def is_valid_activity(activity: Dict) -> bool:
    """Check if an activity has valid essential data."""
    try:
        activity["type"]
        return True
    except (KeyError, TypeError):
        return False


def get_block(
    activities: List[Dict], activity_date: datetime, duration_days: int = 91
) -> List[Dict]:
    """
    Get a block of activities leading up to a specific date.

    Args:
        activities: List of activities in chronological order
        activity_date: Target date to work backwards from
        duration_days: Number of days to look back (default 91 days / 3 months)

    Returns:
        List of activities within the specified time period
    """
    block_activities = []

    for activity in activities:
        if not is_valid_activity(activity):
            continue

        try:
            current_date = datetime.strptime(activity["start_date"][:10], "%Y-%m-%d")
            time_diff = (activity_date - current_date).days

            if 0 <= time_diff < duration_days:
                block_activities.append(activity)

        except Exception as e:
            logger.debug(f"Error processing activity date: {e}")
            continue

    return block_activities


def get_weeks(
    block_activities: List[Dict],
    duration_days: int = 91,
    exclude_last_activity: bool = False,
) -> List[List[Dict]]:
    """
    Split activities into calendar weeks (Monday→Sunday).

    Args:
        block_activities: List of activities in chronological order
        duration_days: Optional duration to consider (0 means use full range)
        exclude_last_activity: Whether to exclude the last activity (used for PB processing)

    Returns:
        List of lists, where each inner list contains activities for one Monday→Sunday week
    """
    try:
        if not block_activities:
            return []

        # Parse end date from last activity
        raw_end = datetime.strptime(block_activities[-1]["start_date"][:10], "%Y-%m-%d")

        if duration_days > 0:
            # Use specified duration
            raw_start = raw_end - timedelta(days=duration_days - 1)
        else:
            # Use full range of activities
            raw_start = datetime.strptime(
                block_activities[0]["start_date"][:10], "%Y-%m-%d"
            )
            duration_days = (raw_end - raw_start).days + 1  # inclusive

        # Anchor start to the Monday of that week
        # weekday(): Monday==0 … Sunday==6
        start_date = raw_start - timedelta(days=raw_start.weekday())

        # Anchor end to the Sunday of that week (so final week is full Mon–Sun)
        end_date = raw_end + timedelta(days=(6 - raw_end.weekday()))

        # Compute total days & number of weeks
        total_days = (end_date - start_date).days + 1  # inclusive
        num_weeks = max(1, math.ceil(total_days / 7))
        weeks = [[] for _ in range(num_weeks)]

        # Determine which activities to process
        activities_to_process = (
            block_activities[:-1] if exclude_last_activity else block_activities
        )

        # Distribute activities into weeks
        for activity in activities_to_process:
            try:
                activity_date = datetime.strptime(
                    activity["start_date"][:10], "%Y-%m-%d"
                )
                week_index = math.floor((activity_date - start_date).days / 7)

                if 0 <= week_index < num_weeks:
                    weeks[week_index].append(activity)
            except Exception as e:
                logger.debug(f"Error assigning activity to week: {e}")
                continue

        # Remove empty weeks from the start
        return list(dropwhile(lambda x: not x, weeks))

    except Exception as e:
        logger.error(f"Error processing weeks: {e}")
        return []
