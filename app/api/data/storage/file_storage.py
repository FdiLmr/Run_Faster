"""
File storage operations for activity data and athlete information.
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def ensure_data_directory(athlete_id: int) -> str:
    """
    Ensure the data directory exists for a given athlete.

    Args:
        athlete_id: The athlete's ID

    Returns:
        str: Path to the athlete's data directory
    """
    athlete_dir = os.path.join("./app/api/data", str(athlete_id))
    if not os.path.exists(athlete_dir):
        os.makedirs(athlete_dir)
    return athlete_dir


def save_activity_data(
    athlete_id: int, activities: List[Dict], timestamp: str = None
) -> None:
    """
    Save activities to a JSON file with timestamp.

    Args:
        athlete_id: The athlete's ID
        activities: List of activity dictionaries
        timestamp: Optional timestamp string, defaults to current time
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create data directory if it doesn't exist
    data_dir = "./data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    filename = f"{data_dir}/athlete_{athlete_id}_activities.json"

    # Load existing data if file exists
    existing_data = {}
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Could not read existing file {filename}, creating new one")

    # Add new data with timestamp
    existing_data[timestamp] = activities

    # Save updated data
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=2)

    logger.info(f"Saved {len(activities)} activities to {filename}")


def save_activity_detail(
    athlete_id: int, activity_id: int, activity_data: Dict[str, Any]
) -> str:
    """
    Save detailed activity data to individual file.

    Args:
        athlete_id: The athlete's ID
        activity_id: The activity's ID
        activity_data: Activity data dictionary

    Returns:
        str: Path to the saved file
    """
    athlete_dir = ensure_data_directory(athlete_id)
    file_path = os.path.join(athlete_dir, f"{activity_id}.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(activity_data, f, indent=2)

    logger.info(f"Saved activity {activity_id} to {file_path}")
    return file_path


def load_activity_detail(athlete_id: int, activity_id: int) -> Optional[Dict[str, Any]]:
    """
    Load detailed activity data from file.

    Args:
        athlete_id: The athlete's ID
        activity_id: The activity's ID

    Returns:
        Dict or None: Activity data if file exists, None otherwise
    """
    athlete_dir = os.path.join("./data", str(athlete_id))
    file_path = os.path.join(athlete_dir, f"{activity_id}.json")

    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Could not decode JSON from {file_path}")
            return None
    return None


def save_activity_streams(
    athlete_id: int, activity_id: int, streams_data: Dict[str, Any]
) -> str:
    """
    Save activity streams data to file.

    Args:
        athlete_id: The athlete's ID
        activity_id: The activity's ID
        streams_data: Streams data dictionary

    Returns:
        str: Path to the saved file
    """
    athlete_dir = ensure_data_directory(athlete_id)
    file_path = os.path.join(athlete_dir, f"{activity_id}_streams.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(streams_data, f, indent=2)

    logger.info(f"Saved streams for activity {activity_id} to {file_path}")
    return file_path


def load_activity_streams(
    athlete_id: int, activity_id: int
) -> Optional[Dict[str, Any]]:
    """
    Load activity streams data from file.

    Args:
        athlete_id: The athlete's ID
        activity_id: The activity's ID

    Returns:
        Dict or None: Streams data if file exists, None otherwise
    """
    athlete_dir = os.path.join("./data", str(athlete_id))
    file_path = os.path.join(athlete_dir, f"{activity_id}_streams.json")

    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Could not decode JSON from {file_path}")
            return None
    return None


def save_athlete_metadata(
    athlete_id: int,
    athlete_data: Dict[str, Any],
    zones_data: Dict[str, Any],
    stats_data: Dict[str, Any],
) -> None:
    """
    Save athlete metadata, zones, and stats to separate files.

    Args:
        athlete_id: The athlete's ID
        athlete_data: Athlete profile data
        zones_data: Heart rate zones data
        stats_data: Athlete statistics data
    """
    data_dir = "./data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    athlete_file = f"{data_dir}/athlete_{athlete_id}_athlete.json"
    zones_file = f"{data_dir}/athlete_{athlete_id}_zones.json"
    stats_file = f"{data_dir}/athlete_{athlete_id}_stats.json"

    try:
        with open(athlete_file, "w", encoding="utf-8") as f:
            json.dump(athlete_data, f, indent=2)
        logger.info(f"Saved athlete metadata to {athlete_file}")

        with open(zones_file, "w", encoding="utf-8") as f:
            json.dump(zones_data, f, indent=2)
        logger.info(f"Saved zones data to {zones_file}")

        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats_data, f, indent=2)
        logger.info(f"Saved stats data to {stats_file}")
    except Exception as e:
        logger.error(f"Error saving athlete files: {e}")
        raise
