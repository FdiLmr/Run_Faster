"""
Pace to heart rate regression models.

This module provides functionality for building regression models that
predict heart rate from pace data, useful for estimating missing HR data.
"""

from typing import List, Tuple, Optional
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import logging
from ..processing.activity_processor import get_run_hr_pace

logger = logging.getLogger(__name__)


def build_pace_to_hr_regressor(
    activities: List[dict], athlete_id: str, zones: List[int]
) -> Tuple[Optional[LinearRegression], Optional[pd.DataFrame]]:
    """
    Build a regression model to predict heart rate from pace.

    Args:
        activities: List of activity dictionaries
        athlete_id: ID of the athlete
        zones: Heart rate zones for the athlete

    Returns:
        Tuple of (regression_model, training_data) or (None, None) if insufficient data
    """
    # Extract pace and heart rate data from running activities
    paces_and_hrs = pd.DataFrame(
        [
            {"athlete_id": athlete_id, "mean_hr": hr, "pace": pace}
            for hr, pace in [
                get_run_hr_pace(act, zones)
                for act in activities
                if act.get("type") == "Run"
            ]
        ]
    )

    if paces_and_hrs.empty:
        logger.info(f"No pace/HR data found for athlete {athlete_id}")
        return None, None

    # Remove rows with missing data
    valid_data = paces_and_hrs.dropna(subset=["mean_hr", "pace"])

    if len(valid_data) <= 5:  # Need more than 5 points for meaningful regression
        logger.info(
            f"Insufficient data points ({len(valid_data)}) for pace-HR regression for athlete {athlete_id}"
        )
        return None, valid_data

    try:
        # Prepare data for regression
        X = valid_data["pace"].values.reshape(-1, 1)
        y = valid_data["mean_hr"].values.reshape(-1, 1)

        # Build and fit the regression model
        regressor = LinearRegression()
        regressor.fit(X, y)

        # Log the coefficients and intercept of the regression model
        logger.info(
            f"Pace-HR regressor for athlete {athlete_id} - coefficients: {regressor.coef_}, intercept: {regressor.intercept_}"
        )

        # Calculate predictions and metrics
        predictions = regressor.predict(X)
        mse = mean_squared_error(y, predictions)
        rmse = mse**0.5
        r2 = r2_score(y, predictions)

        # Log the metrics
        logger.info(
            f"Pace-HR regressor metrics for athlete {athlete_id} - R²: {r2:.4f}, MSE: {mse:.4f}, RMSE: {rmse:.4f}"
        )

        return regressor, valid_data

    except Exception as e:
        logger.error(
            f"Error building pace-to-HR regressor for athlete {athlete_id}: {e}"
        )
        return None, valid_data
