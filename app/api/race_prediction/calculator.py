"""
Mathematical calculation module for race prediction.

Handles Riegel formula calculations and personalized exponent computation.
"""

import math
import logging
from typing import Dict
from .config import (
    DEFAULT_RIEGEL_EXPONENT,
    MIN_VALID_EXPONENT,
    MAX_VALID_EXPONENT,
    OPTIMISTIC_ADJUSTMENT,
    CONSERVATIVE_ADJUSTMENT,
    MIN_OPTIMISTIC_EXPONENT,
    MAX_CONSERVATIVE_EXPONENT,
)

logger = logging.getLogger(__name__)


class RiegelCalculator:
    """Handles Riegel formula calculations for race time predictions."""

    def __init__(self):
        self.default_exponent = DEFAULT_RIEGEL_EXPONENT
        self.min_valid_exponent = MIN_VALID_EXPONENT
        self.max_valid_exponent = MAX_VALID_EXPONENT

    def calculate_riegel_exponent(
        self, time1: float, dist1: float, time2: float, dist2: float
    ) -> float:
        """
        Calculate personalized Riegel exponent using two race performances.

        Args:
            time1: Time in seconds for first distance
            dist1: First distance in meters
            time2: Time in seconds for second distance
            dist2: Second distance in meters

        Returns:
            Calculated exponent value
        """
        try:
            if not self._validate_inputs(time1, dist1, time2, dist2):
                logger.warning("Invalid input values for Riegel exponent calculation")
                return self.default_exponent

            # Ensure dist1 is shorter than dist2
            if dist1 > dist2:
                dist1, dist2 = dist2, dist1
                time1, time2 = time2, time1

            exponent = math.log(time2 / time1) / math.log(dist2 / dist1)

            # Validate the calculated exponent
            if not self._is_valid_exponent(exponent):
                logger.warning(
                    f"Calculated exponent {exponent} is outside normal range, using default"
                )
                return self.default_exponent

            return exponent

        except (ValueError, ZeroDivisionError) as e:
            logger.error(f"Error calculating Riegel exponent: {e}")
            return self.default_exponent

    def predict_race_time(
        self,
        base_distance: float,
        base_time: float,
        target_distance: float,
        exponent: float = None,
    ) -> float:
        """
        Predict race time using Riegel's formula.

        Args:
            base_distance: Distance in meters of the known performance
            base_time: Time in seconds of the known performance
            target_distance: Distance in meters for the prediction
            exponent: Riegel exponent, uses default if None

        Returns:
            Predicted time in seconds
        """
        if exponent is None:
            exponent = self.default_exponent

        if not self._validate_prediction_inputs(
            base_distance, base_time, target_distance
        ):
            logger.warning("Invalid input values for race time prediction")
            return 0

        predicted_time = base_time * (target_distance / base_distance) ** exponent
        return predicted_time

    def get_prediction_ranges(
        self,
        base_distance: float,
        base_time: float,
        target_distance: float,
        exponent: float,
    ) -> Dict[str, float]:
        """
        Generate optimistic, realistic, and conservative predictions.

        Args:
            base_distance: Distance in meters of the known performance
            base_time: Time in seconds of the known performance
            target_distance: Distance in meters for the prediction
            exponent: Calculated Riegel exponent for the athlete

        Returns:
            Dictionary with optimistic, realistic, and conservative predictions
        """
        # Adjust exponent for different prediction ranges
        optimistic_exponent = max(
            exponent + OPTIMISTIC_ADJUSTMENT, MIN_OPTIMISTIC_EXPONENT
        )
        realistic_exponent = exponent
        conservative_exponent = min(
            exponent + CONSERVATIVE_ADJUSTMENT, MAX_CONSERVATIVE_EXPONENT
        )

        return {
            "optimistic": self.predict_race_time(
                base_distance, base_time, target_distance, optimistic_exponent
            ),
            "realistic": self.predict_race_time(
                base_distance, base_time, target_distance, realistic_exponent
            ),
            "conservative": self.predict_race_time(
                base_distance, base_time, target_distance, conservative_exponent
            ),
        }

    def _validate_inputs(
        self, time1: float, dist1: float, time2: float, dist2: float
    ) -> bool:
        """Validate inputs for exponent calculation."""
        return all(value > 0 for value in [time1, dist1, time2, dist2])

    def _validate_prediction_inputs(
        self, base_distance: float, base_time: float, target_distance: float
    ) -> bool:
        """Validate inputs for race time prediction."""
        return all(value > 0 for value in [base_distance, base_time, target_distance])

    def _is_valid_exponent(self, exponent: float) -> bool:
        """Check if calculated exponent is within valid range."""
        return self.min_valid_exponent <= exponent <= self.max_valid_exponent
