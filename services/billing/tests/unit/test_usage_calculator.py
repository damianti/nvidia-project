"""
Unit tests for billing usage calculator functions.
"""

import pytest
from datetime import datetime, timedelta, timezone
from app.services.usage_calculator import (
    calculate_duration_minutes,
    calculate_cost,
    calculate_estimated_cost,
)
from app.utils.config import RATE_PER_MINUTE


class TestCalculateDurationMinutes:
    """Tests for calculate_duration_minutes function."""

    def test_calculate_duration_exact_minutes(self):
        """Test calculation with exact minutes."""
        start = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 10, 30, 0, tzinfo=timezone.utc)
        assert calculate_duration_minutes(start, end) == 30

    def test_calculate_duration_with_seconds(self):
        """Test calculation rounds seconds correctly."""
        start = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 10, 0, 45, tzinfo=timezone.utc)  # 45 seconds
        assert calculate_duration_minutes(start, end) == 1  # Rounds to 1 minute

    def test_calculate_duration_less_than_minute(self):
        """Test calculation for duration less than a minute."""
        start = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 10, 0, 30, tzinfo=timezone.utc)  # 30 seconds
        assert calculate_duration_minutes(start, end) == 0  # Rounds to 0

    def test_calculate_duration_invalid_order(self):
        """Test that invalid time order raises ValueError."""
        start = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc)  # Before start
        with pytest.raises(ValueError, match="end_time.*must be after start_time"):
            calculate_duration_minutes(start, end)


class TestCalculateCost:
    """Tests for calculate_cost function."""

    def test_calculate_cost_standard_rate(self):
        """Test cost calculation with standard rate."""
        duration = 60  # 60 minutes
        cost = calculate_cost(duration)
        expected = 60 * RATE_PER_MINUTE
        assert cost == round(expected, 2)

    def test_calculate_cost_custom_rate(self):
        """Test cost calculation with custom rate."""
        duration = 30  # 30 minutes
        custom_rate = 0.02
        cost = calculate_cost(duration, custom_rate)
        assert cost == 0.60  # 30 * 0.02

    def test_calculate_cost_rounding(self):
        """Test that cost is rounded to 2 decimal places."""
        duration = 1
        custom_rate = 0.015  # Will result in 0.015
        cost = calculate_cost(duration, custom_rate)
        assert cost == 0.01  # Rounded to 2 decimals (0.015 rounds to 0.01)

    def test_calculate_cost_zero_duration(self):
        """Test cost calculation with zero duration."""
        assert calculate_cost(0) == 0.0

    def test_calculate_cost_negative_duration(self):
        """Test that negative duration raises ValueError."""
        with pytest.raises(ValueError, match="duration_minutes must be >= 0"):
            calculate_cost(-1)


class TestCalculateEstimatedCost:
    """Tests for calculate_estimated_cost function."""

    def test_calculate_estimated_cost_with_end_time(self):
        """Test estimated cost calculation with explicit end time."""
        start = datetime.now(timezone.utc) - timedelta(minutes=30)
        end = datetime.now(timezone.utc)
        cost = calculate_estimated_cost(start, end)
        expected = 30 * RATE_PER_MINUTE
        assert cost == round(expected, 2)

    def test_calculate_estimated_cost_without_end_time(self):
        """Test estimated cost calculation using current time."""
        start = datetime.now(timezone.utc) - timedelta(minutes=60)
        cost = calculate_estimated_cost(start)
        # Should be approximately 60 minutes * rate
        expected = 60 * RATE_PER_MINUTE
        assert abs(cost - round(expected, 2)) < 0.01  # Allow small time difference

    def test_calculate_estimated_cost_custom_rate(self):
        """Test estimated cost with custom rate."""
        start = datetime.now(timezone.utc) - timedelta(minutes=10)
        end = datetime.now(timezone.utc)
        custom_rate = 0.02
        cost = calculate_estimated_cost(start, end, custom_rate)
        assert cost == 0.20  # 10 * 0.02

    def test_calculate_estimated_cost_invalid_order(self):
        """Test that invalid time order raises ValueError."""
        start = datetime.now(timezone.utc)
        end = datetime.now(timezone.utc) - timedelta(minutes=10)
        with pytest.raises(ValueError, match="end_time.*must be after start_time"):
            calculate_estimated_cost(start, end)
