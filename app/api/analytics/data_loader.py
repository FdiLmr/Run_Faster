"""
Data loading functionality for athlete analytics.
"""

import os
import json
import ast
import logging
from typing import List, Optional
from sql_methods import read_db
from .constants import DATA_DIR, DEFAULT_HR_ZONES

logger = logging.getLogger(__name__)


class AthleteDataLoader:
    """Handles loading athlete data from various sources."""

    def __init__(self):
        self.data_dir = DATA_DIR

    def load_file_data(self, athlete_id: int) -> Optional[dict]:
        """Load athlete data from legacy text file format."""
        try:
            file_path = os.path.join(self.data_dir, f"{athlete_id}.txt")
            with open(file_path, "r", encoding="utf8") as f:
                return ast.literal_eval(f.read())
        except Exception as e:
            logger.error(f"Error loading file data for athlete {athlete_id}: {e}")
            return None

    def load_latest_athlete_data(self, athlete_id: int) -> Optional[dict]:
        """Load the most recent data for an athlete from individual activity files."""
        try:
            activity_dir = os.path.join(self.data_dir, str(athlete_id))
            logger.debug(f"Looking for activity directory: {activity_dir}")

            if not os.path.exists(activity_dir):
                logger.error(f"No activity directory found for athlete {athlete_id}")
                return None

            # Load individual activity files
            all_activities = self._load_activity_files(activity_dir, athlete_id)
            if not all_activities:
                return None

            # Filter activities against database
            all_activities = self._filter_activities_by_database(all_activities)

            # Sort activities by date
            all_activities = self._sort_activities_by_date(all_activities, athlete_id)

            # Load athlete metadata files
            athlete_metadata = self._load_athlete_metadata(athlete_id)
            if not athlete_metadata:
                return None

            # Combine all data
            final_data = {
                **athlete_metadata["athlete"],
                "_Zones": athlete_metadata["zones"],
                "_Stats": athlete_metadata["stats"],
                "_Activities": all_activities,
            }

            logger.info(
                f"Successfully loaded latest data for athlete {athlete_id}. Total activities: {len(all_activities)}"
            )
            return final_data

        except Exception as e:
            logger.error(
                f"Error loading data for athlete {athlete_id}: {e}", exc_info=True
            )
            return None

    def _load_activity_files(self, activity_dir: str, athlete_id: int) -> List[dict]:
        """Load individual activity JSON files from directory."""
        all_activities = []

        try:
            file_list = os.listdir(activity_dir)
            logger.debug(f"Found {len(file_list)} files in {activity_dir}.")

            for filename in file_list:
                # Load files that are named with numeric activity IDs
                if filename.endswith(".json") and filename[:-5].isdigit():
                    file_path = os.path.join(activity_dir, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            activity_data = json.load(f)
                            all_activities.append(activity_data)
                    except Exception as e:
                        logger.error(
                            f"Error loading file {file_path}: {e}", exc_info=True
                        )

            logger.info(
                f"Loaded {len(all_activities)} activity files for athlete {athlete_id}."
            )
            return all_activities

        except Exception as e:
            logger.error(f"Error loading activity files for athlete {athlete_id}: {e}")
            return []

    def _filter_activities_by_database(self, activities: List[dict]) -> List[dict]:
        """Filter activities to only include those present in the database."""
        try:
            existing_activities_df = read_db("activities")
            if not existing_activities_df.empty:
                valid_ids = set(existing_activities_df["id"].tolist())
                filtered_activities = [
                    act for act in activities if act.get("id") in valid_ids
                ]
                logger.info(
                    f"After filtering, {len(filtered_activities)} activities remain (present in the DB)."
                )
                return filtered_activities
            else:
                logger.info(
                    "No activities found in the DB; returning all loaded activities."
                )
                return activities
        except Exception as e:
            logger.error(f"Error filtering activities by database: {e}")
            return activities

    def _sort_activities_by_date(
        self, activities: List[dict], athlete_id: int
    ) -> List[dict]:
        """Sort activities by start_date in descending order."""
        try:
            activities.sort(key=lambda x: x.get("start_date", ""), reverse=True)
            logger.debug("Sorted activities by start_date (descending).")
            return activities
        except Exception as e:
            logger.error(
                f"Error sorting activities for athlete {athlete_id}: {e}", exc_info=True
            )
            return activities

    def _load_athlete_metadata(self, athlete_id: int) -> Optional[dict]:
        """Load athlete metadata, zones, and stats files."""
        try:
            # Define file paths
            athlete_file = os.path.join(
                self.data_dir, f"athlete_{athlete_id}_athlete.json"
            )
            zones_file = os.path.join(self.data_dir, f"athlete_{athlete_id}_zones.json")
            stats_file = os.path.join(self.data_dir, f"athlete_{athlete_id}_stats.json")

            logger.debug(f"Loading athlete metadata from: {athlete_file}")
            logger.debug(f"Loading zones from: {zones_file}")
            logger.debug(f"Loading stats from: {stats_file}")

            # Load each file
            with open(athlete_file, "r", encoding="utf-8") as f:
                athlete_data = json.load(f)
            logger.debug("Athlete metadata loaded successfully.")

            with open(zones_file, "r", encoding="utf-8") as f:
                zones_data = json.load(f)
            logger.debug("Zones data loaded successfully.")

            with open(stats_file, "r", encoding="utf-8") as f:
                stats_data = json.load(f)
            logger.debug("Stats data loaded successfully.")

            return {"athlete": athlete_data, "zones": zones_data, "stats": stats_data}

        except Exception as e:
            logger.error(f"Error loading athlete metadata for {athlete_id}: {e}")
            return None

    def get_athlete_zones(self, athlete_data: dict) -> List[int]:
        """Extract heart rate zones from athlete data."""
        try:
            zones_raw = athlete_data["_Zones"]["heart_rate"]["zones"]
            return [
                zones_raw[0]["max"],
                zones_raw[1]["max"],
                zones_raw[2]["max"],
                zones_raw[3]["max"],
            ]
        except Exception:
            logger.warning(
                "Could not extract HR zones from athlete data, using defaults"
            )
            return DEFAULT_HR_ZONES.copy()

    def get_error_free_activities(self, activities: List[dict]) -> List[dict]:
        """Filter out activities with errors."""
        error_free = []
        for activity in activities:
            try:
                if "errors" in activity and activity["errors"]:
                    continue
                error_free.append(activity)
            except Exception:
                error_free.append(activity)
        return error_free
