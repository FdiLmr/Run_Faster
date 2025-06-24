from flask import Blueprint, render_template, request, abort
from sqlalchemy import text
import pandas as pd
import logging
import ast

from sql_methods import read_db, write_db_replace, db, test_conn_new, reset_database
from models import Activity, AthleteStats
from core.utils import format_stats_data

logger = logging.getLogger(__name__)

bp = Blueprint("data", __name__)


@bp.route("/sql")
def render_sql_test():
    return test_conn_new()


@bp.route("/update_tokens")
def update_tokens():
    from data.auth.token_manager import refresh_tokens

    res = refresh_tokens()
    print(res)
    return str(res), 200


@bp.route("/fetch_strava_data")
def fetch_strava_data():
    """Fetch raw data from Strava API and store in files/DB."""
    from data.fetchers.activity_fetcher import fetch_strava_data

    res = fetch_strava_data()
    logger.info(f"Strava data fetch result: {res}")
    return str(res), 200


@bp.route("/process_stored_data")
def process_stored_data():
    """Process data from stored files into analytics tables."""
    from data.processors.data_processor import process_stored_data

    res = process_stored_data()
    logger.info(f"Data processing result: {res}")
    return str(res), 200


@bp.route("/reset_processing")
def reset_processing():
    try:
        processing_status = read_db("processing_status")
        processing_status["status"] = "none"
        write_db_replace(processing_status, "processing_status")
        return "Processing status reset successfully", 200
    except Exception as e:
        logger.error(f"Error resetting processing status: {e}")
        return f"Error: {str(e)}", 500


@bp.route("/reset_activities")
def reset_activities():
    try:
        with db.session.begin():
            # Clear activities and stats tables
            db.session.query(Activity).delete()
            db.session.query(AthleteStats).delete()

            # Reset processing status to 'none'
            processing_status = read_db("processing_status")
            processing_status["status"] = "none"
            write_db_replace(processing_status, "processing_status")

            # Reset API call counter
            daily_limit = read_db("daily_limit")
            daily_limit.at[0, "daily"] = 0
            write_db_replace(daily_limit, "daily_limit")

            logger.info("Successfully reset activities and processing status")
            return (
                "Activities cleared and reset successfully. You can now run the processing again.",
                200,
            )
    except Exception as e:
        logger.error(f"Error resetting activities: {e}")
        db.session.rollback()
        return f"Error: {str(e)}", 500


@bp.route("/reset_database")
def reset_database_route():
    logger.info("Starting database reset")
    if reset_database():
        logger.info("Database reset successful")
        return "Database reset successful. Tables have been cleared.", 200
    else:
        return "Error resetting database", 500


