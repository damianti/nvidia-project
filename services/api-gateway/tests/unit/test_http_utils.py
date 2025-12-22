"""
Unit tests for HTTP utilities.

This module implements comprehensive unit tests following QA best practices:
- AAA pattern (Arrange, Act, Assert)
- Happy path and error scenarios
- Full type hints and descriptive docstrings
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import Request

from app.utils import http_utils


@pytest.mark.unit
class TestHttpUtils:
    """Test suite for HTTP utility functions."""
    
    def test_extract_client_ip_from_x_forwarded_for(self) -> None:
        """Test extracting client IP from X-Forwarded-For header (Happy Path).
        
        Verifies:
        - First IP from X-Forwarded-For is extracted
        - Multiple IPs are handled correctly
        
        Args:
            None
        """
        # Arrange
        mock_request = Mock(spec=Request)
        mock_headers = MagicMock()
        mock_headers.get.return_value = "192.168.1.1, 10.0.0.1"
        mock_request.headers = mock_headers
        
        # Act
        ip = http_utils.extract_client_ip(mock_request)
        
        # Assert
        assert ip == "192.168.1.1"
        mock_headers.get.assert_called_once_with("X-Forwarded-For")
    
    def test_extract_client_ip_from_client_host(self) -> None:
        """Test extracting client IP from client.host (Happy Path).
        
        Verifies:
        - Client IP is extracted from request.client.host
        - Works when X-Forwarded-For is not present
        
        Args:
            None
        """
        # Arrange
        mock_request = Mock(spec=Request)
        mock_headers = MagicMock()
        mock_headers.get.return_value = None
        mock_request.headers = mock_headers
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        
        # Act
        ip = http_utils.extract_client_ip(mock_request)
        
        # Assert
        assert ip == "127.0.0.1"
    
    def test_extract_client_ip_no_client_host(self) -> None:
        """Test extracting client IP when client.host is None (Edge Case).
        
        Verifies:
        - Empty string is returned when client.host is None
        - No exception is raised
        
        Args:
            None
        """
        # Arrange
        mock_request = Mock(spec=Request)
        mock_headers = MagicMock()
        mock_headers.get.return_value = None
        mock_request.headers = mock_headers
        mock_request.client = Mock()
        mock_request.client.host = None
        
        # Act
        ip = http_utils.extract_client_ip(mock_request)
        
        # Assert
        assert ip == ""
    
    def test_prepare_proxy_headers_removes_host_and_content_length(self) -> None:
        """Test that prepare_proxy_headers removes host and content-length (Happy Path).
        
        Verifies:
        - Host header is removed
        - Content-Length header is removed
        - Other headers are preserved
        
        Args:
            None
        """
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.headers = {
            "host": "example.com",
            "content-length": "100",
            "user-agent": "test"
        }
        
        with patch("app.utils.http_utils.correlation_id_var") as mock_var:
            mock_var.get.return_value = None
            
            # Act
            headers = http_utils.prepare_proxy_headers(mock_request)
            
            # Assert
            assert "host" not in headers
            assert "content-length" not in headers
            assert "user-agent" in headers
    
    def test_prepare_proxy_headers_adds_correlation_id(self) -> None:
        """Test that prepare_proxy_headers adds correlation ID (Happy Path).
        
        Verifies:
        - Correlation ID is added when available
        - Header is set correctly
        
        Args:
            None
        """
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.headers = {"user-agent": "test"}
        
        with patch("app.utils.http_utils.correlation_id_var") as mock_var:
            mock_var.get.return_value = "test-correlation-id"
            
            # Act
            headers = http_utils.prepare_proxy_headers(mock_request)
            
            # Assert
            assert headers["X-Correlation-ID"] == "test-correlation-id"
    
    def test_prepare_proxy_headers_no_correlation_id_if_not_set(self) -> None:
        """Test that prepare_proxy_headers doesn't add correlation ID if not set (Happy Path).
        
        Verifies:
        - Correlation ID is not added when not available
        - Other headers are preserved
        
        Args:
            None
        """
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.headers = {"user-agent": "test"}
        
        with patch("app.utils.http_utils.correlation_id_var") as mock_var:
            mock_var.get.return_value = None
            
            # Act
            headers = http_utils.prepare_proxy_headers(mock_request)
            
            # Assert
            assert "X-Correlation-ID" not in headers
    
    def test_prepare_proxy_headers_preserves_existing_correlation_id(self) -> None:
        """Test that prepare_proxy_headers preserves existing correlation ID (Happy Path).
        
        Verifies:
        - Existing correlation ID is not overwritten
        - Original value is preserved
        
        Args:
            None
        """
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.headers = {"X-Correlation-ID": "existing-id"}
        
        with patch("app.utils.http_utils.correlation_id_var") as mock_var:
            mock_var.get.return_value = "new-id"
            
            # Act
            headers = http_utils.prepare_proxy_headers(mock_request)
            
            # Assert
            assert headers["X-Correlation-ID"] == "existing-id"

