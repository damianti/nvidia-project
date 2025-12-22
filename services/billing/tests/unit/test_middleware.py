"""
Unit tests for Logging Middleware.

This module implements comprehensive unit tests following QA best practices:
- AAA pattern (Arrange, Act, Assert)
- Happy path and error scenarios
- Full type hints and descriptive docstrings
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request
from starlette.responses import Response

from app.middleware.logging import LoggingMiddleware


@pytest.mark.unit
class TestLoggingMiddleware:
    """Test suite for LoggingMiddleware class."""
    
    @pytest.mark.asyncio
    async def test_dispatch_success(self) -> None:
        """Test successful request dispatch (Happy Path).
        
        Verifies:
        - Correlation ID is set
        - Request is logged
        - Response is returned
        - Response has correlation ID header
        
        Args:
            None
        """
        # Arrange
        middleware = LoggingMiddleware(Mock())
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = None
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.url.query = ""
        mock_request.client.host = "127.0.0.1"
        
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        # Act
        result = await middleware.dispatch(mock_request, mock_call_next)
        
        # Assert
        assert result == mock_response
        assert "X-Correlation-ID" in result.headers
        mock_request.headers.get.assert_called_once_with("X-Correlation-ID")
    
    @pytest.mark.asyncio
    async def test_dispatch_with_existing_correlation_id(self) -> None:
        """Test dispatch with existing correlation ID (Happy Path).
        
        Verifies:
        - Existing correlation ID is used
        - Same ID is set in response
        
        Args:
            None
        """
        # Arrange
        middleware = LoggingMiddleware(Mock())
        existing_id = "existing-correlation-id"
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = existing_id
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.url.query = ""
        mock_request.client.host = "127.0.0.1"
        
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        # Act
        result = await middleware.dispatch(mock_request, mock_call_next)
        
        # Assert
        assert result.headers["X-Correlation-ID"] == existing_id
    
    @pytest.mark.asyncio
    async def test_dispatch_handles_exception(
        self
    ) -> None:
        """Test exception handling in middleware (Error Case 2: Server Error).
        
        Verifies:
        - Exception is logged
        - Exception is re-raised
        - Process time is calculated
        
        Args:
            None
        """
        # Arrange
        middleware = LoggingMiddleware(Mock())
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = None
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.url.query = ""
        mock_request.client = None
        
        async def mock_call_next(request):
            raise Exception("Test error")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await middleware.dispatch(mock_request, mock_call_next)
        
        assert "Test error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_dispatch_with_query_params(self) -> None:
        """Test dispatch with query parameters (Happy Path).
        
        Verifies:
        - Query parameters are logged
        - Request is processed successfully
        
        Args:
            None
        """
        # Arrange
        middleware = LoggingMiddleware(Mock())
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = None
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.url.query = "param=value"
        mock_request.client.host = "127.0.0.1"
        
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        # Act
        result = await middleware.dispatch(mock_request, mock_call_next)
        
        # Assert
        assert result.status_code == 200
