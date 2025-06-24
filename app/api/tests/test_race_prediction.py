"""
Tests for race prediction functionality.

This module tests the race prediction engine including:
- Riegel formula calculations
- Personal best retrieval
- Prediction engine accuracy
- Prediction storage and retrieval
"""

import pandas as pd
from datetime import datetime, timedelta

# Import these within the application context to avoid import errors


class TestRiegelFormula:
    """Test Riegel formula calculations."""

    def test_riegel_basic_calculation(self, app_context):
        """Test basic Riegel formula calculation."""
        from race_prediction.calculator import calculate_riegel_prediction

        # Known time: 5K in 20 minutes (1200 seconds)
        # Predict 10K time
        predicted_time = calculate_riegel_prediction(
            known_distance=5000, known_time=1200, target_distance=10000
        )

        # 10K should be roughly 2x the 5K time with fatigue factor
        assert predicted_time > 2400  # More than 2x due to fatigue
        assert predicted_time < 3000  # But not too much more

    def test_riegel_different_distances(self, app_context):
        """Test Riegel formula for various distance combinations."""
        from race_prediction.calculator import calculate_riegel_prediction

        base_time = 1200  # 20 minutes for 5K

        # Test common distance predictions
        predictions = {
            "10K": calculate_riegel_prediction(5000, base_time, 10000),
            "15K": calculate_riegel_prediction(5000, base_time, 15000),
            "21K": calculate_riegel_prediction(5000, base_time, 21097),  # Half marathon
            "42K": calculate_riegel_prediction(5000, base_time, 42195),  # Marathon
        }

        # Times should increase with distance
        assert predictions["10K"] < predictions["15K"]
        assert predictions["15K"] < predictions["21K"]
        assert predictions["21K"] < predictions["42K"]

        # Marathon should be roughly 4.6-5x the 10K time
        ratio = predictions["42K"] / predictions["10K"]
        assert 4.0 < ratio < 6.0

    def test_riegel_reverse_prediction(self, app_context):
        """Test predicting shorter distance from longer distance."""
        from race_prediction.calculator import calculate_riegel_prediction

        # Known: Half marathon in 90 minutes (5400 seconds)
        # Predict: 5K time
        predicted_5k = calculate_riegel_prediction(
            known_distance=21097, known_time=5400, target_distance=5000
        )

        # 5K should be much faster per km than half marathon
        assert predicted_5k < 1500  # Should be under 25 minutes
        assert predicted_5k > 900  # But not unrealistically fast

    def test_riegel_formula_constants(self, app_context):
        """Test that Riegel formula uses correct fatigue factor."""
        from race_prediction.calculator import RIEGEL_FATIGUE_FACTOR

        # Standard Riegel fatigue factor should be 1.06
        assert abs(RIEGEL_FATIGUE_FACTOR - 1.06) < 0.01

    def test_riegel_edge_cases(self, app_context):
        """Test Riegel formula edge cases."""
        from race_prediction.calculator import calculate_riegel_prediction

        # Same distance should return same time
        same_distance = calculate_riegel_prediction(5000, 1200, 5000)
        assert abs(same_distance - 1200) < 1

        # Very short distances
        short_prediction = calculate_riegel_prediction(1000, 240, 5000)
        assert short_prediction > 0

        # Very long distances
        long_prediction = calculate_riegel_prediction(5000, 1200, 100000)
        assert long_prediction > 0


