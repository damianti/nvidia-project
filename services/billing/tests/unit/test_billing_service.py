"""
Unit tests for billing service functions.

This module implements comprehensive unit tests following QA best practices:
- AAA pattern (Arrange, Act, Assert)
- Fixtures for test data
- Happy path and error scenarios
- Full type hints and descriptive docstrings
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta

from app.services.billing_service import (
    process_container_started,
    process_container_stopped,
    get_billing_summary,
    get_all_billing_summaries,
)
from app.schemas.billing import ContainerEventData
from app.database.models import BillingStatus


@pytest.mark.unit
class TestProcessContainerStarted:
    """Test suite for process_container_started function."""

    @patch("app.services.billing_service.create_usage_record")
    @patch("app.services.billing_service.get_active_by_container_id")
    def test_process_container_started_success(
        self,
        mock_get_active: Mock,
        mock_create: Mock,
        db_session_mock: Mock,
        sample_container_event_data: dict,
    ) -> None:
        """Test successful processing of container started event (Happy Path).

        Verifies:
        - Active record check is performed
        - Usage record is created
        - Correct parameters are passed

        Args:
            mock_get_active: Mocked get_active_by_container_id function
            mock_create: Mocked create_usage_record function
            db_session_mock: Mock database session
            sample_container_event_data: Fixture with container event data
        """
        # Arrange
        mock_get_active.return_value = None  # No existing record
        mock_create.return_value = Mock()

        event_data = ContainerEventData(**sample_container_event_data)

        # Act
        process_container_started(db_session_mock, event_data)

        # Assert
        mock_get_active.assert_called_once_with(
            db_session_mock, event_data.container_id
        )
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["user_id"] == event_data.user_id
        assert call_kwargs["image_id"] == event_data.image_id
        assert call_kwargs["container_id"] == event_data.container_id

    @patch("app.services.billing_service.get_active_by_container_id")
    def test_process_container_started_idempotent(
        self,
        mock_get_active: Mock,
        db_session_mock: Mock,
        sample_container_event_data: dict,
    ) -> None:
        """Test that duplicate events don't create duplicate records (Happy Path).

        Verifies:
        - Existing record is detected
        - No new record is created
        - Function returns early

        Args:
            mock_get_active: Mocked get_active_by_container_id function
            db_session_mock: Mock database session
            sample_container_event_data: Fixture with container event data
        """
        # Arrange
        existing_record = Mock()
        existing_record.id = 1
        mock_get_active.return_value = existing_record

        event_data = ContainerEventData(**sample_container_event_data)

        # Act
        process_container_started(db_session_mock, event_data)

        # Assert
        mock_get_active.assert_called_once_with(
            db_session_mock, event_data.container_id
        )

    @patch("app.services.billing_service.get_active_by_container_id")
    def test_process_container_started_missing_user_id(
        self,
        mock_get_active: Mock,
        db_session_mock: Mock,
        sample_container_event_data: dict,
    ) -> None:
        """Test that events without user_id are skipped (Error Case 1: Invalid Data).

        Verifies:
        - Function returns early
        - No database operations are performed

        Args:
            mock_get_active: Mocked get_active_by_container_id function
            db_session_mock: Mock database session
            sample_container_event_data: Fixture with container event data
        """
        # Arrange
        sample_container_event_data["user_id"] = None
        event_data = ContainerEventData(**sample_container_event_data)

        # Act
        process_container_started(db_session_mock, event_data)

        # Assert
        mock_get_active.assert_not_called()

    @patch("app.services.billing_service.create_usage_record")
    @patch("app.services.billing_service.get_active_by_container_id")
    def test_process_container_started_missing_timestamp(
        self,
        mock_get_active: Mock,
        mock_create: Mock,
        db_session_mock: Mock,
        sample_container_event_data: dict,
    ) -> None:
        """Test processing with missing timestamp (uses current time as fallback).

        Verifies:
        - Function handles missing timestamp gracefully
        - Current time is used as fallback
        - Record is still created

        Args:
            mock_get_active: Mocked get_active_by_container_id function
            mock_create: Mocked create_usage_record function
            db_session_mock: Mock database session
            sample_container_event_data: Fixture with container event data
        """
        # Arrange
        mock_get_active.return_value = None
        sample_container_event_data["timestamp"] = None
        event_data = ContainerEventData(**sample_container_event_data)

        # Act
        process_container_started(db_session_mock, event_data)

        # Assert
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["start_time"] is not None

    @patch("app.services.billing_service.create_usage_record")
    @patch("app.services.billing_service.get_active_by_container_id")
    def test_process_container_started_exception(
        self,
        mock_get_active: Mock,
        mock_create: Mock,
        db_session_mock: Mock,
        sample_container_event_data: dict,
    ) -> None:
        """Test exception handling in process_container_started (Error Case 2: Server Error).

        Verifies:
        - Exception is logged
        - Exception is re-raised

        Args:
            mock_get_active: Mocked get_active_by_container_id function
            mock_create: Mocked create_usage_record function
            db_session_mock: Mock database session
            sample_container_event_data: Fixture with container event data
        """
        # Arrange
        mock_get_active.return_value = None
        mock_create.side_effect = Exception("Database error")

        event_data = ContainerEventData(**sample_container_event_data)

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            process_container_started(db_session_mock, event_data)

        assert "Database error" in str(exc_info.value)


@pytest.mark.unit
class TestProcessContainerStopped:
    """Test suite for process_container_stopped function."""

    @patch("app.services.billing_service.update_usage_record")
    @patch("app.services.billing_service.calculate_duration_minutes")
    @patch("app.services.billing_service.calculate_cost")
    @patch("app.services.billing_service.get_active_by_container_id")
    def test_process_container_stopped_success(
        self,
        mock_get_active: Mock,
        mock_calculate_cost: Mock,
        mock_calculate_duration: Mock,
        mock_update: Mock,
        db_session_mock: Mock,
        sample_container_event_data: dict,
        sample_billing_record: Mock,
    ) -> None:
        """Test successful processing of container stopped event (Happy Path).

        Verifies:
        - Active record is found
        - Duration and cost are calculated
        - Record is updated correctly

        Args:
            mock_get_active: Mocked get_active_by_container_id function
            mock_calculate_cost: Mocked calculate_cost function
            mock_calculate_duration: Mocked calculate_duration_minutes function
            mock_update: Mocked update_usage_record function
            db_session_mock: Mock database session
            sample_container_event_data: Fixture with container event data
            sample_billing_record: Fixture with sample billing record
        """
        # Arrange
        sample_billing_record.start_time = datetime.now(timezone.utc) - timedelta(
            minutes=30
        )
        end_time = datetime.now(timezone.utc)
        duration_minutes = 30
        cost = 0.30

        mock_get_active.return_value = sample_billing_record
        mock_calculate_duration.return_value = duration_minutes
        mock_calculate_cost.return_value = cost

        event_data = ContainerEventData(**sample_container_event_data)
        event_data.event = "container.stopped"
        event_data.timestamp = end_time

        # Act
        process_container_stopped(db_session_mock, event_data)

        # Assert
        mock_get_active.assert_called_once_with(
            db_session_mock, event_data.container_id
        )
        mock_calculate_duration.assert_called_once()
        mock_calculate_cost.assert_called_once_with(duration_minutes=duration_minutes)
        mock_update.assert_called_once()

    @patch("app.services.billing_service.get_active_by_container_id")
    def test_process_container_stopped_no_active_record(
        self,
        mock_get_active: Mock,
        db_session_mock: Mock,
        sample_container_event_data: dict,
    ) -> None:
        """Test stopping container without active record (Error Case 3: Not Found).

        Verifies:
        - Function handles missing record gracefully
        - No exception is raised
        - Function returns early

        Args:
            mock_get_active: Mocked get_active_by_container_id function
            db_session_mock: Mock database session
            sample_container_event_data: Fixture with container event data
        """
        # Arrange
        mock_get_active.return_value = None

        event_data = ContainerEventData(**sample_container_event_data)
        event_data.event = "container.stopped"

        # Act
        process_container_stopped(db_session_mock, event_data)

        # Assert
        mock_get_active.assert_called_once_with(
            db_session_mock, event_data.container_id
        )

    @patch("app.services.billing_service.get_active_by_container_id")
    def test_process_container_stopped_missing_timestamp(
        self,
        mock_get_active: Mock,
        db_session_mock: Mock,
        sample_container_event_data: dict,
        sample_billing_record: Mock,
    ) -> None:
        """Test processing with missing timestamp (uses current time as fallback).

        Verifies:
        - Function handles missing timestamp gracefully
        - Current time is used as fallback

        Args:
            mock_get_active: Mocked get_active_by_container_id function
            db_session_mock: Mock database session
            sample_container_event_data: Fixture with container event data
            sample_billing_record: Fixture with sample billing record
        """
        # Arrange
        mock_get_active.return_value = sample_billing_record
        sample_container_event_data["timestamp"] = None
        event_data = ContainerEventData(**sample_container_event_data)
        event_data.event = "container.stopped"

        with patch(
            "app.services.billing_service.update_usage_record"
        ) as mock_update, patch(
            "app.services.billing_service.calculate_duration_minutes"
        ) as mock_duration, patch(
            "app.services.billing_service.calculate_cost"
        ) as mock_cost:
            mock_duration.return_value = 30
            mock_cost.return_value = 0.30

            # Act
            process_container_stopped(db_session_mock, event_data)

            # Assert
            mock_update.assert_called_once()

    @patch("app.services.billing_service.update_usage_record")
    @patch("app.services.billing_service.calculate_duration_minutes")
    @patch("app.services.billing_service.calculate_cost")
    @patch("app.services.billing_service.get_active_by_container_id")
    def test_process_container_stopped_exception(
        self,
        mock_get_active: Mock,
        mock_calculate_cost: Mock,
        mock_calculate_duration: Mock,
        mock_update: Mock,
        db_session_mock: Mock,
        sample_container_event_data: dict,
        sample_billing_record: Mock,
    ) -> None:
        """Test exception handling in process_container_stopped (Error Case 2: Server Error).

        Verifies:
        - Exception is logged
        - Exception is re-raised

        Args:
            mock_get_active: Mocked get_active_by_container_id function
            mock_calculate_cost: Mocked calculate_cost function
            mock_calculate_duration: Mocked calculate_duration_minutes function
            mock_update: Mocked update_usage_record function
            db_session_mock: Mock database session
            sample_container_event_data: Fixture with container event data
            sample_billing_record: Fixture with sample billing record
        """
        # Arrange
        mock_get_active.return_value = sample_billing_record
        mock_calculate_duration.return_value = 30
        mock_calculate_cost.return_value = 0.30
        mock_update.side_effect = Exception("Database error")

        event_data = ContainerEventData(**sample_container_event_data)
        event_data.event = "container.stopped"

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            process_container_stopped(db_session_mock, event_data)

        assert "Database error" in str(exc_info.value)


@pytest.mark.unit
class TestGetBillingSummary:
    """Test suite for get_billing_summary function (with image_id)."""

    @patch("app.services.billing_service.calculate_estimated_cost")
    @patch("app.services.billing_service.calculate_duration_minutes")
    @patch("app.services.billing_service.get_by_user_and_image")
    def test_get_billing_summary_success(
        self,
        mock_get_by_image: Mock,
        mock_calculate_duration: Mock,
        mock_estimate_cost: Mock,
        db_session_mock: Mock,
        test_user_id: int,
        test_image_id: int,
        sample_billing_record: Mock,
        sample_active_billing_record: Mock,
    ) -> None:
        """Test successful billing summary retrieval (Happy Path).

        Verifies:
        - Records are retrieved correctly
        - Summary is calculated correctly
        - Containers list is populated
        - Active and completed containers are handled differently

        Args:
            mock_get_by_image: Mocked get_by_user_and_image function
            mock_calculate_duration: Mocked calculate_duration_minutes function
            mock_estimate_cost: Mocked calculate_estimated_cost function
            db_session_mock: Mock database session
            test_user_id: Fixture with test user ID
            test_image_id: Fixture with test image ID
            sample_billing_record: Fixture with completed billing record
            sample_active_billing_record: Fixture with active billing record
        """
        # Arrange
        records = [sample_billing_record, sample_active_billing_record]
        mock_get_by_image.return_value = records
        mock_calculate_duration.return_value = 15
        mock_estimate_cost.return_value = 0.15

        # Act
        result = get_billing_summary(db_session_mock, test_user_id, test_image_id)

        # Assert
        assert result.image_id == test_image_id
        assert result.summary.total_containers == 2
        assert len(result.containers) == 2
        assert result.summary.active_containers == 1
        mock_get_by_image.assert_called_once_with(
            db_session_mock, test_user_id, test_image_id
        )

    @patch("app.services.billing_service.get_by_user_and_image")
    def test_get_billing_summary_no_records(
        self,
        mock_get_by_image: Mock,
        db_session_mock: Mock,
        test_user_id: int,
        test_image_id: int,
    ) -> None:
        """Test billing summary with no records (Happy Path - empty result).

        Verifies:
        - Empty response is returned
        - Summary has zero values
        - Containers list is empty

        Args:
            mock_get_by_image: Mocked get_by_user_and_image function
            db_session_mock: Mock database session
            test_user_id: Fixture with test user ID
            test_image_id: Fixture with test image ID
        """
        # Arrange
        mock_get_by_image.return_value = []

        # Act
        result = get_billing_summary(db_session_mock, test_user_id, test_image_id)

        # Assert
        assert result.image_id == test_image_id
        assert result.summary.total_containers == 0
        assert result.summary.total_cost == 0.0
        assert len(result.containers) == 0

    @patch("app.services.billing_service.calculate_estimated_cost")
    @patch("app.services.billing_service.calculate_duration_minutes")
    @patch("app.services.billing_service.get_by_user_and_image")
    def test_get_billing_summary_timezone_naive_start_time(
        self,
        mock_get_by_image: Mock,
        mock_calculate_duration: Mock,
        mock_estimate_cost: Mock,
        db_session_mock: Mock,
        test_user_id: int,
        test_image_id: int,
    ) -> None:
        """Test billing summary with timezone-naive start_time (Edge Case).

        Verifies:
        - Timezone-naive datetime is converted to UTC
        - Calculation proceeds correctly

        Args:
            mock_get_by_image: Mocked get_by_user_and_image function
            mock_calculate_duration: Mocked calculate_duration_minutes function
            mock_estimate_cost: Mocked calculate_estimated_cost function
            db_session_mock: Mock database session
            test_user_id: Fixture with test user ID
            test_image_id: Fixture with test image ID
        """
        # Arrange
        from datetime import datetime as dt

        record = Mock()
        record.status = BillingStatus.ACTIVE
        record.id = 1
        record.container_id = "docker-123"
        record.start_time = dt.now()  # timezone-naive
        record.end_time = None
        record.duration_minutes = None
        record.cost = None

        mock_get_by_image.return_value = [record]
        mock_calculate_duration.return_value = 15
        mock_estimate_cost.return_value = 0.15

        # Act
        result = get_billing_summary(db_session_mock, test_user_id, test_image_id)

        # Assert
        assert result.summary.total_containers == 1
        assert result.summary.active_containers == 1

    @patch("app.services.billing_service.get_by_user_and_image")
    def test_get_billing_summary_last_activity_from_start_time(
        self,
        mock_get_by_image: Mock,
        db_session_mock: Mock,
        test_user_id: int,
        test_image_id: int,
    ) -> None:
        """Test billing summary uses start_time for last_activity when end_time is None (Edge Case).

        Verifies:
        - last_activity is set from start_time when end_time is None
        - Logic handles records without end_time correctly

        Args:
            mock_get_by_image: Mocked get_by_user_and_image function
            db_session_mock: Mock database session
            test_user_id: Fixture with test user ID
            test_image_id: Fixture with test image ID
        """
        # Arrange

        record = Mock()
        record.status = BillingStatus.COMPLETED
        record.id = 1
        record.container_id = "docker-123"
        record.start_time = datetime.now(timezone.utc) - timedelta(hours=2)
        record.end_time = None  # No end_time
        record.duration_minutes = 120
        record.cost = 1.20

        mock_get_by_image.return_value = [record]

        # Act
        result = get_billing_summary(db_session_mock, test_user_id, test_image_id)

        # Assert
        assert result.summary.last_activity is not None
        assert result.summary.last_activity == record.start_time


@pytest.mark.unit
class TestGetAllBillingSummaries:
    """Test suite for get_all_billing_summaries function."""

    @patch("app.services.billing_service.calculate_estimated_cost")
    @patch("app.services.billing_service.calculate_duration_minutes")
    @patch("app.services.billing_service.get_all_by_user")
    def test_get_all_billing_summaries_success(
        self,
        mock_get_all: Mock,
        mock_calculate_duration: Mock,
        mock_estimate_cost: Mock,
        db_session_mock: Mock,
        test_user_id: int,
        sample_billing_record: Mock,
        sample_active_billing_record: Mock,
    ) -> None:
        """Test successful retrieval of all billing summaries (Happy Path).

        Verifies:
        - All records are retrieved
        - Summaries are grouped by image_id
        - Calculations are correct
        - Results are sorted by last_activity

        Args:
            mock_get_all: Mocked get_all_by_user function
            mock_calculate_duration: Mocked calculate_duration_minutes function
            mock_estimate_cost: Mocked calculate_estimated_cost function
            db_session_mock: Mock database session
            test_user_id: Fixture with test user ID
            sample_billing_record: Fixture with completed billing record
            sample_active_billing_record: Fixture with active billing record
        """
        # Arrange
        records = [sample_billing_record, sample_active_billing_record]
        mock_get_all.return_value = records
        mock_calculate_duration.return_value = 15
        mock_estimate_cost.return_value = 0.15

        # Act
        result = get_all_billing_summaries(db_session_mock, test_user_id)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1  # Both records have same image_id
        assert result[0].image_id == sample_billing_record.image_id
        mock_get_all.assert_called_once_with(db_session_mock, test_user_id)

    @patch("app.services.billing_service.get_all_by_user")
    def test_get_all_billing_summaries_empty(
        self, mock_get_all: Mock, db_session_mock: Mock, test_user_id: int
    ) -> None:
        """Test retrieval when user has no records (Happy Path - empty result).

        Verifies:
        - Empty list is returned
        - No errors occur

        Args:
            mock_get_all: Mocked get_all_by_user function
            db_session_mock: Mock database session
            test_user_id: Fixture with test user ID
        """
        # Arrange
        mock_get_all.return_value = []

        # Act
        result = get_all_billing_summaries(db_session_mock, test_user_id)

        # Assert
        assert result == []
        assert len(result) == 0

    @patch("app.services.billing_service.calculate_estimated_cost")
    @patch("app.services.billing_service.calculate_duration_minutes")
    @patch("app.services.billing_service.get_all_by_user")
    def test_get_all_billing_summaries_timezone_naive(
        self,
        mock_get_all: Mock,
        mock_calculate_duration: Mock,
        mock_estimate_cost: Mock,
        db_session_mock: Mock,
        test_user_id: int,
    ) -> None:
        """Test get_all_billing_summaries with timezone-naive start_time (Edge Case).

        Verifies:
        - Timezone-naive datetime is converted to UTC
        - Calculation proceeds correctly

        Args:
            mock_get_all: Mocked get_all_by_user function
            mock_calculate_duration: Mocked calculate_duration_minutes function
            mock_estimate_cost: Mocked calculate_estimated_cost function
            db_session_mock: Mock database session
            test_user_id: Fixture with test user ID
        """
        # Arrange
        from datetime import datetime as dt

        record = Mock()
        record.image_id = 1
        record.status = BillingStatus.ACTIVE
        record.start_time = dt.now()  # timezone-naive
        record.end_time = None
        record.duration_minutes = None
        record.cost = None

        mock_get_all.return_value = [record]
        mock_calculate_duration.return_value = 15
        mock_estimate_cost.return_value = 0.15

        # Act
        result = get_all_billing_summaries(db_session_mock, test_user_id)

        # Assert
        assert len(result) == 1
        assert result[0].active_containers == 1

    @patch("app.services.billing_service.get_all_by_user")
    def test_get_all_billing_summaries_last_activity_from_start_time(
        self, mock_get_all: Mock, db_session_mock: Mock, test_user_id: int
    ) -> None:
        """Test get_all_billing_summaries uses start_time for last_activity (Edge Case).

        Verifies:
        - last_activity is set from start_time when end_time is None
        - Logic handles records without end_time correctly

        Args:
            mock_get_all: Mocked get_all_by_user function
            db_session_mock: Mock database session
            test_user_id: Fixture with test user ID
        """
        # Arrange

        record = Mock()
        record.image_id = 1
        record.status = BillingStatus.COMPLETED
        record.start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        record.end_time = None  # No end_time
        record.duration_minutes = 60
        record.cost = 0.60

        mock_get_all.return_value = [record]

        # Act
        result = get_all_billing_summaries(db_session_mock, test_user_id)

        # Assert
        assert len(result) == 1
        assert result[0].last_activity is not None
        assert result[0].last_activity == record.start_time
