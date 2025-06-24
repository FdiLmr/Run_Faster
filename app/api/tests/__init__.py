"""
Test suite for the Strava Running Analytics API.

This package contains comprehensive tests for all major functionalities:
- Database operations
- Strava API integration
- Data processing and transformation
- Race prediction models
- Authentication and authorization
- API endpoints
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch

# Test configuration
TEST_DATABASE_URI = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_app():
    """Create a test Flask application."""
    from core.app import create_app

    # Override configuration for testing
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": TEST_DATABASE_URI,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": "test-secret-key",
        "CLIENT_ID": "test-client-id",
        "CLIENT_SECRET": "test-client-secret",
        "SESSION_TYPE": "filesystem",
    }

    app = create_app("testing")
    app.config.update(test_config)

    return app


@pytest.fixture(scope="function")
def app_context(test_app):
    """Provide application context for tests."""
    with test_app.app_context():
        yield test_app


@pytest.fixture(scope="function")
def test_client(test_app):
    """Create a test client for API endpoint testing."""
    return test_app.test_client()


@pytest.fixture(scope="function")
def test_db(app_context):
    """Create a clean test database for each test."""
    from sql_methods import db

    db.create_all()
    yield db
    db.drop_all()


@pytest.fixture
def sample_athlete_data():
    """Sample athlete data for testing."""
    return {
        "id": 12345,
        "firstname": "Test",
        "lastname": "Runner",
        "profile_medium": "https://example.com/profile.jpg",
        "profile": "https://example.com/profile_large.jpg",
        "city": "Test City",
        "state": "Test State",
        "country": "Test Country",
        "sex": "M",
        "summit": False,
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
        "_Zones": {
            "heart_rate": {
                "zones": [
                    {"max": 114, "min": 0},
                    {"max": 133, "min": 114},
                    {"max": 152, "min": 133},
                    {"max": 171, "min": 152},
                    {"max": 190, "min": 171},
                ]
            }
        },
        "_Stats": {
            "recent_run_totals": {
                "count": 50,
                "distance": 500000,
                "moving_time": 180000,
                "elapsed_time": 200000,
                "elevation_gain": 5000,
            }
        },
        "_Activities": [],
    }


@pytest.fixture
def sample_activity_data():
    """Sample activity data for testing."""
    return {
        "id": 987654321,
        "athlete_id": 12345,
        "name": "Morning Run",
        "distance": 5000.0,
        "moving_time": 1500,
        "elapsed_time": 1600,
        "total_elevation_gain": 50.0,
        "type": "Run",
        "start_date": "2023-12-01T10:00:00Z",
        "start_date_local": "2023-12-01T10:00:00Z",
        "average_speed": 3.33,
        "max_speed": 4.5,
        "average_heartrate": 150.0,
        "max_heartrate": 175.0,
        "suffer_score": 45.0,
        "has_heartrate": True,
        "resource_state": 3,
        "best_efforts": [
            {
                "name": "5K",
                "elapsed_time": 1500,
                "moving_time": 1500,
                "start_date": "2023-12-01T10:00:00Z",
                "distance": 5000,
            }
        ],
        "laps": [],
        "splits_metric": [],
        "splits_standard": [],
    }


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_strava_client():
    """Mock Strava API client for testing."""
    with patch("data.fetchers.strava_api.StravaAPIClient") as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        yield mock_instance


class TestUtils:
    """Utility functions for testing."""

    @staticmethod
    def create_test_activity_file(athlete_id, activity_id, data, temp_dir):
        """Create a test activity file."""
        athlete_dir = os.path.join(temp_dir, "data", str(athlete_id))
        os.makedirs(athlete_dir, exist_ok=True)

        file_path = os.path.join(athlete_dir, f"{activity_id}.json")
        with open(file_path, "w") as f:
            import json

            json.dump(data, f)

        return file_path

    @staticmethod
    def create_test_athlete_files(
        athlete_id, athlete_data, zones_data, stats_data, temp_dir
    ):
        """Create test athlete metadata files."""
        data_dir = os.path.join(temp_dir, "data")
        os.makedirs(data_dir, exist_ok=True)

        import json

        # Create athlete file
        athlete_file = os.path.join(data_dir, f"athlete_{athlete_id}_athlete.json")
        with open(athlete_file, "w") as f:
            json.dump(athlete_data, f)

        # Create zones file
        zones_file = os.path.join(data_dir, f"athlete_{athlete_id}_zones.json")
        with open(zones_file, "w") as f:
            json.dump(zones_data, f)

        # Create stats file
        stats_file = os.path.join(data_dir, f"athlete_{athlete_id}_stats.json")
        with open(stats_file, "w") as f:
            json.dump(stats_data, f)

        return athlete_file, zones_file, stats_file
