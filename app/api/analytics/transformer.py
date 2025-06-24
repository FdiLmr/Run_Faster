"""
Main athlete data transformation orchestrator.
"""

import pandas as pd
import logging
from running_functions import build_pace_to_hr_regressor
from .data_loader import AthleteDataLoader
from .activity_processor import ActivityProcessor
from .metrics_calculator import MetricsCalculator
from .pb_processor import PersonalBestProcessor
from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class AthleteDataTransformer:
    """Main orchestrator for athlete data transformation and analytics."""

    def __init__(self):
        self.data_loader = AthleteDataLoader()
        self.activity_processor = ActivityProcessor()
        self.metrics_calculator = MetricsCalculator()
        self.pb_processor = PersonalBestProcessor()
        self.database_manager = DatabaseManager()

    def transform_athlete_data(
        self,
        athlete_id: int,
        athlete_data: dict = None,
        populate_all_from_files: int = 0,
    ) -> None:
        """
        Transform athlete data and store in database.

        Args:
            athlete_id: The athlete's ID
            athlete_data: Pre-loaded athlete data (optional)
            populate_all_from_files: Whether to load from files (1) or use provided data (0)
        """
        try:
            # Load athlete data if needed
            if populate_all_from_files or athlete_data is None:
                athlete_data = self.data_loader.load_latest_athlete_data(athlete_id)
                if not athlete_data:
                    logger.error(f"Could not load data for athlete {athlete_id}")
                    return

            # Validate basic data
            if "sex" not in athlete_data:
                logger.error(f"Invalid data for athlete {athlete_id}")
                return

            logger.info(f"Starting transformation for athlete {athlete_id}")

            # Initialize result DataFrames
            dataframes = self._initialize_dataframes()

            # Get clean activities and zones
            activities = self.data_loader.get_error_free_activities(
                athlete_data["_Activities"]
            )
            zones = self.data_loader.get_athlete_zones(athlete_data)

            # Build HR regressor
            regressor, not_nan_rows = build_pace_to_hr_regressor(
                activities, athlete_id, zones
            )
            if not_nan_rows is not None:
                dataframes["average_paces_and_hrs"] = pd.concat(
                    [dataframes["average_paces_and_hrs"], not_nan_rows],
                    ignore_index=True,
                )

            # Prepare athlete metadata
            dataframes["metadata_athletes"] = (
                self.database_manager.prepare_athlete_metadata(athlete_data)
            )

            # Process all activities (chronological order)
            activities.reverse()
            dataframes["all_athlete_activities"], dataframes["all_athlete_weeks"] = (
                self.activity_processor.process_activity_block(
                    activities, athlete_data, athlete_id, zones, regressor
                )
            )

            # Process PB blocks
            (
                dataframes["metadata_blocks"],
                dataframes["features_activities"],
                dataframes["features_weeks"],
            ) = self.activity_processor.process_pb_blocks(
                activities, athlete_id, zones, regressor
            )

            # Calculate block-level features
            dataframes["features_blocks"] = self._calculate_block_features(
                dataframes["metadata_blocks"],
                dataframes["features_weeks"],
                dataframes["all_athlete_weeks"],
                dataframes["features_activities"],
                dataframes["all_athlete_activities"],
                athlete_id,
            )

            # Save all dataframes to database
            self.database_manager.save_dataframes_to_db(dataframes)

            # Process and update personal bests
            self.pb_processor.process_metadata_pbs(
                athlete_data["_Activities"], athlete_id
            )

            # Update race predictions
            self.database_manager.update_race_predictions(athlete_id)

            logger.info(
                f"Successfully completed transformation for athlete {athlete_id}"
            )

        except Exception as e:
            logger.error(
                f"Error transforming athlete data for {athlete_id}: {e}", exc_info=True
            )
            raise

    def _initialize_dataframes(self) -> dict:
        """Initialize empty DataFrames for storing results."""
        return {
            "metadata_athletes": pd.DataFrame(),
            "metadata_blocks": pd.DataFrame(),
            "all_athlete_activities": pd.DataFrame(),
            "all_athlete_weeks": pd.DataFrame(),
            "features_activities": pd.DataFrame(),
            "features_weeks": pd.DataFrame(),
            "features_blocks": pd.DataFrame(),
            "average_paces_and_hrs": pd.DataFrame(),
        }

    def _calculate_block_features(
        self,
        metadata_blocks: pd.DataFrame,
        features_weeks: pd.DataFrame,
        all_athlete_weeks: pd.DataFrame,
        features_activities: pd.DataFrame,
        all_athlete_activities: pd.DataFrame,
        athlete_id: int,
    ) -> pd.DataFrame:
        """Calculate block-level features for all blocks."""
        features_blocks = pd.DataFrame()

        for _, block in metadata_blocks.iterrows():
            block_id = block["block_id"]
            block_weeks = features_weeks[features_weeks["block_id"] == block_id]
            athlete_weeks = all_athlete_weeks[
                all_athlete_weeks["athlete_id"] == athlete_id
            ]

            # Skip blocks without sufficient data
            run_distance_col = (
                "f_run_total_distance"
                if "f_run_total_distance" in block_weeks.columns
                else "f_total_run_distance"
            )

            if (
                block_weeks.empty
                or "f_total_runs" not in block_weeks.columns
                or block_weeks["f_total_runs"].mean() == 0
                or (
                    run_distance_col in block_weeks.columns
                    and block_weeks[run_distance_col][:-2].mean() == 0
                )
            ):
                continue

            # Calculate block metrics
            try:
                block_metrics = self.metrics_calculator.calculate_block_metrics(
                    block_weeks=block_weeks,
                    athlete_weeks=athlete_weeks,
                    features_activities=features_activities,
                    all_athlete_activities=all_athlete_activities,
                    block_id=block_id,
                    athlete_id=athlete_id,
                )

                # Add block identifiers and target variables
                block_metrics.update(
                    {
                        "athlete_id": athlete_id,
                        "block_id": block_id,
                        "y_vdot_delta": block["vdot_delta"],
                        "y_vdot": block["vdot"],
                    }
                )

                features_blocks = pd.concat(
                    [features_blocks, pd.DataFrame([block_metrics])], ignore_index=True
                )

            except Exception as e:
                logger.error(f"Error calculating metrics for block {block_id}: {e}")
                continue

        return features_blocks


# Legacy function for backward compatibility
def transform_athlete_data(
    athlete_id: int, athlete_data: dict = None, populate_all_from_files: int = 0
) -> None:
    """Legacy function that uses the new AthleteDataTransformer class."""
    transformer = AthleteDataTransformer()
    transformer.transform_athlete_data(
        athlete_id, athlete_data, populate_all_from_files
    )
