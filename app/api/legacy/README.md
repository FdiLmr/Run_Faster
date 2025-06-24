# Legacy Files

This folder contains legacy files from the codebase refactoring process. These files have been moved here to clean up the main codebase while preserving them for reference.

## Files in this folder:

### Main Application Files
- **`legacy_main.py`** (52KB) - Original monolithic Flask application before refactoring into modular structure
- **`legacy_update_data.py`** (30KB) - Original data update functionality

### Function Libraries
- **`running_functions_legacy.py`** (18KB) - Original running calculations and analysis functions (refactored into `running/` module)
- **`activity_functions_legacy.py`** (6KB) - Original activity processing functions (refactored into new modular structure)
- **`activity_functions.py`** (902B) - Unused activity functions (no imports found)
- **`search_functions_legacy.py`** (4KB) - Original search functionality (replaced by `search_functions.py`)

### Data Management
- **`sql_methods_legacy.py`** (9KB) - Original database methods (refactored into `database/` module with modular structure)
- **`fetch_athlete_data_legacy.py`** (5KB) - Original athlete data fetching (replaced by `fetch_athlete_data.py`)
- **`athlete_data_transformer_legacy.py`** (534B) - Original data transformation (replaced by `athlete_data_transformer.py`)
- **`update_data_legacy.py`** (732B) - Legacy data update stub

### Transitional/Refactored Files
- **`race_prediction_refactored.py`** (6.6KB) - Wrapper around new modular `race_prediction/` package (superseded by direct module usage)
- **`train_model_refactored.py`** (3.1KB) - Wrapper around new modular `ml/` package (superseded by direct module usage)
- **`visualisations.py`** (595B) - Compatibility shim for `visualizations/` module (superseded by direct imports)

## Status

⚠️ **These files are no longer actively used** in the current application. They have been replaced by:

- **Modular structure**: Organized into `core/`, `routes/`, `database/`, `analytics/`, `running/`, etc.
- **Better separation of concerns**: Each module has specific responsibilities
- **Improved maintainability**: Smaller, focused files are easier to understand and modify
- **Enhanced functionality**: New features and better error handling

## Safety

These files are kept for:
- **Reference**: Understanding the original implementation
- **Rollback capability**: In case any functionality was missed during refactoring
- **Documentation**: Historical context of the codebase evolution

## Removal

These files can be safely deleted if:
1. The refactored application has been thoroughly tested
2. All functionality has been verified to work in the new structure
3. No references to these files exist in the active codebase

## Related Documentation

See the various `*_REFACTORING_README.md` files in the parent directory for detailed information about how each component was refactored. 