@bp.route("/view_athletes")
def view_athletes():
    try:
        metadata_athletes = read_db("metadata_athletes")

        # Create a new processed DataFrame for display
        display_data = []

        for _, athlete in metadata_athletes.iterrows():
            # Format weight properly - handle both string and float cases
            weight_value = athlete["weight"]
            if weight_value and not pd.isna(weight_value):
                try:
                    # Try to convert to float first (in case it's stored as string)
                    weight_float = float(weight_value)
                    weight_display = f"{weight_float:.1f} kg"
                except (ValueError, TypeError):
                    # If conversion fails, just use the string as is
                    weight_display = f"{weight_value} kg"
            else:
                weight_display = "N/A"

            athlete_data = {
                "id": athlete["id"],
                "sex": athlete["sex"],
                "weight": weight_display,
            }

            # Parse the zones data
            try:
                if athlete["zones"] and not pd.isna(athlete["zones"]):
                    zones_str = str(athlete["zones"])

                    # Check if the zones are in dictionary format with min/max values
                    if "'min'" in zones_str and "'max'" in zones_str:
                        # Try to parse the zones as a list of dicts with min/max values
                        try:
                            # Use ast.literal_eval to safely evaluate the string as a Python literal
                            zones_list = ast.literal_eval(zones_str)

                            # Extract the threshold values (max values except the last one)
                            thresholds = []
                            for zone in zones_list:
                                if (
                                    isinstance(zone, dict)
                                    and "max" in zone
                                    and zone["max"] != -1
                                ):
                                    thresholds.append(zone["max"])

                            # Store the thresholds for the template
                            athlete_data["raw_zones"] = thresholds

                            # Generate a readable description
                            if len(thresholds) >= 4:
                                # Get the min values too
                                mins = [
                                    zone.get("min", 0)
                                    for zone in zones_list
                                    if isinstance(zone, dict)
                                ]
                                if len(mins) >= 5:
                                    athlete_data["zones"] = (
                                        f"Z1: {mins[0]}-{thresholds[0]}, "
                                        f"Z2: {mins[1]}-{thresholds[1]}, "
                                        f"Z3: {mins[2]}-{thresholds[2]}, "
                                        f"Z4: {mins[3]}-{thresholds[3]}, "
                                        f"Z5: {mins[4]}+"
                                    )
                                else:
                                    athlete_data["zones"] = zones_str
                            else:
                                athlete_data["zones"] = zones_str
                        except (ValueError, SyntaxError):
                            # If parsing fails, use the original string
                            athlete_data["zones"] = zones_str
                            athlete_data["raw_zones"] = []
                    else:
                        # The old parsing approach for simple threshold lists
                        try:
                            zones_str_values = (
                                str(athlete["zones"]).strip("[]").split(",")
                            )
                            zones = []
                            for z in zones_str_values:
                                try:
                                    if z.strip():
                                        zones.append(int(float(z.strip())))
                                except (ValueError, TypeError):
                                    pass

                            athlete_data["raw_zones"] = zones

                            if len(zones) >= 4:
                                athlete_data["zones"] = (
                                    f"Z1: <{zones[0]}, Z2: {zones[0]}-{zones[1]}, Z3: {zones[1]}-{zones[2]}, Z4: {zones[2]}-{zones[3]}, Z5: >{zones[3]}"
                                )
                            else:
                                athlete_data["zones"] = str(athlete["zones"])
                        except Exception as e:
                            logger.error(f"Error parsing simple zones: {e}")
                            athlete_data["zones"] = zones_str
                            athlete_data["raw_zones"] = []
                else:
                    athlete_data["zones"] = "No zones data"
                    athlete_data["raw_zones"] = []
            except Exception as e:
                logger.error(f"Error parsing zones for athlete {athlete['id']}: {e}")
                athlete_data["zones"] = "Error parsing zones"
                athlete_data["raw_zones"] = []

            display_data.append(athlete_data)

        return render_template(
            "view_athletes.html", athletes=pd.DataFrame(display_data)
        )
    except Exception as e:
        logger.error(f"Error retrieving athlete data: {e}")
        return f"Error retrieving athlete data: {str(e)}"


