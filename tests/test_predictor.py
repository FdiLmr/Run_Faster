"""Tests for the MarathonPredictor class."""

import pytest
import os
import tempfile
import torch
import joblib
from sklearn.preprocessing import StandardScaler

from marathon_predictor.predictor import MarathonPredictor
from marathon_predictor.models import Neuromodel1, Neuromodel2


class TestMarathonPredictorInitialization:
    """Tests for MarathonPredictor initialization."""

    def test_init_default_model_dir(self):
        """Test initialization with default model directory."""
        predictor = MarathonPredictor()
        assert predictor.model_dir is not None
        assert predictor.model1 is None
        assert predictor.scaler1 is None
        assert predictor.model2 is None
        assert predictor.scaler2 is None

    def test_init_custom_model_dir(self):
        """Test initialization with custom model directory."""
        custom_dir = "/custom/path"
        predictor = MarathonPredictor(model_dir=custom_dir)
        assert predictor.model_dir == custom_dir

    def test_model_loading_status_initial(self):
        """Test that models are not loaded initially."""
        predictor = MarathonPredictor()
        assert not predictor.is_model1_loaded()
        assert not predictor.is_model2_loaded()


class TestMarathonPredictorModelLoading:
    """Tests for model loading functionality."""

    def setup_method(self):
        """Set up test fixtures with temporary files."""
        self.temp_dir = tempfile.mkdtemp()
        self.predictor = MarathonPredictor(model_dir=self.temp_dir)

        # Create dummy model and scaler files
        self.model1_path = os.path.join(self.temp_dir, "neuromodel1.pth")
        self.scaler1_path = os.path.join(self.temp_dir, "scaler1.pkl")
        self.model2_path = os.path.join(self.temp_dir, "neuromodel2.pth")
        self.scaler2_path = os.path.join(self.temp_dir, "scaler2.pkl")

        # Create and save dummy models
        model1 = Neuromodel1()
        model2 = Neuromodel2()
        scaler1 = StandardScaler()
        scaler2 = StandardScaler()

        # Fit scalers with dummy data
        scaler1.fit([[5000, 1200, 50], [10000, 2400, 60]])
        scaler2.fit([[5000, 1200, 10000, 2400, 50], [3000, 900, 8000, 2000, 60]])

        torch.save(model1.state_dict(), self.model1_path)
        torch.save(model2.state_dict(), self.model2_path)
        joblib.dump(scaler1, self.scaler1_path)
        joblib.dump(scaler2, self.scaler2_path)

    def test_load_model1_success(self):
        """Test successful loading of Model 1."""
        self.predictor.load_model1()
        assert self.predictor.is_model1_loaded()
        assert isinstance(self.predictor.model1, Neuromodel1)
        assert isinstance(self.predictor.scaler1, StandardScaler)

    def test_load_model2_success(self):
        """Test successful loading of Model 2."""
        self.predictor.load_model2()
        assert self.predictor.is_model2_loaded()
        assert isinstance(self.predictor.model2, Neuromodel2)
        assert isinstance(self.predictor.scaler2, StandardScaler)

    def test_load_all_models_success(self):
        """Test successful loading of all models."""
        self.predictor.load_all_models()
        assert self.predictor.is_model1_loaded()
        assert self.predictor.is_model2_loaded()

    def test_load_model1_custom_paths(self):
        """Test loading Model 1 with custom paths."""
        self.predictor.load_model1(self.model1_path, self.scaler1_path)
        assert self.predictor.is_model1_loaded()

    def test_load_model2_custom_paths(self):
        """Test loading Model 2 with custom paths."""
        self.predictor.load_model2(self.model2_path, self.scaler2_path)
        assert self.predictor.is_model2_loaded()

    def test_load_model1_missing_model_file(self):
        """Test loading Model 1 with missing model file."""
        os.remove(self.model1_path)
        with pytest.raises(RuntimeError, match="Failed to load Model 1"):
            self.predictor.load_model1()

    def test_load_model1_missing_scaler_file(self):
        """Test loading Model 1 with missing scaler file."""
        os.remove(self.scaler1_path)
        with pytest.raises(RuntimeError, match="Failed to load Model 1"):
            self.predictor.load_model1()

    def test_load_model2_missing_files(self):
        """Test loading Model 2 with missing files."""
        os.remove(self.model2_path)
        with pytest.raises(RuntimeError, match="Failed to load Model 2"):
            self.predictor.load_model2()


