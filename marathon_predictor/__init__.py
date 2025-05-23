"""Marathon Time Predictor Package

This package provides neural network models for predicting marathon times
based on previous race performances and training data.
"""

from .models import Neuromodel1, Neuromodel2
from .predictor import MarathonPredictor
from .inference import predict_marathon_time_model1, predict_marathon_time_model2

__version__ = "1.0.0"
__all__ = [
    "Neuromodel1",
    "Neuromodel2",
    "MarathonPredictor",
    "predict_marathon_time_model1",
    "predict_marathon_time_model2",
]
