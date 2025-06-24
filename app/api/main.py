#!/usr/bin/env python3
"""
Refactored Flask application for Strava running analytics.

This is the main entry point for the application. The app has been refactored
into a modular structure with separate blueprints for different functionality.
"""

import os
import sys

# Add the current directory to Python path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.app import create_app

# Create the Flask application
app = create_app(os.getenv("FLASK_ENV", "default"))

if __name__ == "__main__":
    app.run(debug=True)
