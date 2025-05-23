"""Inference functions for marathon time prediction."""

import numpy as np
import torch
from typing import Union, Tuple
from sklearn.preprocessing import StandardScaler

from .models import Neuromodel1, Neuromodel2


def validate_race_inputs(distance: float, time_minutes: float) -> None:
    """Validate race distance and time inputs.
    
    Args:
        distance: Race distance in meters
        time_minutes: Race time in minutes
        
    Raises:
        ValueError: If inputs are invalid
    """
    if distance <= 0:
        raise ValueError(f"Distance must be positive, got {distance}")
    if time_minutes <= 0:
        raise ValueError(f"Time must be positive, got {time_minutes}")
    if distance > 50000:  # 50km seems like a reasonable upper bound
        raise ValueError(f"Distance seems too large: {distance} meters")
    if time_minutes > 600:  # 10 hours seems like a reasonable upper bound
        raise ValueError(f"Time seems too large: {time_minutes} minutes")


def validate_mileage(mileage: float) -> None:
    """Validate weekly training mileage.
    
    Args:
        mileage: Weekly training mileage in miles
        
    Raises:
        ValueError: If mileage is invalid
    """
    if mileage < 0:
        raise ValueError(f"Mileage must be non-negative, got {mileage}")
    if mileage > 200:  # 200 miles/week seems like a reasonable upper bound
        raise ValueError(f"Mileage seems too large: {mileage} miles/week")


def predict_marathon_time_model1(
    model: Neuromodel1, 
    scaler: StandardScaler, 
    distance: float, 
    time_minutes: float, 
    mileage: float
) -> float:
    """Predict marathon time using single race data.
    
    Args:
        model: Trained Neuromodel1 instance
        scaler: Fitted StandardScaler for input normalization
        distance: Race distance in meters
        time_minutes: Race time in minutes
        mileage: Weekly training mileage in miles
        
    Returns:
        Predicted marathon time in minutes
        
    Raises:
        ValueError: If inputs are invalid
        RuntimeError: If model prediction fails
    """
    # Validate inputs
    validate_race_inputs(distance, time_minutes)
    validate_mileage(mileage)
    
    try:
        # Convert time to seconds for model input
        time_seconds = time_minutes * 60
        
        # Prepare input array
        x = np.array([[distance, time_seconds, mileage]], dtype=np.float32)
        
        # Scale inputs
        x_scaled = scaler.transform(x)
        
        # Convert to tensor
        x_tensor = torch.tensor(x_scaled, dtype=torch.float32)
        
        # Make prediction
        model.eval()
        with torch.no_grad():
            prediction = model(x_tensor).item()
            
        if prediction <= 0:
            raise RuntimeError(f"Model returned invalid prediction: {prediction}")
            
        return prediction
        
    except Exception as e:
        if isinstance(e, (ValueError, RuntimeError)):
            raise
        raise RuntimeError(f"Prediction failed: {str(e)}")


def predict_marathon_time_model2(
    model: Neuromodel2, 
    scaler: StandardScaler, 
    distance1: float, 
    time1_minutes: float, 
    distance2: float, 
    time2_minutes: float, 
    mileage: float
) -> float:
    """Predict marathon time using two race data points.
    
    Args:
        model: Trained Neuromodel2 instance
        scaler: Fitted StandardScaler for input normalization
        distance1: First race distance in meters
        time1_minutes: First race time in minutes
        distance2: Second race distance in meters
        time2_minutes: Second race time in minutes
        mileage: Weekly training mileage in miles
        
    Returns:
        Predicted marathon time in minutes
        
    Raises:
        ValueError: If inputs are invalid
        RuntimeError: If model prediction fails
    """
    # Validate inputs
    validate_race_inputs(distance1, time1_minutes)
    validate_race_inputs(distance2, time2_minutes)
    validate_mileage(mileage)
    
    try:
        # Convert times to seconds for model input
        time1_seconds = time1_minutes * 60
        time2_seconds = time2_minutes * 60
        
        # Prepare input array
        x = np.array([[distance1, time1_seconds, distance2, time2_seconds, mileage]], 
                     dtype=np.float32)
        
        # Scale inputs
        x_scaled = scaler.transform(x)
        
        # Convert to tensor
        x_tensor = torch.tensor(x_scaled, dtype=torch.float32)
        
        # Make prediction
        model.eval()
        with torch.no_grad():
            prediction = model(x_tensor).item()
            
        if prediction <= 0:
            raise RuntimeError(f"Model returned invalid prediction: {prediction}")
            
        return prediction
        
    except Exception as e:
        if isinstance(e, (ValueError, RuntimeError)):
            raise
        raise RuntimeError(f"Prediction failed: {str(e)}")