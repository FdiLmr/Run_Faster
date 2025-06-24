"""
Refactored race prediction module using modular race prediction package.

This module provides a clean interface to the race prediction system while maintaining
backward compatibility with the original race_prediction.py functionality.
"""

import logging
from typing import Optional, Dict, Any
from race_prediction import PredictionEngine, TimeFormatter
from race_prediction.config import DEFAULT_RIEGEL_EXPONENT
from race_prediction.calculator import RiegelCalculator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_athlete_predictions(athlete_id: str) -> Optional[Dict[str, Any]]:
    """
    Calculate race predictions for an athlete based on their best performances.

    This function maintains backward compatibility with the original
    race_prediction.py while using the new modular prediction engine.

    Args:
        athlete_id: Athlete's ID

    Returns:
        Dictionary with prediction data or None if insufficient data
    """
    try:
        # Initialize prediction engine
        engine = PredictionEngine()

        # Calculate predictions using the modular system
        result = engine.calculate_athlete_predictions(athlete_id)

        if not result:
            logger.warning(f"Could not calculate predictions for athlete {athlete_id}")
            return None

        # Format result for backward compatibility
        return {
            "exponent": result["exponent"],
            "base_performance": {
                "distance": result["base_performance"]["distance"],
                "time": result["base_performance"]["time"],
                "formatted_time": result["base_performance"].get(
                    "formatted_time", format_time(result["base_performance"]["time"])
                ),
            },
            "predictions": result["predictions"],
        }

    except Exception as e:
        logger.error(f"Error in race prediction pipeline for athlete {athlete_id}: {e}")
        return None


def get_latest_prediction(athlete_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the latest prediction for an athlete from the database.

    Args:
        athlete_id: Athlete's ID

    Returns:
        Prediction data or None if no prediction exists
    """
    try:
        # Initialize prediction engine
        engine = PredictionEngine()

        # Get latest prediction using the modular system
        result = engine.get_latest_prediction(athlete_id)

        if not result:
            logger.info(f"No existing prediction for athlete {athlete_id}")
            return None

        # Format result for backward compatibility
        return {
            "exponent": result["exponent"],
            "base_performance": {
                "distance": result["base_performance"]["distance"],
                "time": result["base_performance"]["time"],
                "formatted_time": result["base_performance"].get(
                    "formatted_time", format_time(result["base_performance"]["time"])
                ),
            },
            "predictions": result["predictions"],
            "created_at": result.get("created_at"),
        }

    except Exception as e:
        logger.error(f"Error retrieving prediction for athlete {athlete_id}: {e}")
        return None


def format_time(seconds: float) -> str:
    """
    Format time in seconds to human-readable format (HH:MM:SS or MM:SS).

    This function maintains backward compatibility with the original formatting.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string
    """
    return TimeFormatter.format_time(seconds)


def refresh_athlete_predictions(athlete_id: str) -> Optional[Dict[str, Any]]:
    """
    Refresh predictions for an athlete by recalculating from current PB data.

    Args:
        athlete_id: Athlete's ID

    Returns:
        Updated prediction data or None if unsuccessful
    """
    try:
        engine = PredictionEngine()
        return engine.refresh_athlete_predictions(athlete_id)
    except Exception as e:
        logger.error(f"Error refreshing predictions for athlete {athlete_id}: {e}")
        return None


def get_prediction_summary(athlete_id: str) -> Dict[str, Any]:
    """
    Get a summary of prediction status for an athlete.

    Args:
        athlete_id: Athlete's ID

    Returns:
        Dictionary with prediction summary information
    """
    try:
        engine = PredictionEngine()
        return engine.get_prediction_summary(athlete_id)
    except Exception as e:
        logger.error(f"Error getting prediction summary for athlete {athlete_id}: {e}")
        return {"athlete_id": athlete_id, "has_predictions": False, "error": str(e)}


# Backward compatibility: expose original constants and functions
# (imported at top of file)


def calculate_riegel_exponent(
    time1: float, dist1: float, time2: float, dist2: float
) -> float:
    """Backward compatibility wrapper for Riegel exponent calculation."""
    calculator = RiegelCalculator()
    return calculator.calculate_riegel_exponent(time1, dist1, time2, dist2)


def predict_race_time(
    base_distance: float,
    base_time: float,
    target_distance: float,
    exponent: float = DEFAULT_RIEGEL_EXPONENT,
) -> float:
    """Backward compatibility wrapper for race time prediction."""
    calculator = RiegelCalculator()
    return calculator.predict_race_time(
        base_distance, base_time, target_distance, exponent
    )


def get_prediction_ranges(
    base_distance: float, base_time: float, target_distance: float, exponent: float
) -> Dict[str, float]:
    """Backward compatibility wrapper for prediction ranges."""
    calculator = RiegelCalculator()
    return calculator.get_prediction_ranges(
        base_distance, base_time, target_distance, exponent
    )


if __name__ == "__main__":
    # Example usage
    athlete_id = "12345"
    predictions = calculate_athlete_predictions(athlete_id)
    if predictions:
        print(f"Predictions calculated for athlete {athlete_id}")
        print(f"Riegel exponent: {predictions['exponent']}")
        print(f"Base performance: {predictions['base_performance']['formatted_time']}")
    else:
        print(f"Could not calculate predictions for athlete {athlete_id}")
