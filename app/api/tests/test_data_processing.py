"""
Tests for data processing and transformation functionality.

This module tests the core data processing pipeline:
- Loading and transforming athlete data
- Activity feature extraction
- Heart rate zone calculations
- Personal best calculations
- Training block analysis
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open

# Import these within the application context to avoid import errors


class TestAthleteDataLoading:
    """Test athlete data loading from JSON files."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_load_athlete_data_basic(self, mock_exists, mock_file, app_context):
        """Test basic athlete data loading."""
        from athlete_data_transformer import load_athlete_data

        mock_exists.return_value = True
        mock_file.return_value.read.return_value = (
            '{"id": 12345, "username": "test_athlete"}'
        )

        data = load_athlete_data("12345")

        assert data is not None
        assert data["id"] == 12345
        assert data["username"] == "test_athlete"

    @patch("os.path.exists")
    def test_load_athlete_data_missing_file(self, mock_exists, app_context):
        """Test handling of missing athlete data file."""
        from athlete_data_transformer import load_athlete_data

        mock_exists.return_value = False

        data = load_athlete_data("nonexistent")
        assert data is None or data == {}

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_load_athlete_data_invalid_json(self, mock_exists, mock_file, app_context):
        """Test handling of invalid JSON in athlete data."""
        from athlete_data_transformer import load_athlete_data

        mock_exists.return_value = True
        mock_file.return_value.read.return_value = "invalid json"

        with pytest.raises(Exception):
            load_athlete_data("12345")

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_load_activity_data(self, mock_exists, mock_file, app_context):
        """Test loading individual activity data."""
        from athlete_data_transformer import load_activity_data

        mock_exists.return_value = True
        activity_data = {
            "id": 123456,
            "name": "Morning Run",
            "distance": 5000.0,
            "type": "Run",
        }
        mock_file.return_value.read.return_value = str(activity_data).replace("'", '"')

        data = load_activity_data("12345", 123456)

        assert data is not None
        assert data["id"] == 123456
        assert data["name"] == "Morning Run"


class TestHeartRateZoneCalculations:
    """Test heart rate zone calculations."""

    def test_calculate_hr_zones_basic(self, app_context):
        """Test basic heart rate zone calculation."""
        from athlete_data_transformer import calculate_hr_zones

        max_hr = 190
        resting_hr = 60

        zones = calculate_hr_zones(max_hr, resting_hr)

        assert len(zones) == 5  # Assuming 5 zones
        assert zones[0] < zones[1] < zones[2] < zones[3] < zones[4]
        assert zones[0] > resting_hr
        assert zones[4] <= max_hr

    def test_hr_zone_classification(self, app_context):
        """Test classifying heart rate values into zones."""
        from athlete_data_transformer import classify_hr_zone

        zones = [120, 140, 160, 170, 180]  # Zone boundaries

        assert classify_hr_zone(110, zones) == 1  # Below zone 1
        assert classify_hr_zone(130, zones) == 2  # Zone 2
        assert classify_hr_zone(165, zones) == 4  # Zone 4
        assert classify_hr_zone(185, zones) == 5  # Above zone 5

    def test_hr_zone_time_calculation(self, app_context):
        """Test calculating time spent in each HR zone."""
        from athlete_data_transformer import calculate_zone_times

        hr_data = [120, 135, 145, 165, 175, 155, 140]
        zones = [130, 145, 160, 170, 180]

        zone_times = calculate_zone_times(hr_data, zones)

        assert len(zone_times) == 5
        assert sum(zone_times) == len(hr_data)
        assert all(time >= 0 for time in zone_times)

    def test_hr_zones_with_missing_data(self, app_context):
        """Test HR zone calculation with missing max/resting HR."""
        from athlete_data_transformer import calculate_hr_zones_with_defaults

        # Should use age-based estimation when max HR is missing
        zones_estimated = calculate_hr_zones_with_defaults(age=30)
        assert len(zones_estimated) == 5
        assert all(zone > 0 for zone in zones_estimated)

        # Should handle missing resting HR
        zones_no_resting = calculate_hr_zones_with_defaults(max_hr=190)
        assert len(zones_no_resting) == 5