@bp.route("/view_activities/<athlete_id>")
def view_activities(athlete_id):
    try:
        activities = db.session.query(Activity).filter_by(athlete_id=athlete_id).all()
        activities_data = []

        for a in activities:
            # Calculate pace for running activities
            pace_display = "N/A"
            pace_raw = 0

            if a.type == "Run" and a.distance and a.moving_time and a.distance > 0:
                # Calculate pace in min/km
                pace_min_per_km = (a.moving_time / 60) / (a.distance / 1000)
                pace_minutes = int(pace_min_per_km)
                pace_seconds = int((pace_min_per_km - pace_minutes) * 60)
                pace_display = f"{pace_minutes}:{pace_seconds:02d} min/km"
                pace_raw = pace_min_per_km
            elif a.average_speed:
                # For non-running activities, show speed
                pace_display = f"{a.average_speed * 3.6:.1f} km/h"
                pace_raw = a.average_speed * 3.6

            # Format time properly
            time_display = "N/A"
            if a.moving_time:
                hours = a.moving_time // 3600
                minutes = (a.moving_time % 3600) // 60
                seconds = a.moving_time % 60
                if hours > 0:
                    time_display = f"{hours}:{minutes:02d}:{seconds:02d}"
                else:
                    time_display = f"{minutes}:{seconds:02d}"

            activity_data = {
                "id": a.id,
                "name": a.name,
                "distance_raw": (
                    a.distance / 1000 if a.distance else 0
                ),  # Raw numeric value for sorting
                "distance": (
                    f"{a.distance/1000:.2f} km" if a.distance else "N/A"
                ),  # Formatted for display
                "time_raw": (
                    a.moving_time if a.moving_time else 0
                ),  # Raw numeric value for sorting
                "time": time_display,  # Formatted for display
                "elapsed_time_raw": (
                    a.elapsed_time if a.elapsed_time else 0
                ),  # Raw numeric value for sorting
                "elapsed_time": time_display,  # Use same formatting as moving time
                "date": a.start_date.strftime("%Y-%m-%d") if a.start_date else "N/A",
                "type": a.type,
                "total_elevation_gain_raw": float(
                    a.total_elevation_gain or 0
                ),  # Raw numeric value
                "total_elevation_gain": (
                    f"{a.total_elevation_gain:.0f} m"
                    if a.total_elevation_gain
                    else "N/A"
                ),
                "pace_raw": pace_raw,  # Raw pace value for sorting
                "pace": pace_display,  # Formatted pace/speed for display
                "average_speed_raw": float(
                    a.average_speed * 3.6 if a.average_speed else 0
                ),  # Raw numeric value
                "average_speed": (
                    f"{a.average_speed * 3.6:.1f} km/h" if a.average_speed else "N/A"
                ),
                "max_speed_raw": float(
                    a.max_speed * 3.6 if a.max_speed else 0
                ),  # Raw numeric value
                "max_speed": f"{a.max_speed * 3.6:.1f} km/h" if a.max_speed else "N/A",
                "avg_hr_raw": float(a.average_heartrate or 0),  # Raw numeric value
                "avg_hr": (
                    f"{a.average_heartrate:.0f} bpm" if a.average_heartrate else "N/A"
                ),
                "max_hr_raw": float(a.max_heartrate or 0),  # Raw numeric value
                "max_hr": f"{a.max_heartrate:.0f} bpm" if a.max_heartrate else "N/A",
                "cadence": (
                    f"{a.average_cadence:.0f} spm" if a.average_cadence else "N/A"
                ),
            }
            activities_data.append(activity_data)

        return render_template(
            "activities.html", activities=activities_data, athlete_id=athlete_id
        )
    except Exception as e:
        return f"Error retrieving activities: {str(e)}"


@bp.route("/view_stats/<athlete_id>")
def view_stats(athlete_id):
    try:
        stats = db.session.get(AthleteStats, athlete_id)
        if stats:
            # Format the stats data for display
            formatted_stats = {
                "athlete_id": stats.athlete_id,
                "recent_run_totals": format_stats_data(stats.recent_run_totals),
                "all_run_totals": format_stats_data(stats.all_run_totals),
                "all_ride_totals": format_stats_data(stats.all_ride_totals),
            }
            return render_template("stats.html", stats=formatted_stats)
        return "No stats found for this athlete"
    except Exception as e:
        return f"Error retrieving stats: {str(e)}"


