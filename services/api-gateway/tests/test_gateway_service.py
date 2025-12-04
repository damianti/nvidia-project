"""
Basic tests for API Gateway service.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request


class TestGatewayService:
    """Basic tests for gateway service functionality."""
    
    @pytest.mark.asyncio
    async def test_validate_and_extract_host(self):
        """Test host header validation."""
        from app.services.gateway_service import validate_and_extract_host
        from app.services.gateway_service import RouteValidationError
        
        # Mock request with valid host
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = "example.com"
        
        result = validate_and_extract_host(mock_request)
        assert result == "example.com"
    
    @pytest.mark.asyncio
    async def test_validate_and_extract_host_missing(self):
        """Test host header validation with missing header."""
        from app.services.gateway_service import validate_and_extract_host
        from app.services.gateway_service import RouteValidationError
        
        # Mock request without host header
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = ""
        
        with pytest.raises(RouteValidationError):
            validate_and_extract_host(mock_request)

