"""
Unit tests for LoadBalancerClient following QA Automation best practices.

This module contains unit tests with:
- AAA pattern (Arrange, Act, Assert)
- Comprehensive error scenarios
- Response structure validation
- Type hints and descriptive docstrings
"""

from typing import Dict, Any
import pytest
from unittest.mock import AsyncMock, Mock
import httpx

from app.clients.lb_client import LoadBalancerClient
from app.models.routing import RoutingInfo, LbError


class TestLoadBalancerClientUnit:
    """Unit tests for LoadBalancerClient."""

    @pytest.fixture
    def lb_client(self) -> LoadBalancerClient:
        """Fixture providing LoadBalancerClient instance.

        Returns:
            LoadBalancerClient instance for testing.
        """
        return LoadBalancerClient("http://load-balancer:3004")

    @pytest.fixture
    def mock_http_client(self) -> AsyncMock:
        """Fixture providing mocked HTTP client.

        Returns:
            AsyncMock configured as httpx.AsyncClient.
        """
        return AsyncMock(spec=httpx.AsyncClient)

    @pytest.fixture
    def sample_routing_data(self) -> Dict[str, Any]:
        """Fixture providing sample routing response data.

        Returns:
            Dictionary with routing information.
        """
        return {
            "target_host": "172.19.0.1",
            "target_port": 32768,
            "container_id": "abc123def456",
            "image_id": 1,
            "ttl": 1800,
        }

    # ========================================================================
    # Route Method Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_route_happy_path(
        self,
        lb_client: LoadBalancerClient,
        mock_http_client: AsyncMock,
        sample_routing_data: Dict[str, Any],
    ) -> None:
        """Test successful routing (happy path).

        Arrange:
            - Mock HTTP client returns 200 with routing data

        Act:
            - Call route method with app_hostname

        Assert:
            - RouteResult.ok is True
            - RouteResult contains RoutingInfo
            - Response structure is valid
        """
        # Arrange
        lb_client.http_client = mock_http_client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_routing_data
        mock_http_client.post.return_value = mock_response

        # Act
        result = await lb_client.route("testapp.localhost")

        # Assert
        assert result.ok is True, "RouteResult should indicate success"
        assert result.data is not None, "RouteResult should contain routing data"
        assert isinstance(
            result.data, RoutingInfo
        ), "RouteResult.data should be RoutingInfo instance"
        assert result.data.target_host == sample_routing_data["target_host"]
        assert result.data.target_port == sample_routing_data["target_port"]
        assert result.data.container_id == sample_routing_data["container_id"]
        assert result.data.image_id == sample_routing_data["image_id"]
        assert result.status_code == 200

        # Verify request was made correctly
        mock_http_client.post.assert_called_once()
        call_kwargs = mock_http_client.post.call_args[1]
        assert "/route" in call_kwargs["url"]
        assert call_kwargs["json"] == {"app_hostname": "testapp.localhost"}

    @pytest.mark.asyncio
    async def test_route_not_found(
        self, lb_client: LoadBalancerClient, mock_http_client: AsyncMock
    ) -> None:
        """Test routing when application not found (error case 1: resource not found).

        Arrange:
            - Mock HTTP client returns 404 Not Found

        Act:
            - Call route method with non-existent app_hostname

        Assert:
            - RouteResult.ok is False
            - RouteResult.error is NOT_FOUND
            - RouteResult.status_code is 404
        """
        # Arrange
        lb_client.http_client = mock_http_client
        mock_response = Mock()
        mock_response.status_code = 404
        mock_http_client.post.return_value = mock_response

        # Act
        result = await lb_client.route("nonexistent.localhost")

        # Assert
        assert result.ok is False, "RouteResult should indicate failure"
        assert (
            result.error == LbError.NOT_FOUND
        ), f"Expected NOT_FOUND error, got {result.error}"
        assert (
            result.status_code == 404
        ), f"Expected status 404, got {result.status_code}"
        assert result.data is None, "RouteResult should not contain data on error"
        assert result.message is not None, "RouteResult should contain error message"

    @pytest.mark.asyncio
    async def test_route_no_capacity(
        self, lb_client: LoadBalancerClient, mock_http_client: AsyncMock
    ) -> None:
        """Test routing when no containers available (error case 2: resource not found).

        Arrange:
            - Mock HTTP client returns 503 Service Unavailable

        Act:
            - Call route method

        Assert:
            - RouteResult.ok is False
            - RouteResult.error is NO_CAPACITY
            - RouteResult.status_code is 503
        """
        # Arrange
        lb_client.http_client = mock_http_client
        mock_response = Mock()
        mock_response.status_code = 503
        mock_http_client.post.return_value = mock_response

        # Act
        result = await lb_client.route("testapp.localhost")

        # Assert
        assert result.ok is False, "RouteResult should indicate failure"
        assert (
            result.error == LbError.NO_CAPACITY
        ), f"Expected NO_CAPACITY error, got {result.error}"
        assert (
            result.status_code == 503
        ), f"Expected status 503, got {result.status_code}"
        assert result.data is None, "RouteResult should not contain data on error"

    @pytest.mark.asyncio
    async def test_route_server_error(
        self, lb_client: LoadBalancerClient, mock_http_client: AsyncMock
    ) -> None:
        """Test routing when load balancer returns server error (error case 3: server error).

        Arrange:
            - Mock HTTP client returns 500 Internal Server Error

        Act:
            - Call route method

        Assert:
            - RouteResult.ok is False
            - RouteResult.error is UNKNOWN
            - RouteResult.status_code is 500
        """
        # Arrange
        lb_client.http_client = mock_http_client
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_http_client.post.return_value = mock_response

        # Act
        result = await lb_client.route("testapp.localhost")

        # Assert
        assert result.ok is False, "RouteResult should indicate failure"
        assert (
            result.error == LbError.UNKNOWN
        ), f"Expected UNKNOWN error, got {result.error}"
        assert (
            result.status_code == 500
        ), f"Expected status 500, got {result.status_code}"
        assert result.message is not None, "RouteResult should contain error message"

    @pytest.mark.asyncio
    async def test_route_parse_error(
        self, lb_client: LoadBalancerClient, mock_http_client: AsyncMock
    ) -> None:
        """Test routing with invalid response format (error case: invalid data).

        Arrange:
            - Mock HTTP client returns 200 with invalid JSON structure

        Act:
            - Call route method

        Assert:
            - RouteResult.ok is False
            - RouteResult.error is UNKNOWN
            - Error message indicates parsing failure
        """
        # Arrange
        lb_client.http_client = mock_http_client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "data"}  # Missing required fields
        mock_response.text = '{"invalid": "data"}'
        mock_http_client.post.return_value = mock_response

        # Act
        result = await lb_client.route("testapp.localhost")

        # Assert
        assert result.ok is False, "RouteResult should indicate failure"
        assert (
            result.error == LbError.UNKNOWN
        ), f"Expected UNKNOWN error, got {result.error}"
        assert (
            result.status_code == 200
        ), "Status code should be 200 even though parsing failed"
        assert (
            "parse" in result.message.lower() or "failed" in result.message.lower()
        ), "Error message should indicate parsing failure"

    @pytest.mark.asyncio
    async def test_route_timeout(
        self, lb_client: LoadBalancerClient, mock_http_client: AsyncMock
    ) -> None:
        """Test routing timeout scenario.

        Arrange:
            - Mock HTTP client raises TimeoutException

        Act:
            - Call route method

        Assert:
            - RouteResult.ok is False
            - RouteResult.error is TIMEOUT
        """
        # Arrange
        lb_client.http_client = mock_http_client
        mock_http_client.post.side_effect = httpx.TimeoutException("Request timeout")

        # Act
        result = await lb_client.route("testapp.localhost")

        # Assert
        assert result.ok is False, "RouteResult should indicate failure"
        assert (
            result.error == LbError.TIMEOUT
        ), f"Expected TIMEOUT error, got {result.error}"
        assert (
            "timeout" in result.message.lower()
        ), "Error message should indicate timeout"

    @pytest.mark.asyncio
    async def test_route_connection_error(
        self, lb_client: LoadBalancerClient, mock_http_client: AsyncMock
    ) -> None:
        """Test routing connection error scenario.

        Arrange:
            - Mock HTTP client raises ConnectionError

        Act:
            - Call route method

        Assert:
            - RouteResult.ok is False
            - RouteResult.error is UNKNOWN
        """
        # Arrange
        lb_client.http_client = mock_http_client
        mock_http_client.post.side_effect = Exception("Connection error")

        # Act
        result = await lb_client.route("testapp.localhost")

        # Assert
        assert result.ok is False, "RouteResult should indicate failure"
        assert (
            result.error == LbError.UNKNOWN
        ), f"Expected UNKNOWN error, got {result.error}"
        assert result.message is not None, "RouteResult should contain error message"

    # ========================================================================
    # Handler Method Tests
    # ========================================================================

    def test_handle_success_valid_data(
        self, lb_client: LoadBalancerClient, sample_routing_data: Dict[str, Any]
    ) -> None:
        """Test _handle_success with valid response data.

        Arrange:
            - Mock response with valid routing data

        Act:
            - Call _handle_success handler

        Assert:
            - RouteResult.ok is True
            - RouteResult.data contains all required fields
        """
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = sample_routing_data

        # Act
        result = lb_client._handle_success(mock_response, "testapp.localhost")

        # Assert
        assert result.ok is True, "RouteResult should indicate success"
        assert result.data is not None, "RouteResult should contain routing data"
        assert result.data.target_host == sample_routing_data["target_host"]
        assert result.data.target_port == int(sample_routing_data["target_port"])
        assert result.data.container_id == sample_routing_data["container_id"]
        assert result.data.image_id == int(sample_routing_data["image_id"])
        assert result.status_code == 200

    def test_handle_success_missing_fields(self, lb_client: LoadBalancerClient) -> None:
        """Test _handle_success with missing required fields (error case: invalid data).

        Arrange:
            - Mock response missing required fields

        Act:
            - Call _handle_success handler

        Assert:
            - RouteResult.ok is False
            - RouteResult.error is UNKNOWN
        """
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            "target_host": "172.19.0.1"
        }  # Missing other fields
        mock_response.text = '{"target_host": "172.19.0.1"}'

        # Act
        result = lb_client._handle_success(mock_response, "testapp.localhost")

        # Assert
        assert result.ok is False, "RouteResult should indicate failure"
        assert (
            result.error == LbError.UNKNOWN
        ), f"Expected UNKNOWN error, got {result.error}"
        assert (
            "parse" in result.message.lower() or "failed" in result.message.lower()
        ), "Error message should indicate parsing failure"

    def test_handle_not_found(self, lb_client: LoadBalancerClient) -> None:
        """Test _handle_not_found handler.

        Arrange:
            - Mock response with 404 status

        Act:
            - Call _handle_not_found handler

        Assert:
            - RouteResult.ok is False
            - RouteResult.error is NOT_FOUND
            - RouteResult.status_code is 404
        """
        # Arrange
        mock_response = Mock()

        # Act
        result = lb_client._handle_not_found(mock_response, "testapp.localhost")

        # Assert
        assert result.ok is False, "RouteResult should indicate failure"
        assert (
            result.error == LbError.NOT_FOUND
        ), f"Expected NOT_FOUND error, got {result.error}"
        assert (
            result.status_code == 404
        ), f"Expected status 404, got {result.status_code}"
        assert result.message == "Website not found"

    def test_handle_no_capacity(self, lb_client: LoadBalancerClient) -> None:
        """Test _handle_no_capacity handler.

        Arrange:
            - Mock response with 503 status

        Act:
            - Call _handle_no_capacity handler

        Assert:
            - RouteResult.ok is False
            - RouteResult.error is NO_CAPACITY
            - RouteResult.status_code is 503
        """
        # Arrange
        mock_response = Mock()

        # Act
        result = lb_client._handle_no_capacity(mock_response, "testapp.localhost")

        # Assert
        assert result.ok is False, "RouteResult should indicate failure"
        assert (
            result.error == LbError.NO_CAPACITY
        ), f"Expected NO_CAPACITY error, got {result.error}"
        assert (
            result.status_code == 503
        ), f"Expected status 503, got {result.status_code}"
        assert result.message == "No containers available"

    def test_handle_unknown_status(self, lb_client: LoadBalancerClient) -> None:
        """Test _handle_unknown_status handler.

        Arrange:
            - Mock response with unexpected status code

        Act:
            - Call _handle_unknown_status handler

        Assert:
            - RouteResult.ok is False
            - RouteResult.error is UNKNOWN
            - RouteResult contains status code
        """
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 418  # I'm a teapot
        mock_response.text = "Unexpected response"

        # Act
        result = lb_client._handle_unknown_status(mock_response, "testapp.localhost")

        # Assert
        assert result.ok is False, "RouteResult should indicate failure"
        assert (
            result.error == LbError.UNKNOWN
        ), f"Expected UNKNOWN error, got {result.error}"
        assert (
            result.status_code == 418
        ), f"Expected status 418, got {result.status_code}"
        assert (
            "unexpected" in result.message.lower() or str(418) in result.message
        ), "Error message should indicate unexpected status"