@bp.route("/view_best_efforts/<athlete_id>")
def view_best_efforts(athlete_id):
    try:
        # Mapping: display label -> corresponding column name in the Activity model.
        effort_categories = {
            "400m": "be_400m",
            "1/2 Mile": "be_half_mile",
            "1km": "be_1km",
            "1 Mile": "be_1_mile",
            "2 mile": "be_2_miles",
            "5km": "be_5km",
            "10km": "be_10km",
            "15km": "be_15km",
            "10 mile": "be_10_miles",
            "20km": "be_20km",
            "Half-Marathon": "be_half_marathon",
            "30km": "be_30km",
            "Marathon": "be_marathon",
            "50km": "be_50km",
        }

        all_efforts = []

        for label, column_name in effort_categories.items():
            # Query for activities that have a non-null best-effort in that column
            efforts = (
                Activity.query.filter(
                    Activity.athlete_id == athlete_id,
                    getattr(Activity, column_name) is not None,
                )
                .order_by(getattr(Activity, column_name))
                .all()
            )

            for act in efforts:
                # Convert start_date to a year if it exists
                year = act.start_date.year if act.start_date else 0
                elapsed = getattr(act, column_name)  # The best effort time in seconds

                all_efforts.append(
                    {
                        "distance_label": label,
                        "activity": act,
                        "elapsed_time": elapsed,
                        "year": year,
                    }
                )

        return render_template(
            "view_best_efforts.html", athlete_id=athlete_id, all_efforts=all_efforts
        )
    except Exception as e:
        logger.error(f"Error retrieving best efforts: {e}")
        return f"Error retrieving best efforts: {e}"


