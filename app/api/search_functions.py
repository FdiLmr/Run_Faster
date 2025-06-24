"""
Search functions - Backward compatibility module.

This module provides backward compatibility by importing all functions
from the new modular running package structure.

The original functionality has been refactored into:
- running.processing.search_functions: Activity search and filtering

For new code, consider importing directly from the specific modules.
"""

# Import all functions from the new modular structure
from running import get_activity, is_valid_activity, get_block, get_weeks

# Re-export for backward compatibility
__all__ = ["get_activity", "is_valid_activity", "get_block", "get_weeks"]
