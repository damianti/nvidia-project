"""
Integration tests for Health and Metrics API endpoints.

This module implements comprehensive integration tests following QA best practices:
- AAA pattern (Arrange, Act, Assert)
- Fixtures for test data
- Happy path scenarios
- Complete response structure validation
- Full type hints and descriptive docstrings
"""
import pytest
import os
from typing import Dict, Any
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Set DATABASE_URL before importing app
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/testdb')

from app.main import app


@pytest.mark.integration
class TestHealthEndpoints:
    """Test suite for Health API endpoints."""
    
    def test_health_check_success(self) -> None:
        """Test successful health check (Happy Path).
        
        Verifies:
        - HTTP 200 status code
        - Response contains status field
        - Status is "healthy"
        
        Args:
            None
        """
        # Arrange
        client = TestClient(app)
        
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert "status" in response_data, "Response should contain 'status' field"
        assert response_data["status"] == "healthy"


@pytest.mark.integration
class TestMetricsEndpoints:
    """Test suite for Metrics API endpoints."""
    
    @patch('app.main.KafkaConsumerService')
    def test_metrics_success(self, mock_kafka_service: Mock) -> None:
        """Test successful metrics retrieval (Happy Path).
        
        Verifies:
        - HTTP 200 status code
        - Response contains required metrics fields
        - All fields are present and have correct types
        
        Args:
            mock_kafka_service: Mocked KafkaConsumerService
        """
        # Arrange
        mock_consumer = Mock()
        mock_consumer.message_count = 100
        mock_consumer.processed_success = 95
        mock_consumer.processed_failures = 5
        mock_kafka_service.return_value = mock_consumer
        
        # Set up app state
        app.state.kafka_consumer = mock_consumer
        
        client = TestClient(app)
        
        # Act
        response = client.get("/metrics")
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        
        # Verify complete structure
        required_fields = [
            "messages_processed",
            "processed_success",
            "processed_failures"
        ]
        for field in required_fields:
            assert field in response_data, f"Missing required field: {field}"
            assert isinstance(response_data[field], int), f"Field {field} should be an integer"
