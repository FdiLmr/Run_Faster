"""Tests for marathon predictor inference functions."""

import pytest
import numpy as np
from unittest.mock import Mock
from sklearn.preprocessing import StandardScaler

from marathon_predictor.models import Neuromodel1, Neuromodel2
from marathon_predictor.inference import (
    validate_race_inputs,
    validate_mileage,
    predict_marathon_time_model1,
    predict_marathon_time_model2,
)


class TestValidationFunctions:
    """Tests for input validation functions."""

    def test_validate_race_inputs_valid(self):
        """Test validation with valid inputs."""
        # Should not raise any exceptions
        validate_race_inputs(5000, 20.5)
        validate_race_inputs(10000, 45.0)
        validate_race_inputs(21097, 120.0)

    def test_validate_race_inputs_negative_distance(self):
        """Test validation with negative distance."""
        with pytest.raises(ValueError, match="Distance must be positive"):
            validate_race_inputs(-1000, 20.0)

    def test_validate_race_inputs_zero_distance(self):
        """Test validation with zero distance."""
        with pytest.raises(ValueError, match="Distance must be positive"):
            validate_race_inputs(0, 20.0)

    def test_validate_race_inputs_negative_time(self):
        """Test validation with negative time."""
        with pytest.raises(ValueError, match="Time must be positive"):
            validate_race_inputs(5000, -10.0)

    def test_validate_race_inputs_zero_time(self):
        """Test validation with zero time."""
        with pytest.raises(ValueError, match="Time must be positive"):
            validate_race_inputs(5000, 0)

    def test_validate_race_inputs_too_large_distance(self):
        """Test validation with unreasonably large distance."""
        with pytest.raises(ValueError, match="Distance seems too large"):
            validate_race_inputs(100000, 300.0)  # 100km

    def test_validate_race_inputs_too_large_time(self):
        """Test validation with unreasonably large time."""
        with pytest.raises(ValueError, match="Time seems too large"):
            validate_race_inputs(5000, 700.0)  # > 10 hours

    def test_validate_mileage_valid(self):
        """Test mileage validation with valid inputs."""
        validate_mileage(0)
        validate_mileage(50.0)
        validate_mileage(100.5)

    def test_validate_mileage_negative(self):
        """Test mileage validation with negative input."""
        with pytest.raises(ValueError, match="Mileage must be non-negative"):
            validate_mileage(-10.0)

    def test_validate_mileage_too_large(self):
        """Test mileage validation with unreasonably large input."""
        with pytest.raises(ValueError, match="Mileage seems too large"):
            validate_mileage(250.0)


