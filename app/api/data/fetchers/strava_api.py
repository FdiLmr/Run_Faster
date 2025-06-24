"""
Core Strava API client for making authenticated requests.
"""

import requests
import time
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class StravaAPIClient:
    """
    Core client for making authenticated requests to the Strava API.
    """

    BASE_URL = "https://www.strava.com/api/v3"

    def __init__(self, access_token: str):
        """
        Initialize the API client with an access token.

        Args:
            access_token: Valid Strava access token
        """
        self.access_token = access_token
        self.headers = {"Authorization": f"Bearer {access_token}"}

    def _make_request(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make a GET request to the Strava API with rate limiting.

        Args:
            endpoint: API endpoint (without base URL)
            params: Optional query parameters

        Returns:
            Dict: JSON response from API

        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        # Basic rate limiting
        time.sleep(0.1)

        return response.json()

    def get_athlete(self) -> Dict[str, Any]:
        """
        Get the authenticated athlete's profile.

        Returns:
            Dict: Athlete profile data
        """
        return self._make_request("/athlete")

    def get_athlete_zones(self) -> Dict[str, Any]:
        """
        Get the authenticated athlete's heart rate and power zones.

        Returns:
            Dict: Zones data
        """
        return self._make_request("/athlete/zones")

    def get_athlete_stats(self, athlete_id: int) -> Dict[str, Any]:
        """
        Get statistics for a specific athlete.

        Args:
            athlete_id: The athlete's ID

        Returns:
            Dict: Athlete statistics
        """
        return self._make_request(f"/athletes/{athlete_id}/stats")

    def get_activities(
        self, page: int = 1, per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get a page of activities for the authenticated athlete.

        Args:
            page: Page number (1-based)
            per_page: Number of activities per page (max 200)

        Returns:
            List: List of activity summaries
        """
        params = {"page": page, "per_page": per_page}
        return self._make_request("/athlete/activities", params)

    def get_activity_detail(self, activity_id: int) -> Dict[str, Any]:
        """
        Get detailed information for a specific activity.

        Args:
            activity_id: The activity's ID

        Returns:
            Dict: Detailed activity data
        """
        return self._make_request(f"/activities/{activity_id}")

    def get_activity_streams(
        self, activity_id: int, stream_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get streams data for a specific activity.

        Args:
            activity_id: The activity's ID
            stream_types: List of stream types to fetch

        Returns:
            Dict: Streams data
        """
        if stream_types is None:
            stream_types = [
                "time",
                "distance",
                "latlng",
                "altitude",
                "velocity_smooth",
                "heartrate",
                "cadence",
                "watts",
                "temp",
                "moving",
                "grade_smooth",
            ]

        params = {"keys": ",".join(stream_types), "key_by_type": "true"}

        return self._make_request(f"/activities/{activity_id}/streams", params)


def get_unprocessed_activities(
    activity_list: List[Dict], existing_ids: set, limit: int = 90
) -> List[Dict]:
    """
    Filter activities to get only those we haven't processed yet.

    Args:
        activity_list: List of activity summaries from API
        existing_ids: Set of activity IDs we already have
        limit: Maximum number of activities to return

    Returns:
        List: Filtered list of new activities
    """
    new_activities = []
    for activity in activity_list:
        if len(new_activities) >= limit:
            break
        if activity["id"] not in existing_ids:
            new_activities.append(activity)
    return new_activities