class TestActivityFeatureExtraction:
    """Test extraction of features from activity data."""

    def test_extract_basic_features(self, app_context, sample_activity_data):
        """Test extraction of basic activity features."""
        from athlete_data_transformer import extract_activity_features

        features = extract_activity_features(sample_activity_data)

        # Check required features are present
        required_features = ["distance", "moving_time", "average_speed", "type"]
        for feature in required_features:
            assert feature in features

        # Check calculated features
        if features["moving_time"] > 0:
            expected_speed = features["distance"] / features["moving_time"]
            assert abs(features["average_speed"] - expected_speed) < 0.1

    def test_extract_run_specific_features(self, app_context):
        """Test extraction of running-specific features."""
        from athlete_data_transformer import extract_run_features

        run_data = {
            "type": "Run",
            "distance": 5000.0,
            "moving_time": 1800,
            "average_heartrate": 150,
            "average_cadence": 180,
            "total_elevation_gain": 100,
        }

        features = extract_run_features(run_data)

        assert "pace" in features
        assert "elevation_per_km" in features
        assert features["pace"] > 0
        assert features["elevation_per_km"] >= 0

    def test_extract_elevation_features(self, app_context):
        """Test extraction of elevation-related features."""
        from athlete_data_transformer import extract_elevation_features

        activity_data = {
            "total_elevation_gain": 200,
            "elev_high": 150,
            "elev_low": 50,
            "distance": 10000,
        }

        features = extract_elevation_features(activity_data)

        assert "elevation_per_km" in features
        assert "elevation_range" in features
        assert features["elevation_per_km"] == 20.0  # 200m / 10km
        assert features["elevation_range"] == 100  # 150 - 50

    def test_extract_pace_features(self, app_context):
        """Test extraction of pace-related features."""
        from athlete_data_transformer import extract_pace_features

        activity_data = {
            "distance": 5000.0,  # 5km
            "moving_time": 1500,  # 25 minutes
            "elapsed_time": 1800,  # 30 minutes total
        }

        features = extract_pace_features(activity_data)

        assert "pace_per_km" in features
        assert "moving_pace" in features
        assert features["pace_per_km"] == 300  # 5 minutes per km in seconds
        assert features["moving_pace"] == 300

    def test_handle_missing_features(self, app_context):
        """Test handling of missing feature data."""
        from athlete_data_transformer import extract_activity_features

        incomplete_data = {
            "id": 123456,
            "name": "Test Activity",
            "type": "Run",
            # Missing distance, time, etc.
        }

        features = extract_activity_features(incomplete_data)

        # Should handle missing data gracefully
        assert features is not None
        assert "type" in features


class TestWeeklyAggregations:
    """Test weekly data aggregations."""

    def test_get_week_start_date(self, app_context):
        """Test getting week start date (Monday)."""
        from athlete_data_transformer import get_week_start_date

        # Test with a Wednesday
        test_date = datetime(2024, 1, 17)  # Wednesday
        week_start = get_week_start_date(test_date)

        assert week_start.weekday() == 0  # Monday
        assert week_start.date() == datetime(2024, 1, 15).date()

    def test_group_activities_by_week(self, app_context):
        """Test grouping activities by week."""
        from athlete_data_transformer import group_activities_by_week

        activities = [
            {"start_date": datetime(2024, 1, 15), "distance": 5000},  # Monday
            {"start_date": datetime(2024, 1, 17), "distance": 3000},  # Wednesday
            {"start_date": datetime(2024, 1, 22), "distance": 8000},  # Next Monday
        ]

        weekly_groups = group_activities_by_week(activities)

        assert len(weekly_groups) == 2
        assert len(weekly_groups[0]) == 2  # First week has 2 activities
        assert len(weekly_groups[1]) == 1  # Second week has 1 activity

    def test_calculate_weekly_totals(self, app_context):
        """Test calculating weekly totals."""
        from athlete_data_transformer import calculate_weekly_totals

        week_activities = [
            {"distance": 5000, "moving_time": 1800, "type": "Run"},
            {"distance": 3000, "moving_time": 1200, "type": "Run"},
            {"distance": 0, "moving_time": 3600, "type": "Ride"},  # Non-run
        ]

        totals = calculate_weekly_totals(week_activities)

        assert totals["total_distance"] == 8000  # Only runs
        assert totals["total_time"] == 3000
        assert totals["activity_count"] == 2
        assert totals["non_run_time"] == 3600

    def test_calculate_weekly_averages(self, app_context):
        """Test calculating weekly averages."""
        from athlete_data_transformer import calculate_weekly_averages

        week_activities = [
            {"average_heartrate": 150, "distance": 5000, "type": "Run"},
            {"average_heartrate": 160, "distance": 3000, "type": "Run"},
        ]

        averages = calculate_weekly_averages(week_activities)

        # Should be distance-weighted average
        expected_avg_hr = (150 * 5000 + 160 * 3000) / 8000
        assert abs(averages["avg_heartrate"] - expected_avg_hr) < 0.1

    def test_weekly_aggregation_with_empty_week(self, app_context):
        """Test weekly aggregation with no activities."""
        from athlete_data_transformer import calculate_weekly_totals

        totals = calculate_weekly_totals([])

        assert totals["total_distance"] == 0
        assert totals["total_time"] == 0
        assert totals["activity_count"] == 0


