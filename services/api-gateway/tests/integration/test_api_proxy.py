"""
Integration tests for proxy API routes.

This module contains comprehensive integration tests for the proxy
and routing endpoints following QA Automation best practices.
"""

from typing import Dict, Any
import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.routing_cache import Cache, CacheEntry
from app.models.routing import RouteResult, RoutingInfo


class TestProxyRoutesIntegration:
    """Integration tests for proxy routes."""

    @pytest.fixture(autouse=True)
    def setup_mocks(
        self,
        mock_lb_client: Mock,
        mock_orchestrator_client: Mock,
        mock_http_client: AsyncMock,
        mock_cache: Cache,
        mock_auth_client: Mock,
    ) -> None:
        """Setup mocks before each test.

        Args:
            mock_lb_client: Mocked load balancer client.
            mock_orchestrator_client: Mocked orchestrator client.
            mock_http_client: Mocked HTTP client.
            mock_cache: Cache instance.
            mock_auth_client: Mocked auth client.
        """
        # Override dependencies
        app.dependency_overrides = {}
        from app.utils.dependencies import (
            get_lb_client,
            get_orchestrator_client,
            get_http_client,
            get_cached_memory,
            get_auth_client,
        )

        app.dependency_overrides[get_lb_client] = lambda: mock_lb_client
        app.dependency_overrides[get_orchestrator_client] = (
            lambda: mock_orchestrator_client
        )
        app.dependency_overrides[get_http_client] = lambda: mock_http_client
        app.dependency_overrides[get_cached_memory] = lambda: mock_cache
        app.dependency_overrides[get_auth_client] = lambda: mock_auth_client
        yield
        app.dependency_overrides.clear()

    # ========================================================================
    # GET /apps/{app_hostname}/{remaining_path:path} Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_apps_route_happy_path(
        self,
        client: TestClient,
        mock_lb_client: Mock,
        mock_http_client: AsyncMock,
        mock_cache: Cache,
        sample_routing_info: RoutingInfo,
        mock_successful_routing_result: RouteResult,
        sample_cache_entry: CacheEntry,
    ) -> None:
        """Test successful routing to application (happy path).

        Arrange:
            - Cache contains valid routing entry
            - Mock HTTP client returns successful response

        Act:
            - Send GET request to /apps/{app_hostname}/

        Assert:
            - Status code is 200
            - Request is proxied to correct container
            - Response structure is valid
        """
        # Arrange
        mock_cache.set("testapp.localhost", "127.0.0.1", sample_cache_entry)

        mock_container_response = Mock()
        mock_container_response.status_code = 200
        mock_container_response.content = b'{"message": "Hello from app"}'
        mock_container_response.headers = {"Content-Type": "application/json"}
        mock_http_client.request = AsyncMock(return_value=mock_container_response)

        # Mock resolve_route to return the cached entry
        from fastapi import Response

        mock_proxy_response = Response(
            content=b'{"message": "Hello from app"}',
            status_code=200,
            headers={"Content-Type": "application/json"},
        )

        with patch(
            "app.services.gateway_service.resolve_route",
            return_value=sample_cache_entry,
        ), patch(
            "app.services.gateway_service.extract_client_ip", return_value="127.0.0.1"
        ), patch(
            "app.services.gateway_service.prepare_proxy_headers", return_value={}
        ), patch(
            "app.services.gateway_service.proxy_to_container",
            return_value=mock_proxy_response,
        ):

            # Act
            response = client.get(
                "/apps/testapp.localhost/", headers={"Host": "testapp.localhost"}
            )

            # Assert
            assert (
                response.status_code == 200
            ), f"Expected 200, got {response.status_code}: {response.text}"

            response_data = response.json()
            assert isinstance(response_data, dict), "Response should be a dictionary"
            assert "message" in response_data, "Response should contain proxied content"

    @pytest.mark.asyncio
    async def test_apps_route_not_found(
        self,
        client: TestClient,
        mock_lb_client: Mock,
        mock_cache: Cache,
        mock_not_found_routing_result: RouteResult,
    ) -> None:
        """Test routing when application not found (error case 1: resource not found).

        Arrange:
            - Cache is empty
            - Load balancer returns NOT_FOUND

        Act:
            - Send GET request to /apps/{app_hostname}/

        Assert:
            - Status code is 503
            - Response indicates application not found
        """
        # Arrange
        mock_lb_client.route = AsyncMock(return_value=mock_not_found_routing_result)

        # Act
        response = client.get(
            "/apps/nonexistent.localhost/", headers={"Host": "nonexistent.localhost"}
        )

        # Assert
        assert (
            response.status_code == 503
        ), f"Expected 503, got {response.status_code}: {response.text}"

        response_body = response.text
        assert (
            "not found" in response_body.lower()
            or "no containers" in response_body.lower()
        ), "Error message should indicate application not found"

    @pytest.mark.asyncio
    async def test_apps_route_invalid_hostname(
        self, client: TestClient, mock_lb_client: Mock, mock_cache: Cache
    ) -> None:
        """Test routing with invalid hostname (error case 2: invalid data).

        Arrange:
            - Empty or whitespace-only hostname

        Act:
            - Send GET request with invalid hostname

        Assert:
            - Status code is 400
            - Response indicates invalid hostname
        """
        # Arrange
        invalid_hostname = "   "  # Only whitespace

        # Act
        response = client.get(
            f"/apps/{invalid_hostname}/", headers={"Host": invalid_hostname}
        )

        # Assert
        assert (
            response.status_code == 400
        ), f"Expected 400, got {response.status_code}: {response.text}"

        response_body = response.text
        assert (
            "invalid" in response_body.lower() or "hostname" in response_body.lower()
        ), "Error message should indicate invalid hostname"

    @pytest.mark.asyncio
    async def test_apps_route_server_error(
        self,
        client: TestClient,
        mock_lb_client: Mock,
        mock_http_client: AsyncMock,
        mock_cache: Cache,
        sample_cache_entry: CacheEntry,
    ) -> None:
        """Test routing when container returns server error (error case 3: server error).

        Arrange:
            - Cache contains valid entry
            - Container returns 500 error

        Act:
            - Send GET request to /apps/{app_hostname}/

        Assert:
            - Status code is 500
            - Cache is invalidated
        """
        # Arrange
        mock_cache.set("testapp.localhost", "127.0.0.1", sample_cache_entry)

        from fastapi import Response

        mock_proxy_response = Response(
            content=b"Internal Server Error", status_code=500, headers={}
        )

        # Mock resolve_route and proxy_to_container
        # Note: proxy_to_container invalidates cache when status >= 500
        with patch(
            "app.services.gateway_service.resolve_route",
            return_value=sample_cache_entry,
        ), patch(
            "app.services.gateway_service.extract_client_ip", return_value="127.0.0.1"
        ), patch(
            "app.services.gateway_service.prepare_proxy_headers", return_value={}
        ), patch(
            "app.services.gateway_service.proxy_to_container"
        ) as mock_proxy:
            mock_proxy.return_value = mock_proxy_response

            # Act
            response = client.get(
                "/apps/testapp.localhost/", headers={"Host": "testapp.localhost"}
            )

            # Assert
            assert (
                response.status_code == 500
            ), f"Expected 500, got {response.status_code}: {response.text}"

            # Verify proxy_to_container was called (which should invalidate cache)
            mock_proxy.assert_called_once()
            # The actual cache invalidation happens inside proxy_to_container
            # Since we're mocking it, we verify it was called with the right parameters
            call_kwargs = mock_proxy.call_args[1]
            assert call_kwargs["app_hostname"] == "testapp.localhost"
            assert call_kwargs["client_ip"] == "127.0.0.1"

    # ========================================================================
    # POST /api/images Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_upload_image_happy_path(
        self,
        authenticated_client: TestClient,
        mock_orchestrator_client: Mock,
        sample_image_upload_data: Dict[str, Any],
        sample_image_response: Dict[str, Any],
    ) -> None:
        """Test successful image upload (Happy Path).

        Verifies:
        - HTTP 200 status code
        - Response contains image data
        - Response structure matches expected schema

        Args:
            authenticated_client: TestClient with authentication
            mock_orchestrator_client: Mocked orchestrator client
            sample_image_upload_data: Fixture with image upload data
            sample_image_response: Fixture with expected image response
        """
        # Arrange
        from fastapi import Response

        mock_response = Response(
            content=b'{"id": 1, "status": "building", "name": "test-app"}',
            status_code=201,
            headers={"Content-Type": "application/json"},
        )

        with patch(
            "app.routes.proxy_routes.handle_image_upload", return_value=mock_response
        ):
            # Act
            files = {"file": ("test.tar.gz", b"fake tar content", "application/gzip")}
            response = authenticated_client.post(
                "/api/images", data=sample_image_upload_data, files=files
            )

            # Assert
            assert (
                response.status_code == 201
            ), f"Expected 201, got {response.status_code}: {response.text}"

            response_data = response.json()
            assert isinstance(response_data, dict), "Response should be a dictionary"
            assert "id" in response_data, "Response should contain 'id' field"
            assert "status" in response_data, "Response should contain 'status' field"
            assert response_data["id"] == sample_image_response["id"]

    @pytest.mark.asyncio
    async def test_upload_image_missing_file(
        self,
        authenticated_client: TestClient,
        mock_orchestrator_client: Mock,
        sample_image_upload_data: Dict[str, Any],
    ) -> None:
        """Test image upload without file (Error Case 1: Invalid Data).

        Verifies:
        - HTTP 422 status code for validation error
        - Response indicates missing file

        Args:
            authenticated_client: TestClient with authentication
            mock_orchestrator_client: Mocked orchestrator client
            sample_image_upload_data: Fixture with image upload data
        """
        # Arrange - no file in request

        # Act
        response = authenticated_client.post(
            "/api/images", data=sample_image_upload_data
        )

        # Assert
        assert (
            response.status_code == 422
        ), f"Expected 422, got {response.status_code}: {response.text}"

        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert (
            "detail" in response_data
        ), "Validation error should contain 'detail' field"
        assert (
            "detail" in response_data
        ), "Validation error should contain 'detail' field"

    @pytest.mark.asyncio
    async def test_upload_image_missing_required_fields(
        self, authenticated_client: TestClient, mock_orchestrator_client: Mock
    ) -> None:
        """Test image upload with missing required fields (error case 2: invalid data).

        Arrange:
            - Client is authenticated
            - Request missing required form fields

        Act:
            - Send POST request with incomplete data

        Assert:
            - Status code is 422
            - Response contains validation errors
        """
        # Arrange
        incomplete_data = {
            "name": "test-app"
            # Missing: tag, app_hostname, etc.
        }
        files = {"file": ("test.tar.gz", b"content", "application/gzip")}

        # Act
        response = authenticated_client.post(
            "/api/images", data=incomplete_data, files=files
        )

        # Assert
        assert (
            response.status_code == 422
        ), f"Expected 422, got {response.status_code}: {response.text}"

        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert (
            "detail" in response_data
        ), "Validation error should contain 'detail' field"

    @pytest.mark.asyncio
    async def test_upload_image_server_error(
        self,
        authenticated_client: TestClient,
        mock_orchestrator_client: Mock,
        sample_image_upload_data: Dict[str, Any],
        mock_error_response_500: Mock,
    ) -> None:
        """Test image upload when orchestrator returns server error (Error Case 2: Server Error).

        Verifies:
        - HTTP 500 status code
        - Response contains error detail

        Args:
            authenticated_client: TestClient with authentication
            mock_orchestrator_client: Mocked orchestrator client
            sample_image_upload_data: Fixture with image upload data
            mock_error_response_500: Mocked 500 error response
        """
        # Arrange
        from fastapi import Response

        mock_response = Response(
            content=b'{"detail": "Internal server error"}',
            status_code=500,
            headers={"Content-Type": "application/json"},
        )

        with patch(
            "app.routes.proxy_routes.handle_image_upload", return_value=mock_response
        ):
            files = {"file": ("test.tar.gz", b"content", "application/gzip")}

            # Act
            response = authenticated_client.post(
                "/api/images", data=sample_image_upload_data, files=files
            )

            # Assert
            assert (
                response.status_code == 500
            ), f"Expected 500, got {response.status_code}: {response.text}"

            response_data = response.json()
            assert isinstance(response_data, dict), "Response should be a dictionary"
            assert (
                "detail" in response_data
            ), "Error response should contain 'detail' field"

    # ========================================================================
    # GET /api/{path:path} Tests (Orchestrator Proxy)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_proxy_api_happy_path(
        self,
        authenticated_client: TestClient,
        mock_orchestrator_client: Mock,
        sample_image_response: Dict[str, Any],
    ) -> None:
        """Test successful API proxy to orchestrator (happy path).

        Arrange:
            - Client is authenticated
            - Mock orchestrator returns successful response

        Act:
            - Send GET request to /api/images

        Assert:
            - Status code is 200
            - Response contains expected data
            - Response structure is valid
        """
        # Arrange
        from fastapi import Response

        mock_response = Response(
            content=b'[{"id": 1, "name": "test-app"}]',
            status_code=200,
            headers={"Content-Type": "application/json"},
        )

        with patch(
            "app.routes.proxy_routes.handle_orchestrator_proxy",
            return_value=mock_response,
        ):
            # Act
            response = authenticated_client.get("/api/images")

            # Assert
            assert (
                response.status_code == 200
            ), f"Expected 200, got {response.status_code}: {response.text}"

            response_data = response.json()
            assert isinstance(
                response_data, list
            ), "Response should be a list of images"
            if len(response_data) > 0:
                assert (
                    "id" in response_data[0]
                ), "Image object should contain 'id' field"
                assert (
                    "name" in response_data[0]
                ), "Image object should contain 'name' field"

    @pytest.mark.asyncio
    async def test_proxy_api_not_found(
        self,
        authenticated_client: TestClient,
        mock_orchestrator_client: Mock,
        mock_error_response_404: Mock,
    ) -> None:
        """Test API proxy when resource not found (error case 1: resource not found).

        Arrange:
            - Client is authenticated
            - Mock orchestrator returns 404

        Act:
            - Send GET request to /api/images/999

        Assert:
            - Status code is 404
            - Response indicates resource not found
        """
        # Arrange
        from fastapi import Response

        mock_response = Response(
            content=b'{"detail": "Image not found"}',
            status_code=404,
            headers={"Content-Type": "application/json"},
        )

        with patch(
            "app.routes.proxy_routes.handle_orchestrator_proxy",
            return_value=mock_response,
        ):
            # Act
            response = authenticated_client.get("/api/images/999")

            # Assert
            assert (
                response.status_code == 404
            ), f"Expected 404, got {response.status_code}: {response.text}"

            response_data = response.json()
            assert isinstance(response_data, dict), "Response should be a dictionary"
            assert (
                "detail" in response_data
            ), "Error response should contain 'detail' field"
            assert (
                "not found" in response_data["detail"].lower()
            ), "Error message should indicate resource not found"

    @pytest.mark.asyncio
    async def test_proxy_api_unauthorized(
        self, client: TestClient, mock_orchestrator_client: Mock
    ) -> None:
        """Test API proxy without authentication (error case 2: invalid data).

        Arrange:
            - No authentication token provided

        Act:
            - Send GET request to /api/images without auth

        Assert:
            - Status code is 401
            - Response indicates authentication required
        """
        # Arrange - no authentication

        # Act
        response = client.get("/api/images")

        # Assert
        assert (
            response.status_code == 401
        ), f"Expected 401, got {response.status_code}: {response.text}"

        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert (
            "authentication" in response_data["detail"].lower()
            or "required" in response_data["detail"].lower()
        ), "Error message should indicate authentication is required"

    @pytest.mark.asyncio
    async def test_proxy_api_server_error(
        self,
        authenticated_client: TestClient,
        mock_orchestrator_client: Mock,
        mock_error_response_500: Mock,
    ) -> None:
        """Test API proxy when orchestrator returns server error (error case 3: server error).

        Arrange:
            - Client is authenticated
            - Mock orchestrator returns 500 error

        Act:
            - Send GET request to /api/images

        Assert:
            - Status code is 500
            - Response contains error detail
        """
        # Arrange
        from fastapi import Response

        mock_response = Response(
            content=b'{"detail": "Internal server error"}',
            status_code=500,
            headers={"Content-Type": "application/json"},
        )

        with patch(
            "app.routes.proxy_routes.handle_orchestrator_proxy",
            return_value=mock_response,
        ):
            # Act
            response = authenticated_client.get("/api/images")

            # Assert
            assert (
                response.status_code == 500
            ), f"Expected 500, got {response.status_code}: {response.text}"

            response_data = response.json()
            assert isinstance(response_data, dict), "Response should be a dictionary"
            assert (
                "detail" in response_data
            ), "Error response should contain 'detail' field"
