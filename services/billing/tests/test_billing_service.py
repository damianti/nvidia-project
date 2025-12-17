"""
Unit tests for billing service.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.services.billing_service import (
    process_container_started,
    process_container_stopped,
    get_billing_summary
)
from app.schemas.billing import ContainerEventData
from app.database.models import BillingStatus


class TestProcessContainerStarted:
    """Tests for process_container_started function."""
    
    @patch('app.services.billing_service.create_usage_record')
    @patch('app.services.billing_service.get_active_by_container_id')
    def test_process_container_started_success(self, mock_get_active, mock_create):
        """Test successful processing of container started event."""
        # Setup mocks
        mock_get_active.return_value = None  # No existing record
        mock_create.return_value = None
        
        db = Mock(spec=Session)
        event_data = ContainerEventData(
            event="container.created",
            user_id=1,
            container_id="container-123",
            container_name="test-container",
            container_ip="172.17.0.2",
            image_id=1,
            internal_port=80,
            external_port=8080,
            app_hostname="example.com",
            timestamp=datetime.now(timezone.utc)
        )
        
        # Test
        process_container_started(db, event_data)
        
        # Assertions
        mock_get_active.assert_called_once_with(db, "container-123")
        mock_create.assert_called_once()
    
    @patch('app.services.billing_service.get_active_by_container_id')
    def test_process_container_started_idempotent(self, mock_get_active):
        """Test that duplicate events don't create duplicate records."""
        # Setup mocks
        existing_record = Mock()
        existing_record.id = 1
        mock_get_active.return_value = existing_record
        
        db = Mock(spec=Session)
        event_data = ContainerEventData(
            event="container.created",
            user_id=1,
            container_id="container-123",
            container_name="test-container",
            container_ip="172.17.0.2",
            image_id=1,
            internal_port=80,
            external_port=8080,
            app_hostname="example.com",
            timestamp=datetime.now(timezone.utc)
        )
        
        # Test
        process_container_started(db, event_data)
        
        # Assertions
        mock_get_active.assert_called_once_with(db, "container-123")
    
    @patch('app.services.billing_service.get_active_by_container_id')
    def test_process_container_started_missing_user_id(self, mock_get_active):
        """Test that events without user_id are skipped."""
        db = Mock(spec=Session)
        event_data = ContainerEventData(
            event="container.created",
            user_id=None,
            container_id="container-123",
            container_name="test-container",
            container_ip="172.17.0.2",
            image_id=1,
            internal_port=80,
            external_port=8080,
            app_hostname="example.com",
            timestamp=datetime.now(timezone.utc)
        )
        
        # Test
        process_container_started(db, event_data)
        
        # Assertions - should not call get_active or create
        mock_get_active.assert_not_called()


class TestProcessContainerStopped:
    """Tests for process_container_stopped function."""
    
    @patch('app.services.billing_service.update_usage_record')
    @patch('app.services.billing_service.get_active_by_container_id')
    def test_process_container_stopped_success(self, mock_get_active, mock_update):
        """Test successful processing of container stopped event."""
        # Setup mocks
        existing_record = Mock()
        existing_record.id = 1
        existing_record.start_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        mock_get_active.return_value = existing_record
        mock_update.return_value = None
        
        db = Mock(spec=Session)
        event_data = ContainerEventData(
            event="container.stopped",
            user_id=1,
            container_id="container-123",
            container_name="test-container",
            container_ip="172.17.0.2",
            image_id=1,
            internal_port=80,
            external_port=8080,
            app_hostname="example.com",
            timestamp=datetime.now(timezone.utc)
        )
        
        # Test
        process_container_stopped(db, event_data)
        
        # Assertions
        mock_get_active.assert_called_once_with(db, "container-123")
        mock_update.assert_called_once()
    
    @patch('app.services.billing_service.get_active_by_container_id')
    def test_process_container_stopped_no_active_record(self, mock_get_active):
        """Test that stopping a container without active record is handled gracefully."""
        # Setup mocks
        mock_get_active.return_value = None  # No active record
        
        db = Mock(spec=Session)
        event_data = ContainerEventData(
            event="container.stopped",
            user_id=1,
            container_id="container-123",
            container_name="test-container",
            container_ip="172.17.0.2",
            image_id=1,
            internal_port=80,
            external_port=8080,
            app_hostname="example.com",
            timestamp=datetime.now(timezone.utc)
        )
        
        # Test - should not raise exception
        process_container_stopped(db, event_data)
        
        # Assertions
        mock_get_active.assert_called_once_with(db, "container-123")