class TestPersonalBestCalculations:
    """Test personal best calculations."""

    def test_find_distance_pbs(self, app_context):
        """Test finding personal bests for standard distances."""
        from athlete_data_transformer import find_distance_pbs

        activities = [
            {
                "distance": 5000,
                "moving_time": 1200,
                "type": "Run",
                "start_date": datetime(2024, 1, 1),
            },
            {
                "distance": 5000,
                "moving_time": 1100,
                "type": "Run",  # Better time
                "start_date": datetime(2024, 1, 15),
            },
            {
                "distance": 10000,
                "moving_time": 2400,
                "type": "Run",
                "start_date": datetime(2024, 1, 10),
            },
        ]

        pbs = find_distance_pbs(activities)

        assert "5K" in pbs
        assert "10K" in pbs
        assert pbs["5K"]["time"] == 1100  # Better 5K time
        assert pbs["10K"]["time"] == 2400

    def test_calculate_vdot_from_pb(self, app_context):
        """Test VDOT calculation from personal best."""
        from athlete_data_transformer import calculate_vdot

        # 5K in 20 minutes (1200 seconds)
        vdot = calculate_vdot(distance=5000, time=1200)

        assert vdot > 0
        assert vdot < 100  # Reasonable VDOT range

    def test_pb_progression_tracking(self, app_context):
        """Test tracking PB progression over time."""
        from athlete_data_transformer import track_pb_progression

        activities = [
            {
                "distance": 5000,
                "moving_time": 1300,
                "type": "Run",
                "start_date": datetime(2024, 1, 1),
            },
            {
                "distance": 5000,
                "moving_time": 1250,
                "type": "Run",
                "start_date": datetime(2024, 2, 1),
            },
            {
                "distance": 5000,
                "moving_time": 1200,
                "type": "Run",
                "start_date": datetime(2024, 3, 1),
            },
        ]

        progression = track_pb_progression(activities, distance=5000)

        assert len(progression) == 3
        assert progression[0]["time"] == 1300
        assert progression[-1]["time"] == 1200  # Best time last

        # Check progression dates are in order
        dates = [p["date"] for p in progression]
        assert dates == sorted(dates)

    def test_pb_validation(self, app_context):
        """Test validation of personal best times."""
        from athlete_data_transformer import validate_pb_time

        # Valid times
        assert validate_pb_time(distance=5000, time=1200) is True
        assert validate_pb_time(distance=10000, time=2400) is True

        # Invalid times (too fast/slow)
        assert validate_pb_time(distance=5000, time=600) is False  # Too fast
        assert validate_pb_time(distance=5000, time=7200) is False  # Too slow


class TestTrainingBlockAnalysis:
    """Test training block analysis."""

    def test_identify_training_blocks(self, app_context):
        """Test identification of training blocks."""
        from athlete_data_transformer import identify_training_blocks

        # Create activities spanning several weeks
        activities = []
        base_date = datetime(2024, 1, 1)

        for week in range(8):
            for day in [0, 2, 4]:  # Mon, Wed, Fri
                date = base_date + timedelta(weeks=week, days=day)
                distance = 5000 if week < 4 else 8000  # Increase distance after 4 weeks
                activities.append(
                    {"start_date": date, "distance": distance, "type": "Run"}
                )

        blocks = identify_training_blocks(activities)

        assert len(blocks) >= 1
        assert all("start_date" in block for block in blocks)
        assert all("end_date" in block for block in blocks)
        assert all("avg_weekly_distance" in block for block in blocks)

    def test_calculate_training_load(self, app_context):
        """Test training load calculation."""
        from athlete_data_transformer import calculate_training_load

        activities = [
            {"distance": 5000, "moving_time": 1800, "intensity": "easy"},
            {"distance": 3000, "moving_time": 900, "intensity": "hard"},
            {"distance": 8000, "moving_time": 2400, "intensity": "moderate"},
        ]

        training_load = calculate_training_load(activities)

        assert training_load > 0
        assert isinstance(training_load, (int, float))

    def test_detect_training_patterns(self, app_context):
        """Test detection of training patterns."""
        from athlete_data_transformer import detect_training_patterns

        # Create pattern: 3 days on, 1 day off
        activities = []
        base_date = datetime(2024, 1, 1)

        for week in range(4):
            for day in [0, 1, 2, 4, 5, 6]:  # Skip Wednesday
                date = base_date + timedelta(weeks=week, days=day)
                activities.append({"start_date": date, "distance": 5000, "type": "Run"})

        patterns = detect_training_patterns(activities)

        assert patterns is not None
        assert "weekly_frequency" in patterns
        assert patterns["weekly_frequency"] == 6


