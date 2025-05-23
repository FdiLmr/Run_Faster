"""Tests for utility functions."""

import pytest
import os
import tempfile
import torch
import joblib
from sklearn.preprocessing import StandardScaler

from utils.marathon_predictor_utils import (
    save_model,
    load_model_and_scaler,
    validate_model_files,
)
from marathon_predictor.models import Neuromodel1, Neuromodel2


class TestSaveModel:
    """Tests for save_model function."""

    def test_save_model_success(self):
        """Test successful model and scaler saving."""
        temp_dir = tempfile.mkdtemp()
        model_path = os.path.join(temp_dir, "test_model.pth")
        scaler_path = os.path.join(temp_dir, "test_scaler.pkl")

        # Create model and scaler
        model = Neuromodel1()
        scaler = StandardScaler()
        scaler.fit([[5000, 1200, 50], [10000, 2400, 60]])

        # Save
        save_model(model, scaler, model_path, scaler_path)

        # Verify files exist
        assert os.path.exists(model_path)
        assert os.path.exists(scaler_path)

    def test_save_model_creates_directories(self):
        """Test that save_model creates directories if they don't exist."""
        temp_dir = tempfile.mkdtemp()
        nested_dir = os.path.join(temp_dir, "nested", "directory")
        model_path = os.path.join(nested_dir, "model.pth")
        scaler_path = os.path.join(nested_dir, "scaler.pkl")

        model = Neuromodel1()
        scaler = StandardScaler()
        scaler.fit([[5000, 1200, 50]])

        save_model(model, scaler, model_path, scaler_path)

        assert os.path.exists(model_path)
        assert os.path.exists(scaler_path)

    def test_save_model_invalid_path(self):
        """Test save_model with invalid path."""
        model = Neuromodel1()
        scaler = StandardScaler()
        scaler.fit([[5000, 1200, 50]])

        # Try to save to a path that can't be created
        # On Windows, this might not raise an error, so we skip if it doesn't
        invalid_path = "Z:/invalid/path/that/cannot/be/created"

        try:
            save_model(model, scaler, invalid_path, invalid_path)
            # If it doesn't raise an error, skip this test
            pytest.skip("Cannot test invalid path on this system")
        except OSError:
            # This is what we expect
            pass


class TestLoadModelAndScaler:
    """Tests for load_model_and_scaler function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.model_path = os.path.join(self.temp_dir, "model.pth")
        self.scaler_path = os.path.join(self.temp_dir, "scaler.pkl")

        # Create and save test model and scaler
        model = Neuromodel1()
        scaler = StandardScaler()
        scaler.fit([[5000, 1200, 50], [10000, 2400, 60]])

        torch.save(model.state_dict(), self.model_path)
        joblib.dump(scaler, self.scaler_path)

    def test_load_model_and_scaler_success(self):
        """Test successful loading of model and scaler."""
        model, scaler = load_model_and_scaler(
            Neuromodel1, self.model_path, self.scaler_path
        )

        assert isinstance(model, Neuromodel1)
        assert isinstance(scaler, StandardScaler)
        assert not model.training  # Should be in eval mode

    def test_load_model_and_scaler_model2(self):
        """Test loading Model 2."""
        # Create Model 2 files
        model2 = Neuromodel2()
        scaler2 = StandardScaler()
        scaler2.fit([[5000, 1200, 10000, 2400, 50]])

        model2_path = os.path.join(self.temp_dir, "model2.pth")
        scaler2_path = os.path.join(self.temp_dir, "scaler2.pkl")

        torch.save(model2.state_dict(), model2_path)
        joblib.dump(scaler2, scaler2_path)

        model, scaler = load_model_and_scaler(Neuromodel2, model2_path, scaler2_path)

        assert isinstance(model, Neuromodel2)
        assert isinstance(scaler, StandardScaler)

    def test_load_model_missing_model_file(self):
        """Test loading with missing model file."""
        with pytest.raises(FileNotFoundError, match="Model file not found"):
            load_model_and_scaler(Neuromodel1, "nonexistent.pth", self.scaler_path)

    def test_load_model_missing_scaler_file(self):
        """Test loading with missing scaler file."""
        with pytest.raises(FileNotFoundError, match="Scaler file not found"):
            load_model_and_scaler(Neuromodel1, self.model_path, "nonexistent.pkl")

    def test_load_model_corrupted_model_file(self):
        """Test loading with corrupted model file."""
        # Create a corrupted model file
        corrupted_path = os.path.join(self.temp_dir, "corrupted.pth")
        with open(corrupted_path, "w") as f:
            f.write("This is not a valid PyTorch model file")

        with pytest.raises(RuntimeError, match="Failed to load model"):
            load_model_and_scaler(Neuromodel1, corrupted_path, self.scaler_path)

    def test_load_model_corrupted_scaler_file(self):
        """Test loading with corrupted scaler file."""
        # Create a corrupted scaler file
        corrupted_scaler_path = os.path.join(self.temp_dir, "corrupted.pkl")
        with open(corrupted_scaler_path, "w") as f:
            f.write("This is not a valid pickle file")

        with pytest.raises(RuntimeError, match="Failed to load model"):
            load_model_and_scaler(Neuromodel1, self.model_path, corrupted_scaler_path)


class TestValidateModelFiles:
    """Tests for validate_model_files function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.model_path = os.path.join(self.temp_dir, "model.pth")
        self.scaler_path = os.path.join(self.temp_dir, "scaler.pkl")

        # Create test files
        model = Neuromodel1()
        scaler = StandardScaler()
        scaler.fit([[5000, 1200, 50]])

        torch.save(model.state_dict(), self.model_path)
        joblib.dump(scaler, self.scaler_path)

    def test_validate_model_files_success(self):
        """Test validation with existing, readable files."""
        assert validate_model_files(self.model_path, self.scaler_path) is True

    def test_validate_model_files_missing_model(self):
        """Test validation with missing model file."""
        assert validate_model_files("nonexistent.pth", self.scaler_path) is False

    def test_validate_model_files_missing_scaler(self):
        """Test validation with missing scaler file."""
        assert validate_model_files(self.model_path, "nonexistent.pkl") is False

    def test_validate_model_files_both_missing(self):
        """Test validation with both files missing."""
        assert validate_model_files("nonexistent.pth", "nonexistent.pkl") is False

    def test_validate_model_files_unreadable(self):
        """Test validation with unreadable files (if possible)."""
        # This test might not work on all systems due to permission restrictions
        try:
            # Try to make files unreadable
            os.chmod(self.model_path, 0o000)
            os.chmod(self.scaler_path, 0o000)

            result = validate_model_files(self.model_path, self.scaler_path)

            # On Windows, chmod might not work as expected
            if result is True:
                pytest.skip("Cannot test unreadable files on this system")
            else:
                assert result is False

        except (OSError, PermissionError):
            # If we can't change permissions, skip this test
            pytest.skip("Cannot test unreadable files on this system")
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(self.model_path, 0o644)
                os.chmod(self.scaler_path, 0o644)
            except (OSError, PermissionError):
                pass


