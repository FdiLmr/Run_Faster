from flask import Blueprint, jsonify, request
import pandas as pd
import json
import os
import logging

from sql_methods import get_db_connection
from race_prediction import (
    get_latest_prediction,
    calculate_athlete_predictions,
    format_time,
)

logger = logging.getLogger(__name__)

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/dashboard-data/<athlete_id>")
def dashboard_data(athlete_id):
    try:
        # Create database connection
        conn = get_db_connection()

        # Try to get HR zone data from features tables first, fall back to activities table
        try:
            # First try to get data from all_athlete_activities which has time_in_z columns
            weekly_query = """
                SELECT 
                    DATE(DATE_SUB(a.start_date, INTERVAL WEEKDAY(a.start_date) DAY)) as week_start,
                    SUM(a.distance) / 1000 as distance_km,
                    SUM(COALESCE(aa.time_in_z1, 0) * a.moving_time / 3600) as zone1_hours,
                    SUM(COALESCE(aa.time_in_z2, 0) * a.moving_time / 3600) as zone2_hours,
                    SUM(COALESCE(aa.time_in_z3, 0) * a.moving_time / 3600) as zone3_hours,
                    SUM(COALESCE(aa.time_in_z4, 0) * a.moving_time / 3600) as zone4_hours,
                    SUM(COALESCE(aa.time_in_z5, 0) * a.moving_time / 3600) as zone5_hours,
                    SUM(CASE WHEN aa.time_in_z1 IS NULL THEN a.moving_time ELSE 0 END) / 3600 as no_hr_hours
                FROM activities a
                LEFT JOIN all_athlete_activities aa ON a.id = aa.activity_id AND a.athlete_id = aa.athlete_id
                WHERE a.athlete_id = %s AND a.type = 'Run'
                AND a.start_date >= DATE_SUB(CURDATE(), INTERVAL 4*7 + WEEKDAY(CURDATE()) DAY)
                GROUP BY week_start
                ORDER BY week_start DESC
                LIMIT 4
            """
            weekly_df = pd.read_sql_query(weekly_query, conn, params=(athlete_id,))

            # If no data or all zones are 0, fall back to simple distance calculation
            if (
                weekly_df.empty
                or weekly_df[
                    [
                        "zone1_hours",
                        "zone2_hours",
                        "zone3_hours",
                        "zone4_hours",
                        "zone5_hours",
                    ]
                ]
                .sum()
                .sum()
                == 0
            ):
                raise Exception(
                    "No HR zone data available, falling back to simple calculation"
                )

        except Exception as e:
            logger.warning(
                f"Could not get HR zone data from features tables: {e}. Falling back to simple distance calculation."
            )
            # Fallback to simple distance calculation without HR zones
            weekly_query = """
                SELECT 
                    DATE(DATE_SUB(start_date, INTERVAL WEEKDAY(start_date) DAY)) as week_start,
                    SUM(distance) / 1000 as distance_km,
                    0 as zone1_hours,
                    0 as zone2_hours,
                    0 as zone3_hours,
                    0 as zone4_hours,
                    0 as zone5_hours,
                    SUM(moving_time) / 3600 as no_hr_hours
                FROM activities 
                WHERE athlete_id = %s AND type = 'Run'
                AND start_date >= DATE_SUB(CURDATE(), INTERVAL 4*7 + WEEKDAY(CURDATE()) DAY)
                GROUP BY week_start
                ORDER BY week_start DESC
                LIMIT 4
            """
            weekly_df = pd.read_sql_query(weekly_query, conn, params=(athlete_id,))

        # Get this week's running distance (Monday to Sunday)
        current_week_query = """
            SELECT SUM(distance) / 1000 as distance_km
            FROM activities
            WHERE athlete_id = %s AND type = 'Run'
            AND start_date >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)
            AND start_date < DATE_ADD(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), INTERVAL 7 DAY)
        """
        weekly_distance_df = pd.read_sql_query(
            current_week_query, conn, params=(athlete_id,)
        )
        weekly_distance = (
            weekly_distance_df.iloc[0]["distance_km"]
            if not weekly_distance_df.empty
            and not pd.isna(weekly_distance_df.iloc[0]["distance_km"])
            else 0
        )

        # Get this month's running distance
        current_month_query = """
            SELECT SUM(distance) / 1000 as distance_km
            FROM activities
            WHERE athlete_id = %s AND type = 'Run'
            AND MONTH(start_date) = MONTH(CURRENT_DATE)
            AND YEAR(start_date) = YEAR(CURRENT_DATE)
        """
        monthly_distance_df = pd.read_sql_query(
            current_month_query, conn, params=(athlete_id,)
        )
        monthly_distance = (
            monthly_distance_df.iloc[0]["distance_km"]
            if not monthly_distance_df.empty
            and not pd.isna(monthly_distance_df.iloc[0]["distance_km"])
            else 0
        )

        # Get total weekly elevation (Monday to Sunday)
        elevation_query = """
            SELECT SUM(total_elevation_gain) as total_elevation
            FROM activities
            WHERE athlete_id = %s AND type = 'Run'
            AND start_date >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)
            AND start_date < DATE_ADD(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), INTERVAL 7 DAY)
        """
        elevation_df = pd.read_sql_query(elevation_query, conn, params=(athlete_id,))
        total_elevation = (
            elevation_df.iloc[0]["total_elevation"]
            if not elevation_df.empty
            and not pd.isna(elevation_df.iloc[0]["total_elevation"])
            else 0
        )

        # Get monthly running volume with HR zone data (last 6 months)
        try:
            # First try to get data from all_athlete_activities which has time_in_z columns
            monthly_query = """
                SELECT 
                    DATE_FORMAT(a.start_date, '%%Y-%%m') as month_id,
                    SUM(a.distance) / 1000 as distance_km,
                    SUM(COALESCE(aa.time_in_z1, 0) * a.moving_time / 3600) as zone1_hours,
                    SUM(COALESCE(aa.time_in_z2, 0) * a.moving_time / 3600) as zone2_hours,
                    SUM(COALESCE(aa.time_in_z3, 0) * a.moving_time / 3600) as zone3_hours,
                    SUM(COALESCE(aa.time_in_z4, 0) * a.moving_time / 3600) as zone4_hours,
                    SUM(COALESCE(aa.time_in_z5, 0) * a.moving_time / 3600) as zone5_hours,
                    SUM(CASE WHEN aa.time_in_z1 IS NULL THEN a.moving_time ELSE 0 END) / 3600 as no_hr_hours
                FROM activities a
                LEFT JOIN all_athlete_activities aa ON a.id = aa.activity_id AND a.athlete_id = aa.athlete_id
                WHERE a.athlete_id = %s AND a.type = 'Run'
                AND a.start_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                GROUP BY month_id
                ORDER BY month_id DESC
                LIMIT 6
            """
            monthly_df = pd.read_sql_query(monthly_query, conn, params=(athlete_id,))

            # If no data or all zones are 0, fall back to simple distance calculation
            if (
                monthly_df.empty
                or monthly_df[
                    [
                        "zone1_hours",
                        "zone2_hours",
                        "zone3_hours",
                        "zone4_hours",
                        "zone5_hours",
                    ]
                ]
                .sum()
                .sum()
                == 0
            ):
                raise Exception(
                    "No HR zone data available, falling back to simple calculation"
                )

        except Exception as e:
            logger.warning(
                f"Could not get monthly HR zone data: {e}. Falling back to simple distance calculation."
            )
            # Fallback to simple distance calculation without HR zones
            monthly_query = """
                SELECT 
                    DATE_FORMAT(start_date, '%%Y-%%m') as month_id,
                    SUM(distance) / 1000 as distance_km,
                    0 as zone1_hours,
                    0 as zone2_hours,
                    0 as zone3_hours,
                    0 as zone4_hours,
                    0 as zone5_hours,
                    SUM(moving_time) / 3600 as no_hr_hours
                FROM activities 
                WHERE athlete_id = %s AND type = 'Run'
                AND start_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                GROUP BY month_id
                ORDER BY month_id DESC
                LIMIT 6
            """
            monthly_df = pd.read_sql_query(monthly_query, conn, params=(athlete_id,))

        # Get recent activities
        recent_activities_query = """
            SELECT 
                id, name, type, start_date as date,
                ROUND(distance / 1000, 2) as distance,
                CONCAT(FLOOR(moving_time/3600), ':', LPAD(FLOOR((moving_time%%3600)/60), 2, '0')) as time,
                CONCAT(FLOOR((moving_time/60) / (distance/1000)), ':', 
                    LPAD(ROUND(((moving_time/60) / (distance/1000) - FLOOR((moving_time/60) / (distance/1000))) * 60), 2, '0')) as pace,
                ROUND(average_heartrate) as avg_hr
            FROM activities
            WHERE athlete_id = %s AND type = 'Run'
            ORDER BY start_date DESC
            LIMIT 5
        """
        try:
            recent_activities_df = pd.read_sql_query(
                recent_activities_query, conn, params=(athlete_id,)
            )
            recent_activities = recent_activities_df.to_dict(orient="records")

            # Format dates properly for JSON serialization
            for activity in recent_activities:
                if isinstance(activity["date"], pd.Timestamp):
                    activity["date"] = activity["date"].isoformat()

        except Exception as e:
            print(f"Error fetching recent activities: {str(e)}")
            recent_activities = []

        # Get training load from suffer_score (current week total, Monday to Sunday)
        training_load_query = """
            SELECT SUM(suffer_score) as total_suffer_score
            FROM activities
            WHERE athlete_id = %s AND type = 'Run' AND suffer_score IS NOT NULL
            AND start_date >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)
            AND start_date < DATE_ADD(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), INTERVAL 7 DAY)
        """
        training_load_df = pd.read_sql_query(
            training_load_query, conn, params=(athlete_id,)
        )

        training_load = (
            training_load_df.iloc[0]["total_suffer_score"]
            if not training_load_df.empty
            and not pd.isna(training_load_df.iloc[0]["total_suffer_score"])
            else 0
        )

        # Prepare weekly volume data for chart with HR zone breakdown
        weekly_labels = []
        weekly_volumes = []
        weekly_zone_data = []

        if not weekly_df.empty:
            for i, row in weekly_df.iterrows():
                # Format the week label in Python to avoid SQL formatting issues
                week_start = row["week_start"]
                if isinstance(week_start, str):
                    from datetime import datetime

                    week_start = datetime.strptime(week_start, "%Y-%m-%d").date()
                week_label = f"Week of {week_start.strftime('%b %d')}"
                weekly_labels.append(week_label)
                weekly_volumes.append(round(row["distance_km"], 1))

                # Calculate zone proportions based on time
                total_time = (
                    row["zone1_hours"]
                    + row["zone2_hours"]
                    + row["zone3_hours"]
                    + row["zone4_hours"]
                    + row["zone5_hours"]
                    + row["no_hr_hours"]
                )

                if total_time > 0:
                    zone_proportions = {
                        "zone1": round(
                            row["zone1_hours"] / total_time * row["distance_km"], 2
                        ),
                        "zone2": round(
                            row["zone2_hours"] / total_time * row["distance_km"], 2
                        ),
                        "zone3": round(
                            row["zone3_hours"] / total_time * row["distance_km"], 2
                        ),
                        "zone4": round(
                            row["zone4_hours"] / total_time * row["distance_km"], 2
                        ),
                        "zone5": round(
                            row["zone5_hours"] / total_time * row["distance_km"], 2
                        ),
                        "no_hr": round(
                            row["no_hr_hours"] / total_time * row["distance_km"], 2
                        ),
                    }
                else:
                    # If no HR data, show all as no_hr
                    zone_proportions = {
                        "zone1": 0,
                        "zone2": 0,
                        "zone3": 0,
                        "zone4": 0,
                        "zone5": 0,
                        "no_hr": round(row["distance_km"], 2),
                    }

                weekly_zone_data.append(zone_proportions)

            # Reverse the lists to show oldest to newest
            weekly_labels.reverse()
            weekly_volumes.reverse()
            weekly_zone_data.reverse()

        # Prepare monthly volume data for chart with HR zone breakdown
        monthly_labels = []
        monthly_volumes = []
        monthly_zone_data = []

        if not monthly_df.empty:
            for i, row in monthly_df.iterrows():
                # Format the month label in Python instead of SQL
                # Use the month_id to create a proper date for formatting
                year_month = row["month_id"]  # Format: '2024-06'
                month_date = pd.to_datetime(
                    year_month + "-01"
                )  # Add day to make it a valid date
                month_label = month_date.strftime("%b %Y")
                monthly_labels.append(month_label)
                monthly_volumes.append(round(row["distance_km"], 1))

                # Calculate zone proportions based on time
                total_time = (
                    row["zone1_hours"]
                    + row["zone2_hours"]
                    + row["zone3_hours"]
                    + row["zone4_hours"]
                    + row["zone5_hours"]
                    + row["no_hr_hours"]
                )

                if total_time > 0:
                    zone_proportions = {
                        "zone1": round(
                            row["zone1_hours"] / total_time * row["distance_km"], 2
                        ),
                        "zone2": round(
                            row["zone2_hours"] / total_time * row["distance_km"], 2
                        ),
                        "zone3": round(
                            row["zone3_hours"] / total_time * row["distance_km"], 2
                        ),
                        "zone4": round(
                            row["zone4_hours"] / total_time * row["distance_km"], 2
                        ),
                        "zone5": round(
                            row["zone5_hours"] / total_time * row["distance_km"], 2
                        ),
                        "no_hr": round(
                            row["no_hr_hours"] / total_time * row["distance_km"], 2
                        ),
                    }
                else:
                    # If no HR data, show all as no_hr
                    zone_proportions = {
                        "zone1": 0,
                        "zone2": 0,
                        "zone3": 0,
                        "zone4": 0,
                        "zone5": 0,
                        "no_hr": round(row["distance_km"], 2),
                    }

                monthly_zone_data.append(zone_proportions)

            # Reverse the lists to show oldest to newest
            monthly_labels.reverse()
            monthly_volumes.reverse()
            monthly_zone_data.reverse()

        # Return the dashboard data
        dashboard_data = {
            "weekly_distance": (
                round(weekly_distance, 1) if weekly_distance is not None else 0
            ),
            "monthly_distance": (
                round(monthly_distance, 1) if monthly_distance is not None else 0
            ),
            "weekly_elevation": (
                round(total_elevation, 0) if total_elevation is not None else 0
            ),
            "training_load": (
                round(training_load, 0) if training_load is not None else 0
            ),
            "weekly_labels": weekly_labels,
            "weekly_volumes": weekly_volumes,
            "weekly_zone_data": weekly_zone_data,
            "monthly_labels": monthly_labels,
            "monthly_volumes": monthly_volumes,
            "monthly_zone_data": monthly_zone_data,
            "recent_activities": recent_activities,
        }

        return jsonify(dashboard_data)

    except Exception as e:
        print(f"Dashboard data error: {str(e)}")
        return (
            jsonify(
                {
                    "error": str(e),
                    "weekly_distance": 0,
                    "monthly_distance": 0,
                    "weekly_elevation": 0,
                    "training_load": 0,
                    "weekly_labels": [],
                    "weekly_volumes": [],
                    "weekly_zone_data": [],
                    "monthly_labels": [],
                    "monthly_volumes": [],
                    "monthly_zone_data": [],
                    "recent_activities": [],
                }
            ),
            500,
        )


