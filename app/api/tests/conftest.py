"""
Test configuration and fixtures for the Strava Running Analytics API.

This module provides shared fixtures and configuration for all tests.
"""

import pytest
import os
import tempfile
import shutil
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock
from flask import Flask

# Ensure we're using test environment
os.environ["FLASK_ENV"] = "testing"


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment before running any tests."""
    # Set environment variables for testing
    os.environ.update(
        {
            "CLIENT_ID": "test_client_id",
            "CLIENT_SECRET": "test_client_secret",
            "FLASK_SECRET_KEY": "test_secret_key",
            "DB_USER": "test_user",
            "DB_PASS": "test_pass",
            "DB_HOST": "localhost",
            "DB_NAME": "test_db",
        }
    )
    yield
    # Cleanup after all tests


@pytest.fixture(scope="function")
def clean_environment():
    """Ensure a clean environment for each test."""
    # Clear any cached modules or global state if needed
    yield
    # Cleanup after each test


@pytest.fixture
def app_context():
    """Create a Flask application context for testing."""
    try:
        from core.app import create_app

        app = create_app()
    except ImportError:
        # Fallback if create_app is not available
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SECRET_KEY"] = "test_secret_key"

    with app.app_context():
        yield app


@pytest.fixture
def test_db(app_context):
    """Create a test database for testing."""
    try:
        from database.legacy_interface import db

        db.create_all()
        yield db
        db.drop_all()
    except ImportError:
        # Mock database if not available
        yield Mock()


@pytest.fixture
def client(app_context):
    """Create a test client for testing Flask routes."""
    return app_context.test_client()


@pytest.fixture
def sample_athlete_data():
    """Sample athlete data for testing."""
    return {
        "id": 12345,
        "username": "test_athlete",
        "firstname": "Test",
        "lastname": "Athlete",
        "city": "Test City",
        "state": "Test State",
        "country": "Test Country",
        "sex": "M",
        "premium": False,
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_activity_data():
    """Sample activity data for testing."""
    return {
        "id": 123456789,
        "athlete_id": "12345",
        "name": "Morning Run",
        "distance": 5000.0,
        "moving_time": 1800,
        "elapsed_time": 1900,
        "total_elevation_gain": 50.0,
        "type": "Run",
        "start_date": datetime(2024, 1, 15, 8, 0, 0),
        "start_date_local": datetime(2024, 1, 15, 8, 0, 0),
        "timezone": "America/New_York",
        "average_speed": 2.78,
        "max_speed": 4.5,
        "average_heartrate": 150.0,
        "max_heartrate": 175.0,
        "average_cadence": 180.0,
        "has_heartrate": True,
        "elev_high": 100.0,
        "elev_low": 50.0,
        "pr_count": 1,
        "achievement_count": 0,
        "kudos_count": 5,
        "comment_count": 0,
        "athlete_count": 1,
        "photo_count": 0,
        "trainer": False,
        "commute": False,
        "manual": False,
        "private": False,
        "flagged": False,
        "gear_id": None,
        "from_accepted_tag": False,
        "upload_id": 987654321,
        "average_temp": 15.0,
        "device_watts": False,
        "has_kudoed": False,
        "suffer_score": 45.0,
    }


@pytest.fixture
def sample_best_efforts():
    """Sample best efforts data for testing."""
    return [
        {
            "name": "5k",
            "elapsed_time": 1200,
            "distance": 5000,
            "start_index": 0,
            "end_index": 1000,
            "pr_rank": 1,
            "achievements": [],
        },
        {
            "name": "10k",
            "elapsed_time": 2500,
            "distance": 10000,
            "start_index": 0,
            "end_index": 2000,
            "pr_rank": 2,
            "achievements": [],
        },
    ]


@pytest.fixture
def sample_strava_activity():
    """Sample Strava API activity response for testing."""
    return {
        "id": 123456789,
        "name": "Morning Run",
        "distance": 5000.0,
        "moving_time": 1800,
        "elapsed_time": 1900,
        "total_elevation_gain": 50.0,
        "type": "Run",
        "start_date": "2024-01-15T08:00:00Z",
        "start_date_local": "2024-01-15T08:00:00",
        "timezone": "America/New_York",
        "average_speed": 2.78,
        "max_speed": 4.5,
        "average_heartrate": 150.0,
        "max_heartrate": 175.0,
        "average_cadence": 180.0,
        "has_heartrate": True,
        "trainer": False,
        "commute": False,
        "manual": False,
        "private": False,
    }


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_large_dataset():
    """Generate a larger sample dataset for performance testing."""
    activities = []
    base_date = datetime(2023, 1, 1)

    for i in range(100):
        activity = {
            "id": 1000000 + i,
            "athlete_id": 12345,
            "name": f"Activity {i}",
            "distance": 5000 + (i * 100),
            "moving_time": 1500 + (i * 10),
            "type": "Run",
            "start_date": (base_date + timedelta(days=i * 3)).isoformat() + "Z",
            "average_heartrate": 140 + (i % 30),
            "max_heartrate": 170 + (i % 20),
        }
        activities.append(activity)

    return activities


@pytest.fixture
def sample_activities_dataframe():
    """Create a sample DataFrame of activities for testing."""
    data = [
        {
            "id": 1,
            "athlete_id": "12345",
            "name": "Morning Run",
            "distance": 5000,
            "moving_time": 1500,
            "type": "Run",
            "start_date": datetime(2023, 12, 1),
            "average_heartrate": 150,
            "be_5km": 1500,
        },
        {
            "id": 2,
            "athlete_id": "12345",
            "name": "Evening Run",
            "distance": 8000,
            "moving_time": 2400,
            "type": "Run",
            "start_date": datetime(2023, 12, 5),
            "average_heartrate": 145,
            "be_5km": 1450,
        },
        {
            "id": 3,
            "athlete_id": "12345",
            "name": "Long Run",
            "distance": 15000,
            "moving_time": 5400,
            "type": "Run",
            "start_date": datetime(2023, 12, 10),
            "average_heartrate": 140,
            "be_10km": 3000,
        },
    ]

    return pd.DataFrame(data)


@pytest.fixture
def mock_database_responses():
    """Mock database responses for different tables."""
    return {
        "activities": pd.DataFrame(
            [
                {
                    "id": 1,
                    "athlete_id": "12345",
                    "name": "Test Activity",
                    "distance": 5000,
                    "type": "Run",
                    "start_date": datetime(2023, 12, 1),
                }
            ]
        ),
        "athlete_metadata": pd.DataFrame(
            [{"athlete_id": "12345", "zones": "[114, 133, 152, 171]", "max_hr": 190}]
        ),
        "race_predictions": pd.DataFrame(
            [
                {
                    "athlete_id": "12345",
                    "exponent": 1.06,
                    "predictions": '{"5K": {"realistic": 1200}}',
                    "created_at": datetime(2023, 12, 1),
                }
            ]
        ),
    }


@pytest.fixture
def mock_strava_responses():
    """Mock Strava API responses."""
    return {
        "athlete": {
            "id": 12345,
            "firstname": "Test",
            "lastname": "Athlete",
            "city": "Test City",
            "state": "Test State",
            "country": "Test Country",
        },
        "zones": {
            "heart_rate": {
                "zones": [
                    {"min": 0, "max": 114},
                    {"min": 114, "max": 133},
                    {"min": 133, "max": 152},
                    {"min": 152, "max": 171},
                    {"min": 171, "max": 190},
                ]
            }
        },
        "activities": [
            {
                "id": 1,
                "name": "Morning Run",
                "distance": 5000,
                "type": "Run",
                "start_date": "2023-12-01T10:00:00Z",
                "moving_time": 1500,
                "average_heartrate": 150,
            }
        ],
        "activity_detail": {
            "id": 1,
            "name": "Morning Run",
            "distance": 5000,
            "type": "Run",
            "start_date": "2023-12-01T10:00:00Z",
            "moving_time": 1500,
            "average_heartrate": 150,
            "best_efforts": [{"name": "5K", "elapsed_time": 1500}],
            "laps": [],
            "splits_metric": [],
        },
        "streams": {
            "time": {"data": [0, 10, 20, 30]},
            "heartrate": {"data": [120, 150, 160, 140]},
            "distance": {"data": [0, 100, 200, 300]},
        },
    }


@pytest.fixture
def authenticated_session(client):
    """Create an authenticated session for testing."""
    with client.session_transaction() as sess:
        sess["access_token"] = "test_access_token"
        sess["athlete_id"] = "12345"
    return client


class DatabaseMocker:
    """Helper class for mocking database operations."""

    def __init__(self):
        self.data = {}

    def set_table_data(self, table_name, data):
        """Set mock data for a table."""
        self.data[table_name] = data

    def mock_read_db(self, table_name):
        """Mock read_db function."""
        return self.data.get(table_name, pd.DataFrame())

    def mock_write_db_replace(self, df, table_name):
        """Mock write_db_replace function."""
        self.data[table_name] = df

    def mock_write_db_insert(self, df, table_name):
        """Mock write_db_insert function."""
        if table_name in self.data:
            self.data[table_name] = pd.concat(
                [self.data[table_name], df], ignore_index=True
            )
        else:
            self.data[table_name] = df


@pytest.fixture
def database_mocker():
    """Provide a database mocker for tests."""
    return DatabaseMocker()


@pytest.fixture
def mock_file_system(temp_data_dir):
    """Mock file system operations."""
    original_cwd = os.getcwd()

    # Change to temp directory for tests
    os.chdir(temp_data_dir)

    # Create data directory structure
    data_dir = os.path.join(temp_data_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    yield temp_data_dir

    # Restore original directory
    os.chdir(original_cwd)


class APITestHelper:
    """Helper class for API testing."""

    @staticmethod
    def assert_valid_json_response(response):
        """Assert that response is valid JSON."""
        assert response.status_code == 200
        assert response.content_type == "application/json"
        data = response.get_json()
        assert isinstance(data, (dict, list))
        return data

    @staticmethod
    def assert_valid_html_response(response):
        """Assert that response is valid HTML."""
        assert response.status_code == 200
        assert "text/html" in response.content_type
        assert len(response.data) > 0

    @staticmethod
    def assert_redirect_response(response, expected_location=None):
        """Assert that response is a redirect."""
        assert response.status_code in [301, 302]
        if expected_location:
            assert expected_location in response.location

    @staticmethod
    def create_test_activity_data(count=1, athlete_id="12345"):
        """Create test activity data."""
        activities = []
        base_date = datetime(2023, 12, 1)

        for i in range(count):
            activity = {
                "id": 1000000 + i,
                "athlete_id": athlete_id,
                "name": f"Test Activity {i}",
                "distance": 5000 + (i * 1000),
                "moving_time": 1500 + (i * 100),
                "type": "Run",
                "start_date": base_date + timedelta(days=i),
            }
            activities.append(activity)

        return activities


@pytest.fixture
def api_test_helper():
    """Provide API test helper."""
    return APITestHelper()


# Performance testing utilities
@pytest.fixture
def performance_timer():
    """Timer for performance testing."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return Timer()


# Custom markers for pytest
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "api: marks tests as API tests")
    config.addinivalue_line("markers", "database: marks tests as database tests")
    config.addinivalue_line(
        "markers", "strava: marks tests as Strava integration tests"
    )


# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Automatically cleanup test data after each test."""
    yield
    # Cleanup logic here if needed
    pass


# Skip tests based on environment
def pytest_collection_modifyitems(config, items):
    """Modify test collection based on environment."""
    if config.getoption("--integration-only"):
        skip_unit = pytest.mark.skip(reason="Running integration tests only")
        for item in items:
            if "integration" not in item.keywords:
                item.add_marker(skip_unit)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--integration-only",
        action="store_true",
        default=False,
        help="run integration tests only",
    )
    parser.addoption(
        "--skip-slow", action="store_true", default=False, help="skip slow tests"
    )
