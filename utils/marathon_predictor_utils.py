"""Utility functions for marathon predictor models."""

import os
import torch
import joblib
from typing import Tuple, Type
from sklearn.preprocessing import StandardScaler


def save_model(
    model: torch.nn.Module, scaler: StandardScaler, model_path: str, scaler_path: str
) -> None:
    """Save a trained model and its scaler to files.

    Args:
        model: Trained PyTorch model
        scaler: Fitted StandardScaler
        model_path: Path to save model state dict
        scaler_path: Path to save scaler

    Raises:
        OSError: If saving fails
    """
    try:
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        os.makedirs(os.path.dirname(scaler_path), exist_ok=True)

        torch.save(model.state_dict(), model_path)
        joblib.dump(scaler, scaler_path)
    except Exception as e:
        raise OSError(f"Failed to save model: {str(e)}")


def load_model_and_scaler(
    model_class: Type[torch.nn.Module], model_path: str, scaler_path: str
) -> Tuple[torch.nn.Module, StandardScaler]:
    """Load a model and its scaler from files.

    Args:
        model_class: Model class to instantiate
        model_path: Path to model state dict
        scaler_path: Path to scaler pickle file

    Returns:
        Tuple of (model, scaler)

    Raises:
        FileNotFoundError: If files don't exist
        RuntimeError: If loading fails
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Scaler file not found: {scaler_path}")

    try:
        model = model_class()
        model.load_state_dict(torch.load(model_path, map_location="cpu"))
        model.eval()

        scaler = joblib.load(scaler_path)

        return model, scaler
    except Exception as e:
        raise RuntimeError(f"Failed to load model: {str(e)}")


def validate_model_files(model_path: str, scaler_path: str) -> bool:
    """Check if model files exist and are readable.

    Args:
        model_path: Path to model file
        scaler_path: Path to scaler file

    Returns:
        True if both files exist and are readable
    """
    return (
        os.path.exists(model_path)
        and os.access(model_path, os.R_OK)
        and os.path.exists(scaler_path)
        and os.access(scaler_path, os.R_OK)
    )
