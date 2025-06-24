"""
Refactored ML training module using modular ML package.

This module provides a clean interface to the ML pipeline while maintaining
backward compatibility with the original train_model.py functionality.
"""

import logging
from typing import Optional, Dict, Any
from ml import MLPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_model(athlete_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Train model for a specific athlete or all athletes.

    This function maintains backward compatibility with the original
    train_model.py while using the new modular ML pipeline.

    Args:
        athlete_id: Optional athlete ID to filter training data

    Returns:
        Dictionary with training results and metrics
    """
    try:
        # Initialize ML pipeline
        pipeline = MLPipeline()

        # Run the complete ML pipeline
        results = pipeline.train_model(athlete_id)

        # Extract key metrics for backward compatibility
        return {
            "absolute_vdot_score": results.get("absolute_vdot_score"),
            "vdot_change_score": results.get("vdot_change_score"),
            "shap_plots_generated": _check_shap_plots_status(results),
            "visualization_status": _get_visualization_status(results),
        }

    except Exception as e:
        logger.error(f"Error in model training pipeline: {e}")
        raise


def _check_shap_plots_status(results: Dict[str, Any]) -> bool:
    """Check if SHAP plots were successfully generated."""
    shap_abs = results.get("absolute_vdot_shap", {})
    shap_change = results.get("vdot_change_shap", {})

    return (
        shap_abs.get("status") == "success" and shap_change.get("status") == "success"
    )


def _get_visualization_status(results: Dict[str, Any]) -> str:
    """Get overall visualization generation status."""
    if "visualization_error" in results:
        return f"Error: {results['visualization_error']}"

    shap_generated = _check_shap_plots_status(results)
    importance_plots = (
        "absolute_vdot_importance_plot" in results
        and "vdot_change_importance_plot" in results
    )

    if shap_generated and importance_plots:
        return "All visualizations generated successfully"
    elif shap_generated or importance_plots:
        return "Some visualizations generated successfully"
    else:
        return "No visualizations generated"


def get_model_results(athlete_id: Optional[str] = None):
    """
    Get model results from database.

    Args:
        athlete_id: Optional athlete ID to filter results

    Returns:
        DataFrame with model results
    """
    try:
        pipeline = MLPipeline()
        return pipeline.get_model_results(athlete_id)
    except Exception as e:
        logger.error(f"Error getting model results: {e}")
        raise


if __name__ == "__main__":
    # Run training for all athletes
    results = train_model()
    print(f"Training completed. Results: {results}")
