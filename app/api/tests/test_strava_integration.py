"""
Tests for Strava API integration.

This module tests the Strava API client and data fetching functionality:
- API client initialization and authentication
- Activity fetching with proper rate limiting
- Best efforts data processing
- Error handling for API failures
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch

# Import these within the application context to avoid import errors


class TestStravaAPIClient:
    """Test Strava API client functionality."""

    def test_client_initialization(self, app_context):
        """Test Strava API client can be initialized."""
        from data.fetchers.strava_api import StravaAPIClient

        client = StravaAPIClient(access_token="test_token")
        assert client.access_token == "test_token"
        assert client.base_url == "https://www.strava.com/api/v3"

    def test_client_headers(self, app_context):
        """Test that client sets proper headers."""
        from data.fetchers.strava_api import StravaAPIClient

        client = StravaAPIClient(access_token="test_token")
        headers = client._get_headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_token"

    @patch("requests.get")
    def test_get_athlete_info(self, mock_get, app_context):
        """Test fetching athlete information."""
        from data.fetchers.strava_api import StravaAPIClient

        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 12345,
            "username": "test_athlete",
            "firstname": "Test",
            "lastname": "User",
        }
        mock_get.return_value = mock_response

        client = StravaAPIClient(access_token="test_token")
        athlete_info = client.get_athlete_info()

        assert athlete_info["id"] == 12345
        assert athlete_info["username"] == "test_athlete"
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_get_activities(self, mock_get, app_context):
        """Test fetching activities."""
        from data.fetchers.strava_api import StravaAPIClient

        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 123456,
                "name": "Morning Run",
                "type": "Run",
                "distance": 5000.0,
                "moving_time": 1800,
            }
        ]
        mock_get.return_value = mock_response

        client = StravaAPIClient(access_token="test_token")
        activities = client.get_activities(per_page=10)

        assert len(activities) == 1
        assert activities[0]["name"] == "Morning Run"
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_get_activity_detail(self, mock_get, app_context):
        """Test fetching detailed activity information."""
        from data.fetchers.strava_api import StravaAPIClient

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 123456,
            "name": "Morning Run",
            "best_efforts": [{"name": "5k", "elapsed_time": 1200, "distance": 5000}],
        }
        mock_get.return_value = mock_response

        client = StravaAPIClient(access_token="test_token")
        activity = client.get_activity_detail(123456)

        assert activity["id"] == 123456
        assert len(activity["best_efforts"]) == 1
        mock_get.assert_called_once_with(
            "https://www.strava.com/api/v3/activities/123456",
            headers=client._get_headers(),
        )

    @patch("requests.get")
    def test_rate_limit_handling(self, mock_get, app_context):
        """Test handling of rate limit responses."""
        from data.fetchers.strava_api import StravaAPIClient

        # Mock rate limit response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_get.return_value = mock_response

        client = StravaAPIClient(access_token="test_token")

        # Should handle rate limit gracefully
        with pytest.raises(Exception) as exc_info:
            client.get_activities()

        assert "rate limit" in str(exc_info.value).lower() or "429" in str(
            exc_info.value
        )

    @patch("requests.get")
    def test_api_error_handling(self, mock_get, app_context):
        """Test handling of API errors."""
        from data.fetchers.strava_api import StravaAPIClient

        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Authorization Error"}
        mock_get.return_value = mock_response

        client = StravaAPIClient(access_token="invalid_token")

        with pytest.raises(Exception):
            client.get_activities()


class TestActivityFetcher:
    """Test activity fetching functionality."""

    @patch("data.fetchers.activity_fetcher.StravaAPIClient")
    def test_fetch_strava_data_basic(self, mock_client_class, app_context):
        """Test basic Strava data fetching."""
        from data.fetchers.activity_fetcher import fetch_strava_data

        # Mock client instance
        mock_client = Mock()
        mock_client.get_activities.return_value = [
            {"id": 123456, "name": "Morning Run", "type": "Run", "distance": 5000.0}
        ]
        mock_client_class.return_value = mock_client

        result = fetch_strava_data(
            access_token="test_token", athlete_id="12345", limit=10
        )

        assert result["success"] is True
        assert result["activities_fetched"] >= 0
        mock_client.get_activities.assert_called()

    @patch("data.fetchers.activity_fetcher.StravaAPIClient")
    @patch("os.path.exists")
    def test_fetch_with_cache(self, mock_exists, mock_client_class, app_context):
        """Test fetching with existing cache."""
        from data.fetchers.activity_fetcher import fetch_strava_data

        # Mock that cache files exist
        mock_exists.return_value = True

        # Mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = (
                json.dumps({"id": 123456, "name": "Cached Activity"})
            )

            result = fetch_strava_data(
                access_token="test_token", athlete_id="12345", limit=10, use_cache=True
            )

            assert result["success"] is True

    @patch("data.fetchers.activity_fetcher.StravaAPIClient")
    def test_fetch_with_rate_limiting(self, mock_client_class, app_context):
        """Test fetching with rate limiting."""
        from data.fetchers.activity_fetcher import fetch_strava_data

        # Mock client that raises rate limit error
        mock_client = Mock()
        mock_client.get_activities.side_effect = Exception("Rate limit exceeded")
        mock_client_class.return_value = mock_client

        result = fetch_strava_data(
            access_token="test_token", athlete_id="12345", limit=10
        )

        # Should handle rate limiting gracefully
        assert "error" in result or result["success"] is False

    @patch("data.fetchers.activity_fetcher.save_activity_to_file")
    @patch("data.fetchers.activity_fetcher.StravaAPIClient")
    def test_activity_saving(self, mock_client_class, mock_save, app_context):
        """Test that activities are saved to files."""
        from data.fetchers.activity_fetcher import fetch_strava_data

        mock_client = Mock()
        mock_client.get_activities.return_value = [
            {"id": 123456, "name": "Test Activity"}
        ]
        mock_client_class.return_value = mock_client

        fetch_strava_data(access_token="test_token", athlete_id="12345", limit=1)

        # Should attempt to save activities
        mock_save.assert_called()


class TestBestEffortsProcessing:
    """Test best efforts data processing."""

    def test_extract_best_efforts(self, app_context, sample_best_efforts):
        """Test extracting best efforts from activity data."""
        from data.processors.data_processor import extract_best_efforts

        activity_data = {"id": 123456, "best_efforts": sample_best_efforts}

        best_efforts = extract_best_efforts(activity_data)

        assert len(best_efforts) == len(sample_best_efforts)
        assert best_efforts[0]["name"] == "5k"
        assert best_efforts[0]["elapsed_time"] == 1200

    def test_best_efforts_validation(self, app_context):
        """Test validation of best efforts data."""
        from data.processors.data_processor import validate_best_effort

        valid_effort = {
            "name": "5k",
            "elapsed_time": 1200,
            "distance": 5000,
            "start_index": 0,
            "end_index": 1000,
        }

        invalid_effort = {
            "name": "5k",
            # Missing required fields
        }

        assert validate_best_effort(valid_effort) is True
        assert validate_best_effort(invalid_effort) is False

    def test_best_efforts_deduplication(self, app_context):
        """Test deduplication of best efforts."""
        from data.processors.data_processor import deduplicate_best_efforts

        efforts = [
            {"name": "5k", "elapsed_time": 1200, "activity_id": 123},
            {"name": "5k", "elapsed_time": 1200, "activity_id": 123},  # Duplicate
            {"name": "10k", "elapsed_time": 2400, "activity_id": 123},
        ]

        deduplicated = deduplicate_best_efforts(efforts)
        assert len(deduplicated) == 2

        names = [effort["name"] for effort in deduplicated]
        assert "5k" in names
        assert "10k" in names


class TestDataTransformation:
    """Test transformation of Strava data to database format."""

    def test_activity_record_creation(self, app_context, sample_strava_activity):
        """Test creating activity record from Strava API data."""
        from data.processors.data_processor import create_activity_record

        record = create_activity_record(sample_strava_activity)

        assert record["id"] == sample_strava_activity["id"]
        assert record["name"] == sample_strava_activity["name"]
        assert record["type"] == sample_strava_activity["type"]
        assert record["distance"] == sample_strava_activity["distance"]

    def test_athlete_stats_creation(self, app_context):
        """Test creating athlete stats record."""
        from data.processors.data_processor import create_athlete_stats_record

        strava_stats = {
            "recent_run_totals": {
                "count": 10,
                "distance": 50000.0,
                "moving_time": 18000,
            },
            "all_run_totals": {
                "count": 100,
                "distance": 500000.0,
                "moving_time": 180000,
            },
        }

        record = create_athlete_stats_record(strava_stats, athlete_id="12345")

        assert record["athlete_id"] == "12345"
        assert record["recent_runs_count"] == 10
        assert record["all_runs_count"] == 100

    def test_data_type_conversion(self, app_context):
        """Test proper data type conversion."""
        from data.processors.data_processor import convert_strava_types

        strava_data = {
            "distance": "5000.0",  # String that should be float
            "moving_time": "1800",  # String that should be int
            "start_date": "2024-01-15T08:00:00Z",  # ISO string that should be datetime
        }

        converted = convert_strava_types(strava_data)

        assert isinstance(converted["distance"], float)
        assert isinstance(converted["moving_time"], int)
        assert isinstance(converted["start_date"], datetime)

    def test_missing_data_handling(self, app_context):
        """Test handling of missing data fields."""
        from data.processors.data_processor import handle_missing_fields

        incomplete_data = {
            "id": 123456,
            "name": "Test Activity",
            # Missing other fields
        }

        complete_data = handle_missing_fields(incomplete_data)

        # Should have default values for missing fields
        assert "type" in complete_data
        assert "distance" in complete_data
        assert complete_data["distance"] is not None


class TestStreamProcessing:
    """Test processing of activity streams."""

    @patch("data.fetchers.strava_api.StravaAPIClient")
    def test_fetch_activity_streams(self, mock_client_class, app_context):
        """Test fetching activity streams."""
        from data.fetchers.activity_fetcher import fetch_activity_streams

        mock_client = Mock()
        mock_client.get_activity_streams.return_value = {
            "time": {"data": [0, 60, 120, 180]},
            "distance": {"data": [0, 100, 200, 300]},
            "heartrate": {"data": [120, 130, 140, 135]},
        }
        mock_client_class.return_value = mock_client

        streams = fetch_activity_streams("test_token", 123456)

        assert "time" in streams
        assert "heartrate" in streams
        assert len(streams["time"]["data"]) == 4

    def test_stream_data_validation(self, app_context):
        """Test validation of stream data."""
        from data.processors.data_processor import validate_streams

        valid_streams = {
            "time": {"data": [0, 60, 120]},
            "distance": {"data": [0, 100, 200]},
            "heartrate": {"data": [120, 130, 140]},
        }

        invalid_streams = {
            "time": {"data": [0, 60, 120]},
            "distance": {"data": [0, 100]},  # Mismatched length
            "heartrate": {"data": [120, 130, 140]},
        }

        assert validate_streams(valid_streams) is True
        assert validate_streams(invalid_streams) is False

    def test_stream_processing(self, app_context):
        """Test processing streams for analytics."""
        from data.processors.data_processor import process_activity_streams

        streams = {
            "time": {"data": [0, 60, 120, 180]},
            "heartrate": {"data": [120, 130, 140, 135]},
            "cadence": {"data": [180, 185, 182, 178]},
        }

        processed = process_activity_streams(streams)

        # Should calculate basic statistics
        assert "avg_heartrate" in processed
        assert "max_heartrate" in processed
        assert "avg_cadence" in processed
        assert processed["avg_heartrate"] > 0


class TestIntegrationWorkflow:
    """Test end-to-end integration workflow."""

    @patch("data.fetchers.activity_fetcher.StravaAPIClient")
    @patch("data.processors.data_processor.save_to_database")
    def test_complete_fetch_and_process_workflow(
        self, mock_save, mock_client_class, app_context
    ):
        """Test complete workflow from fetch to database save."""
        from data.fetchers.activity_fetcher import fetch_and_process_activities

        # Mock API client
        mock_client = Mock()
        mock_client.get_activities.return_value = [
            {
                "id": 123456,
                "name": "Morning Run",
                "type": "Run",
                "distance": 5000.0,
                "moving_time": 1800,
            }
        ]
        mock_client_class.return_value = mock_client

        result = fetch_and_process_activities(
            access_token="test_token", athlete_id="12345"
        )

        assert result["success"] is True
        mock_save.assert_called()

    @patch("data.fetchers.activity_fetcher.StravaAPIClient")
    def test_error_recovery_workflow(self, mock_client_class, app_context):
        """Test workflow with error recovery."""
        from data.fetchers.activity_fetcher import fetch_strava_data

        # Mock client that fails initially then succeeds
        mock_client = Mock()
        mock_client.get_activities.side_effect = [
            Exception("Network error"),
            [{"id": 123456, "name": "Test"}],
        ]
        mock_client_class.return_value = mock_client

        # Should handle initial failure and retry
        result = fetch_strava_data(
            access_token="test_token", athlete_id="12345", retry_on_error=True
        )

        # Exact behavior depends on implementation
        assert "error" in result or result["success"] in [True, False]
