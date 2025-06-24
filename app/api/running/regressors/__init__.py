"""
Regression models for running analytics.

This package contains:
- Pace to heart rate regression models
- Other predictive models for running performance
"""

from .pace_hr import build_pace_to_hr_regressor

__all__ = ["build_pace_to_hr_regressor"]
