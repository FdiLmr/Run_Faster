"""
Refactored athlete data management using modular components.

This module provides a clean interface to the athlete management functionality
by using the new modular AthleteManager and AthleteStatusManager classes.

Legacy functions are maintained for backward compatibility but now delegate
to the new modular components.
"""

import logging
from typing import Optional, Dict, Any
from data.athlete import AthleteManager, AthleteStatusManager

logger = logging.getLogger(__name__)

# Initialize the managers
athlete_manager = AthleteManager()
status_manager = AthleteStatusManager()


def get_athlete(bearer_token: str) -> Optional[Dict[str, Any]]:
    """
    Get athlete profile data from Strava API.

    Legacy function maintained for backward compatibility.
    Delegates to AthleteManager.get_athlete_profile().

    Args:
        bearer_token: Valid Strava access token

    Returns:
        Dict containing athlete profile data, or None if error occurred
    """
    return athlete_manager.get_athlete_profile(bearer_token)


def get_athlete_data_status(athlete_id: int) -> str:
    """
    Get the current processing status for an athlete.

    Legacy function maintained for backward compatibility.
    Delegates to AthleteStatusManager.get_athlete_status().

    Args:
        athlete_id: The athlete's ID

    Returns:
        Current status string ('none', 'processing', 'processed', 'error')
    """
    return status_manager.get_athlete_status(athlete_id)


def queue_athlete_for_processing(
    athlete_id: int, bearer_token: str, refresh_token: str
) -> Optional[str]:
    """
    Queue an athlete for data processing.

    Legacy function maintained for backward compatibility.
    Delegates to AthleteStatusManager.queue_athlete_for_processing().

    Args:
        athlete_id: The athlete's ID
        bearer_token: Valid Strava access token
        refresh_token: Strava refresh token

    Returns:
        Status after queueing ('none' if successful, None if error)
    """
    return status_manager.queue_athlete_for_processing(
        athlete_id, bearer_token, refresh_token
    )


# Additional convenience functions using the new modular structure


def validate_athlete_token(bearer_token: str) -> bool:
    """
    Validate if a bearer token is still valid.

    Args:
        bearer_token: Strava access token to validate

    Returns:
        True if token is valid, False otherwise
    """
    return athlete_manager.validate_athlete_token(bearer_token)


def get_athlete_id_from_token(bearer_token: str) -> Optional[int]:
    """
    Get athlete ID from a bearer token.

    Args:
        bearer_token: Valid Strava access token

    Returns:
        Athlete ID if successful, None otherwise
    """
    return athlete_manager.get_athlete_id_from_token(bearer_token)


def update_athlete_status(athlete_id: int, new_status: str) -> bool:
    """
    Update an athlete's processing status.

    Args:
        athlete_id: The athlete's ID
        new_status: New status to set ('none', 'processing', 'processed', 'error')

    Returns:
        True if successful, False otherwise
    """
    return status_manager.update_athlete_status(athlete_id, new_status)


def get_processing_queue_summary() -> Dict[str, int]:
    """
    Get a summary of athletes by processing status.

    Returns:
        Dictionary with status counts
    """
    return status_manager.get_processing_queue_summary()


def reset_all_athlete_status(target_status: str = "none") -> bool:
    """
    Reset all athletes to a specific status.

    Args:
        target_status: Status to set for all athletes

    Returns:
        True if successful, False otherwise
    """
    return status_manager.reset_all_athlete_status(target_status)
