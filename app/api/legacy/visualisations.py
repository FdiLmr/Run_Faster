"""
Visualization module - Refactored to use modular structure.

This module provides backward compatibility by importing from the new
modular visualization package structure.

For new code, prefer importing directly from the visualizations package:
    from visualizations import athletevsbest, athletevsbestimprovement
"""

# Import from the new modular structure
from visualizations import (
    athletevsbest,
    athletevsbestimprovement,
    double_to_hours_minutes,
)

# Re-export for backward compatibility
__all__ = ["athletevsbest", "athletevsbestimprovement", "double_to_hours_minutes"]