class TestDataValidation:
    """Test data validation and cleaning."""

    def test_validate_activity_data(self, app_context):
        """Test validation of activity data."""
        from athlete_data_transformer import validate_activity_data

        valid_activity = {
            "id": 123456,
            "name": "Morning Run",
            "distance": 5000.0,
            "moving_time": 1800,
            "type": "Run",
        }

        invalid_activity = {
            "id": 123456,
            "distance": -100,  # Invalid negative distance
            "moving_time": 0,  # Invalid zero time
        }

        assert validate_activity_data(valid_activity) is True
        assert validate_activity_data(invalid_activity) is False

    def test_clean_outlier_data(self, app_context):
        """Test removal of outlier data points."""
        from athlete_data_transformer import remove_outliers

        # Data with obvious outliers
        data = [
            100,
            105,
            98,
            102,
            99,
            1000,
            101,
            97,
            103,
            10,
        ]  # 1000 and 10 are outliers

        cleaned_data = remove_outliers(data)

        assert 1000 not in cleaned_data
        assert 10 not in cleaned_data
        assert len(cleaned_data) < len(data)

    def test_handle_missing_timestamps(self, app_context):
        """Test handling of missing timestamps."""
        from athlete_data_transformer import fix_missing_timestamps

        activities = [
            {"id": 1, "start_date": datetime(2024, 1, 1)},
            {"id": 2, "start_date": None},  # Missing timestamp
            {"id": 3, "start_date": datetime(2024, 1, 3)},
        ]

        fixed_activities = fix_missing_timestamps(activities)

        # Should interpolate or handle missing timestamp
        assert all(activity["start_date"] is not None for activity in fixed_activities)

    def test_normalize_activity_types(self, app_context):
        """Test normalization of activity types."""
        from athlete_data_transformer import normalize_activity_types

        activities = [
            {"type": "run"},
            {"type": "Run"},
            {"type": "RUN"},
            {"type": "running"},
            {"type": "bike"},
            {"type": "Ride"},
        ]

        normalized = normalize_activity_types(activities)

        # Should standardize to consistent format
        run_types = [a["type"] for a in normalized if "run" in a["type"].lower()]
        assert all(t == run_types[0] for t in run_types)  # All run types should be same


class TestPerformanceOptimization:
    """Test performance optimization of data processing."""

    @pytest.mark.slow
    def test_process_large_dataset(self, app_context):
        """Test processing large datasets efficiently."""
        from athlete_data_transformer import process_all_activities

        # Create large dataset
        large_dataset = []
        for i in range(500):
            activity = {
                "id": i,
                "name": f"Activity {i}",
                "distance": 5000 + (i % 1000),
                "moving_time": 1800 + (i % 600),
                "type": "Run",
                "start_date": datetime(2024, 1, 1) + timedelta(days=i % 365),
            }
            large_dataset.append(activity)

        # Should process efficiently
        import time

        start_time = time.time()
        result = process_all_activities(large_dataset)
        end_time = time.time()

        # Should complete in reasonable time
        assert end_time - start_time < 10.0  # Adjust threshold as needed
        assert result is not None

    def test_memory_efficient_processing(self, app_context):
        """Test memory-efficient processing."""
        from athlete_data_transformer import process_activities_in_batches

        # Should be able to process in smaller batches
        activities = [{"id": i, "type": "Run"} for i in range(100)]

        result = process_activities_in_batches(activities, batch_size=10)

        assert result is not None
        assert len(result) == len(activities)
