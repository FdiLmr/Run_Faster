"""
Activity fetching and processing from Strava API.
"""

import time
import logging
from datetime import datetime
from typing import Dict, Any, List
from flask import current_app

from sql_methods import read_db, write_db_replace, db
from models import Activity, AthleteStats
from .strava_api import StravaAPIClient, get_unprocessed_activities
from ..storage.file_storage import (
    save_activity_detail,
    load_activity_detail,
    save_activity_streams,
    load_activity_streams,
    save_athlete_metadata,
)

logger = logging.getLogger(__name__)

# Configuration
DEBUG_MODE = True
ACTIVITIES_LIMIT = 50 if DEBUG_MODE else 50
# Best effort mapping for activity processing
BEST_EFFORT_MAPPING = {
    "400m": "be_400m",
    "1/2 mile": "be_half_mile",
    "1K": "be_1km",
    "1 mile": "be_1_mile",
    "2 mile": "be_2_miles",
    "5K": "be_5km",
    "10K": "be_10km",
    "15K": "be_15km",
    "10 mile": "be_10_miles",
    "20K": "be_20km",
    "Half-Marathon": "be_half_marathon",
    "30K": "be_30km",
    "Marathon": "be_marathon",
    "50K": "be_50km",
}


def _process_best_efforts(activity_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process best efforts from activity data into database columns.

    Args:
        activity_data: Raw activity data from Strava API

    Returns:
        Dict: Mapping of best effort column names to values
    """
    be_columns = {col: None for col in BEST_EFFORT_MAPPING.values()}

    for effort in activity_data.get("best_efforts", []):
        name = effort.get("name", "")
        elapsed = effort.get("elapsed_time")
        if name in BEST_EFFORT_MAPPING and elapsed is not None:
            col_name = BEST_EFFORT_MAPPING[name]
            be_columns[col_name] = elapsed

    return be_columns


def _create_activity_record(activity_data: Dict[str, Any], athlete_id: int) -> Activity:
    """
    Create an Activity model instance from Strava API data.

    Args:
        activity_data: Raw activity data from Strava API
        athlete_id: The athlete's ID

    Returns:
        Activity: SQLAlchemy model instance
    """
    be_columns = _process_best_efforts(activity_data)

    return Activity(
        id=activity_data["id"],
        athlete_id=str(athlete_id),
        name=activity_data.get("name"),
        distance=activity_data.get("distance"),
        moving_time=activity_data.get("moving_time"),
        elapsed_time=activity_data.get("elapsed_time"),
        total_elevation_gain=activity_data.get("total_elevation_gain"),
        type=activity_data.get("type"),
        start_date=datetime.strptime(
            activity_data.get("start_date"), "%Y-%m-%dT%H:%M:%SZ"
        ),
        average_speed=activity_data.get("average_speed"),
        max_speed=activity_data.get("max_speed"),
        average_heartrate=activity_data.get("average_heartrate"),
        max_heartrate=activity_data.get("max_heartrate"),
        activity_data=activity_data,
        suffer_score=activity_data.get("suffer_score"),
        map_data=activity_data.get("map"),
        laps_data=activity_data.get("laps"),
        # Best efforts
        **be_columns,
        # Additional fields
        resource_state=activity_data.get("resource_state"),
        sport_type=activity_data.get("sport_type"),
        workout_type=activity_data.get("workout_type"),
        start_date_local=(
            datetime.strptime(
                activity_data.get("start_date_local"), "%Y-%m-%dT%H:%M:%SZ"
            )
            if activity_data.get("start_date_local")
            else None
        ),
        timezone=activity_data.get("timezone"),
        utc_offset=activity_data.get("utc_offset"),
        location_city=activity_data.get("location_city"),
        location_state=activity_data.get("location_state"),
        location_country=activity_data.get("location_country"),
        achievement_count=activity_data.get("achievement_count"),
        kudos_count=activity_data.get("kudos_count"),
        comment_count=activity_data.get("comment_count"),
        athlete_count=activity_data.get("athlete_count"),
        photo_count=activity_data.get("photo_count"),
        trainer=activity_data.get("trainer"),
        commute=activity_data.get("commute"),
        manual=activity_data.get("manual"),
        private=activity_data.get("private"),
        visibility=activity_data.get("visibility"),
        flagged=activity_data.get("flagged"),
        gear_id=activity_data.get("gear_id"),
        start_latlng=activity_data.get("start_latlng"),
        end_latlng=activity_data.get("end_latlng"),
        average_cadence=activity_data.get("average_cadence"),
        average_temp=activity_data.get("average_temp"),
        average_watts=activity_data.get("average_watts"),
        max_watts=activity_data.get("max_watts"),
        weighted_average_watts=activity_data.get("weighted_average_watts"),
        device_watts=activity_data.get("device_watts"),
        kilojoules=activity_data.get("kilojoules"),
        has_heartrate=activity_data.get("has_heartrate"),
        heartrate_opt_out=activity_data.get("heartrate_opt_out"),
        display_hide_heartrate_option=activity_data.get(
            "display_hide_heartrate_option"
        ),
        elev_high=activity_data.get("elev_high"),
        elev_low=activity_data.get("elev_low"),
        upload_id=activity_data.get("upload_id"),
        upload_id_str=activity_data.get("upload_id_str"),
        external_id=activity_data.get("external_id"),
        from_accepted_tag=activity_data.get("from_accepted_tag"),
        pr_count=activity_data.get("pr_count"),
        total_photo_count=activity_data.get("total_photo_count"),
        has_kudoed=activity_data.get("has_kudoed"),
        description=activity_data.get("description"),
        calories=activity_data.get("calories"),
        perceived_exertion=activity_data.get("perceived_exertion"),
        prefer_perceived_exertion=activity_data.get("prefer_perceived_exertion"),
        device_name=activity_data.get("device_name"),
        embed_token=activity_data.get("embed_token"),
        private_note=activity_data.get("private_note"),
        similar_activities=activity_data.get("similar_activities"),
        available_zones=activity_data.get("available_zones"),
        splits_metric=activity_data.get("splits_metric"),
        splits_standard=activity_data.get("splits_standard"),
        laps=activity_data.get("laps"),
        photos=activity_data.get("photos"),
        stats_visibility=activity_data.get("stats_visibility"),
        hide_from_home=activity_data.get("hide_from_home"),
    )


def _process_athlete_activities(
    client: StravaAPIClient, athlete_id: int, existing_ids: set, activities_limit: int
) -> tuple[List[Dict], int]:
    """
    Fetch and process activities for a single athlete.

    Args:
        client: Strava API client
        athlete_id: The athlete's ID
        existing_ids: Set of activity IDs we already have
        activities_limit: Maximum number of activities to process

    Returns:
        Tuple of (activities_list, api_calls_made)
    """
    all_activities = []
    page = 1
    api_calls = 0

    # Keep fetching pages until we have enough new activities
    while True:
        activities_page = client.get_activities(page=page, per_page=100)
        api_calls += 1

        if not activities_page:  # No more activities
            break

        all_activities.extend(activities_page)

        # Check if we have enough new activities
        unprocessed = get_unprocessed_activities(
            all_activities, existing_ids, activities_limit
        )
        if len(unprocessed) >= activities_limit:
            break

        page += 1
        time.sleep(1.5)  # Rate limiting between pages

    logger.info(
        f"Found {len(all_activities)} total activities, {len(unprocessed)} new ones"
    )

    # Process detailed activity data
    processed_activities = []

    for activity in unprocessed[:activities_limit]:
        activity_id = activity["id"]

        try:
            # Try to load from cache first
            activity_data = load_activity_detail(athlete_id, activity_id)

            if activity_data is None:
                # Fetch from API
                activity_data = client.get_activity_detail(activity_id)
                save_activity_detail(athlete_id, activity_id, activity_data)
                api_calls += 1
                logger.info(f"Fetched activity {activity_id} from Strava")
            else:
                logger.info(f"Loaded activity {activity_id} from cache")

            # Fetch streams data
            try:
                streams_data = load_activity_streams(athlete_id, activity_id)

                if streams_data is None:
                    streams_data = client.get_activity_streams(activity_id)
                    save_activity_streams(athlete_id, activity_id, streams_data)
                    api_calls += 1
                    logger.info(
                        f"Fetched streams for activity {activity_id} from Strava"
                    )
                    time.sleep(1.0)  # Rate limiting for streams
                else:
                    logger.info(f"Loaded streams for activity {activity_id} from cache")

            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    logger.warning(
                        f"Rate limit hit while fetching streams for activity {activity_id}. Continuing with basic activity data."
                    )
                else:
                    logger.error(
                        f"Error fetching streams for activity {activity_id}: {e}"
                    )

            # Store activity in database
            try:
                activity_record = _create_activity_record(activity_data, athlete_id)
                db.session.merge(activity_record)
                processed_activities.append(activity_data)
                logger.debug(f"Successfully processed activity {activity_id}")
            except Exception as e:
                logger.error(f"Error storing activity {activity_id}: {e}")
                continue

        except Exception as e:
            if "429" in str(e) or "Too Many Requests" in str(e):
                logger.warning(
                    f"Rate limit hit while fetching activity {activity_id}. Stopping activity processing for this athlete."
                )
                break  # Stop processing more activities for this athlete
            else:
                logger.error(f"Error processing activity {activity_id}: {e}")
                continue  # Skip this activity but try the next one

        # Rate limiting
        time.sleep(1.5)

    return processed_activities, api_calls


def fetch_strava_data() -> str:
    """
    Fetch data from Strava API and store in files and activity table.

    Returns:
        str: Summary of the operation
    """
    start_time = time.time()
    total_activities_fetched = 0
    athletes_processed = 0

    # Get initial API call count
    daily_limit = read_db("daily_limit")
    initial_api_calls = int(daily_limit.iloc[0, 0])
    logger.info(
        f"Starting data processing. Initial API calls today: {initial_api_calls}/25000"
    )

    if initial_api_calls > 25000:
        logger.error("API LIMIT EXCEEDED")
        return "api limit exceeded"

    processing_status = read_db("processing_status")
    athletes_to_process = len(processing_status[processing_status["status"] == "none"])
    logger.info(f"Found {athletes_to_process} athletes to process")

    current_api_calls = initial_api_calls

    for index, row in processing_status.iterrows():
        with current_app.app_context():
            athlete_id = int(row["athlete_id"])

            if athlete_id != 0 and row["status"] == "none":
                athlete_start_time = time.time()
                logger.info(f"Processing athlete {athlete_id}")

                bearer_token = row["bearer_token"]
                client = StravaAPIClient(bearer_token)

                processing_status.at[index, "status"] = "processing"

                try:
                    # Get athlete data
                    athlete_data = client.get_athlete()
                    athlete_zones = client.get_athlete_zones()
                    athlete_stats = client.get_athlete_stats(athlete_id)
                    current_api_calls += 3

                    # Store stats in database
                    try:
                        stats = AthleteStats(
                            athlete_id=str(athlete_id),
                            recent_run_totals=athlete_stats.get("recent_run_totals"),
                            all_run_totals=athlete_stats.get("all_run_totals"),
                            all_ride_totals=athlete_stats.get("all_ride_totals"),
                        )
                        db.session.merge(stats)
                        db.session.commit()
                    except Exception as e:
                        logger.error(f"Error storing stats: {e}")
                        db.session.rollback()

                    # Get existing activities
                    existing_activities = (
                        db.session.query(Activity.id)
                        .filter_by(athlete_id=str(athlete_id))
                        .all()
                    )
                    existing_ids = {a[0] for a in existing_activities}
                    logger.info(f"Found {len(existing_ids)} existing activities")

                    # Process activities
                    activities, activity_api_calls = _process_athlete_activities(
                        client, athlete_id, existing_ids, ACTIVITIES_LIMIT
                    )
                    current_api_calls += activity_api_calls

                    # Commit all activities
                    try:
                        db.session.commit()
                        logger.info(
                            f"Successfully stored {len(activities)} new activities"
                        )
                    except Exception as e:
                        logger.error(f"Error committing activities to database: {e}")
                        db.session.rollback()
                        raise

                    # Save athlete metadata
                    athlete_data["_Zones"] = athlete_zones
                    athlete_data["_Stats"] = athlete_stats
                    athlete_data["_Activities"] = activities

                    save_athlete_metadata(
                        athlete_id, athlete_data, athlete_zones, athlete_stats
                    )

                except Exception as ex:
                    # Update API call count and status regardless of error
                    daily_limit.at[0, "daily"] = current_api_calls
                    write_db_replace(daily_limit, "daily_limit")
                    processing_status.at[index, "status"] = "none"

                    # Check if this is a rate limit error
                    if "429" in str(ex) or "Too Many Requests" in str(ex):
                        logger.warning(
                            f"Rate limit hit while processing athlete {athlete_id}. Saved partial progress."
                        )

                        # Try to save any data we managed to fetch
                        try:
                            if (
                                "athlete_data" in locals()
                                and "athlete_zones" in locals()
                                and "athlete_stats" in locals()
                            ):
                                # Save partial athlete metadata if we got it
                                athlete_data["_Zones"] = athlete_zones
                                athlete_data["_Stats"] = athlete_stats
                                athlete_data["_Activities"] = (
                                    []
                                )  # Empty since activities failed
                                save_athlete_metadata(
                                    athlete_id,
                                    athlete_data,
                                    athlete_zones,
                                    athlete_stats,
                                )
                                logger.info(
                                    f"Saved partial metadata for athlete {athlete_id}"
                                )
                        except Exception as save_ex:
                            logger.error(
                                f"Could not save partial data for athlete {athlete_id}: {save_ex}"
                            )

                        # Continue with next athlete instead of aborting everything
                        logger.info(
                            "Continuing with remaining athletes. Rate limit will reset in 15 minutes."
                        )
                        continue
                    else:
                        # For non-rate-limit errors, log and continue
                        logger.error(
                            f"Error processing athlete {athlete_id}: {str(ex)}"
                        )
                        continue

                # Update status and counters
                processing_status.at[index, "status"] = "none"
                write_db_replace(processing_status, "processing_status")

                daily_limit.at[0, "daily"] = current_api_calls
                write_db_replace(daily_limit, "daily_limit")

                # Update statistics
                activities_count = len(activities)
                total_activities_fetched += activities_count
                athletes_processed += 1
                processing_time = time.time() - athlete_start_time

                avg_time_per_activity = (
                    processing_time / activities_count if activities_count > 0 else 0
                )
                logger.info(
                    f"""
                    Athlete {athlete_id} processing complete:
                    - Activities processed: {activities_count}
                    - Processing time: {processing_time:.2f} seconds
                    - Average time per activity: {avg_time_per_activity:.2f} seconds
                    - Current API calls: {current_api_calls}/25000
                """
                )

                print(f"successfully processed athlete {athlete_id}")

    # Generate summary
    total_time = time.time() - start_time
    api_calls_made = current_api_calls - initial_api_calls

    avg_time_per_athlete = (
        total_time / athletes_processed if athletes_processed > 0 else 0
    )
    avg_time_per_activity = (
        total_time / total_activities_fetched if total_activities_fetched > 0 else 0
    )

    # Check if we hit rate limits
    rate_limit_hit = current_api_calls >= 25000 or api_calls_made >= 100
    remaining_athletes = athletes_to_process - athletes_processed

    summary = f"""
    Data Fetch Complete:
    ===================
    Athletes processed: {athletes_processed}/{athletes_to_process if athletes_to_process > 0 else 'None'}
    Total activities: {total_activities_fetched}
    Total processing time: {total_time:.2f} seconds
    Average time per athlete: {avg_time_per_athlete:.2f} seconds
    Average time per activity: {avg_time_per_activity:.2f} seconds
    API calls made: {api_calls_made}
    Initial API calls: {initial_api_calls}
    Final API calls: {current_api_calls}
    Remaining API calls: {25000 - current_api_calls}
    
    Status: {'Rate limit reached - partial processing' if rate_limit_hit and remaining_athletes > 0 else 'Complete'}
    {f'Remaining athletes: {remaining_athletes} (will be processed when rate limit resets)' if remaining_athletes > 0 else ''}
    
    Note: JSON files are saved even when rate limits are hit.
    Run "Process Stored Data" to process cached files without API calls.
    """

    logger.info(summary)
    return summary
