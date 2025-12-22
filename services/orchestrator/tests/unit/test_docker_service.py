"""
Unit tests for docker_service.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from docker.errors import APIError, BuildError, DockerException
from docker.models.containers import Container

from app.services.docker_service import (
    _collect_build_logs,
    _is_retryable_error,
    _retry_docker_operation,
    get_external_port,
    get_container_ip_from_container,
    build_image_from_context,
    run_container,
    start_container,
    stop_container,
    delete_container,
    get_container_ip,
)


@pytest.mark.unit
class TestCollectBuildLogs:
    """Tests for _collect_build_logs function."""
    
    def test_collect_logs_from_dict_stream(self):
        """Test collecting logs from dict with stream field."""
        logs = [
            {"stream": "Step 1/5 : FROM python:3.11\n"},
            {"stream": "Step 2/5 : COPY app.py .\n"},
        ]
        result = _collect_build_logs(logs)
        
        assert "Step 1/5" in result
        assert "Step 2/5" in result
    
    def test_collect_logs_from_dict_error(self):
        """Test collecting logs from dict with error field."""
        logs = [
            {"error": "Build failed"},
            {"stream": "Some output\n"},
        ]
        result = _collect_build_logs(logs)
        
        assert "ERROR: Build failed" in result
        assert "Some output" in result
    
    def test_collect_logs_from_dict_aux(self):
        """Test collecting logs from dict with aux field (image ID)."""
        logs = [
            {"aux": {"ID": "sha256:abc123"}},
            {"stream": "Successfully built\n"},
        ]
        result = _collect_build_logs(logs)
        
        assert "Successfully built sha256:abc123" in result
    
    def test_collect_logs_from_bytes_json(self):
        """Test collecting logs from bytes that are valid JSON."""
        logs = [
            json.dumps({"stream": "Step 1\n"}).encode('utf-8'),
            json.dumps({"error": "Error occurred"}).encode('utf-8'),
        ]
        result = _collect_build_logs(logs)
        
        assert "Step 1" in result
        assert "ERROR: Error occurred" in result
    
    def test_collect_logs_from_bytes_plain_text(self):
        """Test collecting logs from bytes that are plain text."""
        logs = [
            b"Step 1/5 : FROM python:3.11\n",
            b"Step 2/5 : COPY app.py .\n",
        ]
        result = _collect_build_logs(logs)
        
        assert "Step 1/5" in result
        assert "Step 2/5" in result
    
    def test_collect_logs_from_string(self):
        """Test collecting logs from string chunks."""
        logs = [
            "Step 1/5 : FROM python:3.11\n",
            "Step 2/5 : COPY app.py .\n",
        ]
        result = _collect_build_logs(logs)
        
        assert "Step 1/5" in result
        assert "Step 2/5" in result
    
    def test_collect_logs_mixed_types(self):
        """Test collecting logs from mixed types."""
        logs = [
            {"stream": "Step 1\n"},
            b"Step 2\n",
            "Step 3\n",
        ]
        result = _collect_build_logs(logs)
        
        assert "Step 1" in result
        assert "Step 2" in result
        assert "Step 3" in result
    
    def test_collect_logs_empty(self):
        """Test collecting logs from empty iterator."""
        logs = []
        result = _collect_build_logs(logs)
        
        assert result == ""
    
    def test_collect_logs_exception_handling(self):
        """Test that exceptions during log collection are handled."""
        # Create a mock iterator that raises an exception
        class BadIterator:
            def __iter__(self):
                return self
            def __next__(self):
                raise ValueError("Unexpected error")
        
        result = _collect_build_logs(BadIterator())
        
        assert "Error processing build logs" in result
    
    def test_collect_logs_other_type(self):
        """Test collecting logs from other types (not dict, bytes, or string)."""
        logs = [
            {"stream": "Step 1\n"},
            12345,  # Integer
            {"stream": "Step 2\n"},
        ]
        result = _collect_build_logs(logs)
        
        assert "Step 1" in result
        assert "Step 2" in result
        assert "12345" in result  # Should be converted to string


@pytest.mark.unit
class TestIsRetryableError:
    """Tests for _is_retryable_error function."""
    
    def test_retryable_error_409(self):
        """Test that 409 Conflict is retryable."""
        mock_error = Mock(spec=APIError)
        mock_response = Mock()
        mock_response.status_code = 409
        mock_error.response = mock_response
        
        assert _is_retryable_error(mock_error) is True
    
    def test_retryable_error_500(self):
        """Test that 500 Internal Server Error is retryable."""
        mock_error = Mock(spec=APIError)
        mock_response = Mock()
        mock_response.status_code = 500
        mock_error.response = mock_response
        
        assert _is_retryable_error(mock_error) is True
    
    def test_non_retryable_error_404(self):
        """Test that 404 Not Found is not retryable."""
        mock_error = Mock(spec=APIError)
        mock_response = Mock()
        mock_response.status_code = 404
        mock_error.response = mock_response
        
        assert _is_retryable_error(mock_error) is False
    
    def test_non_api_error(self):
        """Test that non-APIError is not retryable."""
        mock_error = ValueError("Not an APIError")
        
        assert _is_retryable_error(mock_error) is False
    
    def test_api_error_no_response(self):
        """Test APIError without response attribute."""
        mock_error = Mock(spec=APIError)
        del mock_error.response
        
        # Should return True (fallback behavior)
        assert _is_retryable_error(mock_error) is True
    
    def test_api_error_no_status_code(self):
        """Test APIError with response but no status_code."""
        mock_error = Mock(spec=APIError)
        mock_error.response = {}
        
        # Should return True (fallback behavior)
        assert _is_retryable_error(mock_error) is True


@pytest.mark.unit
class TestRetryDockerOperation:
    """Tests for _retry_docker_operation function."""
    
    def test_retry_success_first_attempt(self):
        """Test successful operation on first attempt."""
        operation = Mock(return_value="success")
        
        result = _retry_docker_operation(operation, max_retries=3)
        
        assert result == "success"
        assert operation.call_count == 1
    
    def test_retry_success_after_retries(self):
        """Test successful operation after retries."""
        operation = Mock(side_effect=[
            APIError("Conflict", response=Mock(status_code=409)),
            APIError("Conflict", response=Mock(status_code=409)),
            "success"
        ])
        
        with patch('app.services.docker_service.time.sleep'):  # Mock sleep to speed up test
            result = _retry_docker_operation(operation, max_retries=3)
        
        assert result == "success"
        assert operation.call_count == 3
    
    def test_retry_exhausted(self):
        """Test that retries are exhausted after max attempts."""
        mock_error = APIError("Conflict", response=Mock(status_code=409))
        operation = Mock(side_effect=mock_error)
        
        with patch('app.services.docker_service.time.sleep'):
            with pytest.raises(APIError):
                _retry_docker_operation(operation, max_retries=3)
        
        assert operation.call_count == 3
    
    def test_non_retryable_error_immediate_fail(self):
        """Test that non-retryable errors fail immediately."""
        mock_error = ValueError("Not retryable")
        operation = Mock(side_effect=mock_error)
        
        with pytest.raises(ValueError):
            _retry_docker_operation(operation, max_retries=3)
        
        assert operation.call_count == 1


@pytest.mark.unit
class TestGetExternalPort:
    """Tests for get_external_port function."""
    
    def test_get_external_port_success(self):
        """Test successfully extracting external port."""
        mock_container = Mock(spec=Container)
        mock_container.id = "container-123"
        mock_container.name = "test-container"
        mock_container.attrs = {
            'NetworkSettings': {
                'Ports': {
                    '8080/tcp': [{'HostPort': '32768'}]
                }
            }
        }
        
        result = get_external_port(mock_container, 8080)
        
        assert result == 32768
    
    def test_get_external_port_not_found(self):
        """Test when port binding is not found."""
        mock_container = Mock(spec=Container)
        mock_container.id = "container-123"
        mock_container.name = "test-container"
        mock_container.attrs = {
            'NetworkSettings': {
                'Ports': {}
            }
        }
        
        result = get_external_port(mock_container, 8080)
        
        assert result is None
    
    def test_get_external_port_empty_binding(self):
        """Test when port binding exists but is empty."""
        mock_container = Mock(spec=Container)
        mock_container.id = "container-123"
        mock_container.name = "test-container"
        mock_container.attrs = {
            'NetworkSettings': {
                'Ports': {
                    '8080/tcp': []
                }
            }
        }
        
        result = get_external_port(mock_container, 8080)
        
        assert result is None
    
    def test_get_external_port_missing_attrs(self):
        """Test when container attrs are missing."""
        mock_container = Mock(spec=Container)
        mock_container.id = "container-123"
        mock_container.name = "test-container"
        mock_container.attrs = {}
        
        result = get_external_port(mock_container, 8080)
        
        assert result is None
    
    def test_get_external_port_key_error(self):
        """Test when KeyError occurs during port extraction."""
        mock_container = Mock(spec=Container)
        mock_container.id = "container-123"
        mock_container.name = "test-container"
        # Make attrs.get raise KeyError
        mock_container.attrs = Mock()
        mock_container.attrs.get.side_effect = KeyError("NetworkSettings")
        
        result = get_external_port(mock_container, 8080)
        
        assert result is None
    
    def test_get_external_port_value_error(self):
        """Test when ValueError occurs during port conversion."""
        mock_container = Mock(spec=Container)
        mock_container.id = "container-123"
        mock_container.name = "test-container"
        mock_container.attrs = {
            'NetworkSettings': {
                'Ports': {
                    '8080/tcp': [{'HostPort': 'invalid'}]
                }
            }
        }
        # Mock int() to raise ValueError
        with patch('builtins.int', side_effect=ValueError("invalid literal")):
            result = get_external_port(mock_container, 8080)
        
        assert result is None


@pytest.mark.unit
class TestGetContainerIpFromContainer:
    """Tests for get_container_ip_from_container function."""
    
    def test_get_ip_from_networks(self):
        """Test extracting IP from Networks."""
        mock_container = Mock(spec=Container)
        mock_container.id = "container-123"
        mock_container.name = "test-container"
        mock_container.attrs = {
            'NetworkSettings': {
                'Networks': {
                    'nvidia-network': {
                        'IPAddress': '172.17.0.2'
                    }
                }
            }
        }
        
        result = get_container_ip_from_container(mock_container)
        
        assert result == '172.17.0.2'
    
    def test_get_ip_from_fallback(self):
        """Test extracting IP from fallback IPAddress field."""
        mock_container = Mock(spec=Container)
        mock_container.id = "container-123"
        mock_container.name = "test-container"
        mock_container.attrs = {
            'NetworkSettings': {
                'IPAddress': '172.17.0.3'
            }
        }
        
        result = get_container_ip_from_container(mock_container)
        
        assert result == '172.17.0.3'
    
    def test_get_ip_not_found(self):
        """Test when IP is not found."""
        mock_container = Mock(spec=Container)
        mock_container.id = "container-123"
        mock_container.name = "test-container"
        mock_container.attrs = {
            'NetworkSettings': {}
        }
        
        result = get_container_ip_from_container(mock_container)
        
        assert result is None
    
    def test_get_ip_missing_attrs(self):
        """Test when container attrs are missing."""
        mock_container = Mock(spec=Container)
        mock_container.id = "container-123"
        mock_container.name = "test-container"
        mock_container.attrs = {}
        
        result = get_container_ip_from_container(mock_container)
        
        assert result is None
    
    def test_get_ip_key_error(self):
        """Test when KeyError occurs during IP extraction."""
        mock_container = Mock(spec=Container)
        mock_container.id = "container-123"
        mock_container.name = "test-container"
        # Make attrs.get raise KeyError
        mock_container.attrs = Mock()
        mock_container.attrs.get.side_effect = KeyError("NetworkSettings")
        
        result = get_container_ip_from_container(mock_container)
        
        assert result is None
    
    def test_get_ip_attribute_error(self):
        """Test when AttributeError occurs during IP extraction."""
        mock_container = Mock(spec=Container)
        mock_container.id = "container-123"
        mock_container.name = "test-container"
        # Make attrs not have get method
        mock_container.attrs = None
        
        result = get_container_ip_from_container(mock_container)
        
        assert result is None


@pytest.mark.unit
class TestBuildImageFromContext:
    """Tests for build_image_from_context function."""
    
    @patch('app.services.docker_service.docker')
    def test_build_image_success(self, mock_docker):
        """Test successful image build."""
        # Setup mocks
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_image = Mock()
        mock_logs = [
            {"stream": "Step 1/5\n"},
            {"stream": "Successfully built\n"}
        ]
        mock_client.images.build.return_value = (mock_image, mock_logs)
        mock_docker.from_env.return_value = mock_client
        
        result = build_image_from_context(
            context_dir="/tmp/context",
            image_name="myapp",
            image_tag="latest"
        )
        
        assert "Step 1/5" in result
        assert "Successfully built" in result
        mock_client.images.build.assert_called_once()
    
    @patch('app.services.docker_service.docker')
    def test_build_image_docker_connection_error(self, mock_docker):
        """Test build fails when Docker connection fails."""
        mock_docker.from_env.side_effect = Exception("Cannot connect")
        
        with pytest.raises(HTTPException) as exc_info:
            build_image_from_context(
                context_dir="/tmp/context",
                image_name="myapp",
                image_tag="latest"
            )
        
        assert exc_info.value.status_code == 500
        assert "Cannot connect to Docker" in str(exc_info.value.detail)
    
    @patch('app.services.docker_service.docker')
    def test_build_image_build_error(self, mock_docker):
        """Test build fails with BuildError."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_build_error = BuildError("Build failed", build_log=[{"error": "Build failed"}])
        mock_client.images.build.side_effect = mock_build_error
        mock_docker.from_env.return_value = mock_client
        
        with pytest.raises(HTTPException) as exc_info:
            build_image_from_context(
                context_dir="/tmp/context",
                image_name="myapp",
                image_tag="latest"
            )
        
        assert exc_info.value.status_code == 500
        assert "Docker build failed" in str(exc_info.value.detail)
    
    @patch('app.services.docker_service.docker')
    def test_build_image_api_error(self, mock_docker):
        """Test build fails with APIError."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.images.build.side_effect = APIError("API Error")
        mock_docker.from_env.return_value = mock_client
        
        with pytest.raises(HTTPException) as exc_info:
            build_image_from_context(
                context_dir="/tmp/context",
                image_name="myapp",
                image_tag="latest"
            )
        
        assert exc_info.value.status_code == 500
        assert "Docker API error" in str(exc_info.value.detail)
    
    @patch('app.services.docker_service.docker')
    def test_build_image_docker_exception(self, mock_docker):
        """Test build fails with DockerException."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.images.build.side_effect = DockerException("Docker error")
        mock_docker.from_env.return_value = mock_client
        
        with pytest.raises(HTTPException) as exc_info:
            build_image_from_context(
                context_dir="/tmp/context",
                image_name="myapp",
                image_tag="latest"
            )
        
        assert exc_info.value.status_code == 500
        assert "Docker error while building" in str(exc_info.value.detail)


