"""
Database connection management for handling database connections and configuration.

This module handles:
- Database connection creation and management
- Connection pooling and configuration
- Environment-based database configuration
- Connection testing and validation
"""

import os
import logging
from typing import Optional
from sqlalchemy import create_engine, text, Engine
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """
    Manages database connections and configuration.

    This class handles:
    - Creating database engines
    - Managing connection parameters
    - Testing database connectivity
    - Providing connection instances
    """

    def __init__(self):
        """Initialize the DatabaseConnectionManager."""
        self.db = SQLAlchemy()
        self._engine: Optional[Engine] = None

    def init_app(self, app) -> None:
        """
        Initialize the database with Flask app.

        Args:
            app: Flask application instance
        """
        self.db.init_app(app)
        logger.info("Database initialized with Flask app")

    def get_connection_string(self) -> str:
        """
        Build database connection string from environment variables.

        Returns:
            Database connection string

        Raises:
            ValueError: If required environment variables are missing
        """
        required_vars = ["DB_USER", "DB_PASS", "DB_HOST", "DB_NAME"]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")

        return (
            f'mysql+pymysql://{os.environ.get("DB_USER")}:'
            f'{os.environ.get("DB_PASS")}@{os.environ.get("DB_HOST")}/'
            f'{os.environ.get("DB_NAME")}'
        )

    def create_engine(self, **kwargs) -> Engine:
        """
        Create a new database engine.

        Args:
            **kwargs: Additional engine configuration options

        Returns:
            SQLAlchemy Engine instance
        """
        connection_string = self.get_connection_string()

        # Default engine configuration
        engine_config = {"pool_pre_ping": True, "pool_recycle": 3600, "echo": False}
        engine_config.update(kwargs)

        engine = create_engine(connection_string, **engine_config)
        logger.info("Database engine created successfully")
        return engine

    def get_engine(self) -> Engine:
        """
        Get or create the database engine.

        Returns:
            SQLAlchemy Engine instance
        """
        if self._engine is None:
            self._engine = self.create_engine()
        return self._engine

    def test_connection(self) -> tuple[bool, str]:
        """
        Test database connectivity.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            engine = self.get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info("Database connection test successful")
            return True, "Connection successful!"

        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def get_flask_db(self) -> SQLAlchemy:
        """
        Get the Flask-SQLAlchemy database instance.

        Returns:
            SQLAlchemy instance for Flask integration
        """
        return self.db

    def close_connection(self) -> None:
        """Close the database engine if it exists."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            logger.info("Database engine closed")

    def get_connection_info(self) -> dict:
        """
        Get database connection information (without sensitive data).

        Returns:
            Dictionary with connection information
        """
        return {
            "host": os.environ.get("DB_HOST", "Not set"),
            "database": os.environ.get("DB_NAME", "Not set"),
            "user": os.environ.get("DB_USER", "Not set"),
            "engine_created": self._engine is not None,
        }
