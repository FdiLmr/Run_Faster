"""
Database table management for handling table operations and data manipulation.

This module handles:
- Table existence checking
- Table creation and deletion
- Table metadata operations
- Table inspection and analysis
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import inspect, text
from .connection_manager import DatabaseConnectionManager
from .schema_manager import SchemaManager

logger = logging.getLogger(__name__)


class TableManager:
    """
    Manages database table operations and metadata.

    This class handles:
    - Checking table existence
    - Creating and dropping tables
    - Getting table information
    - Managing table metadata
    """

    def __init__(
        self,
        connection_manager: DatabaseConnectionManager,
        schema_manager: SchemaManager,
    ):
        """
        Initialize the TableManager.

        Args:
            connection_manager: Database connection manager instance
            schema_manager: Schema manager instance
        """
        self.connection_manager = connection_manager
        self.schema_manager = schema_manager

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of the table to check

        Returns:
            True if table exists, False otherwise
        """
        try:
            engine = self.connection_manager.get_engine()
            inspector = inspect(engine)
            exists = table_name in inspector.get_table_names()

            logger.debug(f"Table {table_name} exists: {exists}")
            return exists

        except Exception as e:
            logger.error(f"Error checking if table {table_name} exists: {e}")
            return False

    def get_table_names(self) -> List[str]:
        """
        Get list of all tables in the database.

        Returns:
            List of table names
        """
        try:
            engine = self.connection_manager.get_engine()
            inspector = inspect(engine)
            tables = inspector.get_table_names()

            logger.info(f"Found {len(tables)} tables in database")
            return tables

        except Exception as e:
            logger.error(f"Error getting table names: {e}")
            return []

    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a table.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with table information or None if error
        """
        try:
            if not self.table_exists(table_name):
                return None

            engine = self.connection_manager.get_engine()
            inspector = inspect(engine)

            # Get column information
            columns = inspector.get_columns(table_name)

            # Get row count
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = result.scalar()

            info = {
                "table_name": table_name,
                "exists": True,
                "row_count": row_count,
                "column_count": len(columns),
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col["nullable"],
                        "default": col["default"],
                    }
                    for col in columns
                ],
            }

            logger.info(
                f"Retrieved info for table {table_name}: {row_count} rows, {len(columns)} columns"
            )
            return info

        except Exception as e:
            logger.error(f"Error getting table info for {table_name}: {e}")
            return None

    def drop_table(self, table_name: str) -> bool:
        """
        Drop a table from the database.

        Args:
            table_name: Name of the table to drop

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.table_exists(table_name):
                logger.warning(f"Table {table_name} does not exist, cannot drop")
                return False

            engine = self.connection_manager.get_engine()
            with engine.connect() as conn:
                conn.execute(text(f"DROP TABLE {table_name}"))
                conn.commit()

            logger.info(f"Successfully dropped table {table_name}")
            return True

        except Exception as e:
            logger.error(f"Error dropping table {table_name}: {e}")
            return False

    def truncate_table(self, table_name: str) -> bool:
        """
        Truncate a table (remove all data but keep structure).

        Args:
            table_name: Name of the table to truncate

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.table_exists(table_name):
                logger.warning(f"Table {table_name} does not exist, cannot truncate")
                return False

            engine = self.connection_manager.get_engine()
            with engine.connect() as conn:
                conn.execute(text(f"TRUNCATE TABLE {table_name}"))
                conn.commit()

            logger.info(f"Successfully truncated table {table_name}")
            return True

        except Exception as e:
            logger.error(f"Error truncating table {table_name}: {e}")
            return False

    def create_table_from_schema(self, table_name: str) -> bool:
        """
        Create a table using the predefined schema.

        Args:
            table_name: Name of the table to create

        Returns:
            True if successful, False otherwise
        """
        try:
            schema = self.schema_manager.get_schema(table_name)
            if schema is None:
                logger.error(f"No schema found for table {table_name}")
                return False

            # Create empty DataFrame with schema
            df = self.schema_manager.create_empty_dataframe(table_name)

            # Use pandas to_sql to create the table
            engine = self.connection_manager.get_engine()
            df.to_sql(name=table_name, con=engine, if_exists="replace", index=False)

            logger.info(f"Successfully created table {table_name} from schema")
            return True

        except Exception as e:
            logger.error(f"Error creating table {table_name} from schema: {e}")
            return False

    def get_table_size(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get size information for a table.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with size information or None if error
        """
        try:
            if not self.table_exists(table_name):
                return None

            engine = self.connection_manager.get_engine()
            with engine.connect() as conn:
                # Get table size information
                query = text(
                    """
                    SELECT 
                        table_name,
                        ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb,
                        table_rows,
                        data_length,
                        index_length
                    FROM information_schema.TABLES 
                    WHERE table_schema = DATABASE() 
                    AND table_name = :table_name
                """
                )

                result = conn.execute(query, {"table_name": table_name})
                row = result.fetchone()

                if row:
                    size_info = {
                        "table_name": row[0],
                        "size_mb": float(row[1]) if row[1] else 0.0,
                        "row_count": int(row[2]) if row[2] else 0,
                        "data_length": int(row[3]) if row[3] else 0,
                        "index_length": int(row[4]) if row[4] else 0,
                    }

                    logger.info(
                        f"Table {table_name} size: {size_info['size_mb']} MB, {size_info['row_count']} rows"
                    )
                    return size_info

                return None

        except Exception as e:
            logger.error(f"Error getting table size for {table_name}: {e}")
            return None

    def get_database_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all tables in the database.

        Returns:
            Dictionary with database summary information
        """
        try:
            table_names = self.get_table_names()
            total_tables = len(table_names)
            total_rows = 0
            total_size_mb = 0.0

            table_details = []

            for table_name in table_names:
                info = self.get_table_info(table_name)
                size_info = self.get_table_size(table_name)

                if info and size_info:
                    total_rows += info["row_count"]
                    total_size_mb += size_info["size_mb"]

                    table_details.append(
                        {
                            "name": table_name,
                            "rows": info["row_count"],
                            "columns": info["column_count"],
                            "size_mb": size_info["size_mb"],
                        }
                    )

            summary = {
                "total_tables": total_tables,
                "total_rows": total_rows,
                "total_size_mb": round(total_size_mb, 2),
                "tables": table_details,
            }

            logger.info(
                f"Database summary: {total_tables} tables, {total_rows} total rows, {total_size_mb:.2f} MB"
            )
            return summary

        except Exception as e:
            logger.error(f"Error getting database summary: {e}")
            return {
                "total_tables": 0,
                "total_rows": 0,
                "total_size_mb": 0.0,
                "tables": [],
                "error": str(e),
            }
