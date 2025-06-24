"""
Calculation modules for running analytics.

This package contains:
- VDOT calculations using Daniels' formula
- Personal best detection and analysis
- Statistical outlier detection for training activities
"""

from .vdot import calculate_vdot
from .personal_bests import get_pbs
from .outliers import get_run_outliers

__all__ = ["calculate_vdot", "get_pbs", "get_run_outliers"]
