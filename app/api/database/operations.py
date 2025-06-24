"""
Core database operations for reading and writing data.

This module handles:
- Reading data from database tables
- Writing data to database tables
- Data validation and transformation
- Bulk operations and transactions
"""

import logging
from typing import Optional, Dict
import pandas as pd
from sqlalchemy import text
from .connection_manager import DatabaseConnectionManager
from .schema_manager import SchemaManager
from .table_manager import TableManager

logger = logging.getLogger(__name__)


class DatabaseOperations:
    """
    Handles core database read and write operations.

    This class provides:
    - Reading data from tables
    - Writing data to tables with schema validation
    - Bulk operations
    - Transaction management
    """

    def __init__(
        self,
        connection_manager: DatabaseConnectionManager,
        schema_manager: SchemaManager,
        table_manager: TableManager,
    ):
        """
        Initialize the DatabaseOperations.

        Args:
            connection_manager: Database connection manager instance
            schema_manager: Schema manager instance
            table_manager: Table manager instance
        """
        self.connection_manager = connection_manager
        self.schema_manager = schema_manager
        self.table_manager = table_manager

    def read_table(self, table_name: str) -> pd.DataFrame:
        """
        Read data from a database table.

        Args:
            table_name: Name of the table to read

        Returns:
            DataFrame with table data, empty DataFrame if error or table doesn't exist
        """
        try:
            engine = self.connection_manager.get_engine()
            logger.info(f"Reading from table {table_name}")

            # Check if table exists first
            if not self.table_manager.table_exists(table_name):
                logger.info(
                    f"Table {table_name} does not exist yet, returning empty DataFrame"
                )
                return pd.DataFrame()

            df = pd.read_sql_table(table_name, engine)
            logger.info(f"Read {len(df)} rows from {table_name}")
            return df

        except Exception as e:
            logger.error(
                f"Error reading from database table {table_name}: {e}", exc_info=True
            )
            # Return empty DataFrame instead of raising error
            return pd.DataFrame()

    def write_table_replace(
        self, df: pd.DataFrame, table_name: str, validate_schema: bool = True
    ) -> bool:
        """
        Write DataFrame to database, replacing existing table.

        Args:
            df: DataFrame to write
            table_name: Name of the table to write to
            validate_schema: Whether to validate against schema

        Returns:
            True if successful, False otherwise
        """
        try:
            # Don't try to write empty DataFrames without schema
            if df.empty and len(df.columns) == 0:
                logger.info(
                    f"Skipping write for empty DataFrame without schema: {table_name}"
                )
                return True

            engine = self.connection_manager.get_engine()
            logger.info(f"Writing {len(df)} rows to table {table_name}")

            # Apply schema if DataFrame is empty but we have a schema definition
            if df.empty and validate_schema:
                schema = self.schema_manager.get_schema(table_name)
                if schema:
                    df = self.schema_manager.create_empty_dataframe(table_name)
                    logger.info(f"Applied schema to empty DataFrame for {table_name}")

            # Validate schema if requested
            if validate_schema and not df.empty:
                is_valid, errors = self.schema_manager.validate_dataframe_schema(
                    df, table_name
                )
                if not is_valid:
                    logger.warning(
                        f"Schema validation failed for {table_name}: {errors}"
                    )
                    # Continue anyway but log the issues

            # Write to database
            df.to_sql(name=table_name, con=engine, if_exists="replace", index=False)

            # Verify write
            with engine.connect() as conn:
                count = conn.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                ).scalar()
                logger.info(f"Written {count} rows to {table_name}")

            return True

        except Exception as e:
            logger.error(
                f"Error writing to database table {table_name}: {e}", exc_info=True
            )
            raise

    def write_table_append(
        self, df: pd.DataFrame, table_name: str, validate_schema: bool = True
    ) -> bool:
        """
        Append DataFrame to existing database table.

        Args:
            df: DataFrame to append
            table_name: Name of the table to append to
            validate_schema: Whether to validate against schema

        Returns:
            True if successful, False otherwise
        """
        try:
            if df.empty:
                logger.info(f"Skipping append for empty DataFrame: {table_name}")
                return True

            engine = self.connection_manager.get_engine()
            logger.info(f"Appending {len(df)} rows to table {table_name}")

            # Validate schema if requested
            if validate_schema:
                is_valid, errors = self.schema_manager.validate_dataframe_schema(
                    df, table_name
                )
                if not is_valid:
                    logger.warning(
                        f"Schema validation failed for {table_name}: {errors}"
                    )
                    # Continue anyway but log the issues

            # Append to database
            df.to_sql(name=table_name, con=engine, if_exists="append", index=False)

            logger.info(f"Successfully appended {len(df)} rows to {table_name}")
            return True

        except Exception as e:
            logger.error(
                f"Error appending to database table {table_name}: {e}", exc_info=True
            )
            raise

    def delete_rows(self, table_name: str, condition: Optional[str] = None) -> bool:
        """
        Delete rows from a table.

        Args:
            table_name: Name of the table
            condition: Optional WHERE condition (if None, deletes all rows)

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.table_manager.table_exists(table_name):
                logger.warning(f"Table {table_name} does not exist, cannot delete rows")
                return False

            engine = self.connection_manager.get_engine()

            if condition:
                query = f"DELETE FROM {table_name} WHERE {condition}"
            else:
                query = f"DELETE FROM {table_name}"

            with engine.connect() as conn:
                result = conn.execute(text(query))
                conn.commit()

                rows_affected = result.rowcount
                logger.info(f"Deleted {rows_affected} rows from {table_name}")
                return True

        except Exception as e:
            logger.error(f"Error deleting rows from {table_name}: {e}")
            return False

    def execute_query(
        self, query: str, params: Optional[Dict] = None
    ) -> Optional[pd.DataFrame]:
        """
        Execute a custom SQL query and return results as DataFrame.

        Args:
            query: SQL query to execute
            params: Optional query parameters

        Returns:
            DataFrame with query results, None if error
        """
        try:
            engine = self.connection_manager.get_engine()

            if params:
                df = pd.read_sql_query(query, engine, params=params)
            else:
                df = pd.read_sql_query(query, engine)

            logger.info(f"Query executed successfully, returned {len(df)} rows")
            return df

        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return None

    def bulk_write_tables(
        self, table_data: Dict[str, pd.DataFrame], validate_schemas: bool = True
    ) -> Dict[str, bool]:
        """
        Write multiple DataFrames to their respective tables.

        Args:
            table_data: Dictionary mapping table names to DataFrames
            validate_schemas: Whether to validate schemas

        Returns:
            Dictionary mapping table names to success status
        """
        results = {}

        for table_name, df in table_data.items():
            try:
                success = self.write_table_replace(df, table_name, validate_schemas)
                results[table_name] = success

            except Exception as e:
                logger.error(f"Error in bulk write for table {table_name}: {e}")
                results[table_name] = False

        successful_writes = sum(1 for success in results.values() if success)
        logger.info(
            f"Bulk write completed: {successful_writes}/{len(table_data)} tables successful"
        )

        return results

    def get_table_sample(self, table_name: str, limit: int = 10) -> pd.DataFrame:
        """
        Get a sample of rows from a table.

        Args:
            table_name: Name of the table
            limit: Number of rows to return

        Returns:
            DataFrame with sample data
        """
        try:
            if not self.table_manager.table_exists(table_name):
                logger.warning(f"Table {table_name} does not exist")
                return pd.DataFrame()

            engine = self.connection_manager.get_engine()
            query = f"SELECT * FROM {table_name} LIMIT {limit}"

            df = pd.read_sql_query(query, engine)
            logger.info(f"Retrieved {len(df)} sample rows from {table_name}")
            return df

        except Exception as e:
            logger.error(f"Error getting sample from {table_name}: {e}")
            return pd.DataFrame()