class TestPersonalBestRetrieval:
    """Test personal best retrieval for predictions."""

    def test_get_best_time_for_distance(self, app_context, test_db):
        """Test retrieving best time for a specific distance."""
        from race_prediction.data_retriever import get_best_time_for_distance
        from sql_methods import write_db_replace

        # Add test activities
        activities = pd.DataFrame(
            [
                {
                    "id": 1,
                    "distance": 5000,
                    "moving_time": 1200,
                    "type": "Run",
                    "start_date": datetime(2024, 1, 1),
                },
                {
                    "id": 2,
                    "distance": 5000,
                    "moving_time": 1100,
                    "type": "Run",  # Better time
                    "start_date": datetime(2024, 1, 15),
                },
                {
                    "id": 3,
                    "distance": 4900,
                    "moving_time": 1150,
                    "type": "Run",  # Close distance
                    "start_date": datetime(2024, 1, 10),
                },
            ]
        )
        write_db_replace(activities, "activities")

        best_time = get_best_time_for_distance(5000, tolerance=100)

        assert best_time is not None
        assert best_time == 1100  # Should be the faster time

    def test_get_closest_distance_pb(self, app_context, test_db):
        """Test getting PB for closest available distance."""
        from race_prediction.data_retriever import get_closest_distance_pb
        from sql_methods import write_db_replace

        activities = pd.DataFrame(
            [
                {"id": 1, "distance": 3000, "moving_time": 720, "type": "Run"},
                {"id": 2, "distance": 8000, "moving_time": 2000, "type": "Run"},
                {"id": 3, "distance": 10000, "moving_time": 2400, "type": "Run"},
            ]
        )
        write_db_replace(activities, "activities")

        # Looking for 5K, should find closest distance
        closest_pb = get_closest_distance_pb(5000)

        assert closest_pb is not None
        assert closest_pb["distance"] in [3000, 8000]  # One of the closer distances

    def test_get_all_distance_pbs(self, app_context, test_db):
        """Test retrieving all personal bests."""
        from race_prediction.data_retriever import get_all_distance_pbs
        from sql_methods import write_db_replace

        activities = pd.DataFrame(
            [
                {"id": 1, "distance": 5000, "moving_time": 1200, "type": "Run"},
                {
                    "id": 2,
                    "distance": 5000,
                    "moving_time": 1100,
                    "type": "Run",
                },  # Better 5K
                {"id": 3, "distance": 10000, "moving_time": 2400, "type": "Run"},
                {
                    "id": 4,
                    "distance": 21097,
                    "moving_time": 5400,
                    "type": "Run",
                },  # Half marathon
            ]
        )
        write_db_replace(activities, "activities")

        all_pbs = get_all_distance_pbs()

        assert len(all_pbs) >= 3  # Should have PBs for different distances

        # Check 5K PB is the better time
        pb_5k = next((pb for pb in all_pbs if abs(pb["distance"] - 5000) < 100), None)
        assert pb_5k is not None
        assert pb_5k["time"] == 1100

    def test_pb_filtering_by_date(self, app_context, test_db):
        """Test filtering PBs by date range."""
        from race_prediction.data_retriever import get_pbs_in_date_range
        from sql_methods import write_db_replace

        activities = pd.DataFrame(
            [
                {
                    "id": 1,
                    "distance": 5000,
                    "moving_time": 1300,
                    "type": "Run",
                    "start_date": datetime(2023, 6, 1),  # Old PB
                },
                {
                    "id": 2,
                    "distance": 5000,
                    "moving_time": 1200,
                    "type": "Run",
                    "start_date": datetime(2024, 1, 1),  # Recent PB
                },
            ]
        )
        write_db_replace(activities, "activities")

        # Get PBs from 2024 only
        recent_pbs = get_pbs_in_date_range(
            start_date=datetime(2024, 1, 1), end_date=datetime(2024, 12, 31)
        )

        assert len(recent_pbs) == 1
        assert recent_pbs[0]["time"] == 1200