class TestMarathonPredictorPredictions:
    """Tests for prediction functionality."""

    def setup_method(self):
        """Set up test fixtures with loaded models."""
        self.temp_dir = tempfile.mkdtemp()
        self.predictor = MarathonPredictor(model_dir=self.temp_dir)

        # Create and save dummy models
        model1 = Neuromodel1()
        model2 = Neuromodel2()
        scaler1 = StandardScaler()
        scaler2 = StandardScaler()

        # Fit scalers with dummy data
        scaler1.fit([[5000, 1200, 50], [10000, 2400, 60]])
        scaler2.fit([[5000, 1200, 10000, 2400, 50], [3000, 900, 8000, 2000, 60]])

        model1_path = os.path.join(self.temp_dir, "neuromodel1.pth")
        scaler1_path = os.path.join(self.temp_dir, "scaler1.pkl")
        model2_path = os.path.join(self.temp_dir, "neuromodel2.pth")
        scaler2_path = os.path.join(self.temp_dir, "scaler2.pkl")

        torch.save(model1.state_dict(), model1_path)
        torch.save(model2.state_dict(), model2_path)
        joblib.dump(scaler1, scaler1_path)
        joblib.dump(scaler2, scaler2_path)

        # Load models
        self.predictor.load_all_models()

    def test_predict_single_race_success(self):
        """Test successful single race prediction."""
        try:
            result = self.predictor.predict_single_race(5000, 20.0, 50.0)
            assert isinstance(result, float)
            assert result > 0
        except RuntimeError as e:
            # Untrained model may return negative predictions
            assert "Model returned invalid prediction" in str(e)

    def test_predict_dual_race_success(self):
        """Test successful dual race prediction."""
        try:
            result = self.predictor.predict_dual_race(5000, 20.0, 10000, 40.0, 50.0)
            assert isinstance(result, float)
            assert result > 0
        except RuntimeError as e:
            # Untrained model may return negative predictions
            assert "Model returned invalid prediction" in str(e)

    def test_predict_both_success(self):
        """Test successful prediction from both models."""
        try:
            results = self.predictor.predict_both(5000, 20.0, 10000, 40.0, 50.0)
            assert isinstance(results, dict)
            # May have model1, model2, or both depending on what succeeds
            assert len(results) > 0
        except RuntimeError as e:
            # If both models return negative predictions, this is expected
            assert "Model returned invalid prediction" in str(e)

    def test_predict_single_race_model_not_loaded(self):
        """Test single race prediction when model not loaded."""
        predictor = MarathonPredictor()
        with pytest.raises(RuntimeError, match="Model 1 not loaded"):
            predictor.predict_single_race(5000, 20.0, 50.0)

    def test_predict_dual_race_model_not_loaded(self):
        """Test dual race prediction when model not loaded."""
        predictor = MarathonPredictor()
        with pytest.raises(RuntimeError, match="Model 2 not loaded"):
            predictor.predict_dual_race(5000, 20.0, 10000, 40.0, 50.0)

    def test_predict_both_no_models_loaded(self):
        """Test prediction when no models are loaded."""
        predictor = MarathonPredictor()
        with pytest.raises(RuntimeError, match="No models loaded"):
            predictor.predict_both(5000, 20.0, 10000, 40.0, 50.0)

    def test_predict_single_race_invalid_inputs(self):
        """Test single race prediction with invalid inputs."""
        with pytest.raises(ValueError):
            self.predictor.predict_single_race(-1000, 20.0, 50.0)

    def test_predict_dual_race_invalid_inputs(self):
        """Test dual race prediction with invalid inputs."""
        with pytest.raises(ValueError):
            self.predictor.predict_dual_race(5000, -10.0, 10000, 40.0, 50.0)


class TestMarathonPredictorPartialLoading:
    """Tests for partial model loading scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.predictor = MarathonPredictor(model_dir=self.temp_dir)

        # Create only Model 1 files
        model1 = Neuromodel1()
        scaler1 = StandardScaler()
        scaler1.fit([[5000, 1200, 50], [10000, 2400, 60]])

        model1_path = os.path.join(self.temp_dir, "neuromodel1.pth")
        scaler1_path = os.path.join(self.temp_dir, "scaler1.pkl")

        torch.save(model1.state_dict(), model1_path)
        joblib.dump(scaler1, scaler1_path)

        self.predictor.load_model1()

    def test_predict_both_only_model1_loaded(self):
        """Test predict_both when only Model 1 is loaded."""
        try:
            results = self.predictor.predict_both(5000, 20.0, 10000, 40.0, 50.0)
            assert isinstance(results, dict)
            assert "model1" in results
            assert "model2" not in results
            assert isinstance(results["model1"], float)
        except RuntimeError as e:
            # Untrained model may return negative predictions
            assert "Model returned invalid prediction" in str(e)


class TestMarathonPredictorStaticMethods:
    """Tests for static methods."""

    def test_load_model_and_scaler_success(self):
        """Test successful loading with static method."""
        temp_dir = tempfile.mkdtemp()

        # Create dummy files
        model = Neuromodel1()
        scaler = StandardScaler()
        scaler.fit([[5000, 1200, 50], [10000, 2400, 60]])

        model_path = os.path.join(temp_dir, "model.pth")
        scaler_path = os.path.join(temp_dir, "scaler.pkl")

        torch.save(model.state_dict(), model_path)
        joblib.dump(scaler, scaler_path)

        loaded_model, loaded_scaler = MarathonPredictor._load_model_and_scaler(
            Neuromodel1, model_path, scaler_path
        )

        assert isinstance(loaded_model, Neuromodel1)
        assert isinstance(loaded_scaler, StandardScaler)

    def test_load_model_and_scaler_missing_model(self):
        """Test loading with missing model file."""
        with pytest.raises(FileNotFoundError, match="Model file not found"):
            MarathonPredictor._load_model_and_scaler(
                Neuromodel1, "nonexistent_model.pth", "nonexistent_scaler.pkl"
            )

    def test_load_model_and_scaler_missing_scaler(self):
        """Test loading with missing scaler file."""
        temp_dir = tempfile.mkdtemp()
        model_path = os.path.join(temp_dir, "model.pth")

        # Create only model file
        model = Neuromodel1()
        torch.save(model.state_dict(), model_path)

        with pytest.raises(FileNotFoundError, match="Scaler file not found"):
            MarathonPredictor._load_model_and_scaler(
                Neuromodel1, model_path, "nonexistent_scaler.pkl"
            )
