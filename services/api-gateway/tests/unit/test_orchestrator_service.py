"""
Tests for orchestrator_service
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import Request, Response, UploadFile

from app.services import orchestrator_service
from app.clients.orchestrator_client import OrchestratorClient


class TestOrchestratorService:
    """Tests for orchestrator_service"""

    @pytest.fixture
    def mock_orchestrator_client(self):
        """Mock OrchestratorClient"""
        client = Mock(spec=OrchestratorClient)
        client.base_url = "http://orchestrator:3003"
        client.timeout_s = 30.0
        return client

    @pytest.fixture
    def mock_upload_file(self):
        """Mock UploadFile"""
        file = Mock(spec=UploadFile)
        file.filename = "test.tar.gz"
        file.content_type = "application/gzip"
        file.read = AsyncMock(return_value=b"test file content")
        return file

    @pytest.mark.asyncio
    async def test_handle_image_upload_success(
        self, mock_orchestrator_client, mock_upload_file
    ):
        """Test successful image upload"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'{"id": 1, "status": "building"}'
        mock_response.headers = {"Content-Type": "application/json"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None

            result = await orchestrator_service.handle_image_upload(
                name="test-app",
                tag="latest",
                app_hostname="testapp.localhost",
                container_port=8080,
                min_instances=1,
                max_instances=2,
                cpu_limit="0.5",
                memory_limit="512m",
                file=mock_upload_file,
                user_id=1,
                orchestrator_client=mock_orchestrator_client,
            )

            assert isinstance(result, Response)
            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_handle_orchestrator_proxy_get(self, mock_orchestrator_client):
        """Test proxy GET request"""
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.query_params = {}
        mock_request.headers = {"Content-Type": "application/json"}
        mock_request.body = AsyncMock(return_value=b"")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'{"id": 1}'
        mock_response.headers = {}
        mock_orchestrator_client.proxy_request = AsyncMock(return_value=mock_response)

        result = await orchestrator_service.handle_orchestrator_proxy(
            request=mock_request,
            path="images",
            user_id=1,
            orchestrator_client=mock_orchestrator_client,
        )

        assert isinstance(result, Response)
        assert result.status_code == 200
        mock_orchestrator_client.proxy_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_orchestrator_proxy_multipart(self, mock_orchestrator_client):
        """Test proxy multipart request (Happy Path).

        Verifies:
        - Multipart request is handled correctly
        - Response is returned successfully

        Args:
            mock_orchestrator_client: Mocked orchestrator client
        """

        # Arrange
        async def mock_stream():
            yield b"chunk1"
            yield b"chunk2"

        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.query_params = {}
        mock_request.headers = {"Content-Type": "multipart/form-data; boundary=test"}
        mock_request.stream = mock_stream

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'{"id": 1}'
        mock_response.headers = {}
        mock_orchestrator_client.proxy_request = AsyncMock(return_value=mock_response)

        # Act
        result = await orchestrator_service.handle_orchestrator_proxy(
            request=mock_request,
            path="images",
            user_id=1,
            orchestrator_client=mock_orchestrator_client,
        )

        # Assert
        assert isinstance(result, Response)
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_handle_orchestrator_proxy_multipart_empty_body(
        self, mock_orchestrator_client
    ):
        """Test proxy multipart request with empty body"""
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.query_params = {}
        mock_request.headers = {"Content-Type": "multipart/form-data; boundary=test"}
        mock_request.stream = AsyncMock()
        mock_request.stream.__aiter__.return_value = []
        mock_request.form = AsyncMock(return_value={})

        result = await orchestrator_service.handle_orchestrator_proxy(
            request=mock_request,
            path="images",
            user_id=1,
            orchestrator_client=mock_orchestrator_client,
        )

        assert isinstance(result, Response)
        assert result.status_code == 500

    @pytest.mark.asyncio
    async def test_handle_orchestrator_proxy_multipart_stream_error(
        self, mock_orchestrator_client
    ):
        """Test proxy multipart request with stream error"""
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.query_params = {}
        mock_request.headers = {"Content-Type": "multipart/form-data; boundary=test"}
        mock_request.stream = AsyncMock()
        mock_request.stream.__aiter__.side_effect = Exception("Stream error")

        result = await orchestrator_service.handle_orchestrator_proxy(
            request=mock_request,
            path="images",
            user_id=1,
            orchestrator_client=mock_orchestrator_client,
        )

        assert isinstance(result, Response)
        assert result.status_code == 500
