"""
Athlete status and processing queue management.

This module handles:
- Managing athlete processing status in the database
- Queueing athletes for data processing
- Tracking processing states and progress
"""

import logging
import pandas as pd
from typing import Optional, List, Dict, Any
from sql_methods import read_db, write_db_replace

logger = logging.getLogger(__name__)


class AthleteStatusManager:
    """
    Manages athlete processing status and queue operations.

    This class handles:
    - Checking athlete processing status
    - Queueing athletes for processing
    - Managing processing state transitions
    - Database operations for athlete status
    """

    # Valid processing statuses
    VALID_STATUSES = ["none", "processing", "processed", "error"]

    def __init__(self):
        """Initialize the AthleteStatusManager."""
        pass

    def get_athlete_status(self, athlete_id: int) -> str:
        """
        Get the current processing status for an athlete.

        Args:
            athlete_id: The athlete's ID

        Returns:
            Current status string ('none', 'processing', 'processed', 'error')
            Returns 'none' if athlete not found or error occurs
        """
        try:
            processing_status = read_db("processing_status")
            athlete_id_str = str(athlete_id)

            if processing_status.empty:
                logger.info("Processing status table is empty")
                return "none"

            if athlete_id_str in processing_status["athlete_id"].values:
                mask = processing_status["athlete_id"] == athlete_id_str
                status = processing_status.loc[mask, "status"].iloc[0]
                logger.info(f"Found status '{status}' for athlete {athlete_id}")
                return status

            logger.info(f"No status found for athlete {athlete_id}")
            return "none"

        except Exception as e:
            logger.error(f"Error checking athlete status: {e}")
            return "none"

    def queue_athlete_for_processing(
        self, athlete_id: int, bearer_token: str, refresh_token: str
    ) -> Optional[str]:
        """
        Queue an athlete for data processing.

        Args:
            athlete_id: The athlete's ID
            bearer_token: Valid Strava access token
            refresh_token: Strava refresh token

        Returns:
            Status after queueing ('none' if successful, None if error)
        """
        try:
            logger.info(f"Starting to queue athlete {athlete_id}")

            # Create DataFrame with the new athlete data
            new_row = pd.DataFrame(
                [
                    {
                        "athlete_id": str(athlete_id),
                        "status": "none",
                        "bearer_token": bearer_token,
                        "refresh_token": refresh_token,
                    }
                ]
            )

            try:
                # Try to read existing processing status
                processing_status = read_db("processing_status")
                logger.info(
                    f"Current processing status entries: {len(processing_status)}"
                )

                # Check if athlete already exists
                if str(athlete_id) in processing_status["athlete_id"].values:
                    mask = processing_status["athlete_id"] == str(athlete_id)
                    processing_status.loc[mask, "status"] = "none"
                    processing_status.loc[mask, "bearer_token"] = bearer_token
                    processing_status.loc[mask, "refresh_token"] = refresh_token
                    logger.info("Updated existing athlete entry")
                else:
                    processing_status = pd.concat(
                        [processing_status, new_row], ignore_index=True
                    )
                    logger.info("Added new athlete entry")

            except Exception as e:
                logger.warning(f"Could not read processing_status table: {e}")
                logger.info("Creating new processing status table")
                processing_status = new_row

            # Write back to database
            logger.info(
                f"Writing processing status with {len(processing_status)} entries"
            )
            write_db_replace(processing_status, "processing_status")
            logger.info(f"Successfully queued athlete {athlete_id}")
            return "none"

        except Exception as e:
            logger.error(f"Error queueing athlete {athlete_id}: {e}", exc_info=True)
            return None

    def update_athlete_status(self, athlete_id: int, new_status: str) -> bool:
        """
        Update an athlete's processing status.

        Args:
            athlete_id: The athlete's ID
            new_status: New status to set

        Returns:
            True if successful, False otherwise
        """
        if new_status not in self.VALID_STATUSES:
            logger.error(
                f"Invalid status '{new_status}'. Must be one of: {self.VALID_STATUSES}"
            )
            return False

        try:
            processing_status = read_db("processing_status")
            athlete_id_str = str(athlete_id)

            if athlete_id_str not in processing_status["athlete_id"].values:
                logger.error(f"Athlete {athlete_id} not found in processing status")
                return False

            mask = processing_status["athlete_id"] == athlete_id_str
            processing_status.loc[mask, "status"] = new_status

            write_db_replace(processing_status, "processing_status")
            logger.info(f"Updated athlete {athlete_id} status to '{new_status}'")
            return True

        except Exception as e:
            logger.error(f"Error updating athlete {athlete_id} status: {e}")
            return False

    def get_athletes_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Get all athletes with a specific processing status.

        Args:
            status: Status to filter by

        Returns:
            List of athlete records with the specified status
        """
        try:
            processing_status = read_db("processing_status")

            if processing_status.empty:
                return []

            filtered = processing_status[processing_status["status"] == status]
            return filtered.to_dict("records")

        except Exception as e:
            logger.error(f"Error getting athletes by status '{status}': {e}")
            return []

    def get_processing_queue_summary(self) -> Dict[str, int]:
        """
        Get a summary of athletes by processing status.

        Returns:
            Dictionary with status counts
        """
        try:
            processing_status = read_db("processing_status")

            if processing_status.empty:
                return {status: 0 for status in self.VALID_STATUSES}

            status_counts = processing_status["status"].value_counts().to_dict()

            # Ensure all statuses are represented
            summary = {
                status: status_counts.get(status, 0) for status in self.VALID_STATUSES
            }

            logger.info(f"Processing queue summary: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Error getting processing queue summary: {e}")
            return {status: 0 for status in self.VALID_STATUSES}

    def reset_all_athlete_status(self, target_status: str = "none") -> bool:
        """
        Reset all athletes to a specific status.

        Args:
            target_status: Status to set for all athletes

        Returns:
            True if successful, False otherwise
        """
        if target_status not in self.VALID_STATUSES:
            logger.error(
                f"Invalid status '{target_status}'. Must be one of: {self.VALID_STATUSES}"
            )
            return False

        try:
            processing_status = read_db("processing_status")

            if processing_status.empty:
                logger.info("No athletes to reset")
                return True

            processing_status["status"] = target_status
            write_db_replace(processing_status, "processing_status")

            logger.info(
                f"Reset {len(processing_status)} athletes to status '{target_status}'"
            )
            return True

        except Exception as e:
            logger.error(f"Error resetting athlete statuses: {e}")
            return False
