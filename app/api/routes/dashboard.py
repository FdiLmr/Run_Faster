from flask import Blueprint, render_template, send_file, flash, redirect
import random
import logging

from visualizations import athletevsbest, athletevsbestimprovement
from train_model import train_model
from sql_methods import read_db
from race_prediction import get_latest_prediction, calculate_athlete_predictions

logger = logging.getLogger(__name__)

bp = Blueprint("dashboard", __name__)


@bp.route("/visualize/performance/<athlete_id>")
def visualize_performance(athlete_id):
    """Generate and return performance visualization."""
    try:
        bytes_image = athletevsbest(athlete_id)
        if bytes_image is None:
            return "Error generating visualization", 500
        return send_file(bytes_image, mimetype="image/png")
    except Exception as e:
        logger.error(f"Error in performance visualization: {e}")
        return f"Error: {str(e)}", 500


@bp.route("/visualize/improvement/<athlete_id>")
def visualize_improvement(athlete_id):
    """Generate and return improvement visualization."""
    try:
        bytes_image = athletevsbestimprovement(athlete_id)
        if bytes_image is None:
            return "Error generating visualization", 500
        return send_file(bytes_image, mimetype="image/png")
    except Exception as e:
        logger.error(f"Error in improvement visualization: {e}")
        return f"Error: {str(e)}", 500


@bp.route("/visualize/<athlete_id>")
def visualize(athlete_id):
    """Render the visualization page for an athlete."""
    return render_template(
        "render.html",
        athlete_id=athlete_id,
        random_num=random.randint(1, 1000000),  # Cache busting
    )


@bp.route("/dashboard/<athlete_id>")
def dashboard(athlete_id):
    return render_template("dashboard.html", athlete_id=athlete_id)


@bp.route("/model_results/<athlete_id>")
def model_results(athlete_id):
    """Display model results and SHAP plots for an athlete."""
    try:
        # Check if model outputs exist
        model_outputs = read_db("model_outputs")
        if model_outputs.empty or not any(model_outputs["athlete_id"] == athlete_id):
            # Train model if no results exist
            results = train_model(athlete_id)
            return render_template(
                "model_results.html", athlete_id=athlete_id, model_outputs=results
            )
        else:
            # Get existing results
            athlete_outputs = model_outputs[model_outputs["athlete_id"] == athlete_id]
            results = {
                "absolute_vdot_score": athlete_outputs[
                    athlete_outputs["y_name"] == "absolute_vdot"
                ]["model_score"].iloc[0],
                "vdot_change_score": athlete_outputs[
                    athlete_outputs["y_name"] == "vdot_change"
                ]["model_score"].iloc[0],
            }
            return render_template(
                "model_results.html", athlete_id=athlete_id, model_outputs=results
            )
    except Exception as e:
        logger.error(f"Error displaying model results: {e}")
        return render_template(
            "model_results.html", athlete_id=athlete_id, error_message=str(e)
        )


@bp.route("/train_model/<athlete_id>")
def train_model_route(athlete_id):
    """Train model for a specific athlete."""
    try:
        results = train_model(athlete_id)
        return render_template(
            "model_results.html", athlete_id=athlete_id, model_outputs=results
        )
    except Exception as e:
        logger.error(f"Error training model: {e}")
        return render_template(
            "model_results.html", athlete_id=athlete_id, error_message=str(e)
        )


@bp.route("/race_predictions/<athlete_id>")
def race_predictions(athlete_id):
    """Display the race predictions page for an athlete"""
    # Check if predictions exist, if not calculate them
    prediction_data = get_latest_prediction(athlete_id)

    if not prediction_data:
        prediction_data = calculate_athlete_predictions(athlete_id)

    # If still no prediction data, athlete might not have required PBs
    if not prediction_data:
        flash(
            "Unable to generate predictions. Athlete needs both 5K and 10K personal bests.",
            "warning",
        )
        return redirect(f"/dashboard/{athlete_id}")

    return render_template(
        "race_predictions.html", athlete_id=athlete_id, prediction_data=prediction_data
    )