@pytest.mark.unit
class TestRunContainer:
    """Tests for run_container function."""
    
    @patch('app.services.docker_service.docker')
    @patch('app.services.docker_service._retry_docker_operation')
    def test_run_container_success(self, mock_retry, mock_docker):
        """Test successful container run."""
        # Setup mocks
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_docker.from_env.return_value = mock_client
        
        mock_container = Mock(spec=Container)
        mock_container.id = "container-123"
        mock_container.name = "test-container"
        mock_container.attrs = {
            'NetworkSettings': {
                'Ports': {
                    '8080/tcp': [{'HostPort': '32768'}]
                },
                'Networks': {
                    'nvidia-network': {
                        'IPAddress': '172.17.0.2'
                    }
                }
            }
        }
        mock_container.reload = Mock()
        mock_retry.return_value = mock_container
        
        container, port, ip = run_container(
            image_name="myapp",
            image_tag="latest",
            container_name="test-container",
            env_vars={"ENV": "test"},
            internal_port=8080
        )
        
        assert container == mock_container
        assert port == 32768
        assert ip == '172.17.0.2'
    
    @patch('app.services.docker_service.docker')
    def test_run_container_docker_connection_error(self, mock_docker):
        """Test run fails when Docker connection fails."""
        mock_docker.from_env.side_effect = Exception("Cannot connect")
        
        with pytest.raises(HTTPException) as exc_info:
            run_container(
                image_name="myapp",
                image_tag="latest",
                container_name="test-container",
                env_vars={}
            )
        
        assert exc_info.value.status_code == 500
        assert "Cannot connect to docker DinD" in str(exc_info.value.detail)
    
    @patch('app.services.docker_service.docker')
    @patch('app.services.docker_service._retry_docker_operation')
    def test_run_container_port_extraction_failed(self, mock_retry, mock_docker):
        """Test run fails when port extraction fails."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_docker.from_env.return_value = mock_client
        
        mock_container = Mock(spec=Container)
        mock_container.id = "container-123"
        mock_container.name = "test-container"
        mock_container.attrs = {
            'NetworkSettings': {
                'Ports': {}
            }
        }
        mock_container.reload = Mock()
        mock_container.stop = Mock()
        mock_container.remove = Mock()
        mock_retry.return_value = mock_container
        
        with pytest.raises(HTTPException) as exc_info:
            run_container(
                image_name="myapp",
                image_tag="latest",
                container_name="test-container",
                env_vars={}
            )
        
        assert exc_info.value.status_code == 500
        assert "Failed to assign external port" in str(exc_info.value.detail)
    
    @patch('app.services.docker_service.docker')
    @patch('app.services.docker_service._retry_docker_operation')
    def test_run_container_ip_extraction_failed(self, mock_retry, mock_docker):
        """Test run fails when IP extraction fails."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_docker.from_env.return_value = mock_client
        
        mock_container = Mock(spec=Container)
        mock_container.id = "container-123"
        mock_container.name = "test-container"
        mock_container.attrs = {
            'NetworkSettings': {
                'Ports': {
                    '8080/tcp': [{'HostPort': '32768'}]
                },
                'Networks': {}
            }
        }
        mock_container.reload = Mock()
        mock_container.stop = Mock()
        mock_container.remove = Mock()
        mock_retry.return_value = mock_container
        
        with pytest.raises(HTTPException) as exc_info:
            run_container(
                image_name="myapp",
                image_tag="latest",
                container_name="test-container",
                env_vars={}
            )
        
        assert exc_info.value.status_code == 500
        assert "Could not obtain IP address" in str(exc_info.value.detail)
    
    @patch('app.services.docker_service.docker')
    @patch('app.services.docker_service._retry_docker_operation')
    def test_run_container_docker_exception(self, mock_retry, mock_docker):
        """Test run fails with DockerException."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_docker.from_env.return_value = mock_client
        mock_retry.side_effect = DockerException("Container run failed")
        
        with pytest.raises(HTTPException) as exc_info:
            run_container(
                image_name="myapp",
                image_tag="latest",
                container_name="test-container",
                env_vars={}
            )
        
        assert exc_info.value.status_code == 500
        assert "Docker container run failed" in str(exc_info.value.detail)


@pytest.mark.unit
class TestStartContainer:
    """Tests for start_container function."""
    
    @patch('app.services.docker_service.docker')
    @patch('app.services.docker_service._retry_docker_operation')
    def test_start_container_success(self, mock_retry, mock_docker):
        """Test successful container start."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        
        mock_container = Mock(spec=Container)
        mock_container.id = "container-123"
        mock_container.name = "test-container"
        mock_container.attrs = {
            'NetworkSettings': {
                'Ports': {
                    '8080/tcp': [{'HostPort': '32768'}]
                },
                'Networks': {
                    'nvidia-network': {
                        'IPAddress': '172.17.0.2'
                    }
                }
            }
        }
        mock_container.reload = Mock()
        mock_client.containers.get.return_value = mock_container
        
        container, port, ip = start_container("container-123", 8080)
        
        assert container == mock_container
        assert port == 32768
        assert ip == '172.17.0.2'
        mock_retry.assert_called_once()
    
    @patch('app.services.docker_service.docker')
    def test_start_container_not_found(self, mock_docker):
        """Test start fails when container not found."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_client.containers.get.side_effect = DockerException("Container not found")
        
        with pytest.raises(HTTPException) as exc_info:
            start_container("container-123", 8080)
        
        assert exc_info.value.status_code == 500
        assert "Failed to start" in str(exc_info.value.detail)
    
    @patch('app.services.docker_service.docker')
    @patch('app.services.docker_service._retry_docker_operation')
    def test_start_container_port_extraction_failed(self, mock_retry, mock_docker):
        """Test start fails when port extraction fails."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        
        mock_container = Mock(spec=Container)
        mock_container.id = "container-123"
        mock_container.name = "test-container"
        mock_container.attrs = {
            'NetworkSettings': {
                'Ports': {}
            }
        }
        mock_container.reload = Mock()
        mock_client.containers.get.return_value = mock_container
        
        with pytest.raises(HTTPException) as exc_info:
            start_container("container-123", 8080)
        
        assert exc_info.value.status_code == 500
        assert "Failed to get external port" in str(exc_info.value.detail)
    
    @patch('app.services.docker_service.docker')
    @patch('app.services.docker_service._retry_docker_operation')
    def test_start_container_ip_extraction_failed(self, mock_retry, mock_docker):
        """Test start fails when IP extraction fails."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        
        mock_container = Mock(spec=Container)
        mock_container.id = "container-123"
        mock_container.name = "test-container"
        mock_container.attrs = {
            'NetworkSettings': {
                'Ports': {
                    '8080/tcp': [{'HostPort': '32768'}]
                },
                'Networks': {}
            }
        }
        mock_container.reload = Mock()
        mock_client.containers.get.return_value = mock_container
        
        with pytest.raises(HTTPException) as exc_info:
            start_container("container-123", 8080)
        
        assert exc_info.value.status_code == 500
        assert "Failed to get IP address" in str(exc_info.value.detail)


@pytest.mark.unit
class TestStopContainer:
    """Tests for stop_container function."""
    
    @patch('app.services.docker_service.docker')
    @patch('app.services.docker_service._retry_docker_operation')
    def test_stop_container_success(self, mock_retry, mock_docker):
        """Test successful container stop."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        
        mock_container = Mock(spec=Container)
        mock_client.containers.get.return_value = mock_container
        
        result = stop_container("container-123")
        
        assert result == mock_container
        mock_retry.assert_called_once()
    
    @patch('app.services.docker_service.docker')
    def test_stop_container_not_found(self, mock_docker):
        """Test stop fails when container not found."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_client.containers.get.side_effect = DockerException("Container not found")
        
        with pytest.raises(HTTPException) as exc_info:
            stop_container("container-123")
        
        assert exc_info.value.status_code == 500
        assert "Failed to stop" in str(exc_info.value.detail)


@pytest.mark.unit
class TestDeleteContainer:
    """Tests for delete_container function."""
    
    @patch('app.services.docker_service.docker')
    @patch('app.services.docker_service._retry_docker_operation')
    def test_delete_container_success(self, mock_retry, mock_docker):
        """Test successful container deletion."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        
        mock_container = Mock(spec=Container)
        mock_container.stop = Mock()
        mock_client.containers.get.return_value = mock_container
        
        result = delete_container("container-123")
        
        assert result is True
        mock_container.stop.assert_called_once()
        mock_retry.assert_called_once()
    
    @patch('app.services.docker_service.docker')
    @patch('app.services.docker_service._retry_docker_operation')
    def test_delete_container_stop_fails(self, mock_retry, mock_docker):
        """Test container deletion when stop fails (should continue)."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        
        mock_container = Mock(spec=Container)
        mock_container.stop = Mock(side_effect=Exception("Stop failed"))
        mock_client.containers.get.return_value = mock_container
        
        result = delete_container("container-123")
        
        assert result is True
        mock_container.stop.assert_called_once()
        mock_retry.assert_called_once()  # Should still call remove
    
    @patch('app.services.docker_service.docker')
    def test_delete_container_not_found(self, mock_docker):
        """Test delete fails when container not found."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_client.containers.get.side_effect = DockerException("Container not found")
        
        with pytest.raises(HTTPException) as exc_info:
            delete_container("container-123")
        
        assert exc_info.value.status_code == 500
        assert "Failed to delete" in str(exc_info.value.detail)


