"""
Model training module for ML pipeline.

Handles random forest model training and evaluation.
"""

import numpy as np
import logging
from typing import Tuple
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from .config import DEFAULT_N_ESTIMATORS, DEFAULT_TEST_SIZE, DEFAULT_RANDOM_STATE

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Handles model training and evaluation."""

    def __init__(
        self,
        n_estimators: int = DEFAULT_N_ESTIMATORS,
        test_size: float = DEFAULT_TEST_SIZE,
        random_state: int = DEFAULT_RANDOM_STATE,
    ):
        self.n_estimators = n_estimators
        self.test_size = test_size
        self.random_state = random_state

    def train_random_forest(
        self, X: np.ndarray, y: np.ndarray
    ) -> Tuple[RandomForestRegressor, float, np.ndarray, np.ndarray]:
        """
        Train a random forest model and return model, score, and predictions.

        Args:
            X: Feature matrix
            y: Target variable

        Returns:
            Tuple of (regressor, model_score, y_test, y_pred)
        """
        try:
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=self.test_size, random_state=self.random_state
            )

            # Train model
            regressor = RandomForestRegressor(
                n_estimators=self.n_estimators, random_state=self.random_state
            )
            regressor.fit(X_train, y_train)

            # Make predictions and calculate score
            y_pred = regressor.predict(X_test)
            model_score = r2_score(y_test, y_pred)

            logger.info(f"Model trained with R² score: {model_score:.4f}")

            return regressor, model_score, y_test, y_pred

        except Exception as e:
            logger.error(f"Error training random forest: {e}")
            raise

    def evaluate_model(
        self, regressor: RandomForestRegressor, X_test: np.ndarray, y_test: np.ndarray
    ) -> dict:
        """
        Evaluate a trained model on test data.

        Args:
            regressor: Trained model
            X_test: Test features
            y_test: Test targets

        Returns:
            Dictionary with evaluation metrics
        """
        try:
            y_pred = regressor.predict(X_test)
            r2 = r2_score(y_test, y_pred)

            # Calculate additional metrics
            mse = np.mean((y_test - y_pred) ** 2)
            rmse = np.sqrt(mse)
            mae = np.mean(np.abs(y_test - y_pred))

            return {
                "r2_score": r2,
                "mse": mse,
                "rmse": rmse,
                "mae": mae,
                "predictions": y_pred,
            }

        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            raise
