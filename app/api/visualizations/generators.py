"""
Main visualization generators.

Orchestrates the data loading, processing, and chart generation for athlete performance visualizations.
"""

import logging
from flask import current_app
from .data_loader import VisualizationDataLoader
from .processors import FeatureProcessor, DateProcessor
from .charts import PerformanceChartGenerator

logger = logging.getLogger(__name__)


class AthleteVisualizationGenerator:
    """Main class for generating athlete performance visualizations."""

    def __init__(self):
        self.data_loader = VisualizationDataLoader()
        self.feature_processor = FeatureProcessor()
        self.date_processor = DateProcessor()
        self.chart_generator = PerformanceChartGenerator()

    def generate_athlete_vs_best(self, athlete_id):
        """
        Generate visualization comparing athlete's performance to best athletes.

        Args:
            athlete_id: ID of the athlete to analyze

        Returns:
            io.BytesIO or None: Chart image as bytes, or None if error
        """
        try:
            athlete_id = str(athlete_id)
            logger.info(f"Starting visualization for athlete {athlete_id}")

            with current_app.app_context():
                # Load data
                features_blocks = self.data_loader.load_features_blocks()
                if len(features_blocks) == 0:
                    logger.error("No feature blocks found in database")
                    return None

                metadata_blocks = self.data_loader.load_metadata_blocks()
                model_outputs = self.data_loader.load_model_outputs()

                # Get athlete data
                athlete_last_block = self.data_loader.get_athlete_last_block(
                    features_blocks, athlete_id
                )

                # Get block dates
                try:
                    block_id = athlete_last_block["block_id"]
                    start_date, end_date = self.date_processor.get_block_dates(
                        metadata_blocks, block_id
                    )
                except (KeyError, IndexError):
                    start_date, end_date = self.date_processor.get_block_dates(
                        metadata_blocks, None
                    )

                # Get features for VDOT analysis
                features = self.data_loader.get_features_for_target(
                    model_outputs, "y_vdot"
                )
                logger.info(
                    f"Processing features: {list(features['feature_name'])[:5]}"
                )

                # Get performance percentiles
                top_performers, bottom_performers = (
                    self.data_loader.get_performance_percentiles(
                        features_blocks, "y_vdot"
                    )
                )

                # Process features
                visualization_data = self.feature_processor.process_features(
                    features, athlete_last_block, top_performers, bottom_performers
                )

                if visualization_data is None:
                    return None

                # Generate chart
                return self.chart_generator.create_athlete_vs_best_chart(
                    visualization_data, start_date, end_date
                )

        except Exception as e:
            logger.error(f"Error generating athlete vs best visualization: {e}")
            return None

    def generate_improvement_potential(self, athlete_id):
        """
        Generate visualization comparing athlete's improvement potential to others.

        Args:
            athlete_id: ID of the athlete to analyze

        Returns:
            io.BytesIO or None: Chart image as bytes, or None if error
        """
        try:
            athlete_id = str(athlete_id)
            logger.info(f"Starting improvement visualization for athlete {athlete_id}")

            with current_app.app_context():
                # Load data
                features_blocks = self.data_loader.load_features_blocks()
                if len(features_blocks) == 0:
                    logger.error("No feature blocks found in database")
                    return None

                metadata_blocks = self.data_loader.load_metadata_blocks()
                model_outputs = self.data_loader.load_model_outputs()

                # Get athlete data
                athlete_last_block = self.data_loader.get_athlete_last_block(
                    features_blocks, athlete_id
                )

                # Get block dates
                try:
                    block_id = athlete_last_block["block_id"]
                    start_date, end_date = self.date_processor.get_block_dates(
                        metadata_blocks, block_id
                    )
                except (KeyError, IndexError):
                    start_date, end_date = self.date_processor.get_block_dates(
                        metadata_blocks, None
                    )

                # Get features for VDOT delta analysis
                features = self.data_loader.get_features_for_target(
                    model_outputs, "y_vdot_delta"
                )
                logger.info(
                    f"Processing features: {list(features['feature_name'])[:5]}"
                )

                # Get improvement percentiles
                top_performers, bottom_performers = (
                    self.data_loader.get_performance_percentiles(
                        features_blocks, "y_vdot_delta"
                    )
                )

                # Process features
                visualization_data = self.feature_processor.process_features(
                    features, athlete_last_block, top_performers, bottom_performers
                )

                if visualization_data is None:
                    return None

                # Generate chart
                return self.chart_generator.create_improvement_potential_chart(
                    visualization_data, start_date, end_date
                )

        except Exception as e:
            logger.error(f"Error generating improvement potential visualization: {e}")
            return None


# Create global generator instance
_generator = AthleteVisualizationGenerator()


# Export functions for backward compatibility
def athletevsbest(athlete_id):
    """Generate visualization comparing athlete's performance to best athletes."""
    return _generator.generate_athlete_vs_best(athlete_id)


def athletevsbestimprovement(athlete_id):
    """Generate visualization comparing athlete's improvement to others."""
    return _generator.generate_improvement_potential(athlete_id)
