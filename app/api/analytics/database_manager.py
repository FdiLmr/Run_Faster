"""
Database management functionality for athlete analytics.
"""

import pandas as pd
import logging
from typing import Dict
from sql_methods import write_db_replace, read_db
from .constants import STRING_ONLY_TABLES

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Handles database operations for athlete analytics data."""

    def merge_with_existing_data(
        self, new_data: pd.DataFrame, table_name: str
    ) -> pd.DataFrame:
        """Instead of merging, just return the new data (legacy compatibility)."""
        return new_data

    def save_dataframes_to_db(self, dataframes: Dict[str, pd.DataFrame]) -> None:
        """Save multiple dataframes to database with proper formatting."""
        for table_name, df in dataframes.items():
            try:
                # Convert to string format for specific tables
                if table_name in STRING_ONLY_TABLES:
                    df = df.astype(str)

                write_db_replace(df, table_name)
                logger.info(f"Successfully saved {len(df)} rows to {table_name}")

            except Exception as e:
                logger.error(f"Error saving {table_name} to database: {e}")
                raise

    def prepare_athlete_metadata(self, athlete_data: dict) -> pd.DataFrame:
        """Prepare athlete metadata DataFrame for database storage."""
        metadata_athletes = pd.DataFrame(
            [
                {
                    "id": athlete_data["id"],
                    "sex": athlete_data["sex"],
                    "weight": athlete_data["weight"],
                    "zones": athlete_data["_Zones"]["heart_rate"]["zones"],
                }
            ]
        )

        # Check for existing athlete data and update if necessary
        try:
            existing_athletes = read_db("metadata_athletes")
            if not existing_athletes.empty:
                existing_athletes = existing_athletes.drop_duplicates(subset=["id"])
                metadata_athletes = metadata_athletes.drop_duplicates(subset=["id"])
                existing_athletes.set_index("id", inplace=True)
                metadata_athletes.set_index("id", inplace=True)
                metadata_athletes.update(existing_athletes)
                metadata_athletes.reset_index(inplace=True)
        except Exception as e:
            logger.warning(f"Could not merge with existing athlete metadata: {e}")

        return metadata_athletes

    def update_race_predictions(self, athlete_id: int) -> None:
        """Update race predictions for an athlete."""
        from race_prediction import calculate_athlete_predictions
        from models import RacePrediction
        from sql_methods import db

        try:
            # Delete any existing predictions for this athlete to ensure fresh calculation
            db.session.query(RacePrediction).filter_by(
                athlete_id=str(athlete_id)
            ).delete()
            db.session.commit()

            # Calculate new predictions
            prediction_data = calculate_athlete_predictions(str(athlete_id))
            if prediction_data:
                logger.info(
                    f"Successfully updated race predictions for athlete {athlete_id}"
                )
            else:
                logger.warning(
                    f"Could not generate race predictions for athlete {athlete_id}"
                )

        except Exception as e:
            logger.error(
                f"Error updating race predictions for athlete {athlete_id}: {e}"
            )
            db.session.rollback()
            raise
