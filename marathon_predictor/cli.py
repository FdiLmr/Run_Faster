"""Command-line interface for marathon time prediction."""

import sys
import os
from typing import Tuple

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from marathon_predictor import MarathonPredictor
from utils.time_utils import format_runtime, hms_to_minutes


def get_time_input(label: str) -> float:
    """Get time input from user in hours, minutes, seconds format.
    
    Args:
        label: Description of the time being requested
        
    Returns:
        Time in minutes
        
    Raises:
        ValueError: If input is invalid
    """
    print(f"Enter {label} race time:")
    try:
        h = int(input("  Hours: "))
        m = int(input("  Minutes: "))
        s = int(input("  Seconds: "))
        
        if h < 0 or m < 0 or s < 0:
            raise ValueError("Time components must be non-negative")
        if m >= 60 or s >= 60:
            raise ValueError("Minutes and seconds must be less than 60")
            
        return hms_to_minutes(h, m, s)
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError("Please enter valid integers")
        raise


def get_distance_input(label: str) -> float:
    """Get distance input from user.
    
    Args:
        label: Description of the distance being requested
        
    Returns:
        Distance in meters
        
    Raises:
        ValueError: If input is invalid
    """
    try:
        distance = float(input(f"{label} (in meters): "))
        if distance <= 0:
            raise ValueError("Distance must be positive")
        return distance
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError("Please enter a valid number")
        raise


def get_mileage_input() -> float:
    """Get weekly mileage input from user.
    
    Returns:
        Weekly mileage in miles
        
    Raises:
        ValueError: If input is invalid
    """
    try:
        mileage = float(input("Weekly training mileage (in miles): "))
        if mileage < 0:
            raise ValueError("Mileage must be non-negative")
        return mileage
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError("Please enter a valid number")
        raise


def run_cli() -> None:
    """Run the command-line interface for marathon prediction."""
    print("--- Marathon Time Predictor ---")
    print()
    
    try:
        # Get user inputs
        print("Please provide information about two recent races:")
        print()
        
        dist_r1 = get_distance_input("Distance of Race 1")
        time_r1 = get_time_input("Race 1")
        print()
        
        dist_r2 = get_distance_input("Distance of Race 2")
        time_r2 = get_time_input("Race 2")
        print()
        
        mileage = get_mileage_input()
        print()
        
        # Initialize predictor and load models
        print("Loading models...")
        predictor = MarathonPredictor()
        
        try:
            predictor.load_all_models()
        except Exception as e:
            print(f"Error loading models: {e}")
            print("Please ensure model files are present in the marathon_predictor directory.")
            return
        
        # Make predictions
        print("Making predictions...")
        try:
            predictions = predictor.predict_both(
                dist_r1, time_r1, dist_r2, time_r2, mileage
            )
            
            print("\nPredicted Marathon Time:")
            if "model1" in predictions:
                print(f"  Single Race Model: {format_runtime(predictions['model1'] * 60)}")
            if "model2" in predictions:
                print(f"  Dual Race Model:   {format_runtime(predictions['model2'] * 60)}")
                
        except Exception as e:
            print(f"Error making predictions: {e}")
            return
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return
    except Exception as e:
        print(f"Error: {e}")
        return
    
    print("\nThank you for using the Marathon Time Predictor!")


if __name__ == "__main__":
    run_cli()