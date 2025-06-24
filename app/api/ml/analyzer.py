"""
Feature analysis module for ML pipeline.

Handles feature importance calculation and analysis.
"""

import numpy as np
import pandas as pd
import logging
from datetime import date
from typing import List, Optional
from sklearn.ensemble import RandomForestRegressor

logger = logging.getLogger(__name__)


class FeatureAnalyzer:
    """Handles feature importance analysis."""

    def calculate_feature_importance(
        self,
        regressor: RandomForestRegressor,
        feature_names: List[str],
        y_name: str,
        model_score: float,
        athlete_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Calculate and format feature importance metrics.

        Args:
            regressor: Trained random forest model
            feature_names: List of feature names
            y_name: Target variable name
            model_score: Model R² score
            athlete_id: Optional athlete ID

        Returns:
            DataFrame with feature importance data
        """
        try:
            importances = regressor.feature_importances_
            indices = np.argsort(importances)[::-1]  # Sort in descending order

            model_run_date = str(date.today())

            # Create list of dictionaries for better performance
            importance_data = []

            for index in indices:
                row_data = {
                    "y_name": y_name,
                    "feature_name": feature_names[index],
                    "importance": importances[index],
                    "model_score": model_score,
                    "model_run_date": model_run_date,
                }
                if athlete_id:
                    row_data["athlete_id"] = athlete_id

                importance_data.append(row_data)

            # Create DataFrame from list of dictionaries (more efficient)
            model_outputs = pd.DataFrame(importance_data)

            logger.info(
                f"Calculated feature importance for {len(feature_names)} features"
            )

            return model_outputs

        except Exception as e:
            logger.error(f"Error calculating feature importance: {e}")
            raise

    def get_top_features(
        self, importance_df: pd.DataFrame, n_features: int = 10
    ) -> pd.DataFrame:
        """
        Get top N most important features.

        Args:
            importance_df: DataFrame with feature importance data
            n_features: Number of top features to return

        Returns:
            DataFrame with top N features
        """
        try:
            return importance_df.nlargest(n_features, "importance")
        except Exception as e:
            logger.error(f"Error getting top features: {e}")
            raise

    def analyze_feature_distribution(self, importance_df: pd.DataFrame) -> dict:
        """
        Analyze the distribution of feature importances.

        Args:
            importance_df: DataFrame with feature importance data

        Returns:
            Dictionary with distribution statistics
        """
        try:
            importances = importance_df["importance"]

            return {
                "mean_importance": importances.mean(),
                "std_importance": importances.std(),
                "min_importance": importances.min(),
                "max_importance": importances.max(),
                "median_importance": importances.median(),
                "total_features": len(importances),
            }

        except Exception as e:
            logger.error(f"Error analyzing feature distribution: {e}")
            raise
