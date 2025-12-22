from unittest.mock import Mock, MagicMock

def make_docker_build_fail(msg="Docker build failed"):
    mock_build = MagicMock()
    mock_build.side_effect = Exception(msg)
    return mock_build

def make_docker_build_success(logs="Build OK"):
    mock_build = MagicMock()
    mock_build.return_value = logs
    return mock_build

def make_kafka_producer():
    producer = Mock()
    producer.produce_json = Mock()
    return producer