"""
Activity and block processing functionality for athlete analytics.
"""

import pandas as pd
import logging
from typing import List, Tuple
from search_functions import get_weeks, get_block
from running_functions import extract_activity_features, extract_week_features, get_pbs
from .constants import MIN_ACTIVITIES_PER_BLOCK

logger = logging.getLogger(__name__)


class ActivityProcessor:
    """Handles processing of activities, weeks, and training blocks."""

    def process_activity_block(
        self,
        activities: List[dict],
        athlete_data: dict,
        athlete_id: str,
        zones: List[int],
        hr_regressor,
        block_id: str = "0",
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Process a block of activities and return activity and week features."""
        activities_df = pd.DataFrame()
        weeks_df = pd.DataFrame()

        weeks = get_weeks(activities, duration_days=0, exclude_last_activity=False)

        for week_num, week in enumerate(weeks):
            week_id = f"{block_id}_{week_num}"

            # Process activities in week
            for activity in week:
                activities_df = extract_activity_features(
                    activities_df,
                    activity,
                    zones,
                    activity["type"],
                    athlete_data["id"],
                    block_id,
                    week_id,
                    hr_regressor,
                )

            # Process week features
            week_activities = activities_df[activities_df["week_id"] == week_id]
            week_runs = week_activities[week_activities["activity_type"] == 2]
            week_non_runs = week_activities[week_activities["activity_type"] != 2]

            week_features = extract_week_features(
                week_runs, week_non_runs, athlete_id, block_id, week_id, len(week_runs)
            )
            weeks_df = pd.concat(
                [weeks_df, pd.DataFrame([week_features])], ignore_index=True
            )

        return activities_df, weeks_df

    def process_pb_blocks(
        self, activities: List[dict], athlete_id: str, zones: List[int], hr_regressor
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Process personal best blocks and extract features."""
        metadata_blocks = pd.DataFrame()
        features_activities = pd.DataFrame()
        features_weeks = pd.DataFrame()

        # Get significant personal bests
        # Returns lists of [vdot, predicted marathon time (hrs), pb_date, activity_id, distance_category]
        significant_pbs = get_pbs(activities)

        for i, pb in enumerate(significant_pbs):
            activity_date, block_id = pb[2], pb[3]
            block = get_block(activities, activity_date)

            # Skip if the block is too short
            if len(block) < MIN_ACTIVITIES_PER_BLOCK:
                continue

            # Find previous VDOT for the same distance category
            prev_vdot = self._find_previous_vdot(significant_pbs, i, pb[4])
            vdot_delta = pb[0] - prev_vdot if prev_vdot is not None else 0

            # Add block metadata
            block_metadata = {
                "athlete_id": athlete_id,
                "vdot": pb[0],
                "vdot_delta": vdot_delta,
                "predicted_marathon_time": pb[1],
                "pb_date": pb[2],
                "block_id": block_id,
            }
            metadata_blocks = pd.concat(
                [metadata_blocks, pd.DataFrame([block_metadata])], ignore_index=True
            )

            # Process activities by week for this block
            block_activities, block_weeks = self.process_activity_block(
                block,  # activities list
                {"id": athlete_id},  # mock athlete_data dict with required 'id' field
                athlete_id,  # athlete_id
                zones,  # zones
                hr_regressor,  # hr_regressor
                block_id,  # block_id
            )

            features_activities = pd.concat(
                [features_activities, block_activities], ignore_index=True
            )
            features_weeks = pd.concat([features_weeks, block_weeks], ignore_index=True)

        return metadata_blocks, features_activities, features_weeks

    def _find_previous_vdot(
        self, significant_pbs: List, current_index: int, distance_category: str
    ) -> float:
        """Find the most recent previous VDOT for the same distance category."""
        for j in range(current_index - 1, -1, -1):
            if significant_pbs[j][4] == distance_category:
                return significant_pbs[j][0]
        return None
