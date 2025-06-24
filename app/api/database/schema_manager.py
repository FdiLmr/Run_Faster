"""
Database schema management for defining and managing table schemas.

This module handles:
- Table schema definitions
- Schema validation and creation
- Default schema management
- Schema evolution and migration support
"""

import logging
from typing import Dict, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class SchemaManager:
    """
    Manages database table schemas and schema-related operations.

    This class handles:
    - Defining table schemas
    - Creating DataFrames with proper schemas
    - Validating data against schemas
    - Managing schema evolution
    """

    # Default table schemas
    DEFAULT_SCHEMAS = {
        "metadata_athletes": {
            "id": "str",
            "sex": "str",
            "weight": "float",
            "zones": "str",
        },
        "metadata_blocks": {
            "athlete_id": "str",
            "vdot": "float",
            "vdot_delta": "float",
            "predicted_marathon_time": "float",
            "pb_date": "datetime64[ns]",
            "block_id": "str",
        },
        "all_athlete_activities": {
            "athlete_id": "str",
            "block_id": "str",
            "week_id": "str",
            "activity_type": "int",
            "activity_id": "str",
            "elapsed_time": "float",
            "distance": "float",
            "mean_hr": "float",
            "stdev_hr": "float",
            "freq_hr": "float",
            "time_in_z1": "float",
            "time_in_z2": "float",
            "time_in_z3": "float",
            "time_in_z4": "float",
            "time_in_z5": "float",
            "elevation": "float",
            "stdev_elevation": "float",
            "freq_elevation": "float",
            "pace": "float",
            "stdev_pace": "float",
            "freq_pace": "float",
            "cadence": "float",
            "athlete_count": "float",
        },
        "all_athlete_weeks": {
            "athlete_id": "str",
            "block_id": "str",
            "week_id": "str",
            "f_total_runs": "int",
            "f_total_run_distance": "float",
            "f_total_run_time": "float",
            "f_total_non_run_distance": "float",
            "f_total_non_run_time": "float",
        },
        "features_activities": {
            "athlete_id": "str",
            "block_id": "str",
            "week_id": "str",
            "activity_type": "int",
            "activity_id": "str",
            "elapsed_time": "float",
            "distance": "float",
            "mean_hr": "float",
        },
        "features_weeks": {
            "athlete_id": "str",
            "block_id": "str",
            "week_id": "str",
            "f_total_runs": "int",
            "f_run_distance": "float",
            "f_run_time": "float",
            "f_non_run_distance": "float",
            "f_non_run_time": "float",
        },
        "features_blocks": {
            "athlete_id": "str",
            "block_id": "str",
            "y_vdot_delta": "float",
            "y_vdot": "float",
            "f_slope_run_distance": "float",
            "f_slope_run_time": "float",
            "f_slope_mean_run_hr": "float",
            "f_taper_factor_run_distance": "float",
            "f_taper_factor_run_time": "float",
            "f_taper_factor_mean_run_hr": "float",
        },
        "average_paces_and_hrs": {
            "athlete_id": "str",
            "mean_hr": "float",
            "pace": "float",
        },
        "processing_status": {
            "athlete_id": "str",
            "status": "str",
            "bearer_token": "str",
            "refresh_token": "str",
        },
        "activities": {
            "id": "str",
            "athlete_id": "str",
            "name": "str",
            "distance": "float",
            "moving_time": "int",
            "elapsed_time": "int",
            "total_elevation_gain": "float",
            "type": "str",
            "start_date": "datetime64[ns]",
            "average_speed": "float",
            "max_speed": "float",
            "average_heartrate": "float",
            "max_heartrate": "float",
        },
        "athlete_stats": {
            "athlete_id": "str",
            "biggest_ride_distance": "float",
            "biggest_climb_elevation_gain": "float",
            "recent_ride_totals": "str",
            "recent_run_totals": "str",
            "ytd_ride_totals": "str",
            "ytd_run_totals": "str",
            "all_ride_totals": "str",
            "all_run_totals": "str",
        },
        "daily_limit": {"daily": "int"},
    }

    def __init__(self):
        """Initialize the SchemaManager."""
        pass

    def get_schema(self, table_name: str) -> Optional[Dict[str, str]]:
        """
        Get schema definition for a table.

        Args:
            table_name: Name of the table

        Returns:
            Schema dictionary or None if not found
        """
        return self.DEFAULT_SCHEMAS.get(table_name)

    def get_all_schemas(self) -> Dict[str, Dict[str, str]]:
        """
        Get all schema definitions.

        Returns:
            Dictionary of all schemas
        """
        return self.DEFAULT_SCHEMAS.copy()

    def create_empty_dataframe(self, table_name: str) -> pd.DataFrame:
        """
        Create an empty DataFrame with the correct schema for a table.

        Args:
            table_name: Name of the table

        Returns:
            Empty DataFrame with proper schema

        Raises:
            ValueError: If schema not found for table
        """
        schema = self.get_schema(table_name)
        if schema is None:
            raise ValueError(f"No schema found for table: {table_name}")

        df = pd.DataFrame(columns=schema.keys())
        for col, dtype in schema.items():
            df[col] = pd.Series(dtype=dtype)

        logger.info(f"Created empty DataFrame for table {table_name} with schema")
        return df

    def validate_dataframe_schema(
        self, df: pd.DataFrame, table_name: str
    ) -> tuple[bool, List[str]]:
        """
        Validate a DataFrame against a table schema.

        Args:
            df: DataFrame to validate
            table_name: Name of the table to validate against

        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        schema = self.get_schema(table_name)
        if schema is None:
            return False, [f"No schema found for table: {table_name}"]

        errors = []

        # Check for missing columns
        missing_cols = set(schema.keys()) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing columns: {missing_cols}")

        # Check for extra columns
        extra_cols = set(df.columns) - set(schema.keys())
        if extra_cols:
            errors.append(f"Extra columns: {extra_cols}")

        # Check data types (basic validation)
        for col, expected_dtype in schema.items():
            if col in df.columns:
                actual_dtype = str(df[col].dtype)
                if not self._is_compatible_dtype(actual_dtype, expected_dtype):
                    errors.append(
                        f"Column {col}: expected {expected_dtype}, got {actual_dtype}"
                    )

        is_valid = len(errors) == 0
        if is_valid:
            logger.info(f"DataFrame schema validation passed for table {table_name}")
        else:
            logger.warning(
                f"DataFrame schema validation failed for table {table_name}: {errors}"
            )

        return is_valid, errors

    def _is_compatible_dtype(self, actual: str, expected: str) -> bool:
        """
        Check if actual data type is compatible with expected type.

        Args:
            actual: Actual pandas dtype as string
            expected: Expected dtype as string

        Returns:
            True if compatible, False otherwise
        """
        # Basic compatibility mapping
        compatibility_map = {
            "str": ["object", "string"],
            "int": ["int64", "int32", "int16", "int8"],
            "float": [
                "float64",
                "float32",
                "int64",
                "int32",
            ],  # int can be converted to float
            "datetime64[ns]": ["datetime64[ns]", "object"],
        }

        compatible_types = compatibility_map.get(expected, [expected])
        return actual in compatible_types

    def apply_schema_to_dataframe(
        self, df: pd.DataFrame, table_name: str
    ) -> pd.DataFrame:
        """
        Apply schema to a DataFrame, creating missing columns and converting types.

        Args:
            df: DataFrame to apply schema to
            table_name: Name of the table schema to apply

        Returns:
            DataFrame with schema applied

        Raises:
            ValueError: If schema not found for table
        """
        schema = self.get_schema(table_name)
        if schema is None:
            raise ValueError(f"No schema found for table: {table_name}")

        # Create a copy to avoid modifying original
        result_df = df.copy()

        # Add missing columns with default values
        for col, dtype in schema.items():
            if col not in result_df.columns:
                if dtype == "str":
                    result_df[col] = ""
                elif dtype in ["int", "float"]:
                    result_df[col] = 0
                elif dtype == "datetime64[ns]":
                    result_df[col] = pd.NaT
                else:
                    result_df[col] = None

        # Reorder columns to match schema
        result_df = result_df[list(schema.keys())]

        logger.info(f"Applied schema to DataFrame for table {table_name}")
        return result_df

    def get_table_names(self) -> List[str]:
        """
        Get list of all table names with defined schemas.

        Returns:
            List of table names
        """
        return list(self.DEFAULT_SCHEMAS.keys())

    def add_schema(self, table_name: str, schema: Dict[str, str]) -> None:
        """
        Add a new schema definition.

        Args:
            table_name: Name of the table
            schema: Schema definition dictionary
        """
        self.DEFAULT_SCHEMAS[table_name] = schema.copy()
        logger.info(f"Added schema for table {table_name}")

    def remove_schema(self, table_name: str) -> bool:
        """
        Remove a schema definition.

        Args:
            table_name: Name of the table

        Returns:
            True if removed, False if not found
        """
        if table_name in self.DEFAULT_SCHEMAS:
            del self.DEFAULT_SCHEMAS[table_name]
            logger.info(f"Removed schema for table {table_name}")
            return True
        return False
