"""
Unit tests for usage repository functions.

This module implements comprehensive unit tests following QA best practices:
- AAA pattern (Arrange, Act, Assert)
- Fixtures for test data
- Happy path and error scenarios
- Full type hints and descriptive docstrings
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from app.repositories.usage_repository import (
    create_usage_record,
    get_active_by_container_id,
    update_usage_record,
    get_by_user_and_image,
    get_all_by_user,
)
from app.database.models import Billing, BillingStatus


@pytest.mark.unit
class TestCreateUsageRecord:
    """Test suite for create_usage_record function."""

    def test_create_usage_record_success(
        self, db_session_mock: Mock, test_user_id: int, test_image_id: int
    ) -> None:
        """Test successful usage record creation (Happy Path).

        Verifies:
        - Record is added to database
        - Commit is called
        - Refresh is called
        - Correct attributes are set

        Args:
            db_session_mock: Mock database session
            test_user_id: Fixture with test user ID
            test_image_id: Fixture with test image ID
        """
        # Arrange
        container_id = "docker-123"
        start_time = datetime.now(timezone.utc)

        mock_billing = Mock(spec=Billing)
        db_session_mock.add = Mock()
        db_session_mock.commit = Mock()
        db_session_mock.refresh = Mock()

        with patch(
            "app.repositories.usage_repository.Billing", return_value=mock_billing
        ):
            # Act
            result = create_usage_record(
                db=db_session_mock,
                user_id=test_user_id,
                image_id=test_image_id,
                container_id=container_id,
                start_time=start_time,
            )

            # Assert
            assert result == mock_billing
            db_session_mock.add.assert_called_once()
            db_session_mock.commit.assert_called_once()
            db_session_mock.refresh.assert_called_once_with(mock_billing)


@pytest.mark.unit
class TestGetActiveByContainerId:
    """Test suite for get_active_by_container_id function."""

    def test_get_active_by_container_id_found(
        self, db_session_mock: Mock, sample_billing_record: Mock
    ) -> None:
        """Test finding active record by container ID (Happy Path).

        Verifies:
        - Query is executed correctly
        - Active record is returned

        Args:
            db_session_mock: Mock database session
            sample_billing_record: Fixture with sample billing record
        """
        # Arrange
        container_id = "docker-123"
        sample_billing_record.status = BillingStatus.ACTIVE

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_billing_record
        db_session_mock.query.return_value = mock_query

        # Act
        result = get_active_by_container_id(db_session_mock, container_id)

        # Assert
        assert result == sample_billing_record
        db_session_mock.query.assert_called_once_with(Billing)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()

    def test_get_active_by_container_id_not_found(self, db_session_mock: Mock) -> None:
        """Test when no active record exists (Happy Path - empty result).

        Verifies:
        - Query is executed correctly
        - None is returned when no record found

        Args:
            db_session_mock: Mock database session
        """
        # Arrange
        container_id = "docker-999"

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        db_session_mock.query.return_value = mock_query

        # Act
        result = get_active_by_container_id(db_session_mock, container_id)

        # Assert
        assert result is None
        db_session_mock.query.assert_called_once_with(Billing)


@pytest.mark.unit
class TestUpdateUsageRecord:
    """Test suite for update_usage_record function."""

    def test_update_usage_record_success(
        self, db_session_mock: Mock, sample_billing_record: Mock
    ) -> None:
        """Test successful usage record update (Happy Path).

        Verifies:
        - Record attributes are updated
        - Commit is called
        - Refresh is called
        - Status is set to COMPLETED

        Args:
            db_session_mock: Mock database session
            sample_billing_record: Fixture with sample billing record
        """
        # Arrange
        end_time = datetime.now(timezone.utc)
        duration_minutes = 30
        cost = 0.30

        # Act
        result = update_usage_record(
            db=db_session_mock,
            usage_record=sample_billing_record,
            end_time=end_time,
            duration_minutes=duration_minutes,
            cost=cost,
        )

        # Assert
        assert result == sample_billing_record
        assert sample_billing_record.end_time == end_time
        assert sample_billing_record.duration_minutes == duration_minutes
        assert sample_billing_record.cost == cost
        assert sample_billing_record.status == BillingStatus.COMPLETED
        db_session_mock.commit.assert_called_once()
        db_session_mock.refresh.assert_called_once_with(sample_billing_record)


@pytest.mark.unit
class TestGetByUserAndImage:
    """Test suite for get_by_user_and_image function."""

    def test_get_by_user_and_image_success(
        self,
        db_session_mock: Mock,
        test_user_id: int,
        test_image_id: int,
        sample_billing_record: Mock,
    ) -> None:
        """Test successful retrieval by user and image (Happy Path).

        Verifies:
        - Query is executed correctly
        - Records are returned in correct order
        - Filter conditions are correct

        Args:
            db_session_mock: Mock database session
            test_user_id: Fixture with test user ID
            test_image_id: Fixture with test image ID
            sample_billing_record: Fixture with sample billing record
        """
        # Arrange
        records = [sample_billing_record]

        mock_query = Mock()
        mock_filter = Mock()
        mock_order_by = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order_by
        mock_order_by.all.return_value = records
        db_session_mock.query.return_value = mock_query

        # Act
        result = get_by_user_and_image(db_session_mock, test_user_id, test_image_id)

        # Assert
        assert result == records
        assert len(result) == 1
        db_session_mock.query.assert_called_once_with(Billing)
        mock_query.filter.assert_called_once()
        mock_filter.order_by.assert_called_once()
        mock_order_by.all.assert_called_once()

    def test_get_by_user_and_image_empty(
        self, db_session_mock: Mock, test_user_id: int, test_image_id: int
    ) -> None:
        """Test retrieval when no records exist (Happy Path - empty result).

        Verifies:
        - Query is executed correctly
        - Empty list is returned

        Args:
            db_session_mock: Mock database session
            test_user_id: Fixture with test user ID
            test_image_id: Fixture with test image ID
        """
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_order_by = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order_by
        mock_order_by.all.return_value = []
        db_session_mock.query.return_value = mock_query

        # Act
        result = get_by_user_and_image(db_session_mock, test_user_id, test_image_id)

        # Assert
        assert result == []
        assert len(result) == 0


@pytest.mark.unit
class TestGetAllByUser:
    """Test suite for get_all_by_user function."""

    def test_get_all_by_user_success(
        self, db_session_mock: Mock, test_user_id: int, sample_billing_record: Mock
    ) -> None:
        """Test successful retrieval of all user records (Happy Path).

        Verifies:
        - Query is executed correctly
        - All records are returned
        - Filter by user_id is correct

        Args:
            db_session_mock: Mock database session
            test_user_id: Fixture with test user ID
            sample_billing_record: Fixture with sample billing record
        """
        # Arrange
        records = [sample_billing_record]

        mock_query = Mock()
        mock_filter = Mock()
        mock_order_by = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order_by
        mock_order_by.all.return_value = records
        db_session_mock.query.return_value = mock_query

        # Act
        result = get_all_by_user(db_session_mock, test_user_id)

        # Assert
        assert result == records
        assert len(result) == 1
        db_session_mock.query.assert_called_once_with(Billing)
        mock_query.filter.assert_called_once()
        mock_filter.order_by.assert_called_once()
        mock_order_by.all.assert_called_once()

    def test_get_all_by_user_empty(
        self, db_session_mock: Mock, test_user_id: int
    ) -> None:
        """Test retrieval when user has no records (Happy Path - empty result).

        Verifies:
        - Query is executed correctly
        - Empty list is returned

        Args:
            db_session_mock: Mock database session
            test_user_id: Fixture with test user ID
        """
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_order_by = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order_by
        mock_order_by.all.return_value = []
        db_session_mock.query.return_value = mock_query

        # Act
        result = get_all_by_user(db_session_mock, test_user_id)

        # Assert
        assert result == []
        assert len(result) == 0