class TestUtilsIntegration:
    """Integration tests for utility functions."""

    def test_save_and_load_roundtrip(self):
        """Test that saving and loading preserves model functionality."""
        temp_dir = tempfile.mkdtemp()
        model_path = os.path.join(temp_dir, "model.pth")
        scaler_path = os.path.join(temp_dir, "scaler.pkl")

        # Create original model and scaler
        original_model = Neuromodel1()
        original_scaler = StandardScaler()

        # Fit scaler and get a prediction from original model
        training_data = [[5000, 1200, 50], [10000, 2400, 60]]
        original_scaler.fit(training_data)

        torch.tensor([[7500, 1800, 55]], dtype=torch.float32)
        test_input_scaled = original_scaler.transform([[7500, 1800, 55]])
        test_tensor = torch.tensor(test_input_scaled, dtype=torch.float32)

        original_model.eval()
        with torch.no_grad():
            original_prediction = original_model(test_tensor).item()

        # Save model and scaler
        save_model(original_model, original_scaler, model_path, scaler_path)

        # Load model and scaler
        loaded_model, loaded_scaler = load_model_and_scaler(
            Neuromodel1, model_path, scaler_path
        )

        # Test that loaded model produces same prediction
        loaded_input_scaled = loaded_scaler.transform([[7500, 1800, 55]])
        loaded_tensor = torch.tensor(loaded_input_scaled, dtype=torch.float32)

        with torch.no_grad():
            loaded_prediction = loaded_model(loaded_tensor).item()

        # Predictions should be identical (or very close due to floating point)
        assert abs(original_prediction - loaded_prediction) < 1e-6

    def test_validate_then_load(self):
        """Test validation followed by loading."""
        temp_dir = tempfile.mkdtemp()
        model_path = os.path.join(temp_dir, "model.pth")
        scaler_path = os.path.join(temp_dir, "scaler.pkl")

        # Initially files don't exist
        assert not validate_model_files(model_path, scaler_path)

        # Create and save files
        model = Neuromodel2()
        scaler = StandardScaler()
        scaler.fit([[5000, 1200, 10000, 2400, 50]])

        save_model(model, scaler, model_path, scaler_path)

        # Now validation should pass
        assert validate_model_files(model_path, scaler_path)

        # And loading should work
        loaded_model, loaded_scaler = load_model_and_scaler(
            Neuromodel2, model_path, scaler_path
        )

        assert isinstance(loaded_model, Neuromodel2)
        assert isinstance(loaded_scaler, StandardScaler)
