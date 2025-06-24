"""
Data preprocessing module for ML pipeline.

Handles feature preparation, cleaning, and transformation.
"""

import numpy as np
import pandas as pd
import logging
from typing import Tuple, Optional, List
from .config import REQUIRED_FEATURES, FEATURE_START_COL, TARGET_OFFSET

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Handles data preprocessing for ML models."""

    def __init__(self):
        self.feature_names: List[str] = []
        self.required_features = REQUIRED_FEATURES

    def prepare_features(
        self, features_blocks: pd.DataFrame, athlete_id: Optional[str] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare features for model training.

        Args:
            features_blocks: DataFrame with feature data
            athlete_id: Optional athlete ID to filter data

        Returns:
            Tuple of (X, y_absolute, y_change) arrays
        """
        try:
            if features_blocks.empty:
                raise ValueError("No features data available")

            # Filter for specific athlete if provided
            processed_data = self._filter_athlete_data(features_blocks, athlete_id)

            # Extract and process features
            X = self._extract_features(processed_data)

            # Extract target variables
            y_absolute, y_change = self._extract_targets(processed_data)

            return X, y_absolute, y_change

        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            raise

    def _filter_athlete_data(
        self, features_blocks: pd.DataFrame, athlete_id: Optional[str]
    ) -> pd.DataFrame:
        """Filter data for specific athlete if provided."""
        if not athlete_id:
            return features_blocks

        athlete_data = features_blocks[features_blocks["athlete_id"] == int(athlete_id)]
        if athlete_data.empty:
            logger.warning(
                f"No features data available for athlete {athlete_id}, using all data instead"
            )
            return features_blocks

        return athlete_data

    def _extract_features(self, data: pd.DataFrame) -> np.ndarray:
        """Extract and process feature columns."""
        # Get feature columns (excluding athlete_id, block_id, and target variables)
        feature_cols = data.columns[FEATURE_START_COL:TARGET_OFFSET]
        self.feature_names = list(feature_cols)

        # Convert features to numeric, replacing non-numeric values with NaN
        X = data[feature_cols].apply(pd.to_numeric, errors="coerce")

        # Add missing required features
        X = self._add_missing_features(X)

        # Handle missing values
        X = self._handle_missing_values(X)

        return X.to_numpy()

    def _add_missing_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Add missing required features with default values."""
        for feature in self.required_features:
            if feature not in X.columns:
                X[feature] = 0
                logger.info(f"Added missing feature '{feature}' with default value 0")

        return X

    def _handle_missing_values(self, X: pd.DataFrame) -> pd.DataFrame:
        """Fill NaN values with appropriate defaults."""
        for col in X.columns:
            col_mean = X[col].mean()
            if pd.isna(col_mean):  # If entire column is NaN
                X[col] = X[col].fillna(0)
            else:
                X[col] = X[col].fillna(col_mean)

        return X

    def _extract_targets(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Extract and process target variables."""
        # Convert target variables to numeric and handle NaN
        y_absolute = pd.to_numeric(data.iloc[:, TARGET_OFFSET], errors="coerce").fillna(
            0
        )
        y_change = pd.to_numeric(
            data.iloc[:, TARGET_OFFSET + 1], errors="coerce"
        ).fillna(0)

        return y_absolute.to_numpy(), y_change.to_numpy()

    def get_feature_names(self) -> List[str]:
        """Get the list of feature names after preprocessing."""
        return self.feature_names