@pytest.mark.unit
class TestGetContainerIp:
    """Tests for get_container_ip function."""
    
    @patch('app.services.docker_service.docker')
    def test_get_container_ip_success_from_networks(self, mock_docker):
        """Test successfully getting IP from Networks."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        
        mock_container = Mock(spec=Container)
        mock_container.reload = Mock()
        mock_container.attrs = {
            'NetworkSettings': {
                'Networks': {
                    'nvidia-network': {
                        'IPAddress': '172.17.0.2'
                    }
                }
            }
        }
        mock_client.containers.get.return_value = mock_container
        
        result = get_container_ip("container-123")
        
        assert result == '172.17.0.2'
    
    @patch('app.services.docker_service.docker')
    def test_get_container_ip_success_from_fallback(self, mock_docker):
        """Test successfully getting IP from fallback."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        
        mock_container = Mock(spec=Container)
        mock_container.reload = Mock()
        mock_container.attrs = {
            'NetworkSettings': {
                'IPAddress': '172.17.0.3'
            }
        }
        mock_client.containers.get.return_value = mock_container
        
        result = get_container_ip("container-123")
        
        assert result == '172.17.0.3'
    
    @patch('app.services.docker_service.docker')
    def test_get_container_ip_not_found(self, mock_docker):
        """Test get IP fails when IP not found."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        
        mock_container = Mock(spec=Container)
        mock_container.reload = Mock()
        mock_container.attrs = {
            'NetworkSettings': {}
        }
        mock_client.containers.get.return_value = mock_container
        
        with pytest.raises(HTTPException) as exc_info:
            get_container_ip("container-123")
        
        assert exc_info.value.status_code == 500
        assert "Could not find IP address" in str(exc_info.value.detail)
    
    @patch('app.services.docker_service.docker')
    def test_get_container_ip_docker_exception(self, mock_docker):
        """Test get IP fails with DockerException."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_client.containers.get.side_effect = DockerException("Container not found")
        
        with pytest.raises(HTTPException) as exc_info:
            get_container_ip("container-123")
        
        assert exc_info.value.status_code == 500
        assert "Failed to get container IP" in str(exc_info.value.detail)
