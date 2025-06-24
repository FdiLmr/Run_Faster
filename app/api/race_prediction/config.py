"""
Configuration settings for race prediction system.
"""

from typing import Dict

# Common race distances in meters
RACE_DISTANCES: Dict[str, float] = {
    "400m": 400,
    "800m": 800,
    "1km": 1000,
    "1 Mile": 1609.34,
    "3km": 3000,
    "2 Mile": 3218.69,
    "5km": 5000,
    "10km": 10000,
    "15km": 15000,
    "10 Mile": 16093.4,
    "Half Marathon": 21097.5,
    "25km": 25000,
    "30km": 30000,
    "Marathon": 42195,
    "50km": 50000,
    "50 Mile": 80467.2,
    "100km": 100000,
}

# Riegel formula configuration
DEFAULT_RIEGEL_EXPONENT = 1.06
MIN_VALID_EXPONENT = 0.95
MAX_VALID_EXPONENT = 1.20

# Prediction range adjustments
OPTIMISTIC_ADJUSTMENT = -0.05
CONSERVATIVE_ADJUSTMENT = 0.05
MIN_OPTIMISTIC_EXPONENT = 1.06
MAX_CONSERVATIVE_EXPONENT = 1.22

# Database configuration
METADATA_PBS_TABLE = "metadata_pbs"

# Distance categories for PB lookup
DISTANCE_CATEGORIES = {"5K": 5000, "10K": 10000}
