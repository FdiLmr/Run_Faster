"""
Race Prediction Package

This package provides modular components for predicting race times based on
personal best performances using Riegel's formula and personalized exponents.

Main Components:
- RiegelCalculator: Mathematical calculations for race predictions
- PersonalBestRetriever: Data retrieval for athlete performances
- PredictionEngine: Main prediction logic and orchestration
- TimeFormatter: Time formatting utilities
- PredictionStorage: Database operations for predictions
"""

from .calculator import RiegelCalculator
from .formatter import TimeFormatter


# Import modules with database dependencies only when needed
def get_data_retriever():
    from .data_retriever import PersonalBestRetriever

    return PersonalBestRetriever


def get_prediction_engine():
    from .engine import PredictionEngine

    return PredictionEngine


def get_prediction_storage():
    from .storage import PredictionStorage

    return PredictionStorage


# For backward compatibility, expose the classes
PersonalBestRetriever = get_data_retriever
PredictionEngine = get_prediction_engine
PredictionStorage = get_prediction_storage


# Expose the main functions that the Flask application expects
def get_latest_prediction(athlete_id):
    """Get the latest prediction for an athlete from the database."""
    engine = get_prediction_engine()()
    return engine.get_latest_prediction(athlete_id)


def calculate_athlete_predictions(athlete_id):
    """Calculate race predictions for an athlete based on their best performances."""
    engine = get_prediction_engine()()
    return engine.calculate_athlete_predictions(athlete_id)


# Also expose individual calculator functions for backward compatibility
def calculate_riegel_exponent(time1, dist1, time2, dist2):
    """Calculate personalized Riegel exponent using two race performances."""
    calculator = RiegelCalculator()
    return calculator.calculate_riegel_exponent(time1, dist1, time2, dist2)


def predict_race_time(base_distance, base_time, target_distance, exponent=None):
    """Predict race time using Riegel's formula."""
    calculator = RiegelCalculator()
    if exponent is None:
        from .config import DEFAULT_RIEGEL_EXPONENT

        exponent = DEFAULT_RIEGEL_EXPONENT
    return calculator.predict_race_time(
        base_distance, base_time, target_distance, exponent
    )


def get_prediction_ranges(base_distance, base_time, target_distance, exponent):
    """Generate optimistic, realistic, and conservative predictions."""
    calculator = RiegelCalculator()
    return calculator.get_prediction_ranges(
        base_distance, base_time, target_distance, exponent
    )


def format_time(seconds):
    """Format time in seconds to human-readable format."""
    return TimeFormatter.format_time(seconds)


__all__ = [
    "RiegelCalculator",
    "PersonalBestRetriever",
    "PredictionEngine",
    "TimeFormatter",
    "PredictionStorage",
    "get_latest_prediction",
    "calculate_athlete_predictions",
    "calculate_riegel_exponent",
    "predict_race_time",
    "get_prediction_ranges",
    "format_time",
]
