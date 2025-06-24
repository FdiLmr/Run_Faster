import requests
import urllib.parse
import logging
from flask import session
from .config import Config

logger = logging.getLogger(__name__)


def authorize_url():
    """Generate authorization uri for Strava OAuth."""
    params = {
        "client_id": Config.CLIENT_ID,
        "response_type": "code",
        "redirect_uri": f"{Config.APP_URL}/authorization_successful",
        "scope": "read,profile:read_all,activity:read",
        "state": "https://github.com/sladkovm/strava-oauth",
        "approval_prompt": "force",
    }
    values_url = urllib.parse.urlencode(params)
    base_url = "https://www.strava.com/oauth/authorize"
    rv = base_url + "?" + values_url
    logger.debug(f"Authorization URL: {rv}")
    return rv


def refresh_access_token(refresh_token):
    """Refresh Strava access token using refresh token."""
    params = {
        "client_id": Config.CLIENT_ID,
        "client_secret": Config.CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    r = requests.post("https://www.strava.com/oauth/token", data=params)
    if r.status_code == 200:
        return r.json()
    else:
        logger.error(f"Error refreshing access token: {r.text}")
        return None


def format_stats_data(stats_dict):
    """Format stats data for display with proper units and formatting."""
    if not stats_dict:
        return {}

    formatted = {}

    for key, value in stats_dict.items():
        if key == "count":
            formatted[key] = f"{value} activities"
        elif "distance" in key:
            if value is not None:
                formatted[key] = f"{value/1000:.2f} km"
            else:
                formatted[key] = "0.00 km"
        elif "time" in key or "moving_time" in key or "elapsed_time" in key:
            if value is not None:
                hours = value // 3600
                minutes = (value % 3600) // 60
                seconds = value % 60
                if hours > 0:
                    formatted[key] = f"{hours}:{minutes:02d}:{seconds:02d}"
                else:
                    formatted[key] = f"{minutes}:{seconds:02d}"
            else:
                formatted[key] = "00:00"
        elif "elevation" in key:
            if value is not None:
                formatted[key] = f"{value:.0f} m"
            else:
                formatted[key] = "0 m"
        elif "speed" in key:
            if value is not None:
                formatted[key] = f"{value * 3.6:.1f} km/h"
            else:
                formatted[key] = "0.0 km/h"
        elif "pace" in key:
            if value is not None and value > 0:
                pace_min_per_km = 1000 / (value * 60)
                minutes = int(pace_min_per_km)
                seconds = int((pace_min_per_km - minutes) * 60)
                formatted[key] = f"{minutes}:{seconds:02d} min/km"
            else:
                formatted[key] = "0:00 min/km"
        elif "heartrate" in key or "hr" in key:
            if value is not None:
                formatted[key] = f"{value:.0f} bpm"
            else:
                formatted[key] = "N/A"
        elif "calories" in key:
            if value is not None:
                formatted[key] = f"{value:.0f} kcal"
            else:
                formatted[key] = "0 kcal"
        elif "achievement_count" in key or "pr_count" in key:
            if value is not None:
                formatted[key] = f"{value} achievements"
            else:
                formatted[key] = "0 achievements"
        else:
            formatted[key] = value

    return formatted


def register_context_processors(app):
    """Register context processors for templates."""

    @app.context_processor
    def inject_user():
        """Make session available to all templates."""
        return dict(session=session)

    @app.context_processor
    def utility_processor():
        """Make utility functions available to templates."""
        try:
            from race_prediction import format_time

            return dict(format_time=format_time)
        except ImportError:
            # Fallback if import fails
            def fallback_format_time(seconds):
                try:
                    seconds = float(seconds)
                    hours = int(seconds // 3600)
                    minutes = int((seconds % 3600) // 60)
                    secs = int(seconds % 60)
                    if hours > 0:
                        return f"{hours}:{minutes:02d}:{secs:02d}"
                    else:
                        return f"{minutes}:{secs:02d}"
                except (ValueError, TypeError):
                    return str(seconds)

            return dict(format_time=fallback_format_time)
