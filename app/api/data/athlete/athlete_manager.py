"""
Athlete data management for fetching and handling athlete information from Strava API.

This module handles:
- Fetching athlete profile data from Strava
- Managing athlete authentication tokens
- Providing athlete data to other parts of the application
"""

import os
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class AthleteManager:
    """
    Manages athlete data fetching and basic athlete operations.

    This class handles the core athlete data operations including:
    - Fetching athlete profile from Strava API
    - Managing athlete authentication
    - Providing athlete data access
    """

    CLIENT_ID = os.environ.get("CLIENT_ID")
    STRAVA_API_BASE = "https://www.strava.com/api/v3"

    def __init__(self):
        """Initialize the AthleteManager."""
        pass

    def get_athlete_profile(self, bearer_token: str) -> Optional[Dict[str, Any]]:
        """
        Fetch athlete profile data from Strava API.

        Args:
            bearer_token: Valid Strava access token

        Returns:
            Dict containing athlete profile data, or None if error occurred

        Raises:
            requests.RequestException: If API request fails
        """
        url = f"{self.STRAVA_API_BASE}/athlete"
        headers = {"Authorization": f"Bearer {bearer_token}"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raises HTTPError for bad responses

            athlete_data = response.json()
            athlete_id = athlete_data.get("id")

            if athlete_id:
                logger.info(f"Successfully retrieved data for athlete {athlete_id}")
            else:
                logger.warning("Athlete data retrieved but no ID found")

            return athlete_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error requesting athlete data from Strava: {e}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing athlete data: {e}")
            return None

    def get_athlete_id_from_token(self, bearer_token: str) -> Optional[int]:
        """
        Get athlete ID from a bearer token.

        Args:
            bearer_token: Valid Strava access token

        Returns:
            Athlete ID if successful, None otherwise
        """
        athlete_data = self.get_athlete_profile(bearer_token)
        if athlete_data:
            return athlete_data.get("id")
        return None

    def validate_athlete_token(self, bearer_token: str) -> bool:
        """
        Validate if a bearer token is still valid.

        Args:
            bearer_token: Strava access token to validate

        Returns:
            True if token is valid, False otherwise
        """
        try:
            athlete_data = self.get_athlete_profile(bearer_token)
            return athlete_data is not None
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return False
