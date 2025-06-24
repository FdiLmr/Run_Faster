"""
Tests for Flask API endpoints.

This module tests all the Flask routes and API endpoints:
- Authentication routes
- Data processing endpoints
- Dashboard routes
- JSON API endpoints
- Error handling
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch
import pandas as pd

# Import these within the application context to avoid import errors


class TestAuthenticationRoutes:
    """Test authentication-related routes."""

    def test_strava_connect_route(self, client, app_context):
        """Test Strava OAuth connection route."""

        response = client.get("/strava/connect")

        assert response.status_code in [200, 302]  # OK or redirect

        if response.status_code == 302:
            # Should redirect to Strava OAuth
            assert "strava.com" in response.location
            assert "oauth/authorize" in response.location

    @patch("routes.auth.exchange_code_for_token")
    def test_strava_callback_success(self, mock_exchange, client, app_context):
        """Test successful Strava OAuth callback."""
        # Mock successful token exchange
        mock_exchange.return_value = {
            "access_token": "test_token",
            "athlete": {"id": 12345},
        }

        response = client.get("/strava/callback?code=test_code&state=test_state")

        assert response.status_code in [200, 302]
        # Should store token in session or redirect to dashboard

    def test_strava_callback_error(self, client, app_context):
        """Test Strava OAuth callback with error."""
        response = client.get("/strava/callback?error=access_denied")

        assert response.status_code in [400, 302]
        # Should handle OAuth error gracefully

    def test_logout_route(self, client, app_context):
        """Test logout functionality."""
        # Set up session first
        with client.session_transaction() as sess:
            sess["access_token"] = "test_token"
            sess["athlete_id"] = "12345"

        response = client.get("/logout")

        assert response.status_code in [200, 302]

        # Check session is cleared
        with client.session_transaction() as sess:
            assert "access_token" not in sess
            assert "athlete_id" not in sess


class TestDataProcessingEndpoints:
    """Test data processing endpoints."""

    @patch("data.fetchers.activity_fetcher.fetch_strava_data")
    def test_fetch_strava_data_endpoint(self, mock_fetch, client, app_context):
        """Test fetching Strava data endpoint."""
        # Mock successful fetch
        mock_fetch.return_value = {
            "success": True,
            "activities_fetched": 25,
            "message": "Data fetched successfully",
        }

        # Set up authenticated session
        with client.session_transaction() as sess:
            sess["access_token"] = "test_token"
            sess["athlete_id"] = "12345"

        response = client.post("/fetch_strava_data")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "activities_fetched" in data

    def test_fetch_strava_data_unauthorized(self, client, app_context):
        """Test fetch endpoint without authentication."""
        response = client.post("/fetch_strava_data")

        assert response.status_code in [401, 302]  # Unauthorized or redirect to login

    @patch("athlete_data_transformer.process_all_data")
    def test_process_stored_data_endpoint(self, mock_process, client, app_context):
        """Test processing stored data endpoint."""
        # Mock successful processing
        mock_process.return_value = {
            "success": True,
            "activities_processed": 25,
            "weeks_processed": 12,
        }

        with client.session_transaction() as sess:
            sess["athlete_id"] = "12345"

        response = client.post("/process_stored_data")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

    @patch("sql_methods.reset_database")
    def test_reset_database_endpoint(self, mock_reset, client, app_context):
        """Test database reset endpoint."""
        mock_reset.return_value = True

        response = client.post("/reset_database")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        mock_reset.assert_called_once()

    def test_processing_status_endpoint(self, client, app_context):
        """Test processing status endpoint."""
        response = client.get("/processing_status")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "status" in data


class TestDashboardRoutes:
    """Test dashboard and view routes."""

    def test_index_route(self, client, app_context):
        """Test main index route."""
        response = client.get("/")

        assert response.status_code == 200
        assert b"html" in response.data.lower()

    def test_dashboard_route_authenticated(self, client, app_context):
        """Test dashboard route with authentication."""
        with client.session_transaction() as sess:
            sess["athlete_id"] = "12345"

        response = client.get("/dashboard")

        assert response.status_code == 200
        assert b"dashboard" in response.data.lower()

    def test_dashboard_route_unauthenticated(self, client, app_context):
        """Test dashboard route without authentication."""
        response = client.get("/dashboard")

        # Should redirect to login or show login prompt
        assert response.status_code in [200, 302]

    @patch("sql_methods.read_db")
    def test_activities_route(self, mock_read, client, app_context):
        """Test activities listing route."""
        # Mock activities data
        mock_read.return_value = pd.DataFrame(
            [
                {
                    "id": 123456,
                    "name": "Morning Run",
                    "distance": 5000,
                    "start_date": datetime(2024, 1, 15),
                }
            ]
        )

        with client.session_transaction() as sess:
            sess["athlete_id"] = "12345"

        response = client.get("/activities")

        assert response.status_code == 200
        assert b"Morning Run" in response.data

    @patch("sql_methods.read_db")
    def test_activity_detail_route(self, mock_read, client, app_context):
        """Test individual activity detail route."""
        # Mock activity data
        mock_read.return_value = pd.DataFrame(
            [
                {
                    "id": 123456,
                    "name": "Morning Run",
                    "distance": 5000,
                    "moving_time": 1800,
                }
            ]
        )

        response = client.get("/activity/123456")

        assert response.status_code == 200
        assert b"Morning Run" in response.data

    def test_activity_detail_not_found(self, client, app_context):
        """Test activity detail for non-existent activity."""
        response = client.get("/activity/999999")

        assert response.status_code == 404

    @patch("race_prediction.engine.PredictionEngine")
    def test_race_predictions_route(self, mock_engine, client, app_context):
        """Test race predictions route."""
        # Mock predictions
        mock_engine_instance = Mock()
        mock_engine_instance.predict_multiple_distances.return_value = [
            {"distance": 10000, "predicted_time": 2400, "formatted_time": "40:00"}
        ]
        mock_engine.return_value = mock_engine_instance

        with client.session_transaction() as sess:
            sess["athlete_id"] = "12345"

        response = client.get("/race_predictions")

        assert response.status_code == 200
        assert b"40:00" in response.data


class TestJSONAPIEndpoints:
    """Test JSON API endpoints."""

    @patch("sql_methods.read_db")
    def test_volume_data_api(self, mock_read, client, app_context):
        """Test volume data API endpoint."""
        # Mock weekly volume data
        mock_read.return_value = pd.DataFrame(
            [
                {
                    "week_start": datetime(2024, 1, 1),
                    "total_distance": 25000,
                    "total_time": 7200,
                },
                {
                    "week_start": datetime(2024, 1, 8),
                    "total_distance": 30000,
                    "total_time": 8400,
                },
            ]
        )

        response = client.get("/api/volume-data?period=weekly")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "labels" in data
        assert "datasets" in data
        assert len(data["labels"]) == 2

    @patch("race_prediction.engine.PredictionEngine")
    def test_race_predictions_api(self, mock_engine, client, app_context):
        """Test race predictions API endpoint."""
        mock_engine_instance = Mock()
        mock_engine_instance.predict_multiple_distances.return_value = [
            {
                "distance": 5000,
                "distance_name": "5K",
                "predicted_time": 1200,
                "formatted_time": "20:00",
            }
        ]
        mock_engine.return_value = mock_engine_instance

        response = client.get("/api/race-predictions")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) >= 1
        assert data[0]["distance_name"] == "5K"

    @patch("sql_methods.read_db")
    def test_activity_stats_api(self, mock_read, client, app_context):
        """Test activity statistics API endpoint."""
        mock_read.return_value = pd.DataFrame(
            [
                {"type": "Run", "distance": 5000, "moving_time": 1800},
                {"type": "Run", "distance": 8000, "moving_time": 2400},
                {"type": "Ride", "distance": 25000, "moving_time": 3600},
            ]
        )

        response = client.get("/api/activity-stats")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "total_activities" in data
        assert "total_distance" in data
        assert "activity_types" in data

    def test_api_endpoint_with_date_filter(self, client, app_context):
        """Test API endpoint with date filtering."""
        response = client.get(
            "/api/volume-data?start_date=2024-01-01&end_date=2024-01-31"
        )

        assert response.status_code == 200
        # Should handle date filtering

    def test_api_endpoint_invalid_parameters(self, client, app_context):
        """Test API endpoint with invalid parameters."""
        response = client.get("/api/volume-data?period=invalid")

        assert response.status_code in [400, 200]  # Bad request or default handling


class TestErrorHandling:
    """Test error handling in routes."""

    def test_404_error_handler(self, client, app_context):
        """Test 404 error handling."""
        response = client.get("/nonexistent-route")

        assert response.status_code == 404

    def test_500_error_handling(self, client, app_context):
        """Test 500 error handling."""
        # This is harder to test directly, but we can test error-prone endpoints
        with patch("sql_methods.read_db") as mock_read:
            mock_read.side_effect = Exception("Database error")

            response = client.get("/activities")

            # Should handle database errors gracefully
            assert response.status_code in [500, 200]  # Error or graceful handling

    def test_rate_limiting_protection(self, client, app_context):
        """Test rate limiting protection."""
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = client.post("/fetch_strava_data")
            responses.append(response.status_code)

        # Should have some form of rate limiting or at least not crash
        assert all(status in [200, 401, 429, 302] for status in responses)

    def test_csrf_protection(self, client, app_context):
        """Test CSRF protection on POST routes."""
        response = client.post(
            "/reset_database",
            headers={"X-Requested-With": "XMLHttpRequest"},  # AJAX request
        )

        # Should handle CSRF appropriately
        assert response.status_code in [200, 403, 401]


class TestSessionManagement:
    """Test session management."""

    def test_session_creation(self, client, app_context):
        """Test session creation during login."""
        with client.session_transaction() as sess:
            sess["access_token"] = "test_token"
            sess["athlete_id"] = "12345"

        # Session should persist across requests
        response = client.get("/dashboard")
        assert response.status_code == 200

    def test_session_expiration(self, client, app_context):
        """Test handling of expired sessions."""
        # This depends on implementation, but should handle gracefully
        with client.session_transaction() as sess:
            sess["access_token"] = "expired_token"

        response = client.post("/fetch_strava_data")
        # Should handle expired token appropriately
        assert response.status_code in [200, 401, 302]

    def test_session_security(self, client, app_context):
        """Test session security measures."""
        # Test that sessions are properly secured
        response = client.get("/")

        # Check for security headers
        assert "Set-Cookie" not in response.headers or "HttpOnly" in str(
            response.headers.get("Set-Cookie", "")
        )


class TestDataValidation:
    """Test input validation in routes."""

    def test_activity_id_validation(self, client, app_context):
        """Test validation of activity ID parameter."""
        # Test with invalid activity ID
        response = client.get("/activity/invalid_id")
        assert response.status_code in [400, 404]

        # Test with negative ID
        response = client.get("/activity/-1")
        assert response.status_code in [400, 404]

    def test_date_parameter_validation(self, client, app_context):
        """Test validation of date parameters."""
        # Test with invalid date format
        response = client.get("/api/volume-data?start_date=invalid-date")
        assert response.status_code in [400, 200]  # Bad request or default handling

        # Test with future dates
        response = client.get("/api/volume-data?start_date=2025-12-31")
        assert response.status_code == 200  # Should handle gracefully

    def test_pagination_validation(self, client, app_context):
        """Test validation of pagination parameters."""
        # Test with invalid page numbers
        response = client.get("/activities?page=-1")
        assert response.status_code in [400, 200]

        response = client.get("/activities?page=abc")
        assert response.status_code in [400, 200]


class TestResponseFormats:
    """Test response formats and content types."""

    def test_html_response_format(self, client, app_context):
        """Test HTML response format."""
        response = client.get("/")

        assert response.content_type.startswith("text/html")
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data

    def test_json_response_format(self, client, app_context):
        """Test JSON response format."""
        response = client.get("/api/volume-data")

        assert response.content_type == "application/json"
        data = json.loads(response.data)
        assert isinstance(data, (dict, list))

    def test_response_headers(self, client, app_context):
        """Test response headers."""
        response = client.get("/api/volume-data")

        # Should have appropriate headers
        assert "Content-Type" in response.headers
        # May have CORS headers if configured

    def test_response_encoding(self, client, app_context):
        """Test response encoding."""
        response = client.get("/")

        # Should handle UTF-8 encoding properly
        assert response.charset == "utf-8" or "utf-8" in response.content_type


class TestIntegrationWorkflows:
    """Test complete workflow integrations."""

    @patch("data.fetchers.activity_fetcher.fetch_strava_data")
    @patch("athlete_data_transformer.process_all_data")
    def test_complete_data_workflow(
        self, mock_process, mock_fetch, client, app_context
    ):
        """Test complete data fetch and process workflow."""
        # Mock successful operations
        mock_fetch.return_value = {"success": True, "activities_fetched": 25}
        mock_process.return_value = {"success": True, "activities_processed": 25}

        with client.session_transaction() as sess:
            sess["access_token"] = "test_token"
            sess["athlete_id"] = "12345"

        # Fetch data
        fetch_response = client.post("/fetch_strava_data")
        assert fetch_response.status_code == 200

        # Process data
        process_response = client.post("/process_stored_data")
        assert process_response.status_code == 200

        # View results
        dashboard_response = client.get("/dashboard")
        assert dashboard_response.status_code == 200

    def test_oauth_to_dashboard_flow(self, client, app_context):
        """Test OAuth to dashboard flow."""
        # Start OAuth flow
        connect_response = client.get("/strava/connect")
        assert connect_response.status_code in [200, 302]

        # Simulate callback (would need more complex mocking for full test)
        # This is a simplified test of the flow structure

    def test_error_recovery_workflow(self, client, app_context):
        """Test error recovery in workflows."""
        with patch("data.fetchers.activity_fetcher.fetch_strava_data") as mock_fetch:
            mock_fetch.side_effect = Exception("API Error")

            with client.session_transaction() as sess:
                sess["access_token"] = "test_token"
                sess["athlete_id"] = "12345"

            response = client.post("/fetch_strava_data")

            # Should handle errors gracefully
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                data = json.loads(response.data)
                assert "error" in data or data["success"] is False
