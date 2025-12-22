"""
Tests for dependencies
"""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException, Request
import httpx

from app.utils import dependencies
from app.services.routing_cache import Cache
from app.clients.lb_client import LoadBalancerClient
from app.clients.orchestrator_client import OrchestratorClient
from app.clients.auth_client import AuthClient


class TestDependencies:
    """Tests for dependencies"""
    
    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI Request"""
        request = Mock(spec=Request)
        request.app = Mock()
        request.app.state = Mock()
        return request
    
    def test_get_from_app_state_success(self, mock_request):
        """Test getting value from app state"""
        mock_request.app.state.test_attr = "test_value"
        
        result = dependencies.get_from_app_state(
            request=mock_request,
            attr_name="test_attr",
            error_message="Not found"
        )
        
        assert result == "test_value"
    
    def test_get_from_app_state_not_found(self, mock_request):
        """Test getting value when not found (Error Case 3: Not Found).
        
        Verifies:
        - HTTPException is raised with 500 status
        - Error message is included
        
        Args:
            mock_request: Mock FastAPI Request
        """
        # Arrange - ensure attribute doesn't exist
        if hasattr(mock_request.app.state, "nonexistent"):
            delattr(mock_request.app.state, "nonexistent")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            dependencies.get_from_app_state(
                request=mock_request,
                attr_name="nonexistent",
                error_message="Not found"
            )
        
        assert exc_info.value.status_code == 500
        assert "Not found" in str(exc_info.value.detail)
    
    def test_get_from_app_state_wrong_type(self, mock_request):
        """Test getting value with wrong type"""
        mock_request.app.state.test_attr = "string_value"
        
        with pytest.raises(HTTPException) as exc_info:
            dependencies.get_from_app_state(
                request=mock_request,
                attr_name="test_attr",
                error_message="Wrong type",
                expected_type=int
            )
        
        assert exc_info.value.status_code == 500
    
    def test_get_http_client_from_state(self, mock_request):
        """Test getting HTTP client from app state"""
        mock_client = Mock(spec=httpx.AsyncClient)
        mock_request.app.state.http_client = mock_client
        
        result = dependencies.get_http_client(mock_request)
        
        assert result == mock_client
    
    def test_get_http_client_fallback(self, mock_request):
        """Test getting HTTP client with fallback"""
        mock_request.app.state.http_client = None
        
        result = dependencies.get_http_client(mock_request)
        
        assert isinstance(result, httpx.AsyncClient)
    
    def test_get_cached_memory(self, mock_request):
        """Test getting cached memory"""
        cache = Cache()
        mock_request.app.state.cached_memory = cache
        
        result = dependencies.get_cached_memory(mock_request)
        
        assert result == cache
    
    def test_get_lb_client(self, mock_request):
        """Test getting load balancer client"""
        lb_client = LoadBalancerClient("http://lb:3004")
        mock_request.app.state.lb_client = lb_client
        
        result = dependencies.get_lb_client(mock_request)
        
        assert result == lb_client
    
    def test_get_orchestrator_client(self, mock_request):
        """Test getting orchestrator client"""
        orch_client = OrchestratorClient("http://orch:3003")
        mock_request.app.state.orchestrator_client = orch_client
        
        result = dependencies.get_orchestrator_client(mock_request)
        
        assert result == orch_client
    
    def test_get_auth_client(self, mock_request):
        """Test getting auth client"""
        auth_client = AuthClient("http://auth:3005")
        mock_request.app.state.auth_client = auth_client
        
        result = dependencies.get_auth_client(mock_request)
        
        assert result == auth_client
    
    @pytest.mark.asyncio
    async def test_verify_token_and_get_user_id_from_cookie(self, mock_request):
        """Test verifying token from cookie (Happy Path).
        
        Verifies:
        - Token is extracted from cookie
        - User ID is returned correctly
        
        Args:
            mock_request: Mock FastAPI Request
        """
        # Arrange
        mock_request.cookies = {"access_token": "test-token"}
        mock_auth_client = Mock(spec=AuthClient)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "email": "test@example.com"}
        mock_auth_client.get_current_user = AsyncMock(return_value=mock_response)
        
        # Act
        result = await dependencies.verify_token_and_get_user_id(
            request=mock_request,
            authorization=None,
            auth_client=mock_auth_client
        )
        
        # Assert
        assert result == 1
    
    @pytest.mark.asyncio
    async def test_verify_token_and_get_user_id_from_header(self, mock_request):
        """Test verifying token from header (Happy Path).
        
        Verifies:
        - Token is extracted from Authorization header
        - User ID is returned correctly
        
        Args:
            mock_request: Mock FastAPI Request
        """
        # Arrange
        mock_request.cookies = {}
        mock_auth_client = Mock(spec=AuthClient)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 2, "email": "test2@example.com"}
        mock_auth_client.get_current_user = AsyncMock(return_value=mock_response)
        
        # Act
        result = await dependencies.verify_token_and_get_user_id(
            request=mock_request,
            authorization="Bearer test-token",
            auth_client=mock_auth_client
        )
        
        # Assert
        assert result == 2
    
    @pytest.mark.asyncio
    async def test_verify_token_and_get_user_id_invalid_header_format(self, mock_request):
        """Test verifying token with invalid header format"""
        mock_request.cookies = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await dependencies.verify_token_and_get_user_id(
                request=mock_request,
                authorization="InvalidFormat",
                auth_client=Mock()
            )
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_verify_token_and_get_user_id_no_auth(self, mock_request):
        """Test verifying token when no auth provided"""
        mock_request.cookies = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await dependencies.verify_token_and_get_user_id(
                request=mock_request,
                authorization=None,
                auth_client=Mock()
            )
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_verify_token_and_get_user_id_auth_failed(self, mock_request):
        """Test verifying token when auth fails (Error Case 1: Invalid Data).
        
        Verifies:
        - HTTPException is raised with 401 status
        - Error detail is included
        
        Args:
            mock_request: Mock FastAPI Request
        """
        # Arrange
        mock_request.cookies = {"access_token": "invalid-token"}
        mock_auth_client = Mock(spec=AuthClient)
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid token"}
        mock_auth_client.get_current_user = AsyncMock(return_value=mock_response)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await dependencies.verify_token_and_get_user_id(
                request=mock_request,
                authorization=None,
                auth_client=mock_auth_client
            )
        
        assert exc_info.value.status_code == 401