class TestPredictionEngine:
    """Test the main prediction engine."""

    def test_prediction_engine_initialization(self, app_context):
        """Test prediction engine can be initialized."""
        from race_prediction.engine import PredictionEngine

        engine = PredictionEngine()
        assert engine is not None

    def test_generate_single_prediction(self, app_context, test_db):
        """Test generating a single race prediction."""
        from race_prediction.engine import PredictionEngine
        from sql_methods import write_db_replace

        # Add a PB to use for prediction
        activities = pd.DataFrame(
            [{"id": 1, "distance": 5000, "moving_time": 1200, "type": "Run"}]
        )
        write_db_replace(activities, "activities")

        engine = PredictionEngine()
        prediction = engine.predict_race_time(target_distance=10000, base_distance=5000)

        assert prediction is not None
        assert prediction["target_distance"] == 10000
        assert prediction["predicted_time"] > 0
        assert "confidence" in prediction

    def test_generate_multiple_predictions(self, app_context, test_db):
        """Test generating predictions for multiple distances."""
        from race_prediction.engine import PredictionEngine
        from sql_methods import write_db_replace

        activities = pd.DataFrame(
            [{"id": 1, "distance": 5000, "moving_time": 1200, "type": "Run"}]
        )
        write_db_replace(activities, "activities")

        engine = PredictionEngine()
        predictions = engine.predict_multiple_distances([10000, 21097, 42195])

        assert len(predictions) == 3
        assert all("predicted_time" in p for p in predictions)
        assert all(p["predicted_time"] > 0 for p in predictions)

        # Times should increase with distance
        times = [p["predicted_time"] for p in predictions]
        assert times == sorted(times)

    def test_prediction_with_multiple_pbs(self, app_context, test_db):
        """Test prediction using multiple personal bests."""
        from race_prediction.engine import PredictionEngine
        from sql_methods import write_db_replace

        activities = pd.DataFrame(
            [
                {"id": 1, "distance": 5000, "moving_time": 1200, "type": "Run"},
                {"id": 2, "distance": 10000, "moving_time": 2500, "type": "Run"},
            ]
        )
        write_db_replace(activities, "activities")

        engine = PredictionEngine()
        prediction = engine.predict_with_multiple_bases(target_distance=21097)

        assert prediction is not None
        assert "predictions" in prediction
        assert len(prediction["predictions"]) >= 2  # From both PBs
        assert "average_prediction" in prediction

    def test_prediction_confidence_calculation(self, app_context):
        """Test prediction confidence calculation."""
        from race_prediction.engine import calculate_prediction_confidence

        # More recent PB should have higher confidence
        recent_pb = {"date": datetime.now() - timedelta(days=30)}
        old_pb = {"date": datetime.now() - timedelta(days=365)}

        recent_confidence = calculate_prediction_confidence(
            recent_pb, target_distance=10000
        )
        old_confidence = calculate_prediction_confidence(old_pb, target_distance=10000)

        assert recent_confidence > old_confidence
        assert 0 <= recent_confidence <= 1
        assert 0 <= old_confidence <= 1


class TestPredictionAccuracy:
    """Test prediction accuracy validation."""

    def test_validate_prediction_against_actual(self, app_context):
        """Test validating predictions against actual results."""
        from race_prediction.engine import validate_prediction

        prediction = {"predicted_time": 2400, "target_distance": 10000}

        actual_result = {"actual_time": 2450, "distance": 10000}

        validation = validate_prediction(prediction, actual_result)

        assert "accuracy_percentage" in validation
        assert "time_difference" in validation
        assert validation["time_difference"] == 50  # 50 seconds difference

    def test_prediction_accuracy_metrics(self, app_context):
        """Test calculation of prediction accuracy metrics."""
        from race_prediction.engine import calculate_accuracy_metrics

        predictions = [
            {"predicted": 1200, "actual": 1180},  # 20s fast
            {"predicted": 2400, "actual": 2450},  # 50s slow
            {"predicted": 5400, "actual": 5350},  # 50s fast
        ]

        metrics = calculate_accuracy_metrics(predictions)

        assert "mean_error" in metrics
        assert "mean_absolute_error" in metrics
        assert "accuracy_percentage" in metrics
        assert metrics["mean_absolute_error"] == 40  # (20+50+50)/3


class TestPredictionStorage:
    """Test prediction storage and retrieval."""

    def test_save_prediction(self, app_context, test_db):
        """Test saving a prediction to database."""
        from race_prediction.storage import PredictionStorage

        storage = PredictionStorage()

        prediction_data = {
            "athlete_id": "12345",
            "target_distance": 10000,
            "predicted_time": 2400,
            "base_distance": 5000,
            "base_time": 1200,
            "prediction_date": datetime.now(),
            "confidence": 0.85,
        }

        result = storage.save_prediction(prediction_data)
        assert result is True

    def test_retrieve_predictions(self, app_context, test_db):
        """Test retrieving saved predictions."""
        from race_prediction.storage import PredictionStorage

        storage = PredictionStorage()

        # Save a prediction first
        prediction_data = {
            "athlete_id": "12345",
            "target_distance": 10000,
            "predicted_time": 2400,
            "prediction_date": datetime.now(),
        }
        storage.save_prediction(prediction_data)

        # Retrieve predictions
        predictions = storage.get_predictions_for_athlete("12345")

        assert len(predictions) >= 1
        assert predictions[0]["target_distance"] == 10000

    def test_update_prediction_with_actual(self, app_context, test_db):
        """Test updating prediction with actual race result."""
        from race_prediction.storage import PredictionStorage

        storage = PredictionStorage()

        # Save initial prediction
        prediction_data = {
            "athlete_id": "12345",
            "target_distance": 10000,
            "predicted_time": 2400,
            "prediction_date": datetime.now(),
        }
        prediction_id = storage.save_prediction(prediction_data)

        # Update with actual result
        actual_data = {
            "actual_time": 2450,
            "race_date": datetime.now() + timedelta(days=30),
        }

        result = storage.update_with_actual_result(prediction_id, actual_data)
        assert result is True

        # Verify update
        updated_prediction = storage.get_prediction_by_id(prediction_id)
        assert updated_prediction["actual_time"] == 2450


