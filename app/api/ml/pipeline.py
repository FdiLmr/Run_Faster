"""
Main ML pipeline orchestration module.

Coordinates data preprocessing, model training, analysis, and visualization.
"""

import pandas as pd
import logging
from typing import Optional, Dict, Any
from sql_methods import write_db_replace, read_db
from .config import FEATURES_TABLE, MODEL_OUTPUTS_TABLE, TARGET_VARIABLES
from .preprocessor import DataPreprocessor
from .trainer import ModelTrainer
from .analyzer import FeatureAnalyzer
from .visualizer import ShapVisualizer

logger = logging.getLogger(__name__)


class MLPipeline:
    """Main ML pipeline orchestrator."""

    def __init__(self):
        self.preprocessor = DataPreprocessor()
        self.trainer = ModelTrainer()
        self.analyzer = FeatureAnalyzer()
        self.visualizer = ShapVisualizer()

    def train_model(self, athlete_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Train model for a specific athlete or all athletes.

        Args:
            athlete_id: Optional athlete ID to filter training data

        Returns:
            Dictionary with training results and metrics
        """
        try:
            logger.info(f"Starting ML pipeline for athlete: {athlete_id or 'all'}")

            # Load and prepare data
            features_blocks = self._load_features_data()
            X, y_absolute, y_change = self.preprocessor.prepare_features(
                features_blocks, athlete_id
            )
            feature_names = self.preprocessor.get_feature_names()

            # Initialize results
            results = {}
            model_outputs = pd.DataFrame()

            # Train models for both target variables
            abs_results = self._train_absolute_vdot_model(
                X, y_absolute, feature_names, athlete_id
            )
            results.update(abs_results)
            model_outputs = pd.concat(
                [model_outputs, abs_results["absolute_vdot_importance"]],
                ignore_index=True,
            )

            change_results = self._train_vdot_change_model(
                X, y_change, feature_names, athlete_id
            )
            results.update(change_results)
            model_outputs = pd.concat(
                [model_outputs, change_results["vdot_change_importance"]],
                ignore_index=True,
            )

            # Save results to database
            self._save_model_outputs(model_outputs)

            # Generate visualizations
            visualization_results = self._generate_visualizations(
                results, X, feature_names, athlete_id
            )
            results.update(visualization_results)

            logger.info("ML pipeline completed successfully")

            return results

        except Exception as e:
            logger.error(f"Error in ML pipeline: {e}")
            raise

    def _load_features_data(self) -> pd.DataFrame:
        """Load features data from database."""
        features_blocks = read_db(FEATURES_TABLE)
        if features_blocks.empty:
            raise ValueError("No features data available in database")

        logger.info(f"Loaded {len(features_blocks)} feature records")
        return features_blocks

    def _train_absolute_vdot_model(
        self, X, y_absolute, feature_names, athlete_id
    ) -> Dict[str, Any]:
        """Train model for absolute VDOT prediction."""
        try:
            regressor_abs, score_abs, y_test, y_pred = self.trainer.train_random_forest(
                X, y_absolute
            )

            # Calculate feature importance
            importance_df = self.analyzer.calculate_feature_importance(
                regressor_abs,
                feature_names,
                TARGET_VARIABLES["absolute"],
                score_abs,
                athlete_id,
            )

            return {
                "absolute_vdot_score": score_abs,
                "absolute_vdot_model": regressor_abs,
                "absolute_vdot_importance": importance_df,
            }

        except Exception as e:
            logger.error(f"Error training absolute VDOT model: {e}")
            raise

    def _train_vdot_change_model(
        self, X, y_change, feature_names, athlete_id
    ) -> Dict[str, Any]:
        """Train model for VDOT change prediction."""
        try:
            regressor_change, score_change, y_test, y_pred = (
                self.trainer.train_random_forest(X, y_change)
            )

            # Calculate feature importance
            importance_df = self.analyzer.calculate_feature_importance(
                regressor_change,
                feature_names,
                TARGET_VARIABLES["change"],
                score_change,
                athlete_id,
            )

            return {
                "vdot_change_score": score_change,
                "vdot_change_model": regressor_change,
                "vdot_change_importance": importance_df,
            }

        except Exception as e:
            logger.error(f"Error training VDOT change model: {e}")
            raise

    def _save_model_outputs(self, model_outputs: pd.DataFrame):
        """Save model outputs to database."""
        try:
            write_db_replace(model_outputs, MODEL_OUTPUTS_TABLE)
            logger.info(f"Saved {len(model_outputs)} model output records to database")
        except Exception as e:
            logger.error(f"Error saving model outputs: {e}")
            raise

    def _generate_visualizations(
        self, results: Dict[str, Any], X, feature_names, athlete_id
    ) -> Dict[str, Any]:
        """Generate SHAP and feature importance visualizations."""
        visualization_results = {}

        try:
            # Generate SHAP plots for absolute VDOT model
            if "absolute_vdot_model" in results:
                shap_result_abs = self.visualizer.generate_shap_plots(
                    results["absolute_vdot_model"],
                    X,
                    feature_names,
                    TARGET_VARIABLES["absolute"],
                    athlete_id,
                )
                visualization_results["absolute_vdot_shap"] = shap_result_abs

            # Generate SHAP plots for VDOT change model
            if "vdot_change_model" in results:
                shap_result_change = self.visualizer.generate_shap_plots(
                    results["vdot_change_model"],
                    X,
                    feature_names,
                    TARGET_VARIABLES["change"],
                    athlete_id,
                )
                visualization_results["vdot_change_shap"] = shap_result_change

            # Generate feature importance plots
            if "absolute_vdot_importance" in results:
                importance_plot_abs = self.visualizer.generate_feature_importance_plot(
                    results["absolute_vdot_importance"],
                    TARGET_VARIABLES["absolute"],
                    athlete_id,
                )
                visualization_results["absolute_vdot_importance_plot"] = (
                    importance_plot_abs
                )

            if "vdot_change_importance" in results:
                importance_plot_change = (
                    self.visualizer.generate_feature_importance_plot(
                        results["vdot_change_importance"],
                        TARGET_VARIABLES["change"],
                        athlete_id,
                    )
                )
                visualization_results["vdot_change_importance_plot"] = (
                    importance_plot_change
                )

        except Exception as e:
            logger.warning(f"Could not generate visualizations: {e}")
            visualization_results["visualization_error"] = str(e)

        return visualization_results

    def get_model_results(self, athlete_id: Optional[str] = None) -> pd.DataFrame:
        """
        Get model results from database.

        Args:
            athlete_id: Optional athlete ID to filter results

        Returns:
            DataFrame with model results
        """
        try:
            model_outputs = read_db(MODEL_OUTPUTS_TABLE)

            if athlete_id and not model_outputs.empty:
                model_outputs = model_outputs[
                    model_outputs["athlete_id"] == int(athlete_id)
                ]

            return model_outputs

        except Exception as e:
            logger.error(f"Error getting model results: {e}")
            raise
