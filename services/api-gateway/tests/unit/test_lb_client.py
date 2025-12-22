"""
Tests for LoadBalancerClient
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from app.clients.lb_client import LoadBalancerClient
from app.models.routing import RouteResult, RoutingInfo, LbError


class TestLoadBalancerClient:
    """Tests for LoadBalancerClient"""
    
    @pytest.fixture
    def lb_client(self):
        """Create LoadBalancerClient instance"""
        return LoadBalancerClient("http://load-balancer:3004")
    
    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client"""
        return AsyncMock(spec=httpx.AsyncClient)
    
    @pytest.mark.asyncio
    async def test_route_success(self, lb_client, mock_http_client):
        """Test successful routing"""
        lb_client.http_client = mock_http_client
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "target_host": "172.19.0.1",
            "target_port": 32768,
            "container_id": "abc123",
            "image_id": 1,
            "ttl": 1800
        }
        mock_http_client.post.return_value = mock_response
        
        result = await lb_client.route("testapp.localhost")
        
        assert result.ok is True
        assert result.data is not None
        assert result.data.target_host == "172.19.0.1"
        assert result.data.target_port == 32768
        assert result.status_code == 200
    
    @pytest.mark.asyncio
    async def test_route_not_found(self, lb_client, mock_http_client):
        """Test route not found (404)"""
        lb_client.http_client = mock_http_client
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_http_client.post.return_value = mock_response
        
        result = await lb_client.route("nonexistent.localhost")
        
        assert result.ok is False
        assert result.error == LbError.NOT_FOUND
        assert result.status_code == 404
    
    @pytest.mark.asyncio
    async def test_route_no_capacity(self, lb_client, mock_http_client):
        """Test no capacity (503)"""
        lb_client.http_client = mock_http_client
        
        mock_response = Mock()
        mock_response.status_code = 503
        mock_http_client.post.return_value = mock_response
        
        result = await lb_client.route("testapp.localhost")
        
        assert result.ok is False
        assert result.error == LbError.NO_CAPACITY
        assert result.status_code == 503
    
    @pytest.mark.asyncio
    async def test_route_timeout(self, lb_client, mock_http_client):
        """Test route timeout"""
        lb_client.http_client = mock_http_client
        mock_http_client.post.side_effect = httpx.TimeoutException("Timeout")
        
        result = await lb_client.route("testapp.localhost")
        
        assert result.ok is False
        assert result.error == LbError.TIMEOUT
    
    @pytest.mark.asyncio
    async def test_route_parse_error(self, lb_client, mock_http_client):
        """Test route with invalid response format"""
        lb_client.http_client = mock_http_client
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "data"}  # Missing required fields
        mock_response.text = "invalid json"
        mock_http_client.post.return_value = mock_response
        
        result = await lb_client.route("testapp.localhost")
        
        assert result.ok is False
        assert result.error == LbError.UNKNOWN
    
    @pytest.mark.asyncio
    async def test_route_unknown_status(self, lb_client, mock_http_client):
        """Test route with unknown status code"""
        lb_client.http_client = mock_http_client
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_http_client.post.return_value = mock_response
        
        result = await lb_client.route("testapp.localhost")
        
        assert result.ok is False
        assert result.error == LbError.UNKNOWN
        assert result.status_code == 500
    
    @pytest.mark.asyncio
    async def test_route_exception(self, lb_client, mock_http_client):
        """Test route with general exception"""
        lb_client.http_client = mock_http_client
        mock_http_client.post.side_effect = Exception("Connection error")
        
        result = await lb_client.route("testapp.localhost")
        
        assert result.ok is False
        assert result.error == LbError.UNKNOWN
    
    @pytest.mark.asyncio
    async def test_build_headers_with_correlation_id(self, lb_client):
        """Test building headers with correlation ID"""
        with patch("app.clients.lb_client.correlation_id_var") as mock_var:
            mock_var.get.return_value = "test-correlation-id"
            headers = lb_client._build_headers()
            assert headers == {"X-Correlation-ID": "test-correlation-id"}
    
    @pytest.mark.asyncio
    async def test_build_headers_without_correlation_id(self, lb_client):
        """Test building headers without correlation ID"""
        with patch("app.clients.lb_client.correlation_id_var") as mock_var:
            mock_var.get.return_value = None
            headers = lb_client._build_headers()
            assert headers == {}
    
    def test_handle_success(self, lb_client):
        """Test _handle_success method"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "target_host": "172.19.0.1",
            "target_port": "32768",
            "container_id": "abc123",
            "image_id": "1",
            "ttl": 1800
        }
        
        result = lb_client._handle_success(mock_response, "testapp.localhost")
        
        assert result.ok is True
        assert result.data.target_host == "172.19.0.1"
        assert result.data.target_port == 32768
    
    def test_handle_not_found(self, lb_client):
        """Test _handle_not_found method"""
        mock_response = Mock()
        result = lb_client._handle_not_found(mock_response, "testapp.localhost")
        
        assert result.ok is False
        assert result.error == LbError.NOT_FOUND
        assert result.status_code == 404
    
    def test_handle_no_capacity(self, lb_client):
        """Test _handle_no_capacity method"""
        mock_response = Mock()
        result = lb_client._handle_no_capacity(mock_response, "testapp.localhost")
        
        assert result.ok is False
        assert result.error == LbError.NO_CAPACITY
        assert result.status_code == 503

