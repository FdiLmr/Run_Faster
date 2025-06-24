"""
Simple tests to verify the testing setup is working.

These tests don't require complex imports and can verify that the basic
test infrastructure is functioning correctly.
"""

import pytest
import os


class TestBasicSetup:
    """Test basic testing setup."""

    def test_pytest_working(self):
        """Test that pytest is working correctly."""
        assert True
        assert 1 + 1 == 2
        assert "test" in "testing"

    def test_environment_variables(self):
        """Test that test environment variables are set."""
        assert os.environ.get("FLASK_ENV") == "testing"
        assert os.environ.get("CLIENT_ID") == "test_client_id"
        assert os.environ.get("CLIENT_SECRET") == "test_client_secret"

    @pytest.mark.unit
    def test_unit_marker(self):
        """Test that unit test marker works."""
        assert True

    @pytest.mark.integration
    def test_integration_marker(self):
        """Test that integration test marker works."""
        assert True

    @pytest.mark.slow
    def test_slow_marker(self):
        """Test that slow test marker works."""
        import time

        time.sleep(0.1)  # Simulate slow test
        assert True


class TestFixtures:
    """Test that fixtures are working."""

    def test_sample_athlete_data_fixture(self, sample_athlete_data):
        """Test sample athlete data fixture."""
        assert sample_athlete_data is not None
        assert sample_athlete_data["id"] == 12345
        assert "firstname" in sample_athlete_data
        assert "username" in sample_athlete_data

    def test_sample_activity_data_fixture(self, sample_activity_data):
        """Test sample activity data fixture."""
        assert sample_activity_data is not None
        assert sample_activity_data["id"] == 123456789
        assert sample_activity_data["name"] == "Morning Run"
        assert sample_activity_data["type"] == "Run"

    def test_temp_data_dir_fixture(self, temp_data_dir):
        """Test temporary data directory fixture."""
        assert os.path.exists(temp_data_dir)
        assert os.path.isdir(temp_data_dir)

        # Create a test file
        test_file = os.path.join(temp_data_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")

        assert os.path.exists(test_file)


class TestUtilities:
    """Test utility functions and helpers."""

    def test_api_test_helper(self, api_test_helper):
        """Test API test helper functions."""
        assert api_test_helper is not None

        # Test create_test_activity_data method
        activities = api_test_helper.create_test_activity_data(count=3)
        assert len(activities) == 3
        assert activities[0]["athlete_id"] == "12345"
        assert activities[0]["name"] == "Test Activity 0"

    def test_performance_timer(self, performance_timer):
        """Test performance timer utility."""
        assert performance_timer is not None

        performance_timer.start()
        import time

        time.sleep(0.01)  # Small delay
        performance_timer.stop()

        assert performance_timer.elapsed is not None
        assert performance_timer.elapsed > 0


class TestPytestMarkers:
    """Test different pytest markers."""

    @pytest.mark.unit
    def test_unit_test(self):
        """A unit test example."""

        def add_numbers(a, b):
            return a + b

        assert add_numbers(2, 3) == 5
        assert add_numbers(-1, 1) == 0

    @pytest.mark.integration
    def test_integration_test(self):
        """An integration test example."""
        # Simulate testing interaction between components
        components = {"database": {"status": "connected"}, "api": {"status": "running"}}

        assert all(
            comp["status"] in ["connected", "running"] for comp in components.values()
        )

    @pytest.mark.api
    def test_api_test(self):
        """An API test example."""
        # Simulate API response structure
        api_response = {
            "status": "success",
            "data": {"id": 1, "name": "test"},
            "message": "Request processed successfully",
        }

        assert api_response["status"] == "success"
        assert "data" in api_response
        assert api_response["data"]["id"] == 1

    @pytest.mark.database
    def test_database_test(self):
        """A database test example."""
        # Simulate database operations
        mock_database = {
            "activities": [{"id": 1, "name": "Run"}],
            "athletes": [{"id": 12345, "name": "Test Athlete"}],
        }

        assert len(mock_database["activities"]) == 1
        assert mock_database["athletes"][0]["id"] == 12345

    @pytest.mark.strava
    def test_strava_test(self):
        """A Strava integration test example."""
        # Simulate Strava API response
        strava_response = {
            "id": 123456,
            "name": "Morning Run",
            "type": "Run",
            "distance": 5000.0,
        }

        assert strava_response["type"] == "Run"
        assert strava_response["distance"] > 0


class TestErrorHandling:
    """Test error handling capabilities."""

    def test_exception_handling(self):
        """Test that exceptions are handled correctly."""

        def divide_by_zero():
            return 1 / 0

        with pytest.raises(ZeroDivisionError):
            divide_by_zero()

    def test_assertion_errors(self):
        """Test that assertion errors work correctly."""
        with pytest.raises(AssertionError):
            assert 1 == 2

    def test_custom_exceptions(self):
        """Test custom exception handling."""

        class CustomError(Exception):
            pass

        def raise_custom_error():
            raise CustomError("This is a custom error")

        with pytest.raises(CustomError, match="custom error"):
            raise_custom_error()


class TestParametrizedTests:
    """Test parametrized test functionality."""

    @pytest.mark.parametrize("input_value,expected", [(1, 2), (2, 4), (3, 6), (4, 8)])
    def test_multiply_by_two(self, input_value, expected):
        """Test multiply by two with different inputs."""

        def multiply_by_two(x):
            return x * 2

        assert multiply_by_two(input_value) == expected

    @pytest.mark.parametrize(
        "distance,expected_type",
        [(1000, "short"), (5000, "medium"), (10000, "long"), (42195, "marathon")],
    )
    def test_categorize_distance(self, distance, expected_type):
        """Test distance categorization."""

        def categorize_distance(d):
            if d < 3000:
                return "short"
            elif d < 8000:
                return "medium"
            elif d < 25000:
                return "long"
            else:
                return "marathon"

        assert categorize_distance(distance) == expected_type
