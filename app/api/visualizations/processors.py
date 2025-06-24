"""
Data processing utilities for visualization components.

Handles percentile calculations, feature processing, and data transformations.
"""

import math
import pandas as pd
import datetime
import logging
from .config import FEATURE_LABELS, PROBLEMATIC_FEATURES

logger = logging.getLogger(__name__)


class PercentileCalculator:
    """Handles percentile calculations for athlete performance metrics."""

    @staticmethod
    def calculate_athlete_percentile(athlete_score, top_value, bottom_value):
        """
        Calculate athlete's percentile based on top and bottom performer values.

        Args:
            athlete_score: The athlete's score for this feature
            top_value: Average value of top 10% performers
            bottom_value: Average value of bottom 10% performers

        Returns:
            float: Percentile value (0-100)
        """
        # Handle edge cases
        if top_value == 0.0 and bottom_value == 0.0:
            return 50  # Default to middle if no data

        if math.isnan(athlete_score):
            return 5  # Default to low if no score

        if math.isnan(top_value) or math.isnan(bottom_value):
            return 50  # Default to middle if missing percentiles

        # Calculate percentiles based on whether higher or lower is better
        if bottom_value > top_value:
            # Lower values are better (e.g., race times)
            perc_compare_top, perc_compare_bottom = bottom_value, top_value

            if athlete_score > perc_compare_bottom:
                return 5
            elif athlete_score < perc_compare_top:
                return 95
            else:
                try:
                    return 100 * (
                        (
                            (
                                (athlete_score - bottom_value)
                                / (top_value - bottom_value)
                            )
                            * 0.8
                        )
                        + 0.1
                    )
                except ZeroDivisionError:
                    return 50
        else:
            # Higher values are better (e.g., distance, time)
            perc_compare_top, perc_compare_bottom = top_value, bottom_value

            if athlete_score < perc_compare_bottom:
                return 5
            elif athlete_score > perc_compare_top:
                return 95
            else:
                try:
                    return 100 * (
                        (
                            (
                                (athlete_score - bottom_value)
                                / (top_value - bottom_value)
                            )
                            * 0.8
                        )
                        + 0.1
                    )
                except ZeroDivisionError:
                    return 50


class FeatureProcessor:
    """Processes features for visualization output."""

    def __init__(self):
        self.percentile_calculator = PercentileCalculator()

    def process_features(
        self,
        features,
        athlete_block,
        top_performers,
        bottom_performers,
        max_features=20,
    ):
        """
        Process features to create visualization data.

        Args:
            features: DataFrame of features with importance scores
            athlete_block: Series containing athlete's feature values
            top_performers: DataFrame of top performing athletes
            bottom_performers: DataFrame of bottom performing athletes
            max_features: Maximum number of features to process

        Returns:
            pd.DataFrame: Processed visualization data
        """
        visualization_outputs = pd.DataFrame()
        processed_features = 0

        for index, feature in features.head(max_features).iterrows():
            feature_name = feature["feature_name"]
            feature_importance = feature.get("importance", 1.0)

            # Skip if feature not in labels
            if feature_name not in FEATURE_LABELS:
                logger.debug(f"Skipping feature {feature_name} - not in labels")
                continue

            # Skip problematic features
            if feature_name in PROBLEMATIC_FEATURES:
                logger.debug(f"Skipping problematic feature {feature_name}")
                continue

            # Get athlete's score with safe fallback
            try:
                athlete_score = round(float(athlete_block.get(feature_name, 0.0)), 2)
                logger.debug(
                    f"Processing feature {feature_name} with score {athlete_score}"
                )
            except (ValueError, TypeError):
                athlete_score = 0.0
                logger.debug(f"Error getting score for {feature_name}, using 0.0")

            # Get percentile values with safe fallbacks
            try:
                top_value = (
                    top_performers[feature_name].mean()
                    if feature_name in top_performers
                    else 0.0
                )
                bottom_value = (
                    bottom_performers[feature_name].mean()
                    if feature_name in bottom_performers
                    else 0.0
                )
                logger.debug(
                    f"Feature {feature_name} - top: {top_value}, bottom: {bottom_value}"
                )
            except KeyError:
                top_value = 0.0
                bottom_value = 0.0
                logger.debug(f"Error getting percentiles for {feature_name}, using 0.0")

            # Calculate athlete percentile
            athlete_percentile = (
                self.percentile_calculator.calculate_athlete_percentile(
                    athlete_score, top_value, bottom_value
                )
            )

            # Calculate athlete need (importance weighted by room for improvement)
            athlete_need = feature_importance * (100 - athlete_percentile)
            processed_features += 1

            # Add to visualization outputs
            feature_data = {
                "feature_name": feature_name,
                "feature_importance": feature_importance,
                "athlete_score": athlete_score,
                "athlete_percentile": athlete_percentile,
                "athlete_need": athlete_need,
                "tenth": 10,
                "ninetieth": 90,
                "one-hundredth": 100,
                "value_at_tenth": round(bottom_value, 2),
                "value_at_ninetieth": round(top_value, 2),
            }

            visualization_outputs = pd.concat(
                [visualization_outputs, pd.DataFrame([feature_data])], ignore_index=True
            )

        logger.info(
            f"Processed {processed_features} features out of {len(features)} total features"
        )

        if len(visualization_outputs) == 0:
            logger.error("No visualization data could be generated")
            return None

        # Sort by athlete need (descending) then reverse for display
        visualization_outputs = visualization_outputs.sort_values(
            by=["athlete_need"], ascending=False
        )
        visualization_outputs = visualization_outputs.iloc[::-1]
        visualization_outputs = visualization_outputs.reset_index(drop=True)

        return visualization_outputs


class DateProcessor:
    """Handles date processing for visualization metadata."""

    @staticmethod
    def get_block_dates(metadata_blocks, block_id):
        """
        Get start and end dates for a block.

        Args:
            metadata_blocks: DataFrame of metadata blocks
            block_id: ID of the block to get dates for

        Returns:
            tuple: (start_date, end_date)
        """
        try:
            block_metadata = metadata_blocks[
                metadata_blocks["block_id"] == block_id
            ].iloc[0]
            end_date = block_metadata["pb_date"]
            start_date = end_date - datetime.timedelta(days=91)
            return start_date, end_date

        except (KeyError, IndexError):
            logger.warning("Could not find block metadata, using current date")
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=91)
            return start_date, end_date
