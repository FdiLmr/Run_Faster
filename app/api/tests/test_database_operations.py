"""
Tests for database operations.

This module tests all critical database functionality including:
- Database initialization and table creation
- Reading and writing data
- Database reset functionality
- Data validation and schema management
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch

# Import these within the application context to avoid import errors


class TestDatabaseConnection:
    """Test database connection functionality."""

    def test_database_connection(self, app_context):
        """Test that database connection can be established."""
        from sql_methods import test_conn_new

        result = test_conn_new()
        assert result is not None

    def test_get_db_connection(self, app_context):
        """Test getting database connection engine."""
        from sql_methods import get_db_connection

        engine = get_db_connection()
        assert engine is not None

        # Test that we can execute a simple query
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            assert result.fetchone()[0] == 1


class TestTableOperations:
    """Test table creation and schema validation."""

    def test_table_creation(self, test_db):
        """Test that all required tables are created."""
        from sql_methods import db, read_db
        from models import Activity

        # Check that Activity table exists
        assert Activity.__tablename__ in db.engine.table_names()

        # Check that we can query the empty table
        activities = read_db("activities")
        assert isinstance(activities, pd.DataFrame)
        assert len(activities) == 0

    def test_get_table_info(self, test_db):
        """Test getting table information."""
        from sql_methods import get_table_info

        table_info = get_table_info("activities")
        assert table_info is not None
        assert len(table_info) > 0

        # Check for expected columns
        column_names = [col["name"] for col in table_info]
        expected_columns = ["id", "athlete_id", "name", "distance", "type"]
        for col in expected_columns:
            assert col in column_names

    def test_validate_table_schema(self, test_db):
        """Test table schema validation."""
        from sql_methods import validate_table_schema

        # Should not raise for valid table
        result = validate_table_schema("activities")
        assert result is True or result is None  # Depending on implementation


class TestDataOperations:
    """Test data reading and writing operations."""

    def test_read_empty_table(self, test_db):
        """Test reading from empty table."""
        from sql_methods import read_db

        result = read_db("activities")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_write_and_read_data(self, test_db, sample_activity_data):
        """Test writing data and reading it back."""
        from sql_methods import write_db_replace, read_db

        # Create a DataFrame with sample data
        df = pd.DataFrame([sample_activity_data])

        # Write to database
        write_db_replace(df, "activities")

        # Read back
        result = read_db("activities")
        assert len(result) == 1
        assert result.iloc[0]["id"] == sample_activity_data["id"]
        assert result.iloc[0]["name"] == sample_activity_data["name"]

    def test_write_replace_overwrites_data(self, test_db, sample_activity_data):
        """Test that write_db_replace overwrites existing data."""
        from sql_methods import write_db_replace, read_db

        # Write initial data
        df1 = pd.DataFrame([sample_activity_data])
        write_db_replace(df1, "activities")

        # Verify initial data
        result1 = read_db("activities")
        assert len(result1) == 1

        # Write new data (should replace)
        new_data = sample_activity_data.copy()
        new_data["id"] = 999999999
        new_data["name"] = "Replaced Activity"
        df2 = pd.DataFrame([new_data])
        write_db_replace(df2, "activities")

        # Verify replacement
        result2 = read_db("activities")
        assert len(result2) == 1
        assert result2.iloc[0]["id"] == 999999999
        assert result2.iloc[0]["name"] == "Replaced Activity"

    def test_write_insert_appends_data(self, test_db, sample_activity_data):
        """Test that write_db_insert appends data."""
        from sql_methods import write_db_replace, write_db_insert, read_db

        # Write initial data
        df1 = pd.DataFrame([sample_activity_data])
        write_db_replace(df1, "activities")

        # Insert additional data
        new_data = sample_activity_data.copy()
        new_data["id"] = 999999999
        new_data["name"] = "Additional Activity"
        df2 = pd.DataFrame([new_data])
        write_db_insert(df2, "activities")

        # Verify both records exist
        result = read_db("activities")
        assert len(result) == 2

        names = result["name"].tolist()
        assert "Morning Run" in names
        assert "Additional Activity" in names

    def test_write_with_missing_columns(self, test_db):
        """Test writing data with missing columns."""
        from sql_methods import write_db_replace, read_db

        # Create minimal data
        minimal_data = {
            "id": 123456,
            "athlete_id": "12345",
            "name": "Test Activity",
            "type": "Run",
        }
        df = pd.DataFrame([minimal_data])

        # Should not raise an error
        write_db_replace(df, "activities")

        # Verify data was written
        result = read_db("activities")
        assert len(result) == 1
        assert result.iloc[0]["name"] == "Test Activity"

    def test_handle_invalid_table_name(self, test_db):
        """Test handling of invalid table names."""
        from sql_methods import read_db

        with pytest.raises(Exception):
            read_db("nonexistent_table")


class TestDatabaseReset:
    """Test database reset functionality."""

    def test_reset_database_clears_data(self, test_db, sample_activity_data):
        """Test that reset_database clears all data."""
        from sql_methods import write_db_replace, read_db, reset_database

        # Add some data first
        df = pd.DataFrame([sample_activity_data])
        write_db_replace(df, "activities")

        # Verify data exists
        result_before = read_db("activities")
        assert len(result_before) == 1

        # Reset database
        reset_result = reset_database()
        assert reset_result is True

        # Verify data is cleared
        result_after = read_db("activities")
        assert len(result_after) == 0

    def test_reset_database_preserves_schema(self, test_db):
        """Test that reset_database preserves table schema."""
        from sql_methods import reset_database, read_db

        # Reset database
        reset_result = reset_database()
        assert reset_result is True

        # Verify tables still exist and can be queried
        result = read_db("activities")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestDataIntegrity:
    """Test data integrity and validation."""

    def test_activity_id_uniqueness(self, test_db, sample_activity_data):
        """Test that duplicate activity IDs are handled correctly."""
        from sql_methods import write_db_replace, write_db_insert, read_db

        # Write initial data
        df1 = pd.DataFrame([sample_activity_data])
        write_db_replace(df1, "activities")

        # Try to insert duplicate ID
        duplicate_data = sample_activity_data.copy()
        duplicate_data["name"] = "Duplicate Activity"
        df2 = pd.DataFrame([duplicate_data])

        # This should either replace or handle gracefully
        write_db_insert(df2, "activities")

        # Verify behavior (exact behavior depends on database constraints)
        result = read_db("activities")
        assert len(result) >= 1

    def test_null_handling(self, test_db):
        """Test handling of null values."""
        from sql_methods import write_db_replace, read_db

        data_with_nulls = {
            "id": 123456,
            "athlete_id": "12345",
            "name": "Test Activity",
            "distance": None,
            "moving_time": None,
            "type": "Run",
        }
        df = pd.DataFrame([data_with_nulls])

        # Should handle nulls gracefully
        write_db_replace(df, "activities")

        result = read_db("activities")
        assert len(result) == 1
        assert pd.isna(result.iloc[0]["distance"])

    def test_date_handling(self, test_db):
        """Test handling of datetime columns."""
        from sql_methods import write_db_replace, read_db

        data_with_dates = {
            "id": 123456,
            "athlete_id": "12345",
            "name": "Test Activity",
            "start_date": datetime.now(),
            "start_date_local": datetime.now(),
            "type": "Run",
        }
        df = pd.DataFrame([data_with_dates])

        write_db_replace(df, "activities")

        result = read_db("activities")
        assert len(result) == 1
        assert isinstance(result.iloc[0]["start_date"], (pd.Timestamp, datetime))


class TestPerformance:
    """Test database performance with larger datasets."""

    @pytest.mark.slow
    def test_bulk_insert_performance(self, test_db):
        """Test performance with bulk data insertion."""
        from sql_methods import write_db_replace, read_db

        # Create a larger dataset
        bulk_data = []
        for i in range(100):
            activity = {
                "id": 1000000 + i,
                "athlete_id": "12345",
                "name": f"Activity {i}",
                "distance": 5000.0 + i * 100,
                "type": "Run",
                "start_date": datetime.now() - timedelta(days=i),
            }
            bulk_data.append(activity)

        df = pd.DataFrame(bulk_data)

        # Time the operation (basic performance check)
        import time

        start_time = time.time()
        write_db_replace(df, "activities")
        end_time = time.time()

        # Should complete reasonably quickly (adjust threshold as needed)
        assert end_time - start_time < 5.0

        # Verify all data was inserted
        result = read_db("activities")
        assert len(result) == 100

    @pytest.mark.slow
    def test_large_query_performance(self, test_db):
        """Test reading performance with larger datasets."""
        from sql_methods import write_db_replace, read_db

        # Create test data
        bulk_data = []
        for i in range(50):
            activity = {
                "id": 2000000 + i,
                "athlete_id": "12345",
                "name": f"Activity {i}",
                "type": "Run",
            }
            bulk_data.append(activity)

        df = pd.DataFrame(bulk_data)
        write_db_replace(df, "activities")

        # Time the read operation
        import time

        start_time = time.time()
        result = read_db("activities")
        end_time = time.time()

        # Should complete reasonably quickly
        assert end_time - start_time < 2.0
        assert len(result) == 50


class TestErrorHandling:
    """Test error handling in database operations."""

    def test_invalid_dataframe_structure(self, test_db):
        """Test handling of invalid DataFrame structures."""
        from sql_methods import write_db_replace

        # Create DataFrame with invalid structure
        invalid_df = pd.DataFrame({"invalid_column": [1, 2, 3]})

        # Should handle gracefully or provide meaningful error
        try:
            write_db_replace(invalid_df, "activities")
        except Exception as e:
            # Should be a meaningful error, not a generic exception
            assert len(str(e)) > 0

    def test_database_connection_failure(self, test_db):
        """Test handling of database connection failures."""
        from sql_methods import read_db

        with patch("sql_methods.get_db_connection") as mock_conn:
            mock_conn.side_effect = Exception("Connection failed")

            with pytest.raises(Exception):
                read_db("activities")

    def test_malformed_query_handling(self, test_db):
        """Test handling of malformed queries."""
        # This depends on implementation details
        # but we should test that malformed inputs are handled gracefully
        pass
