import sys
import os

sys.path.append(os.path.abspath(os.path.join(".")))  # Adjust the path as necessary

import pytest
from utils.time_utils import format_runtime, hms_to_minutes


@pytest.mark.parametrize(
    "input_sec, expected",
    [
        # simple minutes+seconds
        (0, "0:00"),
        (59, "0:59"),
        (60, "1:00"),
        (150, "2:30"),
        # rounding floats
        (150.2, "2:30"),  # rounds down
        (150.5, "2:31"),  # rounds up
        # hours
        (3600, "1:00:00"),
        (3661, "1:01:01"),
        (7325, "2:02:05"),
        # big number
        (10_000, "2:46:40"),
    ],
)
def test_format_runtime_valid(input_sec, expected):
    assert format_runtime(input_sec) == expected


def test_negative_raises():
    with pytest.raises(ValueError):
        format_runtime(-1)


def test_exact_hour_boundary():
    # Makes sure it doesn't print "60:00" but "1:00:00"
    assert format_runtime(3599.9) == "59:59"  # rounds down
    assert format_runtime(3600.1) == "1:00:00"  # rounds up


class TestFormatRuntimeAdditional:
    """Additional tests for format_runtime function."""
    
    def test_zero_seconds(self):
        """Test formatting zero seconds."""
        assert format_runtime(0) == "0:00"
    
    def test_very_small_positive(self):
        """Test very small positive values."""
        assert format_runtime(0.1) == "0:00"
        assert format_runtime(0.4) == "0:00"
        assert format_runtime(0.5) == "0:01"
    
    def test_marathon_times(self):
        """Test realistic marathon times."""
        # Sub-3 hour marathon (2:59:59)
        assert format_runtime(10799) == "2:59:59"
        
        # 4 hour marathon
        assert format_runtime(14400) == "4:00:00"
        
        # Boston qualifying time for 18-34 male (3:00:00)
        assert format_runtime(10800) == "3:00:00"
    
    def test_ultra_marathon_times(self):
        """Test very long race times."""
        # 24 hour race
        assert format_runtime(86400) == "24:00:00"
        
        # 100 mile race (~20 hours)
        assert format_runtime(72000) == "20:00:00"
    
    def test_edge_cases_near_hour_boundaries(self):
        """Test edge cases near hour boundaries."""
        # Just under 1 hour - gets clamped
        assert format_runtime(3599) == "59:59"
        assert format_runtime(3599.4) == "59:59"
        assert format_runtime(3599.5) == "59:59"  # Clamped to stay under 1 hour
        
        # Just under 2 hours - also gets clamped
        assert format_runtime(7199) == "1:59:59"
        assert format_runtime(7199.5) == "1:59:59"  # Clamped to stay under 2 hours
    
    def test_rounding_behavior(self):
        """Test specific rounding behavior."""
        # Test round-half-up behavior
        assert format_runtime(30.5) == "0:31"  # rounds up
        assert format_runtime(30.4) == "0:30"  # rounds down
        assert format_runtime(90.5) == "1:31"  # rounds up
        assert format_runtime(90.4) == "1:30"  # rounds down


class TestHmsToMinutes:
    """Tests for hms_to_minutes function."""
    
    def test_zero_time(self):
        """Test conversion of zero time."""
        assert hms_to_minutes(0, 0, 0) == 0
    
    def test_only_hours(self):
        """Test conversion with only hours."""
        assert hms_to_minutes(1, 0, 0) == 60
        assert hms_to_minutes(2, 0, 0) == 120
        assert hms_to_minutes(3, 0, 0) == 180
    
    def test_only_minutes(self):
        """Test conversion with only minutes."""
        assert hms_to_minutes(0, 30, 0) == 30
        assert hms_to_minutes(0, 45, 0) == 45
        assert hms_to_minutes(0, 90, 0) == 90  # More than 60 minutes
    
    def test_only_seconds(self):
        """Test conversion with only seconds."""
        assert hms_to_minutes(0, 0, 30) == 0.5
        assert hms_to_minutes(0, 0, 60) == 1.0
        assert hms_to_minutes(0, 0, 90) == 1.5
    
    def test_combined_time(self):
        """Test conversion with hours, minutes, and seconds."""
        # 1:30:45 = 90.75 minutes
        assert hms_to_minutes(1, 30, 45) == 90.75
        
        # 2:15:30 = 135.5 minutes
        assert hms_to_minutes(2, 15, 30) == 135.5
        
        # 0:20:15 = 20.25 minutes
        assert hms_to_minutes(0, 20, 15) == 20.25
    
    def test_marathon_times(self):
        """Test conversion of realistic marathon times."""
        # 3:00:00 marathon
        assert hms_to_minutes(3, 0, 0) == 180
        
        # 4:30:15 marathon
        assert hms_to_minutes(4, 30, 15) == 270.25
        
        # 2:59:59 marathon
        assert hms_to_minutes(2, 59, 59) == 179 + 59/60
    
    def test_5k_times(self):
        """Test conversion of 5K race times."""
        # 20:00 5K
        assert hms_to_minutes(0, 20, 0) == 20
        
        # 18:30 5K
        assert hms_to_minutes(0, 18, 30) == 18.5
        
        # 25:45 5K
        assert hms_to_minutes(0, 25, 45) == 25.75
    
    def test_fractional_seconds(self):
        """Test that function handles integer seconds correctly."""
        # The function expects integer seconds, but let's test edge cases
        assert hms_to_minutes(1, 0, 30) == 60.5
        assert hms_to_minutes(0, 1, 30) == 1.5
    
    def test_large_values(self):
        """Test with large time values."""
        # 24 hour race
        assert hms_to_minutes(24, 0, 0) == 1440
        
        # Ultra marathon time
        assert hms_to_minutes(12, 30, 45) == 750.75


class TestTimeUtilsIntegration:
    """Integration tests for time utility functions."""
    
    def test_roundtrip_conversion(self):
        """Test converting time to minutes and back to formatted string."""
        # Test cases: (h, m, s) -> minutes -> seconds -> formatted
        test_cases = [
            (0, 20, 0),    # 5K time
            (0, 40, 30),   # 10K time
            (1, 30, 0),    # Half marathon time
            (3, 15, 45),   # Marathon time
        ]
        
        for h, m, s in test_cases:
            # Convert to minutes
            minutes = hms_to_minutes(h, m, s)
            
            # Convert back to seconds
            total_seconds = minutes * 60
            
            # Format as runtime
            formatted = format_runtime(total_seconds)
            
            # Verify the formatted time makes sense
            if h > 0:
                assert ":" in formatted
                parts = formatted.split(":")
                assert len(parts) == 3  # H:MM:SS format
            else:
                parts = formatted.split(":")
                assert len(parts) == 2  # M:SS format
    
    def test_realistic_race_scenarios(self):
        """Test with realistic race time scenarios."""
        scenarios = [
            # (distance, typical_time_hms, description)
            ("5K", (0, 20, 0), "Average 5K time"),
            ("10K", (0, 42, 0), "Average 10K time"),
            ("Half Marathon", (1, 45, 0), "Average half marathon"),
            ("Marathon", (4, 0, 0), "4-hour marathon"),
        ]
        
        for distance, (h, m, s), description in scenarios:
            minutes = hms_to_minutes(h, m, s)
            seconds = minutes * 60
            formatted = format_runtime(seconds)
            
            # Verify conversion makes sense
            assert minutes > 0, f"Invalid time for {description}"
            assert seconds > 0, f"Invalid seconds for {description}"
            assert formatted != "0:00", f"Invalid format for {description}"
