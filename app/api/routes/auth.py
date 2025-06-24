from flask import Blueprint, session, request, render_template, redirect
import requests
import logging
import os

from core.utils import authorize_url, refresh_access_token
from core.config import Config

logger = logging.getLogger(__name__)

bp = Blueprint("auth", __name__)


@bp.route("/")
def render_index():
    return render_template("index.html")


@bp.route("/about")
def render_about():
    return render_template("about.html")


@bp.route("/login")
def login():
    """Redirect user to the Strava Authorization page."""
    logger.debug(f"Using CLIENT_ID: {Config.CLIENT_ID}")
    logger.debug(f"CLIENT_SECRET: {Config.CLIENT_SECRET}")
    return redirect(authorize_url())


@bp.route("/authorization_successful")
def authorization_successful():
    from fetch_athlete_data import (
        get_athlete,
        get_athlete_data_status,
        queue_athlete_for_processing,
    )

    logger.debug("Starting authorization_successful")
    logger.debug(f"Session contents: {session}")

    # Get the token from session with a default value of None
    token = session.get("token")
    refresh_token = session.get("refresh_token")
    logger.debug(f"Retrieved token from session: {token}")

    if token:
        logger.debug("Using existing token")
        athlete_data = get_athlete(token)
        if athlete_data is None:
            logger.debug("Token expired, refreshing token")
            response_data = refresh_access_token(refresh_token)
            if response_data:
                session["token"] = response_data["access_token"]
                session["refresh_token"] = response_data["refresh_token"]
                athlete_data = get_athlete(session["token"])
                if athlete_data is None:
                    return "Error requesting athlete data from Strava. Please try again later."
            else:
                logger.debug(
                    "Invalid refresh token, clearing session and redirecting to authorization page"
                )
                session.clear()
                return redirect(authorize_url())
    else:
        logger.debug("No existing token, exchanging code for token")
        code = request.args.get("code")
        if not code:
            logger.error("No authorization code received")
            return "Authorization failed. No code received."

        params = {
            "client_id": Config.CLIENT_ID,
            "client_secret": Config.CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
        }

        logger.debug(f"Token exchange parameters: {params}")
        r = requests.post("https://www.strava.com/oauth/token", data=params)
        logger.debug(f"Token exchange response: {r.text}")

        if r.status_code == 200:
            response_data = r.json()
            session["token"] = response_data["access_token"]
            session["refresh_token"] = response_data["refresh_token"]
            logger.debug(f"Stored new token in session: {session['token']}")
            athlete_data = get_athlete(session["token"])
            if athlete_data is None:
                return (
                    "Error requesting athlete data from Strava. Please try again later."
                )
        else:
            logger.error(f"Error fetching access token: {r.text}")
            return "Error fetching access token. Please try again later."

    try:
        athlete_id = athlete_data["id"]
        logger.debug(f"Retrieved athlete_id: {athlete_id}")

        # Queue athlete for processing regardless of current status
        queue_result = queue_athlete_for_processing(
            athlete_id, session["token"], session["refresh_token"]
        )
        logger.info(f"Queue result: {queue_result}")

        # Check status after queueing
        athlete_data_status = get_athlete_data_status(athlete_id)
        logger.debug(f"Athlete data status: {athlete_data_status}")

        if athlete_data_status == "processed":
            return render_template(
                "render.html",
                athlete_id=athlete_id,
                random_num=str(os.urandom(8).hex()),
            )
        else:
            return render_template("processing.html", status="processing")

    except KeyError as e:
        logger.error(f"Error accessing athlete data: {str(e)}")
        return "Error retrieving athlete data. Please try again later."


@bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")
