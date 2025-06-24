"""
Visualization module for ML pipeline.

Handles SHAP plot generation and other visualizations.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import logging
from typing import List, Optional
from sklearn.ensemble import RandomForestRegressor
from .config import SHAP_PLOTS_DIR

logger = logging.getLogger(__name__)


class ShapVisualizer:
    """Handles SHAP visualization generation."""

    def __init__(self, plots_dir: str = SHAP_PLOTS_DIR):
        self.plots_dir = plots_dir
        self._ensure_plots_directory()

    def _ensure_plots_directory(self):
        """Create plots directory if it doesn't exist."""
        os.makedirs(self.plots_dir, exist_ok=True)

    def generate_shap_plots(
        self,
        regressor: RandomForestRegressor,
        X: np.ndarray,
        feature_names: List[str],
        plot_type: str,
        athlete_id: Optional[str] = None,
    ) -> dict:
        """
        Generate and save SHAP plots.

        Args:
            regressor: Trained random forest model
            X: Feature matrix
            feature_names: List of feature names
            plot_type: Type identifier for plot naming
            athlete_id: Optional athlete ID for personalized plots

        Returns:
            Dictionary with plot file paths and status
        """
        try:
            import shap
        except ImportError:
            logger.warning("SHAP package not installed. Skipping visualization.")
            return {"status": "skipped", "reason": "SHAP not installed"}

        try:
            # Clear any existing plots
            plt.clf()

            # Create SHAP explainer and values
            explainer = shap.TreeExplainer(regressor)
            shap_values = explainer.shap_values(X)

            # Create DataFrame for SHAP plotting
            feature_df = pd.DataFrame(X, columns=feature_names)

            plot_paths = {}

            # Generate summary plot
            summary_path = self._generate_summary_plot(
                shap_values, feature_df, plot_type, athlete_id
            )
            plot_paths["summary"] = summary_path

            # Generate bar plot
            bar_path = self._generate_bar_plot(
                shap_values, feature_df, plot_type, athlete_id
            )
            plot_paths["bar"] = bar_path

            logger.info(f"Generated SHAP plots for {plot_type}")

            return {"status": "success", "plots": plot_paths}

        except Exception as e:
            logger.error(f"Error generating SHAP plots: {e}")
            return {"status": "error", "reason": str(e)}

    def _generate_summary_plot(
        self,
        shap_values: np.ndarray,
        feature_df: pd.DataFrame,
        plot_type: str,
        athlete_id: Optional[str],
    ) -> str:
        """Generate and save SHAP summary plot."""
        import shap

        plt.clf()
        shap.summary_plot(shap_values, feature_df, show=False)
        plt.tight_layout()

        filename = self._get_plot_filename(plot_type, "summary", athlete_id)
        filepath = os.path.join(self.plots_dir, filename)

        plt.savefig(filepath, dpi=300, bbox_inches="tight")
        plt.close()

        return filepath

    def _generate_bar_plot(
        self,
        shap_values: np.ndarray,
        feature_df: pd.DataFrame,
        plot_type: str,
        athlete_id: Optional[str],
    ) -> str:
        """Generate and save SHAP bar plot."""
        import shap

        plt.clf()
        shap.summary_plot(shap_values, feature_df, plot_type="bar", show=False)
        plt.tight_layout()

        filename = self._get_plot_filename(plot_type, "bar", athlete_id)
        filepath = os.path.join(self.plots_dir, filename)

        plt.savefig(filepath, dpi=300, bbox_inches="tight")
        plt.close()

        return filepath

    def _get_plot_filename(
        self, plot_type: str, chart_type: str, athlete_id: Optional[str]
    ) -> str:
        """Generate appropriate filename for plot."""
        if athlete_id:
            return f"{plot_type}_{chart_type}_{athlete_id}.png"
        else:
            return f"{plot_type}_{chart_type}.png"

    def generate_feature_importance_plot(
        self,
        importance_df: pd.DataFrame,
        plot_type: str,
        athlete_id: Optional[str] = None,
        top_n: int = 15,
    ) -> str:
        """
        Generate feature importance bar plot.

        Args:
            importance_df: DataFrame with feature importance data
            plot_type: Type identifier for plot naming
            athlete_id: Optional athlete ID
            top_n: Number of top features to plot

        Returns:
            Path to saved plot
        """
        try:
            plt.clf()

            # Get top N features
            top_features = importance_df.nlargest(top_n, "importance")

            # Create horizontal bar plot
            plt.figure(figsize=(10, 8))
            plt.barh(range(len(top_features)), top_features["importance"])
            plt.yticks(range(len(top_features)), top_features["feature_name"])
            plt.xlabel("Feature Importance")
            plt.title(
                f'Top {top_n} Feature Importances - {plot_type.replace("_", " ").title()}'
            )
            plt.gca().invert_yaxis()
            plt.tight_layout()

            filename = self._get_plot_filename(plot_type, "importance", athlete_id)
            filepath = os.path.join(self.plots_dir, filename)

            plt.savefig(filepath, dpi=300, bbox_inches="tight")
            plt.close()

            logger.info(f"Generated feature importance plot: {filepath}")

            return filepath

        except Exception as e:
            logger.error(f"Error generating feature importance plot: {e}")
            raise