@bp.route("/activity-details/<activity_id>")
def activity_details(activity_id):
    try:
        athlete_id = request.args.get("athlete_id")
        if not athlete_id:
            return jsonify({"error": "Missing athlete_id parameter"}), 400

        # Build the file path: data/{athlete_id}/{activity_id}.json
        file_path = os.path.join("./data", str(athlete_id), f"{activity_id}.json")
        if not os.path.exists(file_path):
            return jsonify({"error": "Activity file not found"}), 404

        with open(file_path, "r", encoding="utf-8") as f:
            activity_data = json.load(f)

        # For demonstration, assume the detailed activity JSON has a 'laps' list,
        # and that each lap may have an 'average_heartrate' field.
        hr_trends = []
        if "laps" in activity_data:
            for lap in activity_data["laps"]:
                if "average_heartrate" in lap:
                    hr_trends.append(lap["average_heartrate"])

        return jsonify({"activity_id": activity_id, "hr_trends": hr_trends})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/volume-data/<athlete_id>")
def volume_data(athlete_id):
    # Get query parameters: granularity (weekly or monthly), start_date, end_date
    granularity = request.args.get("granularity", "weekly")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # Build query using MySQL pyformat syntax
    query = "SELECT id, distance, start_date FROM activities WHERE athlete_id = %(athlete_id)s AND type = 'Run'"
    params = {"athlete_id": athlete_id}
    if start_date:
        query += " AND start_date >= %(start_date)s"
        params["start_date"] = start_date
    if end_date:
        query += " AND start_date <= %(end_date)s"
        params["end_date"] = end_date

    engine = get_db_connection()
    df = pd.read_sql_query(query, engine, params=params)

    # Convert start_date column to datetime
    df["start_date"] = pd.to_datetime(df["start_date"])

    # Determine the overall date range from query parameters or data
    if start_date:
        start = pd.to_datetime(start_date)
    elif not df.empty:
        start = df["start_date"].min()
    else:
        start = pd.Timestamp.today()
    if end_date:
        end = pd.to_datetime(end_date)
    elif not df.empty:
        end = df["start_date"].max()
    else:
        end = pd.Timestamp.today()

    # Depending on granularity, generate complete period range and assign period column
    if granularity == "monthly":
        all_periods = pd.period_range(start=start, end=end, freq="M")
        df["period"] = df["start_date"].dt.to_period("M")
    else:
        # For weekly grouping, we use weeks ending on Sunday (adjust as needed)
        all_periods = pd.period_range(start=start, end=end, freq="W-SUN")
        df["period"] = df["start_date"].dt.to_period("W-SUN")

    # Group by period and sum the distance
    agg = df.groupby("period")["distance"].sum().reset_index()

    # Reindex using the complete period range so missing weeks/months get 0
    agg = agg.set_index("period").reindex(all_periods, fill_value=0).reset_index()
    agg.rename(columns={"index": "period"}, inplace=True)

    # Convert period to string and calculate kilometers
    agg["period"] = agg["period"].astype(str)
    agg["distance_km"] = (agg["distance"] / 1000).round(2)

    return jsonify(agg[["period", "distance_km"]].to_dict(orient="records"))