@bp.route("/activity/<activity_id>")
def activity_detail(activity_id):
    athlete_id = request.args.get("athlete_id")
    if not athlete_id:
        return "Athlete ID is required", 400

    # Get navigation data - find previous and next activities
    nav_query = text(
        """
        SELECT id, name, start_date
        FROM activities 
        WHERE athlete_id = :athlete_id 
        ORDER BY start_date DESC, id DESC
    """
    )
    nav_results = db.session.execute(nav_query, {"athlete_id": athlete_id}).fetchall()

    # Find current activity position and get prev/next
    prev_activity = None
    next_activity = None

    for i, nav_result in enumerate(nav_results):
        if str(nav_result.id) == str(activity_id):
            if i > 0:
                prev_activity = nav_results[i - 1]
            if i < len(nav_results) - 1:
                next_activity = nav_results[i + 1]
            break

    # First try to get from the processed all_athlete_activities table
    query = text(
        """
        SELECT athlete_id, block_id, week_id, activity_type, activity_id, elapsed_time, distance, 
               mean_hr, stdev_hr, freq_hr, time_in_z1, time_in_z2, time_in_z3, time_in_z4, time_in_z5, 
               elevation, stdev_elevation, freq_elevation, pace, stdev_pace, freq_pace, cadence, athlete_count 
        FROM all_athlete_activities 
        WHERE athlete_id = :athlete_id AND activity_id = :activity_id 
        LIMIT 1
    """
    )
    result = db.session.execute(
        query, {"athlete_id": athlete_id, "activity_id": activity_id}
    ).fetchone()

    if result:
        # Convert the SQLAlchemy Row to a dictionary using the _mapping attribute
        record = dict(result._mapping)

        # Get additional data from the raw activities table for name, date, suffer_score, best efforts
        activity = (
            db.session.query(Activity)
            .filter_by(athlete_id=athlete_id, id=activity_id)
            .first()
        )

        if activity:
            record["name"] = activity.name
            record["start_date"] = activity.start_date
            record["suffer_score"] = activity.suffer_score

            # Calculate best efforts with paces
            best_effort_distances = [
                ("400m", activity.be_400m, 400),
                ("1/2 Mile", activity.be_half_mile, 804.67),
                ("1km", activity.be_1km, 1000),
                ("1 Mile", activity.be_1_mile, 1609.34),
                ("2 mile", activity.be_2_miles, 3218.69),
                ("5km", activity.be_5km, 5000),
                ("10km", activity.be_10km, 10000),
                ("15km", activity.be_15km, 15000),
                ("10 mile", activity.be_10_miles, 16093.4),
                ("20km", activity.be_20km, 20000),
                ("Half-Marathon", activity.be_half_marathon, 21097.5),
                ("30km", activity.be_30km, 30000),
                ("Marathon", activity.be_marathon, 42195),
                ("50km", activity.be_50km, 50000),
            ]

            best_efforts = []
            for distance_label, time_seconds, distance_meters in best_effort_distances:
                if time_seconds:
                    # Calculate pace in min/km
                    pace_per_km = (time_seconds / 60) / (distance_meters / 1000)
                    best_efforts.append(
                        {
                            "distance": distance_label,
                            "time": time_seconds,
                            "pace": pace_per_km,
                        }
                    )

            record["best_efforts"] = best_efforts

        return render_template(
            "activity_detail.html",
            activity=record,
            athlete_id=athlete_id,
            prev_activity=prev_activity,
            next_activity=next_activity,
        )

    # If not found in processed table, try to get from raw activities table
    try:
        activity = (
            db.session.query(Activity)
            .filter_by(athlete_id=athlete_id, id=activity_id)
            .first()
        )

        if not activity:
            abort(404, description="Activity not found")

        # Create a record dictionary with the same structure as the processed table
        # but using raw activity data
        pace_value = None
        if activity.distance and activity.moving_time and activity.distance > 0:
            # Calculate pace in m/s (to match the processed data format)
            pace_value = activity.distance / activity.moving_time

        record = {
            "athlete_id": activity.athlete_id,
            "activity_id": activity.id,
            "activity_type": activity.type,
            "name": activity.name,
            "start_date": activity.start_date,
            "suffer_score": activity.suffer_score,
            "elapsed_time": activity.elapsed_time,
            "distance": activity.distance,
            "elevation": activity.total_elevation_gain,
            "mean_hr": activity.average_heartrate,
            "pace": pace_value,
            # Set default values for processed fields that don't exist in raw data
            "block_id": None,
            "week_id": None,
            "stdev_hr": None,
            "freq_hr": None,
            "time_in_z1": None,
            "time_in_z2": None,
            "time_in_z3": None,
            "time_in_z4": None,
            "time_in_z5": None,
            "stdev_elevation": None,
            "freq_elevation": None,
            "stdev_pace": None,
            "freq_pace": None,
            "cadence": activity.average_cadence,
            "athlete_count": None,
        }

        # Calculate best efforts with paces
        best_effort_distances = [
            ("400m", activity.be_400m, 400),
            ("1/2 Mile", activity.be_half_mile, 804.67),
            ("1km", activity.be_1km, 1000),
            ("1 Mile", activity.be_1_mile, 1609.34),
            ("2 mile", activity.be_2_miles, 3218.69),
            ("5km", activity.be_5km, 5000),
            ("10km", activity.be_10km, 10000),
            ("15km", activity.be_15km, 15000),
            ("10 mile", activity.be_10_miles, 16093.4),
            ("20km", activity.be_20km, 20000),
            ("Half-Marathon", activity.be_half_marathon, 21097.5),
            ("30km", activity.be_30km, 30000),
            ("Marathon", activity.be_marathon, 42195),
            ("50km", activity.be_50km, 50000),
        ]

        best_efforts = []
        for distance_label, time_seconds, distance_meters in best_effort_distances:
            if time_seconds:
                # Calculate pace in min/km
                pace_per_km = (time_seconds / 60) / (distance_meters / 1000)
                best_efforts.append(
                    {
                        "distance": distance_label,
                        "time": time_seconds,
                        "pace": pace_per_km,
                    }
                )

        record["best_efforts"] = best_efforts

        return render_template(
            "activity_detail.html",
            activity=record,
            athlete_id=athlete_id,
            prev_activity=prev_activity,
            next_activity=next_activity,
        )

    except Exception as e:
        logger.error(f"Error retrieving activity {activity_id}: {e}")
        abort(404, description="Activity not found")