class TestPredictionFormatting:
    """Test prediction result formatting."""

    def test_format_time_display(self, app_context):
        """Test formatting time for display."""
        from race_prediction.formatter import format_time_display

        # Test various time formats
        assert format_time_display(1200) == "20:00"  # 20 minutes
        assert format_time_display(3661) == "1:01:01"  # 1 hour, 1 minute, 1 second
        assert format_time_display(90) == "1:30"  # 1 minute 30 seconds

    def test_format_pace_display(self, app_context):
        """Test formatting pace for display."""
        from race_prediction.formatter import format_pace_display

        # 5K in 20 minutes = 4:00/km pace
        pace = format_pace_display(distance=5000, time=1200)
        assert pace == "4:00/km"

        # 10K in 40 minutes = 4:00/km pace
        pace = format_pace_display(distance=10000, time=2400)
        assert pace == "4:00/km"

    def test_format_prediction_range(self, app_context):
        """Test formatting prediction ranges."""
        from race_prediction.formatter import format_prediction_range

        prediction = {"conservative": 2500, "realistic": 2400, "optimistic": 2300}

        formatted = format_prediction_range(prediction)

        assert "conservative" in formatted
        assert "realistic" in formatted
        assert "optimistic" in formatted
        assert formatted["realistic"] == "40:00"

    def test_format_prediction_summary(self, app_context):
        """Test formatting complete prediction summary."""
        from race_prediction.formatter import format_prediction_summary

        prediction_data = {
            "target_distance": 10000,
            "predicted_time": 2400,
            "base_distance": 5000,
            "base_time": 1200,
            "confidence": 0.85,
            "prediction_date": datetime(2024, 1, 15),
        }

        summary = format_prediction_summary(prediction_data)

        assert "distance_name" in summary  # e.g., "10K"
        assert "predicted_time_formatted" in summary
        assert "pace" in summary
        assert "confidence_percentage" in summary


class TestRacePredictionIntegration:
    """Test end-to-end race prediction workflow."""

    def test_complete_prediction_workflow(self, app_context, test_db):
        """Test complete prediction workflow from PB to formatted result."""
        from race_prediction.engine import PredictionEngine
        from race_prediction.formatter import format_prediction_summary
        from sql_methods import write_db_replace

        # Add test data
        activities = pd.DataFrame(
            [
                {
                    "id": 1,
                    "distance": 5000,
                    "moving_time": 1200,
                    "type": "Run",
                    "start_date": datetime(2024, 1, 1),
                }
            ]
        )
        write_db_replace(activities, "activities")

        # Generate prediction
        engine = PredictionEngine()
        prediction = engine.predict_race_time(target_distance=10000)

        # Format result
        formatted = format_prediction_summary(prediction)

        assert prediction is not None
        assert formatted is not None
        assert formatted["distance_name"] == "10K"
        assert "predicted_time_formatted" in formatted

    def test_prediction_with_no_pbs(self, app_context, test_db):
        """Test prediction when no personal bests are available."""
        from race_prediction.engine import PredictionEngine

        engine = PredictionEngine()
        prediction = engine.predict_race_time(target_distance=10000)

        # Should handle gracefully when no PBs available
        assert prediction is None or "error" in prediction

    def test_prediction_caching(self, app_context, test_db):
        """Test caching of prediction results."""
        from race_prediction.engine import PredictionEngine
        from sql_methods import write_db_replace

        activities = pd.DataFrame(
            [{"id": 1, "distance": 5000, "moving_time": 1200, "type": "Run"}]
        )
        write_db_replace(activities, "activities")

        engine = PredictionEngine()

        # Generate same prediction twice
        prediction1 = engine.predict_race_time(target_distance=10000, use_cache=True)
        prediction2 = engine.predict_race_time(target_distance=10000, use_cache=True)

        # Second call should be faster (cached)
        assert prediction1["predicted_time"] == prediction2["predicted_time"]