@bp.route("/race-prediction-data/<athlete_id>")
def race_prediction_data(athlete_id):
    """API endpoint to get prediction data for the dashboard widget"""
    prediction_data = get_latest_prediction(athlete_id)

    if not prediction_data:
        prediction_data = calculate_athlete_predictions(athlete_id)

    if not prediction_data:
        return jsonify({"error": "Insufficient data for predictions"})

    # Return a simplified version for the dashboard widget
    key_races = ["5km", "10km", "Half Marathon", "Marathon"]
    simplified_data = {
        "exponent": prediction_data["exponent"],
        "created_at": prediction_data.get("created_at", ""),
        "key_predictions": {
            race: {
                "realistic": format_time(
                    prediction_data["predictions"][race]["realistic"]
                )
            }
            for race in key_races
            if race in prediction_data["predictions"]
        },
    }

    return jsonify(simplified_data)


@bp.route("/full-race-predictions/<athlete_id>")
def full_race_predictions(athlete_id):
    """API endpoint to get full prediction data with all race distances and times"""
    prediction_data = get_latest_prediction(athlete_id)

    if not prediction_data:
        prediction_data = calculate_athlete_predictions(athlete_id)

    if not prediction_data:
        return jsonify({"error": "Insufficient data for predictions"})

    # Process predictions to include formatted times
    formatted_predictions = {}
    for race, predictions in prediction_data["predictions"].items():
        formatted_predictions[race] = {
            "optimistic": format_time(predictions["optimistic"]),
            "realistic": format_time(predictions["realistic"]),
            "conservative": format_time(predictions["conservative"]),
        }

    # Return full prediction data with formatted times
    result = {
        "exponent": prediction_data["exponent"],
        "base_performance": prediction_data["base_performance"],
        "predictions": formatted_predictions,
        "created_at": prediction_data.get("created_at", ""),
    }

    return jsonify(result)
