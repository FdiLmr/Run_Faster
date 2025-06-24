"""
Database storage module for race predictions.

Handles storing and retrieving race prediction data from the database.
"""

import datetime
import logging
from typing import Optional, Dict, Any
from sqlalchemy import desc
from models import RacePrediction
from sql_methods import db

logger = logging.getLogger(__name__)


class PredictionStorage:
    """Handles database operations for race predictions."""

    def __init__(self):
        self.model = RacePrediction
        self.db = db

    def store_prediction(
        self, athlete_id: str, exponent: float, best_distance: float, best_time: float
    ) -> bool:
        """
        Store a race prediction in the database.

        Args:
            athlete_id: Athlete's ID
            exponent: Calculated Riegel exponent
            best_distance: Distance of best performance in meters
            best_time: Time of best performance in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            prediction = self.model(
                athlete_id=athlete_id,
                riegel_exponent=exponent,
                best_distance=best_distance,
                best_time=best_time,
                created_at=datetime.datetime.now(),
            )

            self.db.session.add(prediction)
            self.db.session.commit()

            logger.info(f"Stored race prediction for athlete {athlete_id}")
            return True

        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Error storing race prediction: {e}")
            return False

    def get_latest_prediction(self, athlete_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest prediction for an athlete from the database.

        Args:
            athlete_id: Athlete's ID

        Returns:
            Prediction data dictionary or None if no prediction exists
        """
        try:
            prediction = (
                self.model.query.filter_by(athlete_id=athlete_id)
                .order_by(desc(self.model.created_at))
                .first()
            )

            if not prediction:
                logger.info(f"No existing prediction for athlete {athlete_id}")
                return None

            return {
                "athlete_id": prediction.athlete_id,
                "riegel_exponent": prediction.riegel_exponent,
                "best_distance": prediction.best_distance,
                "best_time": prediction.best_time,
                "created_at": prediction.created_at,
            }

        except Exception as e:
            logger.error(f"Error retrieving prediction for athlete {athlete_id}: {e}")
            return None

    def get_all_predictions(self, athlete_id: str) -> list:
        """
        Get all predictions for an athlete from the database.

        Args:
            athlete_id: Athlete's ID

        Returns:
            List of prediction dictionaries
        """
        try:
            predictions = (
                self.model.query.filter_by(athlete_id=athlete_id)
                .order_by(desc(self.model.created_at))
                .all()
            )

            return [
                {
                    "athlete_id": pred.athlete_id,
                    "riegel_exponent": pred.riegel_exponent,
                    "best_distance": pred.best_distance,
                    "best_time": pred.best_time,
                    "created_at": pred.created_at,
                }
                for pred in predictions
            ]

        except Exception as e:
            logger.error(
                f"Error retrieving all predictions for athlete {athlete_id}: {e}"
            )
            return []

    def delete_old_predictions(self, athlete_id: str, keep_count: int = 5) -> bool:
        """
        Delete old predictions, keeping only the most recent ones.

        Args:
            athlete_id: Athlete's ID
            keep_count: Number of recent predictions to keep

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all predictions for the athlete
            predictions = (
                self.model.query.filter_by(athlete_id=athlete_id)
                .order_by(desc(self.model.created_at))
                .all()
            )

            if len(predictions) <= keep_count:
                logger.info(f"No old predictions to delete for athlete {athlete_id}")
                return True

            # Delete old predictions beyond the keep_count
            old_predictions = predictions[keep_count:]
            for pred in old_predictions:
                self.db.session.delete(pred)

            self.db.session.commit()

            logger.info(
                f"Deleted {len(old_predictions)} old predictions for athlete {athlete_id}"
            )
            return True

        except Exception as e:
            self.db.session.rollback()
            logger.error(
                f"Error deleting old predictions for athlete {athlete_id}: {e}"
            )
            return False

    def prediction_exists(self, athlete_id: str) -> bool:
        """
        Check if any prediction exists for an athlete.

        Args:
            athlete_id: Athlete's ID

        Returns:
            True if prediction exists, False otherwise
        """
        try:
            count = self.model.query.filter_by(athlete_id=athlete_id).count()
            return count > 0

        except Exception as e:
            logger.error(
                f"Error checking prediction existence for athlete {athlete_id}: {e}"
            )
            return False

    def update_prediction(
        self, athlete_id: str, exponent: float, best_distance: float, best_time: float
    ) -> bool:
        """
        Update or create a prediction for an athlete.

        Args:
            athlete_id: Athlete's ID
            exponent: Calculated Riegel exponent
            best_distance: Distance of best performance in meters
            best_time: Time of best performance in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            # Try to get existing prediction
            existing = (
                self.model.query.filter_by(athlete_id=athlete_id)
                .order_by(desc(self.model.created_at))
                .first()
            )

            if existing:
                # Update existing prediction
                existing.riegel_exponent = exponent
                existing.best_distance = best_distance
                existing.best_time = best_time
                existing.created_at = datetime.datetime.now()

                self.db.session.commit()
                logger.info(f"Updated race prediction for athlete {athlete_id}")
            else:
                # Create new prediction
                return self.store_prediction(
                    athlete_id, exponent, best_distance, best_time
                )

            return True

        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Error updating prediction for athlete {athlete_id}: {e}")
            return False
