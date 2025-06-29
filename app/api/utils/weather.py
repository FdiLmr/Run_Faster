"""
Weather data utilities for activity analysis.

This module provides functionality for fetching historical weather data
for activities based on their location and time.
"""

import requests
from datetime import datetime
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

# Suppress urllib3 debug logging to reduce noise
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Simple in-memory cache for weather data
_weather_cache = {}


def get_weather_at_activity(start_date: str, start_latlng: List[float]) -> Dict[str, Optional[float]]:
    """
    Fetches temperature and humidity for a given datetime and coordinates using Open-Meteo.
    Uses caching to avoid repeated API calls for the same location/time.

    Args:
        start_date (str): Activity start date/time, e.g., '2025-06-28 07:21:48'
        start_latlng (list): [latitude, longitude], e.g., [48.85, 2.49]

    Returns:
        dict: {'temperature': float or None, 'humidity': float or None}
    """
    if not start_date or not start_latlng or len(start_latlng) != 2:
        logger.warning(f"Invalid input data: start_date={start_date}, start_latlng={start_latlng}")
        return {"temperature": None, "humidity": None}

    try:
        # Parse date and hour - handle both ISO format and standard format
        if "T" in start_date:
            # ISO format: '2025-05-25T07:30:35Z'
            dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        else:
            # Standard format: '2025-05-25 07:30:35'
            dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        
        date_str = dt.strftime("%Y-%m-%d")
        hour = dt.hour
        lat, lon = start_latlng

        # Create cache key based on date, hour, and rounded coordinates (to 2 decimal places)
        cache_key = f"{date_str}_{hour}_{round(lat, 2)}_{round(lon, 2)}"
        
        # Check cache first
        if cache_key in _weather_cache:
            return _weather_cache[cache_key]

        # Validate coordinates
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            logger.warning(f"Invalid coordinates: lat={lat}, lon={lon}")
            result = {"temperature": None, "humidity": None}
            _weather_cache[cache_key] = result
            return result

        # Build Open-Meteo API URL
        url = (
            f"https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={lat}&longitude={lon}"
            f"&start_date={date_str}&end_date={date_str}"
            f"&hourly=temperature_2m,relative_humidity_2m"
            f"&timezone=auto"
        )

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Find the index for the correct hour
        times = data["hourly"]["time"]
        idx = next(
            (i for i, t in enumerate(times) if datetime.fromisoformat(t).hour == hour),
            None
        )

        if idx is not None:
            temperature = data["hourly"]["temperature_2m"][idx]
            humidity = data["hourly"]["relative_humidity_2m"][idx]
            result = {"temperature": temperature, "humidity": humidity}
        else:
            logger.warning(f"No weather data found for hour {hour} on {date_str}")
            result = {"temperature": None, "humidity": None}
        
        # Cache the result
        _weather_cache[cache_key] = result
        return result

    except ValueError as e:
        logger.error(f"Error parsing date '{start_date}': {e}")
        result = {"temperature": None, "humidity": None}
        return result
    except requests.RequestException as e:
        logger.error(f"Error fetching weather data: {e}")
        result = {"temperature": None, "humidity": None}
        return result
    except Exception as e:
        logger.error(f"Unexpected error fetching weather: {e}")
        result = {"temperature": None, "humidity": None}
        return result


def get_weather_for_activity_id(activity_id: str, start_date: str, start_latlng: List[float]) -> Dict[str, Optional[float]]:
    """
    Get weather data for a specific activity ID with caching.
    
    Args:
        activity_id (str): Unique activity identifier
        start_date (str): Activity start date/time
        start_latlng (list): [latitude, longitude]
    
    Returns:
        dict: {'temperature': float or None, 'humidity': float or None}
    """
    # Check if we already have weather data for this specific activity
    activity_cache_key = f"activity_{activity_id}"
    
    if activity_cache_key in _weather_cache:
        return _weather_cache[activity_cache_key]
    
    # Get weather data and cache it for this specific activity
    weather_data = get_weather_at_activity(start_date, start_latlng)
    _weather_cache[activity_cache_key] = weather_data
    
    return weather_data


def clear_weather_cache():
    """Clear the weather data cache."""
    global _weather_cache
    _weather_cache = {}
    logger.info("Weather cache cleared")


def get_cache_stats():
    """Get statistics about the weather cache."""
    return {
        "cache_size": len(_weather_cache),
        "cached_keys": list(_weather_cache.keys())
    }


def batch_get_weather_for_activities(activities: List[Dict]) -> Dict[str, Dict[str, Optional[float]]]:
    """
    Fetch weather data for a batch of activities.

    Args:
        activities: List of activity dictionaries with 'id', 'start_date', and 'start_latlng'

    Returns:
        Dictionary mapping activity_id to weather data
    """
    weather_data = {}
    total_activities = len(activities)
    
    for i, activity in enumerate(activities):
        activity_id = str(activity.get("id"))
        start_date = activity.get("start_date")
        start_latlng = activity.get("start_latlng")
        
        if start_date and start_latlng:
            # Convert ISO format to our expected format if needed
            if "T" in start_date:
                try:
                    dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                    start_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    logger.warning(f"Could not parse date format for activity {activity_id}: {e}")
                    continue
            
            weather = get_weather_at_activity(start_date, start_latlng)
            weather_data[activity_id] = weather
            
            # Log progress every 50 activities
            if (i + 1) % 50 == 0:
                logger.info(f"Fetched weather data for {i + 1}/{total_activities} activities")
        else:
            logger.debug(f"Skipping weather fetch for activity {activity_id} - missing data")
            weather_data[activity_id] = {"temperature": None, "humidity": None}
    
    if total_activities > 0:
        logger.info(f"Completed weather data fetch for {total_activities} activities")
    
    return weather_data 