class TestGetBillingSummary:
    """Tests for get_billing_summary function."""
    
    @patch('app.services.billing_service.get_all_by_user')
    @patch('app.services.billing_service.calculate_cost')
    def test_get_billing_summary_success(self, mock_calculate, mock_get_all):
        """Test successful billing summary retrieval."""
        # Setup mocks
        mock_record1 = Mock()
        mock_record1.status = BillingStatus.COMPLETED
        mock_record1.duration_minutes = 60
        mock_record1.cost = 0.60
        
        mock_record2 = Mock()
        mock_record2.status = BillingStatus.COMPLETED
        mock_record2.duration_minutes = 30
        mock_record2.cost = 0.30
        
        mock_get_all.return_value = [mock_record1, mock_record2]
        
        db = Mock(spec=Session)
        
        # Test
        result = get_billing_summary(db, user_id=1)
        
        # Assertions
        assert result.total_cost == 0.90
        assert result.total_containers == 2
        mock_get_all.assert_called_once_with(db, 1)
    
    @patch('app.services.billing_service.get_all_by_user')
    def test_get_billing_summary_no_records(self, mock_get_all):
        """Test billing summary with no records."""
        mock_get_all.return_value = []
        
        db = Mock(spec=Session)
        
        # Test
        result = get_billing_summary(db, user_id=1)
        
        # Assertions
        assert result.total_cost == 0.0
        assert result.total_containers == 0


class TestGetBillingSummary:
    """Tests for get_billing_summary function (with image_id)."""
    
    @patch('app.services.billing_service.get_by_user_and_image')
    @patch('app.services.billing_service.calculate_estimated_cost')
    def test_get_billing_summary_with_image_success(self, mock_estimate, mock_get_by_image):
        """Test successful billing summary retrieval for specific image."""
        # Setup mocks
        mock_record1 = Mock()
        mock_record1.id = 1
        mock_record1.container_id = "container-123"
        mock_record1.status = BillingStatus.COMPLETED
        mock_record1.duration_minutes = 60
        mock_record1.cost = 0.60
        mock_record1.start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        mock_record1.end_time = datetime.now(timezone.utc)
        
        mock_record2 = Mock()
        mock_record2.id = 2
        mock_record2.container_id = "container-456"
        mock_record2.status = BillingStatus.ACTIVE
        mock_record2.duration_minutes = None
        mock_record2.cost = None
        mock_record2.start_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        mock_record2.end_time = None
        
        mock_get_by_image.return_value = [mock_record1, mock_record2]
        mock_estimate.return_value = 0.30
        
        db = Mock(spec=Session)
        
        # Test
        result = get_billing_summary(db, user_id=1, image_id=1)
        
        # Assertions
        assert len(result.containers) == 2
        assert result.summary.total_containers == 2
        mock_get_by_image.assert_called_once_with(db, 1, 1)
    
    @patch('app.services.billing_service.get_by_user_and_image')
    def test_get_billing_summary_with_image_no_records(self, mock_get_by_image):
        """Test billing summary with no records for image."""
        mock_get_by_image.return_value = []
        
        db = Mock(spec=Session)
        
        # Test
        result = get_billing_summary(db, user_id=1, image_id=1)
        
        # Assertions
        assert len(result.containers) == 0
        assert result.summary.total_containers == 0

