"""
Refactored database operations using modular components.

This module provides a clean interface to the database management functionality
by using the new modular database components while maintaining backward compatibility.

Legacy functions are maintained for backward compatibility but now delegate
to the new modular components.
"""

import logging
from database.legacy_interface import _db as db

# Import all functions from the database module for backward compatibility
from database import (
    init_db,
    read_db,
    write_db_replace,
    write_db_insert,
    delete_rows,
    test_conn_new,
    reset_database,
    get_table_info,
    get_database_summary,
    validate_table_schema,
    get_db_connection,
    get_db,
)

# Re-export all legacy functions for backward compatibility
__all__ = [
    "init_db",
    "read_db",
    "write_db_replace",
    "write_db_insert",
    "delete_rows",
    "test_conn_new",
    "reset_database",
    "get_table_info",
    "get_database_summary",
    "validate_table_schema",
    "get_db_connection",
    "get_db",
    "db",
]

logger = logging.getLogger(__name__)

# Legacy compatibility - these functions are now imported from the database module
# All existing code will continue to work without changes

# All legacy functions are now imported from the database module
# and re-exported for backward compatibility
