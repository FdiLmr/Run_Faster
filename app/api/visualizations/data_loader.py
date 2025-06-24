"""
Data loading utilities for visualization components.

Handles database connections and data retrieval for athlete performance analysis.
"""

import pandas as pd
import logging
from flask import current_app
from sql_methods import get_db_connection
from .config import DEFAULT_FEATURES

logger = logging.getLogger(__name__)


class VisualizationDataLoader:
    """Handles data loading for visualization components."""

    def __init__(self):
        self.engine = None

    def _get_engine(self):
        """Get database engine with Flask app context."""
        if not self.engine:
            with current_app.app_context():
                self.engine = get_db_connection()
        return self.engine

    def load_features_blocks(self):
        """Load all features blocks from database."""
        try:
            engine = self._get_engine()
            features_blocks = pd.read_sql("SELECT * FROM features_blocks", engine)

            logger.info(f"Found {len(features_blocks)} total feature blocks")
            logger.info(f"Features blocks columns: {features_blocks.columns.tolist()}")

            if len(features_blocks) > 0:
                logger.info(
                    f"Sample athlete_ids: {features_blocks['athlete_id'].head().tolist()}"
                )
                logger.info(f"athlete_id type: {features_blocks['athlete_id'].dtype}")

                # Convert athlete_id column to string for comparison
                features_blocks["athlete_id"] = features_blocks["athlete_id"].astype(
                    str
                )

            return features_blocks

        except Exception as e:
            logger.error(f"Error loading features blocks: {e}")
            return pd.DataFrame()

    def load_metadata_blocks(self):
        """Load metadata blocks from database."""
        try:
            engine = self._get_engine()
            metadata_blocks = pd.read_sql("SELECT * FROM metadata_blocks", engine)
            logger.info(f"Found {len(metadata_blocks)} metadata blocks")
            return metadata_blocks

        except Exception as e:
            logger.error(f"Error loading metadata blocks: {e}")
            return pd.DataFrame()

    def load_model_outputs(self):
        """Load model outputs from database with fallback."""
        try:
            engine = self._get_engine()
            model_outputs = pd.read_sql("SELECT * FROM model_outputs", engine)
            logger.info(f"Found {len(model_outputs)} model outputs")
            return model_outputs

        except Exception as e:
            logger.warning(
                f"Could not read model_outputs table: {e}, using default values"
            )
            return pd.DataFrame(columns=["y_name", "feature_name", "importance"])

    def get_athlete_blocks(self, features_blocks, athlete_id):
        """Get blocks for specific athlete."""
        athlete_id = str(athlete_id)
        athlete_blocks = features_blocks[features_blocks["athlete_id"] == athlete_id]

        logger.info(f"Found {len(athlete_blocks)} blocks for athlete {athlete_id}")
        if len(athlete_blocks) > 0:
            logger.info(
                f"Sample of athlete's block data: {athlete_blocks.iloc[-1].to_dict()}"
            )

        return athlete_blocks

    def get_athlete_last_block(self, features_blocks, athlete_id):
        """Get athlete's most recent block with fallback."""
        athlete_blocks = self.get_athlete_blocks(features_blocks, athlete_id)

        if len(athlete_blocks) == 0:
            logger.warning(
                f"No blocks found for athlete {athlete_id}, using empty values"
            )
            return pd.Series(0.0, index=features_blocks.columns)
        else:
            return athlete_blocks.iloc[-1]

    def get_features_for_target(self, model_outputs, target_name):
        """Get features for specific target variable with fallback."""
        if "y_name" in model_outputs.columns and len(model_outputs) > 0:
            features = model_outputs[model_outputs["y_name"] == target_name]
            features = features.sort_values(["importance"], ascending=[False])

            if len(features) > 0:
                return features

        # Fallback to default features
        logger.info(f"No model outputs found for {target_name}, using default features")
        return pd.DataFrame(
            {
                "feature_name": DEFAULT_FEATURES,
                "importance": [1.0] * len(DEFAULT_FEATURES),
            }
        )

    def get_performance_percentiles(self, features_blocks, target_column):
        """Get top and bottom performers based on target column."""
        if target_column not in features_blocks.columns:
            logger.warning(
                f"Column {target_column} not found, returning empty DataFrames"
            )
            return features_blocks.head(0), features_blocks.head(0)

        # Sort by target column and ensure we have valid values
        valid_blocks = features_blocks[features_blocks[target_column].notna()]

        if len(valid_blocks) == 0:
            logger.warning(f"No valid {target_column} values found")
            return features_blocks.head(0), features_blocks.head(0)

        # Get top and bottom 10%
        top_count = max(1, round(0.1 * len(valid_blocks)))
        bottom_count = max(1, round(0.1 * len(valid_blocks)))

        top_performers = valid_blocks.sort_values(
            [target_column], ascending=[False]
        ).head(top_count)
        bottom_performers = valid_blocks.sort_values(
            [target_column], ascending=[True]
        ).head(bottom_count)

        logger.info(
            f"Found {len(top_performers)} top performers and {len(bottom_performers)} bottom performers"
        )

        return top_performers, bottom_performers
