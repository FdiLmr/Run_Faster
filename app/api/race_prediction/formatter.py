"""
Time formatting utilities for race prediction.

Handles conversion of time values to human-readable formats.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TimeFormatter:
    """Handles time formatting for race predictions."""

    @staticmethod
    def format_time(seconds: float) -> str:
        """
        Format time in seconds to human-readable format (HH:MM:SS or MM:SS).

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        try:
            if seconds < 0:
                return "Invalid time"

            if seconds < 60:
                return f"{seconds:.1f}s"
            elif seconds < 3600:
                minutes = int(seconds // 60)
                secs = int(seconds % 60)
                return f"{minutes}:{secs:02d}"
            else:
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                return f"{hours}:{minutes:02d}:{secs:02d}"

        except (ValueError, TypeError) as e:
            logger.error(f"Error formatting time {seconds}: {e}")
            return "Invalid time"

    @staticmethod
    def format_prediction_ranges(predictions: Dict[str, float]) -> Dict[str, str]:
        """
        Format all prediction ranges to human-readable format.

        Args:
            predictions: Dictionary with prediction times in seconds

        Returns:
            Dictionary with formatted time strings
        """
        try:
            formatted = {}
            for key, time_seconds in predictions.items():
                formatted[key] = TimeFormatter.format_time(time_seconds)
            return formatted

        except Exception as e:
            logger.error(f"Error formatting prediction ranges: {e}")
            return {}

    @staticmethod
    def format_race_predictions(
        race_predictions: Dict[str, Dict[str, float]],
    ) -> Dict[str, Dict[str, str]]:
        """
        Format complete race prediction data with all distances and ranges.

        Args:
            race_predictions: Dictionary with race predictions for all distances

        Returns:
            Dictionary with formatted predictions
        """
        try:
            formatted_predictions = {}

            for race_name, predictions in race_predictions.items():
                formatted_predictions[race_name] = (
                    TimeFormatter.format_prediction_ranges(predictions)
                )

            return formatted_predictions

        except Exception as e:
            logger.error(f"Error formatting race predictions: {e}")
            return {}

    @staticmethod
    def seconds_to_minutes(seconds: float) -> float:
        """
        Convert seconds to minutes.

        Args:
            seconds: Time in seconds

        Returns:
            Time in minutes
        """
        return seconds / 60.0

    @staticmethod
    def minutes_to_seconds(minutes: float) -> float:
        """
        Convert minutes to seconds.

        Args:
            minutes: Time in minutes

        Returns:
            Time in seconds
        """
        return minutes * 60.0

    @staticmethod
    def format_performance_summary(performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format performance summary with readable time formats.

        Args:
            performance_data: Dictionary with performance data

        Returns:
            Dictionary with formatted performance data
        """
        try:
            formatted_data = performance_data.copy()

            # Format time if present
            if "time" in formatted_data:
                formatted_data["formatted_time"] = TimeFormatter.format_time(
                    formatted_data["time"]
                )

            # Format any other time fields
            time_fields = ["elapsed_time", "best_time", "pb_time"]
            for field in time_fields:
                if field in formatted_data:
                    formatted_data[f"formatted_{field}"] = TimeFormatter.format_time(
                        formatted_data[field]
                    )

            return formatted_data

        except Exception as e:
            logger.error(f"Error formatting performance summary: {e}")
            return performance_data
