"""Main predictor class for marathon time prediction."""

import os
import torch
import joblib
from typing import Optional, Tuple, Dict
from sklearn.preprocessing import StandardScaler

from .models import Neuromodel1, Neuromodel2
from .inference import predict_marathon_time_model1, predict_marathon_time_model2


class MarathonPredictor:
    """Main class for marathon time prediction using neural networks.

    This class provides a unified interface for loading models and making predictions
    using either single race data (Model 1) or dual race data (Model 2).
    """

    def __init__(self, model_dir: Optional[str] = None):
        """Initialize the marathon predictor.

        Args:
            model_dir: Directory containing model files. If None, uses the package directory.
        """
        if model_dir is None:
            model_dir = os.path.dirname(__file__)

        self.model_dir = model_dir
        self.model1: Optional[Neuromodel1] = None
        self.scaler1: Optional[StandardScaler] = None
        self.model2: Optional[Neuromodel2] = None
        self.scaler2: Optional[StandardScaler] = None

    def load_model1(
        self, model_path: Optional[str] = None, scaler_path: Optional[str] = None
    ) -> None:
        """Load Model 1 (single race prediction).

        Args:
            model_path: Path to model file. If None, uses default path.
            scaler_path: Path to scaler file. If None, uses default path.

        Raises:
            FileNotFoundError: If model files don't exist
            RuntimeError: If loading fails
        """
        if model_path is None:
            model_path = os.path.join(self.model_dir, "neuromodel1.pth")
        if scaler_path is None:
            scaler_path = os.path.join(self.model_dir, "scaler1.pkl")

        try:
            self.model1, self.scaler1 = self._load_model_and_scaler(
                Neuromodel1, model_path, scaler_path
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load Model 1: {str(e)}")

    def load_model2(
        self, model_path: Optional[str] = None, scaler_path: Optional[str] = None
    ) -> None:
        """Load Model 2 (dual race prediction).

        Args:
            model_path: Path to model file. If None, uses default path.
            scaler_path: Path to scaler file. If None, uses default path.

        Raises:
            FileNotFoundError: If model files don't exist
            RuntimeError: If loading fails
        """
        if model_path is None:
            model_path = os.path.join(self.model_dir, "neuromodel2.pth")
        if scaler_path is None:
            scaler_path = os.path.join(self.model_dir, "scaler2.pkl")

        try:
            self.model2, self.scaler2 = self._load_model_and_scaler(
                Neuromodel2, model_path, scaler_path
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load Model 2: {str(e)}")

    def load_all_models(self) -> None:
        """Load both models with default paths."""
        self.load_model1()
        self.load_model2()

    def predict_single_race(
        self, distance: float, time_minutes: float, mileage: float
    ) -> float:
        """Predict marathon time using single race data.

        Args:
            distance: Race distance in meters
            time_minutes: Race time in minutes
            mileage: Weekly training mileage in miles

        Returns:
            Predicted marathon time in minutes

        Raises:
            RuntimeError: If Model 1 is not loaded
            ValueError: If inputs are invalid
        """
        if self.model1 is None or self.scaler1 is None:
            raise RuntimeError("Model 1 not loaded. Call load_model1() first.")

        return predict_marathon_time_model1(
            self.model1, self.scaler1, distance, time_minutes, mileage
        )

    def predict_dual_race(
        self,
        distance1: float,
        time1_minutes: float,
        distance2: float,
        time2_minutes: float,
        mileage: float,
    ) -> float:
        """Predict marathon time using dual race data.

        Args:
            distance1: First race distance in meters
            time1_minutes: First race time in minutes
            distance2: Second race distance in meters
            time2_minutes: Second race time in minutes
            mileage: Weekly training mileage in miles

        Returns:
            Predicted marathon time in minutes

        Raises:
            RuntimeError: If Model 2 is not loaded
            ValueError: If inputs are invalid
        """
        if self.model2 is None or self.scaler2 is None:
            raise RuntimeError("Model 2 not loaded. Call load_model2() first.")

        return predict_marathon_time_model2(
            self.model2,
            self.scaler2,
            distance1,
            time1_minutes,
            distance2,
            time2_minutes,
            mileage,
        )

    def predict_both(
        self,
        distance1: float,
        time1_minutes: float,
        distance2: float,
        time2_minutes: float,
        mileage: float,
    ) -> Dict[str, float]:
        """Get predictions from both models.

        Args:
            distance1: First race distance in meters
            time1_minutes: First race time in minutes
            distance2: Second race distance in meters
            time2_minutes: Second race time in minutes
            mileage: Weekly training mileage in miles

        Returns:
            Dictionary with predictions from both models

        Raises:
            RuntimeError: If models are not loaded
            ValueError: If inputs are invalid
        """
        results = {}

        if self.model1 is not None and self.scaler1 is not None:
            # Use the second race for single race prediction
            results["model1"] = self.predict_single_race(
                distance2, time2_minutes, mileage
            )

        if self.model2 is not None and self.scaler2 is not None:
            results["model2"] = self.predict_dual_race(
                distance1, time1_minutes, distance2, time2_minutes, mileage
            )

        if not results:
            raise RuntimeError(
                "No models loaded. Call load_model1() and/or load_model2() first."
            )

        return results

    def is_model1_loaded(self) -> bool:
        """Check if Model 1 is loaded."""
        return self.model1 is not None and self.scaler1 is not None

    def is_model2_loaded(self) -> bool:
        """Check if Model 2 is loaded."""
        return self.model2 is not None and self.scaler2 is not None

    @staticmethod
    def _load_model_and_scaler(
        model_class, model_path: str, scaler_path: str
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
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Scaler file not found: {scaler_path}")

        model = model_class()
        model.load_state_dict(torch.load(model_path, map_location="cpu"))
        model.eval()

        scaler = joblib.load(scaler_path)

        return model, scaler
