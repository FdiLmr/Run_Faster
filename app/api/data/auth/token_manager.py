"""
Token management for Strava OAuth authentication.
"""

import os
import logging
import requests
from sql_methods import write_db_replace, read_db

logger = logging.getLogger(__name__)


def refresh_tokens():
    """
    Refresh OAuth tokens for all athletes with expired tokens.

    Returns:
        int: 0 for success, 1 for failure
    """
    try:
        processing_status = read_db("processing_status")

        for index, row in processing_status.iterrows():
            if row["athlete_id"] != 0 and row["status"] == "none":
                params = {
                    "client_id": os.environ.get("CLIENT_ID"),
                    "client_secret": os.environ.get("CLIENT_SECRET"),
                    "refresh_token": row["refresh_token"],
                    "grant_type": "refresh_token",
                }

                r = requests.post("https://www.strava.com/oauth/token", data=params)
                r.raise_for_status()
                response_data = r.json()

                processing_status.at[index, "bearer_token"] = response_data[
                    "access_token"
                ]
                processing_status.at[index, "refresh_token"] = response_data[
                    "refresh_token"
                ]

        write_db_replace(processing_status, "processing_status")
        logger.info("Successfully refreshed tokens for all athletes")
        return 0
    except Exception as e:
        logger.error(f"Error refreshing tokens: {e}")
        return 1
