"""
Personal best processing functionality for athlete analytics.
"""

import logging
from datetime import datetime
from typing import List
from sql_methods import db
from models import MetadataPB

logger = logging.getLogger(__name__)


class PersonalBestProcessor:
    """Handles processing and storage of personal best records."""

    def process_metadata_pbs(self, activities: List[dict], athlete_id: int) -> None:
        """
        Process the 'best_efforts' in each activity and insert PB entries
        into the metadata_pbs table for each distance category where a PB exists.
        Only stores the best (fastest) time for each distance category per athlete.

        Args:
            activities (list): List of activity dictionaries (raw JSON data).
            athlete_id (int or str): The athlete's ID.
        """
        # First, collect all PBs from all activities for each distance category
        all_pbs = {}  # Format: {distance_category: [pb_effort1, pb_effort2, ...]}

        for activity in activities:
            best_efforts = activity.get("best_efforts", [])
            for effort in best_efforts:
                # Only process efforts where pr_rank is not null (i.e. it's a PB)
                if effort.get("pr_rank") is not None:
                    distance_category = effort.get("name")  # e.g., "5K", "10K", etc.

                    if distance_category not in all_pbs:
                        all_pbs[distance_category] = []

                    all_pbs[distance_category].append(effort)

        # For each distance category, find the best (fastest) PB
        for distance_category, efforts in all_pbs.items():
            if not efforts:
                continue

            # Sort efforts by elapsed_time (fastest first)
            efforts.sort(key=lambda e: e.get("elapsed_time", float("inf")))
            best_effort = efforts[0]

            # Parse the date
            pb_date = self._parse_pb_date(best_effort.get("start_date"))

            # Check if there's an existing PB for this athlete and distance
            existing_pb = (
                db.session.query(MetadataPB)
                .filter_by(
                    athlete_id=str(athlete_id), distance_category=distance_category
                )
                .first()
            )

            if existing_pb:
                # Only update if the new PB is faster
                if (
                    best_effort.get("elapsed_time", float("inf"))
                    < existing_pb.elapsed_time
                ):
                    self._update_existing_pb(
                        existing_pb, best_effort, pb_date, athlete_id, distance_category
                    )
            else:
                # Create a new PB record
                self._create_new_pb(best_effort, pb_date, athlete_id, distance_category)

        # Commit all changes
        try:
            db.session.commit()
            logger.info(f"Successfully processed PBs for athlete {athlete_id}")
        except Exception as e:
            logger.error(f"Error committing PB changes for athlete {athlete_id}: {e}")
            db.session.rollback()
            raise

    def _parse_pb_date(self, start_date_str: str) -> datetime:
        """Parse PB date from string format."""
        try:
            return datetime.strptime(start_date_str[:10], "%Y-%m-%d")
        except Exception as e:
            logger.warning(f"Could not parse PB date '{start_date_str}': {e}")
            return None

    def _update_existing_pb(
        self,
        existing_pb: MetadataPB,
        best_effort: dict,
        pb_date: datetime,
        athlete_id: int,
        distance_category: str,
    ) -> None:
        """Update an existing PB record with new data."""
        existing_pb.elapsed_time = best_effort.get("elapsed_time")
        existing_pb.distance = best_effort.get("distance")
        existing_pb.pr_rank = best_effort.get("pr_rank")
        existing_pb.start_date = pb_date
        existing_pb.activity_id = str(best_effort.get("activity", {}).get("id"))
        existing_pb.pb_data = best_effort

        logger.info(
            f"Updated PB for athlete {athlete_id}, {distance_category}: {best_effort.get('elapsed_time')}s"
        )

    def _create_new_pb(
        self,
        best_effort: dict,
        pb_date: datetime,
        athlete_id: int,
        distance_category: str,
    ) -> None:
        """Create a new PB record."""
        pb = MetadataPB(
            athlete_id=str(athlete_id),
            distance_category=distance_category,
            elapsed_time=best_effort.get("elapsed_time"),
            distance=best_effort.get("distance"),
            pr_rank=best_effort.get("pr_rank"),
            start_date=pb_date,
            activity_id=str(best_effort.get("activity", {}).get("id")),
            pb_data=best_effort,
        )
        db.session.add(pb)

        logger.info(
            f"Added new PB for athlete {athlete_id}, {distance_category}: {best_effort.get('elapsed_time')}s"
        )
