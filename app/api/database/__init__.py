"""
Database management module for handling database connections, operations, and schema management.
"""

from .connection_manager import DatabaseConnectionManager
from .table_manager import TableManager
from .schema_manager import SchemaManager
from .operations import DatabaseOperations

# Legacy function imports for backward compatibility
from .legacy_interface import (
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
    db,
)

__all__ = [
    "DatabaseConnectionManager",
    "TableManager",
    "SchemaManager",
    "DatabaseOperations",
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
