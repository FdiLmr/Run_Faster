"""
Configuration settings for machine learning models.
"""

# Model configuration
DEFAULT_N_ESTIMATORS = 50
DEFAULT_TEST_SIZE = 0.2
DEFAULT_RANDOM_STATE = 42

# Feature configuration
REQUIRED_FEATURES = ["r_proportion_alpine_ski", "r_proportion_crossfit"]

# Target variable names
TARGET_VARIABLES = {"absolute": "absolute_vdot", "change": "vdot_change"}

# Database configuration
FEATURES_TABLE = "features_blocks"
MODEL_OUTPUTS_TABLE = "model_outputs"

# Visualization configuration
SHAP_PLOTS_DIR = "static/shap_plots"
PLOT_TYPES = ["summary", "bar"]

# Column indices (assuming standard format)
FEATURE_START_COL = 2  # Skip athlete_id, block_id
TARGET_OFFSET = -2  # Last 2 columns are targets
