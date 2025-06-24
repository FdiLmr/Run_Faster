"""
Main prediction engine for race predictions.

Orchestrates all components to generate comprehensive race time predictions.
"""

import logging
from typing import Optional, Dict, Any
from .config import RACE_DISTANCES
from .calculator import RiegelCalculator
from .data_retriever import PersonalBestRetriever
from .formatter import TimeFormatter
from .storage import PredictionStorage

logger = logging.getLogger(__name__)


class PredictionEngine:
    """Main orchestrator for race time predictions."""

    def __init__(self):
        self.calculator = RiegelCalculator()
        self.data_retriever = PersonalBestRetriever()
        self.formatter = TimeFormatter()
        self.storage = PredictionStorage()
        self.race_distances = RACE_DISTANCES

    def calculate_athlete_predictions(
        self, athlete_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate comprehensive race predictions for an athlete.

        Args:
            athlete_id: Athlete's ID

        Returns:
            Dictionary with complete prediction data or None if insufficient data
        """
        try:
            logger.info(
                f"Starting race prediction calculation for athlete {athlete_id}"
            )

            # Get athlete's personal best data
            pb_summary = self.data_retriever.get_athlete_pb_summary(athlete_id)
            if not pb_summary:
                logger.warning(f"Insufficient PB data for athlete {athlete_id}")
                return None

            # Extract data for calculations
            personal_bests = pb_summary["personal_bests"]
            best_performance = pb_summary["best_performance"]

            # Calculate personalized Riegel exponent
            exponent = self.calculator.calculate_riegel_exponent(
                personal_bests["5K"]["elapsed_time"],
                personal_bests["5K"]["distance"],
                personal_bests["10K"]["elapsed_time"],
                personal_bests["10K"]["distance"],
            )

            # Generate predictions for all race distances
            predictions = self._generate_all_predictions(
                best_performance["distance"], best_performance["time"], exponent
            )

            # Store prediction in database
            self.storage.store_prediction(
                athlete_id,
                exponent,
                best_performance["distance"],
                best_performance["time"],
            )

            # Format the complete result
            result = self._format_prediction_result(
                exponent, best_performance, predictions, pb_summary
            )

            logger.info(f"Successfully calculated predictions for athlete {athlete_id}")
            return result

        except Exception as e:
            logger.error(
                f"Error calculating race predictions for athlete {athlete_id}: {e}"
            )
            return None

    def get_latest_prediction(self, athlete_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest prediction for an athlete from the database.

        Args:
            athlete_id: Athlete's ID

        Returns:
            Prediction data or None if no prediction exists
        """
        try:
            # Get stored prediction data
            stored_prediction = self.storage.get_latest_prediction(athlete_id)
            if not stored_prediction:
                logger.info(f"No existing prediction for athlete {athlete_id}")
                return None

            # Generate predictions for all race distances using stored data
            predictions = self._generate_all_predictions(
                stored_prediction["best_distance"],
                stored_prediction["best_time"],
                stored_prediction["riegel_exponent"],
            )

            # Format the result
            base_performance = {
                "distance": stored_prediction["best_distance"],
                "time": stored_prediction["best_time"],
                "vdot": None,  # Not stored, would need recalculation
            }

            result = self._format_prediction_result(
                stored_prediction["riegel_exponent"],
                base_performance,
                predictions,
                None,  # PB summary not available from stored data
                stored_prediction["created_at"],
            )

            logger.info(f"Retrieved stored prediction for athlete {athlete_id}")
            return result

        except Exception as e:
            logger.error(f"Error retrieving prediction for athlete {athlete_id}: {e}")
            return None

    def _generate_all_predictions(
        self, base_distance: float, base_time: float, exponent: float
    ) -> Dict[str, Dict[str, float]]:
        """
        Generate predictions for all standard race distances.

        Args:
            base_distance: Base performance distance in meters
            base_time: Base performance time in seconds
            exponent: Riegel exponent for calculations

        Returns:
            Dictionary with predictions for all race distances
        """
        predictions = {}

        for race_name, distance in self.race_distances.items():
            predictions[race_name] = self.calculator.get_prediction_ranges(
                base_distance, base_time, distance, exponent
            )

        return predictions

    def _format_prediction_result(
        self,
        exponent: float,
        base_performance: Dict[str, Any],
        predictions: Dict[str, Dict[str, float]],
        pb_summary: Optional[Dict[str, Any]] = None,
        created_at: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Format the complete prediction result with all necessary data.

        Args:
            exponent: Calculated Riegel exponent
            base_performance: Best performance data
            predictions: Race predictions for all distances
            pb_summary: Optional PB summary data
            created_at: Optional creation timestamp

        Returns:
            Formatted prediction result dictionary
        """
        # Format base performance
        formatted_base = self.formatter.format_performance_summary(base_performance)

        # Format all predictions
        formatted_predictions = self.formatter.format_race_predictions(predictions)

        result = {
            "exponent": exponent,
            "base_performance": formatted_base,
            "predictions": predictions,
            "formatted_predictions": formatted_predictions,
        }

        # Add PB summary if available
        if pb_summary:
            result["personal_bests"] = pb_summary["personal_bests"]
            result["vdot_scores"] = pb_summary["vdot_scores"]

        # Add creation timestamp if available
        if created_at:
            result["created_at"] = created_at

        return result

    def refresh_athlete_predictions(self, athlete_id: str) -> Optional[Dict[str, Any]]:
        """
        Refresh predictions for an athlete by recalculating from current PB data.

        Args:
            athlete_id: Athlete's ID

        Returns:
            Updated prediction data or None if unsuccessful
        """
        try:
            logger.info(f"Refreshing predictions for athlete {athlete_id}")

            # Calculate new predictions
            new_predictions = self.calculate_athlete_predictions(athlete_id)

            if new_predictions:
                # Clean up old predictions (keep only recent ones)
                self.storage.delete_old_predictions(athlete_id, keep_count=3)
                logger.info(
                    f"Successfully refreshed predictions for athlete {athlete_id}"
                )

            return new_predictions

        except Exception as e:
            logger.error(f"Error refreshing predictions for athlete {athlete_id}: {e}")
            return None

    def get_prediction_summary(self, athlete_id: str) -> Dict[str, Any]:
        """
        Get a summary of prediction status for an athlete.

        Args:
            athlete_id: Athlete's ID

        Returns:
            Dictionary with prediction summary information
        """
        try:
            has_prediction = self.storage.prediction_exists(athlete_id)
            latest_prediction = None

            if has_prediction:
                latest_prediction = self.storage.get_latest_prediction(athlete_id)

            return {
                "athlete_id": athlete_id,
                "has_predictions": has_prediction,
                "latest_prediction_date": (
                    latest_prediction["created_at"] if latest_prediction else None
                ),
                "prediction_count": len(self.storage.get_all_predictions(athlete_id)),
            }

        except Exception as e:
            logger.error(
                f"Error getting prediction summary for athlete {athlete_id}: {e}"
            )
            return {
                "athlete_id": athlete_id,
                "has_predictions": False,
                "latest_prediction_date": None,
                "prediction_count": 0,
                "error": str(e),
            }
