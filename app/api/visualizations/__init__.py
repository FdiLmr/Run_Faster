"""
Visualization package for athlete performance analysis.

This package provides visualization tools for comparing athlete performance
against benchmarks and analyzing improvement potential.
"""

from .generators import athletevsbest, athletevsbestimprovement
from .utils import double_to_hours_minutes

__all__ = ["athletevsbest", "athletevsbestimprovement", "double_to_hours_minutes"]