class TestPredictMarathonTimeModel1:
    """Tests for Model 1 prediction function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.model = Neuromodel1()
        self.scaler = StandardScaler()

        # Fit scaler with some dummy data
        dummy_data = np.array([[5000, 1200, 50], [10000, 2400, 60]])
        self.scaler.fit(dummy_data)

    def test_predict_valid_inputs(self):
        """Test prediction with valid inputs."""
        try:
            result = predict_marathon_time_model1(
                self.model, self.scaler, 5000, 20.0, 50.0
            )
            assert isinstance(result, float)
            assert result > 0
        except RuntimeError as e:
            # Untrained model may return negative predictions
            assert "Model returned invalid prediction" in str(e)

    def test_predict_invalid_distance(self):
        """Test prediction with invalid distance."""
        with pytest.raises(ValueError, match="Distance must be positive"):
            predict_marathon_time_model1(self.model, self.scaler, -1000, 20.0, 50.0)

    def test_predict_invalid_time(self):
        """Test prediction with invalid time."""
        with pytest.raises(ValueError, match="Time must be positive"):
            predict_marathon_time_model1(self.model, self.scaler, 5000, -10.0, 50.0)

    def test_predict_invalid_mileage(self):
        """Test prediction with invalid mileage."""
        with pytest.raises(ValueError, match="Mileage must be non-negative"):
            predict_marathon_time_model1(self.model, self.scaler, 5000, 20.0, -10.0)

    def test_predict_model_returns_negative(self):
        """Test handling when model returns negative prediction."""
        # Mock the model to return negative value
        mock_model = Mock()
        mock_model.eval.return_value = None
        mock_model.return_value.item.return_value = -100.0

        with pytest.raises(RuntimeError, match="Model returned invalid prediction"):
            predict_marathon_time_model1(mock_model, self.scaler, 5000, 20.0, 50.0)

    def test_predict_scaler_error(self):
        """Test handling when scaler fails."""
        # Create a scaler that will fail
        bad_scaler = Mock()
        bad_scaler.transform.side_effect = Exception("Scaler error")

        with pytest.raises(RuntimeError, match="Prediction failed"):
            predict_marathon_time_model1(self.model, bad_scaler, 5000, 20.0, 50.0)


class TestPredictMarathonTimeModel2:
    """Tests for Model 2 prediction function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.model = Neuromodel2()
        self.scaler = StandardScaler()

        # Fit scaler with some dummy data
        dummy_data = np.array(
            [[5000, 1200, 10000, 2400, 50], [3000, 900, 8000, 2000, 60]]
        )
        self.scaler.fit(dummy_data)

    def test_predict_valid_inputs(self):
        """Test prediction with valid inputs."""
        try:
            result = predict_marathon_time_model2(
                self.model, self.scaler, 5000, 20.0, 10000, 40.0, 50.0
            )
            assert isinstance(result, float)
            assert result > 0
        except RuntimeError as e:
            # Untrained model may return negative predictions
            assert "Model returned invalid prediction" in str(e)

    def test_predict_invalid_first_distance(self):
        """Test prediction with invalid first distance."""
        with pytest.raises(ValueError, match="Distance must be positive"):
            predict_marathon_time_model2(
                self.model, self.scaler, -1000, 20.0, 10000, 40.0, 50.0
            )

    def test_predict_invalid_second_distance(self):
        """Test prediction with invalid second distance."""
        with pytest.raises(ValueError, match="Distance must be positive"):
            predict_marathon_time_model2(
                self.model, self.scaler, 5000, 20.0, 0, 40.0, 50.0
            )

    def test_predict_invalid_first_time(self):
        """Test prediction with invalid first time."""
        with pytest.raises(ValueError, match="Time must be positive"):
            predict_marathon_time_model2(
                self.model, self.scaler, 5000, -10.0, 10000, 40.0, 50.0
            )

    def test_predict_invalid_second_time(self):
        """Test prediction with invalid second time."""
        with pytest.raises(ValueError, match="Time must be positive"):
            predict_marathon_time_model2(
                self.model, self.scaler, 5000, 20.0, 10000, 0, 50.0
            )

    def test_predict_invalid_mileage(self):
        """Test prediction with invalid mileage."""
        with pytest.raises(ValueError, match="Mileage must be non-negative"):
            predict_marathon_time_model2(
                self.model, self.scaler, 5000, 20.0, 10000, 40.0, -10.0
            )

    def test_predict_model_returns_negative(self):
        """Test handling when model returns negative prediction."""
        # Mock the model to return negative value
        mock_model = Mock()
        mock_model.eval.return_value = None
        mock_model.return_value.item.return_value = -100.0

        with pytest.raises(RuntimeError, match="Model returned invalid prediction"):
            predict_marathon_time_model2(
                mock_model, self.scaler, 5000, 20.0, 10000, 40.0, 50.0
            )

    def test_predict_scaler_error(self):
        """Test handling when scaler fails."""
        # Create a scaler that will fail
        bad_scaler = Mock()
        bad_scaler.transform.side_effect = Exception("Scaler error")

        with pytest.raises(RuntimeError, match="Prediction failed"):
            predict_marathon_time_model2(
                self.model, bad_scaler, 5000, 20.0, 10000, 40.0, 50.0
            )


class TestInferenceIntegration:
    """Integration tests for inference functions."""

    def test_model1_realistic_prediction(self):
        """Test Model 1 with realistic running data."""
        model = Neuromodel1()
        scaler = StandardScaler()

        # Fit with realistic training data
        training_data = np.array(
            [
                [5000, 1200, 50],  # 5K in 20 min, 50 mpw
                [10000, 2500, 60],  # 10K in ~42 min, 60 mpw
                [21097, 5400, 70],  # Half marathon in 1:30, 70 mpw
            ]
        )
        scaler.fit(training_data)

        # Test prediction for 10K in 40 minutes
        # Note: Untrained model may return any value, so we just test it doesn't crash
        try:
            result = predict_marathon_time_model1(model, scaler, 10000, 40.0, 60.0)
            # If prediction succeeds, it should be a float
            assert isinstance(result, float)
        except RuntimeError as e:
            # If model returns negative prediction, that's expected for untrained model
            assert "Model returned invalid prediction" in str(e)

    def test_model2_realistic_prediction(self):
        """Test Model 2 with realistic running data."""
        model = Neuromodel2()
        scaler = StandardScaler()

        # Fit with realistic training data
        training_data = np.array(
            [
                [5000, 1200, 10000, 2500, 50],
                [3000, 720, 8000, 2000, 60],
                [5000, 1100, 21097, 5400, 70],
            ]
        )
        scaler.fit(training_data)

        # Test prediction for 5K and 10K times
        # Note: Untrained model may return any value, so we just test it doesn't crash
        try:
            result = predict_marathon_time_model2(
                model, scaler, 5000, 20.0, 10000, 40.0, 60.0
            )
            # If prediction succeeds, it should be a float
            assert isinstance(result, float)
        except RuntimeError as e:
            # If model returns negative prediction, that's expected for untrained model
            assert "Model returned invalid prediction" in str(e)
