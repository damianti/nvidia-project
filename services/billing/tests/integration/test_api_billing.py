"""
Integration tests for Billing API endpoints.

This module implements comprehensive integration tests following QA best practices:
- AAA pattern (Arrange, Act, Assert)
- Fixtures for test data
- Happy path and error scenarios
- Complete response structure validation
- Full type hints and descriptive docstrings
"""
import pytest
import os
from typing import Dict, Any, List
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from datetime import datetime, timezone

# Set DATABASE_URL before importing app
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/testdb')

from app.main import app
from app.utils.dependencies import get_user_id
from app.database.config import get_db
from app.schemas.billing import BillingSummaryResponse, BillingDetailResponse


@pytest.mark.integration
class TestBillingEndpoints:
    """Test suite for Billing API endpoints."""
    
    def setup_method(self) -> None:
        """Setup method that runs before each test.
        
        Configures dependency overrides for database and user authentication.
        """
        # Arrange: Override dependencies
        self.mock_db = Mock()
        self.mock_db.execute = Mock(return_value=Mock())
        app.dependency_overrides[get_user_id] = lambda: 1
        app.dependency_overrides[get_db] = lambda: iter([self.mock_db])
    
    def teardown_method(self) -> None:
        """Teardown method that runs after each test.
        
        Clears all dependency overrides to prevent test interference.
        """
        app.dependency_overrides.clear()
    
    @patch('app.api.billing.get_all_billing_summaries')
    def test_get_user_billings_success(
        self,
        mock_get_all: Mock,
        test_user_id: int
    ) -> None:
        """Test successful retrieval of all user billing summaries (Happy Path).
        
        Verifies:
        - HTTP 200 status code
        - Response is a list
        - All items have required structure
        - Correct number of items
        
        Args:
            mock_get_all: Mocked billing service get_all_billing_summaries function
            test_user_id: Fixture with test user ID
        """
        # Arrange
        mock_summaries = [
            BillingSummaryResponse(
                image_id=1,
                total_containers=2,
                total_minutes=60,
                total_cost=0.60,
                active_containers=1,
                last_activity=datetime.now(timezone.utc)
            ),
            BillingSummaryResponse(
                image_id=2,
                total_containers=1,
                total_minutes=30,
                total_cost=0.30,
                active_containers=0,
                last_activity=datetime.now(timezone.utc)
            ),
        ]
        mock_get_all.return_value = mock_summaries
        
        client = TestClient(app)
        
        # Act
        response = client.get("/images")
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert isinstance(response_data, list), "Response should be a list"
        assert len(response_data) == 2, f"Expected 2 summaries, got {len(response_data)}"
        
        # Verify structure of each summary
        for summary in response_data:
            required_fields = [
                "image_id", "total_containers", "total_minutes",
                "total_cost", "active_containers", "last_activity"
            ]
            for field in required_fields:
                assert field in summary, f"Missing required field: {field}"
        
        assert response_data[0]["image_id"] == 1
        assert response_data[0]["total_cost"] == 0.60
        assert response_data[1]["image_id"] == 2
        assert response_data[1]["total_cost"] == 0.30
        
        mock_get_all.assert_called_once()
    
    @patch('app.api.billing.get_all_billing_summaries')
    def test_get_user_billings_empty(
        self,
        mock_get_all: Mock
    ) -> None:
        """Test retrieval when user has no billing records (Happy Path - empty result).
        
        Verifies:
        - HTTP 200 status code
        - Response is an empty list
        
        Args:
            mock_get_all: Mocked billing service get_all_billing_summaries function
        """
        # Arrange
        mock_get_all.return_value = []
        
        client = TestClient(app)
        
        # Act
        response = client.get("/images")
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert isinstance(response_data, list), "Response should be a list"
        assert len(response_data) == 0, "Response should be empty"
    
    @patch('app.api.billing.get_all_billing_summaries')
    def test_get_user_billings_server_error(
        self,
        mock_get_all: Mock
    ) -> None:
        """Test retrieval with server error (Error Case 2: Server Error).
        
        Verifies:
        - HTTP 500 status code
        - Error response structure
        - Error message presence
        
        Args:
            mock_get_all: Mocked billing service get_all_billing_summaries function
        """
        # Arrange
        mock_get_all.side_effect = Exception("Database connection failed")
        
        client = TestClient(app)
        
        # Act
        response = client.get("/images")
        
        # Assert
        assert response.status_code == 500, f"Expected 500, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert "Failed to retrieve billing summaries" in response_data["detail"]
    
    @patch('app.api.billing.get_billing_summary')
    @patch('app.api.billing.get_by_user_and_image')
    def test_get_image_billing_success(
        self,
        mock_get_by_image: Mock,
        mock_get_summary: Mock,
        test_user_id: int,
        test_image_id: int
    ) -> None:
        """Test successful retrieval of image billing detail (Happy Path).
        
        Verifies:
        - HTTP 200 status code
        - Complete response structure
        - Summary and containers are present
        - Correct data mapping
        
        Args:
            mock_get_by_image: Mocked repository get_by_user_and_image function
            mock_get_summary: Mocked billing service get_billing_summary function
            test_user_id: Fixture with test user ID
            test_image_id: Fixture with test image ID
        """
        # Arrange
        mock_record = Mock()
        mock_get_by_image.return_value = [mock_record]
        
        mock_detail = BillingDetailResponse(
            image_id=test_image_id,
            summary=BillingSummaryResponse(
                image_id=test_image_id,
                total_containers=1,
                total_minutes=30,
                total_cost=0.30,
                active_containers=0,
                last_activity=datetime.now(timezone.utc)
            ),
            containers=[]
        )
        mock_get_summary.return_value = mock_detail
        
        client = TestClient(app)
        
        # Act
        response = client.get(f"/images/{test_image_id}")
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        
        # Verify complete structure
        required_fields = ["image_id", "summary", "containers"]
        for field in required_fields:
            assert field in response_data, f"Missing required field: {field}"
        
        # Verify summary structure
        summary = response_data["summary"]
        summary_fields = [
            "image_id", "total_containers", "total_minutes",
            "total_cost", "active_containers", "last_activity"
        ]
        for field in summary_fields:
            assert field in summary, f"Missing required field in summary: {field}"
        
        assert response_data["image_id"] == test_image_id
        assert summary["total_containers"] == 1
        assert summary["total_cost"] == 0.30
        assert isinstance(response_data["containers"], list)
        
        mock_get_by_image.assert_called_once()
        mock_get_summary.assert_called_once()
    
    @patch('app.api.billing.get_by_user_and_image')
    def test_get_image_billing_not_found(
        self,
        mock_get_by_image: Mock,
        test_image_id: int
    ) -> None:
        """Test image billing retrieval when image doesn't exist (Error Case 3: Not Found).
        
        Verifies:
        - HTTP 404 status code
        - Error response structure
        - Appropriate error message
        
        Args:
            mock_get_by_image: Mocked repository get_by_user_and_image function
            test_image_id: Fixture with test image ID
        """
        # Arrange
        mock_get_by_image.return_value = []
        
        client = TestClient(app)
        
        # Act
        response = client.get(f"/images/{test_image_id}")
        
        # Assert
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert "not found" in response_data["detail"].lower() or "does not belong" in response_data["detail"].lower()
    
    @patch('app.api.billing.get_billing_summary')
    @patch('app.api.billing.get_by_user_and_image')
    def test_get_image_billing_server_error(
        self,
        mock_get_by_image: Mock,
        mock_get_summary: Mock,
        test_image_id: int
    ) -> None:
        """Test image billing retrieval with server error (Error Case 2: Server Error).
        
        Verifies:
        - HTTP 500 status code
        - Error response structure
        
        Args:
            mock_get_by_image: Mocked repository get_by_user_and_image function
            mock_get_summary: Mocked billing service get_billing_summary function
            test_image_id: Fixture with test image ID
        """
        # Arrange
        mock_record = Mock()
        mock_get_by_image.return_value = [mock_record]
        mock_get_summary.side_effect = Exception("Database query failed")
        
        client = TestClient(app)
        
        # Act
        response = client.get(f"/images/{test_image_id}")
        
        # Assert
        assert response.status_code == 500, f"Expected 500, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert "Failed to retrieve billing detail" in response_data["detail"]
