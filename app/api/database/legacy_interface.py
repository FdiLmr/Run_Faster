"""
Legacy interface for backward compatibility with original sql_methods.py functions.

This module provides the same function signatures as the original sql_methods.py
while delegating to the new modular components.
"""

import logging
from typing import Optional
import pandas as pd
from sqlalchemy import text

from .connection_manager import DatabaseConnectionManager
from .schema_manager import SchemaManager
from .table_manager import TableManager
from .operations import DatabaseOperations

logger = logging.getLogger(__name__)

# Global instances for backward compatibility
_connection_manager = None
_schema_manager = None
_table_manager = None
_operations = None
_db = None


def _get_managers():
    """Get or create manager instances."""
    global _connection_manager, _schema_manager, _table_manager, _operations

    if _connection_manager is None:
        _connection_manager = DatabaseConnectionManager()
        _schema_manager = SchemaManager()
        _table_manager = TableManager(_connection_manager, _schema_manager)
        _operations = DatabaseOperations(
            _connection_manager, _schema_manager, _table_manager
        )

    return _connection_manager, _schema_manager, _table_manager, _operations


def init_db(app):
    """
    Initialize the database with Flask app.

    Legacy function maintained for backward compatibility.
    """
    global _db
    connection_manager, _, _, _ = _get_managers()
    connection_manager.init_app(app)
    _db = connection_manager.get_flask_db()
    logger.info("Database initialized via legacy interface")


def get_db_connection():
    """
    Get database connection engine.

    Legacy function maintained for backward compatibility.
    """
    connection_manager, _, _, _ = _get_managers()
    return connection_manager.get_engine()


def read_db(table_name: str) -> pd.DataFrame:
    """
    Read data from a database table.

    Legacy function maintained for backward compatibility.
    Delegates to DatabaseOperations.read_table().

    Args:
        table_name: Name of the table to read

    Returns:
        DataFrame with table data
    """
    _, _, _, operations = _get_managers()
    return operations.read_table(table_name)


def write_db_replace(df: pd.DataFrame, table_name: str) -> bool:
    """
    Write DataFrame to database, replacing existing table.

    Legacy function maintained for backward compatibility.
    Delegates to DatabaseOperations.write_table_replace().

    Args:
        df: DataFrame to write
        table_name: Name of the table to write to

    Returns:
        True if successful
    """
    _, _, _, operations = _get_managers()
    return operations.write_table_replace(df, table_name)


def write_db_insert(df: pd.DataFrame, table_name: str) -> bool:
    """
    Append DataFrame to existing database table.

    Legacy function maintained for backward compatibility.
    Delegates to DatabaseOperations.write_table_append().

    Args:
        df: DataFrame to append
        table_name: Name of the table to append to

    Returns:
        True if successful
    """
    _, _, _, operations = _get_managers()
    return operations.write_table_append(df, table_name)


def delete_rows(table_name: str) -> bool:
    """
    Delete all rows from a table.

    Legacy function maintained for backward compatibility.
    Delegates to DatabaseOperations.delete_rows().

    Args:
        table_name: Name of the table to delete from

    Returns:
        True if successful, False otherwise
    """
    _, _, _, operations = _get_managers()
    return operations.delete_rows(table_name)


def test_conn_new() -> str:
    """
    Test database connectivity.

    Legacy function maintained for backward compatibility.
    Delegates to DatabaseConnectionManager.test_connection().

    Returns:
        Connection status message
    """
    connection_manager, _, _, _ = _get_managers()
    success, message = connection_manager.test_connection()
    return message


def reset_database() -> bool:
    """
    Safely reset all tables.

    Legacy function maintained for backward compatibility.
    Enhanced with the new modular components.

    Returns:
        True if successful, False otherwise
    """
    try:
        global _db
        if _db is None:
            logger.error("Database not initialized, cannot reset")
            return False

        # Get table manager for better table handling
        _, _, table_manager, _ = _get_managers()

        _db.session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        _db.session.commit()

        # List of tables to truncate (from original implementation)
        tables = [
            "activities",
            "athlete_stats",
            "metadata_athletes",
            "metadata_blocks",
            "all_athlete_activities",
            "all_athlete_weeks",
            "features_activities",
            "features_weeks",
            "features_blocks",
            "average_paces_and_hrs",
            "processing_status",
            "daily_limit",
        ]

        # Truncate all tables that exist
        for table in tables:
            try:
                if table_manager.table_exists(table):
                    _db.session.execute(text(f"TRUNCATE TABLE {table}"))
                    logger.info(f"Truncated table: {table}")
                else:
                    logger.info(f"Table {table} does not exist, skipping")
            except Exception as e:
                logger.warning(f"Could not truncate {table}: {e}")

        # Reinitialize daily_limit with 0 if table exists
        if table_manager.table_exists("daily_limit"):
            _db.session.execute(text("INSERT INTO daily_limit (daily) VALUES (0)"))

        _db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        _db.session.commit()
        logger.info("Database reset completed successfully via legacy interface")
        return True

    except Exception as e:
        if _db:
            _db.session.rollback()
        logger.error(f"Error resetting database via legacy interface: {e}")
        return False


# Additional utility functions for enhanced functionality


def get_table_info(table_name: str) -> Optional[dict]:
    """
    Get information about a table.

    Enhanced function not in original sql_methods.py.

    Args:
        table_name: Name of the table

    Returns:
        Dictionary with table information
    """
    _, _, table_manager, _ = _get_managers()
    return table_manager.get_table_info(table_name)


def get_database_summary() -> dict:
    """
    Get a summary of the entire database.

    Enhanced function not in original sql_methods.py.

    Returns:
        Dictionary with database summary
    """
    _, _, table_manager, _ = _get_managers()
    return table_manager.get_database_summary()


def validate_table_schema(df: pd.DataFrame, table_name: str) -> tuple[bool, list]:
    """
    Validate a DataFrame against a table schema.

    Enhanced function not in original sql_methods.py.

    Args:
        df: DataFrame to validate
        table_name: Name of the table to validate against

    Returns:
        Tuple of (is_valid, errors)
    """
    _, schema_manager, _, _ = _get_managers()
    return schema_manager.validate_dataframe_schema(df, table_name)


def get_db():
    """
    Get the Flask-SQLAlchemy database instance.

    Legacy function maintained for backward compatibility.

    Returns:
        SQLAlchemy database instance
    """
    global _db
    if _db is None:
        connection_manager, _, _, _ = _get_managers()
        _db = connection_manager.get_flask_db()
    return _db


# Create a db object that can be imported directly
# Note: This will be None until init_db is called
db = _db


class DBProxy:
    """Proxy object that provides access to the database instance."""

    def __getattr__(self, name):
        global _db
        if _db is None:
            # Try to get from current app context if available
            try:
                from flask import current_app

                if (
                    hasattr(current_app, "extensions")
                    and "sqlalchemy" in current_app.extensions
                ):
                    _db = current_app.extensions["sqlalchemy"].db
                else:
                    # Fallback to getting from connection manager
                    connection_manager, _, _, _ = _get_managers()
                    _db = connection_manager.get_flask_db()
            except Exception:
                raise RuntimeError("Database not initialized. Call init_db(app) first.")

        return getattr(_db, name)


# Create a proxy that will work even before init_db is called
db = DBProxy()
