"""Tests for marathon predictor neural network models."""

import pytest
import torch
from marathon_predictor.models import Neuromodel1, Neuromodel2


class TestNeuromodel1:
    """Tests for Neuromodel1 (single race prediction)."""

    def test_model_initialization(self):
        """Test that model initializes correctly."""
        model = Neuromodel1()
        assert isinstance(model, torch.nn.Module)
        assert hasattr(model, "network")

    def test_model_initialization_with_custom_params(self):
        """Test model initialization with custom parameters."""
        model = Neuromodel1(input_size=3, hidden_sizes=(10, 15))
        assert isinstance(model, torch.nn.Module)

        # Test that the network has the right structure
        layers = list(model.network.children())
        assert len(layers) == 5  # Linear, ReLU, Linear, ReLU, Linear
        assert isinstance(layers[0], torch.nn.Linear)
        assert layers[0].in_features == 3
        assert layers[0].out_features == 10

    def test_invalid_input_size(self):
        """Test that invalid input size raises error."""
        with pytest.raises(ValueError, match="expects exactly 3 input features"):
            Neuromodel1(input_size=5)

    def test_forward_pass(self):
        """Test forward pass with valid input."""
        model = Neuromodel1()
        x = torch.randn(1, 3)  # batch_size=1, features=3

        output = model(x)
        assert output.shape == (1, 1)
        assert isinstance(output, torch.Tensor)

    def test_forward_pass_batch(self):
        """Test forward pass with batch input."""
        model = Neuromodel1()
        x = torch.randn(5, 3)  # batch_size=5, features=3

        output = model(x)
        assert output.shape == (5, 1)

    def test_forward_pass_invalid_input_shape(self):
        """Test that invalid input shape raises error."""
        model = Neuromodel1()
        x = torch.randn(1, 5)  # Wrong number of features

        with pytest.raises(ValueError, match="Expected input with 3 features"):
            model(x)

    def test_model_parameters(self):
        """Test that model has trainable parameters."""
        model = Neuromodel1()
        params = list(model.parameters())
        assert len(params) > 0

        # Check that parameters require gradients
        for param in params:
            assert param.requires_grad


class TestNeuromodel2:
    """Tests for Neuromodel2 (dual race prediction)."""

    def test_model_initialization(self):
        """Test that model initializes correctly."""
        model = Neuromodel2()
        assert isinstance(model, torch.nn.Module)
        assert hasattr(model, "network")

    def test_model_initialization_with_custom_params(self):
        """Test model initialization with custom parameters."""
        model = Neuromodel2(input_size=5, hidden_sizes=(8, 16))
        assert isinstance(model, torch.nn.Module)

        # Test that the network has the right structure
        layers = list(model.network.children())
        assert len(layers) == 5  # Linear, ReLU, Linear, ReLU, Linear
        assert isinstance(layers[0], torch.nn.Linear)
        assert layers[0].in_features == 5
        assert layers[0].out_features == 8

    def test_invalid_input_size(self):
        """Test that invalid input size raises error."""
        with pytest.raises(ValueError, match="expects exactly 5 input features"):
            Neuromodel2(input_size=3)

    def test_forward_pass(self):
        """Test forward pass with valid input."""
        model = Neuromodel2()
        x = torch.randn(1, 5)  # batch_size=1, features=5

        output = model(x)
        assert output.shape == (1, 1)
        assert isinstance(output, torch.Tensor)

    def test_forward_pass_batch(self):
        """Test forward pass with batch input."""
        model = Neuromodel2()
        x = torch.randn(3, 5)  # batch_size=3, features=5

        output = model(x)
        assert output.shape == (3, 1)

    def test_forward_pass_invalid_input_shape(self):
        """Test that invalid input shape raises error."""
        model = Neuromodel2()
        x = torch.randn(1, 3)  # Wrong number of features

        with pytest.raises(ValueError, match="Expected input with 5 features"):
            model(x)

    def test_model_parameters(self):
        """Test that model has trainable parameters."""
        model = Neuromodel2()
        params = list(model.parameters())
        assert len(params) > 0

        # Check that parameters require gradients
        for param in params:
            assert param.requires_grad


class TestModelComparison:
    """Tests comparing both models."""

    def test_different_architectures(self):
        """Test that models have different architectures."""
        model1 = Neuromodel1()
        model2 = Neuromodel2()

        # Get first layer input sizes
        first_layer1 = list(model1.network.children())[0]
        first_layer2 = list(model2.network.children())[0]

        assert first_layer1.in_features == 3
        assert first_layer2.in_features == 5

    def test_models_produce_different_outputs(self):
        """Test that models produce different outputs for same-sized inputs."""
        model1 = Neuromodel1()
        model2 = Neuromodel2()

        # Create inputs with same values but different shapes
        x1 = torch.tensor([[1000.0, 1800.0, 50.0]])  # distance, time, mileage
        x2 = torch.tensor(
            [[1000.0, 1800.0, 2000.0, 2400.0, 50.0]]
        )  # two races + mileage

        output1 = model1(x1)
        output2 = model2(x2)

        # Outputs should be different (very unlikely to be exactly equal)
        assert not torch.allclose(output1, output2[:, :1])  # Compare first output only
