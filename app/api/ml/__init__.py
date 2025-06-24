"""
Machine Learning Package for VDOT Prediction

This package provides modular components for training machine learning models
to predict VDOT (running fitness metric) based on training features.

Main Components:
- DataPreprocessor: Feature preparation and cleaning
- ModelTrainer: Random forest model training and evaluation
- FeatureAnalyzer: Feature importance analysis
- ShapVisualizer: SHAP plot generation
- MLPipeline: Main orchestration class
"""

from .preprocessor import DataPreprocessor
from .trainer import ModelTrainer
from .analyzer import FeatureAnalyzer
from .visualizer import ShapVisualizer
from .pipeline import MLPipeline

__all__ = [
    "DataPreprocessor",
    "ModelTrainer",
    "FeatureAnalyzer",
    "ShapVisualizer",
    "MLPipeline",
]
