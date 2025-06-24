"""
Data retrieval module for race prediction.

Handles fetching personal best performances from the database.
"""

import logging
import pandas as pd
from typing import Optional, Dict, Tuple
from sql_methods import read_db
from running_functions import calculate_vdot
from .config import METADATA_PBS_TABLE, DISTANCE_CATEGORIES

logger = logging.getLogger(__name__)


class PersonalBestRetriever:
    """Handles retrieval of personal best performances for athletes."""

    def __init__(self):
        self.table_name = METADATA_PBS_TABLE
        self.distance_categories = DISTANCE_CATEGORIES

    def get_athlete_personal_bests(self, athlete_id: str) -> Optional[Dict]:
        """
        Get athlete's 5K and 10K personal bests.

        Args:
            athlete_id: Athlete's ID

        Returns:
            Dictionary with PB data or None if insufficient data
        """
        try:
            # Read the entire metadata_pbs table and filter in Python
            pbs_df = read_db(self.table_name)

            if pbs_df.empty:
                logger.warning(f"No PB data found in {self.table_name}")
                return None

            # Filter for this athlete's data
            athlete_pbs = pbs_df[pbs_df["athlete_id"] == athlete_id]

            if athlete_pbs.empty:
                logger.warning(f"No PB data found for athlete {athlete_id}")
                return None

            # Get 5K and 10K personal bests
            pb_5k = self._get_best_performance(athlete_pbs, "5K")
            pb_10k = self._get_best_performance(athlete_pbs, "10K")

            if pb_5k is None or pb_10k is None:
                logger.warning(f"Missing 5K or 10K PB for athlete {athlete_id}")
                return None

            return {"5K": pb_5k, "10K": pb_10k}

        except Exception as e:
            logger.error(
                f"Error retrieving personal bests for athlete {athlete_id}: {e}"
            )
            return None

    def calculate_vdot_scores(self, personal_bests: Dict) -> Tuple[float, float]:
        """
        Calculate VDOT scores for 5K and 10K performances.

        Args:
            personal_bests: Dictionary with 5K and 10K PB data

        Returns:
            Tuple of (vdot_5k, vdot_10k)
        """
        try:
            pb_5k = personal_bests["5K"]
            pb_10k = personal_bests["10K"]

            # Calculate VDOT for both performances
            # Convert seconds to minutes for the calculate_vdot function
            vdot_5k, _ = calculate_vdot(
                pb_5k["distance"],  # distance in meters
                pb_5k["elapsed_time"] / 60,  # convert seconds to minutes
            )

            vdot_10k, _ = calculate_vdot(
                pb_10k["distance"],  # distance in meters
                pb_10k["elapsed_time"] / 60,  # convert seconds to minutes
            )

            logger.info(f"Calculated VDOTs: 5K={vdot_5k}, 10K={vdot_10k}")

            return vdot_5k, vdot_10k

        except Exception as e:
            logger.error(f"Error calculating VDOT scores: {e}")
            return 0, 0

    def select_best_performance(
        self, personal_bests: Dict, vdot_5k: float, vdot_10k: float
    ) -> Dict:
        """
        Select the performance with better VDOT as base for predictions.

        Args:
            personal_bests: Dictionary with 5K and 10K PB data
            vdot_5k: VDOT score for 5K performance
            vdot_10k: VDOT score for 10K performance

        Returns:
            Dictionary with best performance data
        """
        if vdot_5k >= vdot_10k:
            best_pb = personal_bests["5K"]
            logger.info(f"Using 5K as base performance (better VDOT={vdot_5k})")
        else:
            best_pb = personal_bests["10K"]
            logger.info(f"Using 10K as base performance (better VDOT={vdot_10k})")

        return {
            "distance": best_pb["distance"],
            "time": best_pb["elapsed_time"],
            "vdot": max(vdot_5k, vdot_10k),
        }

    def _get_best_performance(
        self, athlete_pbs: pd.DataFrame, distance_category: str
    ) -> Optional[Dict]:
        """
        Get the best performance for a specific distance category.

        Args:
            athlete_pbs: DataFrame with athlete's PB data
            distance_category: Distance category (e.g., '5K', '10K')

        Returns:
            Dictionary with best performance data or None
        """
        try:
            # Get all performances for this distance category and sort by elapsed_time
            category_pbs = athlete_pbs[
                athlete_pbs["distance_category"] == distance_category
            ].sort_values("elapsed_time")

            if category_pbs.empty:
                return None

            # Return the fastest performance
            return category_pbs.iloc[0].to_dict()

        except Exception as e:
            logger.error(f"Error getting best {distance_category} performance: {e}")
            return None

    def get_athlete_pb_summary(self, athlete_id: str) -> Optional[Dict]:
        """
        Get a complete summary of athlete's PB data for predictions.

        Args:
            athlete_id: Athlete's ID

        Returns:
            Dictionary with complete PB summary or None
        """
        try:
            # Get personal bests
            personal_bests = self.get_athlete_personal_bests(athlete_id)
            if not personal_bests:
                return None

            # Calculate VDOT scores
            vdot_5k, vdot_10k = self.calculate_vdot_scores(personal_bests)
            if vdot_5k == 0 and vdot_10k == 0:
                return None

            # Select best performance
            best_performance = self.select_best_performance(
                personal_bests, vdot_5k, vdot_10k
            )

            return {
                "personal_bests": personal_bests,
                "vdot_scores": {"5K": vdot_5k, "10K": vdot_10k},
                "best_performance": best_performance,
            }

        except Exception as e:
            logger.error(f"Error getting PB summary for athlete {athlete_id}: {e}")
            return None
