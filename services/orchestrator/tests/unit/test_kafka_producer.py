"""
Unit tests for kafka_producer service.
"""

import pytest
import os
from unittest.mock import Mock, patch

from app.services.kafka_producer import KafkaProducerSingleton


@pytest.mark.unit
class TestKafkaProducerSingleton:
    """Tests for KafkaProducerSingleton class."""

    def test_singleton_instance(self):
        """Test that instance() returns the same instance."""
        # Reset singleton for test
        KafkaProducerSingleton._instance = None

        instance1 = KafkaProducerSingleton.instance()
        instance2 = KafkaProducerSingleton.instance()

        assert instance1 is instance2
        assert isinstance(instance1, KafkaProducerSingleton)

    @patch.dict(
        os.environ,
        {"KAFKA_BOOTSTRAP_SERVERS": "test-kafka:9092", "HOSTNAME": "test-host"},
    )
    @patch("app.services.kafka_producer.Producer")
    def test_init_config(self, mock_producer_class):
        """Test that __init__ configures producer correctly."""
        KafkaProducerSingleton._instance = None

        KafkaProducerSingleton.instance()

        # Verify Producer was called with correct config
        mock_producer_class.assert_called_once()
        call_args = mock_producer_class.call_args[0][0]

        assert call_args["bootstrap.servers"] == "test-kafka:9092"
        assert call_args["client.id"] == "test-host"
        assert call_args["acks"] == "all"
        assert call_args["enable.idempotence"] is True
        assert call_args["retries"] == 5

    @patch.dict(os.environ, {}, clear=True)
    @patch("app.services.kafka_producer.Producer")
    def test_init_default_config(self, mock_producer_class):
        """Test that __init__ uses default config when env vars not set."""
        KafkaProducerSingleton._instance = None

        KafkaProducerSingleton.instance()

        call_args = mock_producer_class.call_args[0][0]
        assert call_args["bootstrap.servers"] == "kafka:9092"
        assert call_args["client.id"] == "orchestrator-producer"

    @patch("app.services.kafka_producer.Producer")
    def test_produce_json_success(self, mock_producer_class):
        """Test produce_json with valid data."""
        KafkaProducerSingleton._instance = None

        mock_producer = Mock()
        mock_producer.produce = Mock()
        mock_producer.poll = Mock()
        mock_producer_class.return_value = mock_producer

        instance = KafkaProducerSingleton.instance()

        test_data = {"event": "test", "data": {"key": "value"}}
        instance.produce_json("test-topic", "test-key", test_data)

        # Verify produce was called
        mock_producer.produce.assert_called_once()
        call_kwargs = mock_producer.produce.call_args[1]

        assert call_kwargs["topic"] == "test-topic"
        assert call_kwargs["key"] == "test-key"
        assert '"event": "test"' in call_kwargs["value"]  # JSON string
        assert call_kwargs["callback"] == instance.delivery_report

        # Verify poll was called
        mock_producer.poll.assert_called_once_with(0)

    @patch("app.services.kafka_producer.Producer")
    def test_produce_json_with_none_key(self, mock_producer_class):
        """Test produce_json with None key."""
        KafkaProducerSingleton._instance = None

        mock_producer = Mock()
        mock_producer.produce = Mock()
        mock_producer.poll = Mock()
        mock_producer_class.return_value = mock_producer

        instance = KafkaProducerSingleton.instance()

        instance.produce_json("test-topic", None, {"data": "test"})

        call_kwargs = mock_producer.produce.call_args[1]
        assert call_kwargs["key"] is None

    @patch("app.services.kafka_producer.logger")
    @patch("app.services.kafka_producer.Producer")
    def test_delivery_report_success(self, mock_producer_class, mock_logger):
        """Test delivery_report callback on success."""
        KafkaProducerSingleton._instance = None

        mock_producer = Mock()
        mock_producer_class.return_value = mock_producer

        instance = KafkaProducerSingleton.instance()

        # Create mock message
        mock_msg = Mock()
        mock_msg.topic.return_value = "test-topic"
        mock_msg.partition.return_value = 0
        mock_msg.offset.return_value = 12345

        # Call delivery_report with no error
        instance.delivery_report(None, mock_msg)

        # Verify success log
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args[0][0] == "kafka.delivery.success"
        assert call_args[1]["extra"]["topic"] == "test-topic"
        assert call_args[1]["extra"]["partition"] == 0
        assert call_args[1]["extra"]["offset"] == 12345

    @patch("app.services.kafka_producer.logger")
    @patch("app.services.kafka_producer.Producer")
    def test_delivery_report_error(self, mock_producer_class, mock_logger):
        """Test delivery_report callback on error."""
        KafkaProducerSingleton._instance = None

        mock_producer = Mock()
        mock_producer_class.return_value = mock_producer

        instance = KafkaProducerSingleton.instance()

        # Create mock error and message
        mock_error = Mock()
        mock_error.__str__ = Mock(return_value="Test error")

        mock_msg = Mock()
        mock_msg.topic.return_value = "test-topic"
        mock_msg.partition.return_value = 1

        # Call delivery_report with error
        instance.delivery_report(mock_error, mock_msg)

        # Verify error log
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert call_args[0][0] == "kafka.delivery.failed"
        assert "error" in call_args[1]["extra"]
        assert call_args[1]["extra"]["topic"] == "test-topic"
        assert call_args[1]["extra"]["partition"] == 1

    @patch("app.services.kafka_producer.logger")
    @patch("app.services.kafka_producer.Producer")
    def test_delivery_report_error_no_message(self, mock_producer_class, mock_logger):
        """Test delivery_report callback on error with no message."""
        KafkaProducerSingleton._instance = None

        mock_producer = Mock()
        mock_producer_class.return_value = mock_producer

        instance = KafkaProducerSingleton.instance()

        mock_error = Mock()
        mock_error.__str__ = Mock(return_value="Test error")

        # Call delivery_report with error but no message
        instance.delivery_report(mock_error, None)

        # Verify error log with unknown topic
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert call_args[1]["extra"]["topic"] == "unknown"
        assert call_args[1]["extra"]["partition"] is None

    @patch("app.services.kafka_producer.Producer")
    def test_flush(self, mock_producer_class):
        """Test flush method."""
        KafkaProducerSingleton._instance = None

        mock_producer = Mock()
        mock_producer.flush = Mock()
        mock_producer_class.return_value = mock_producer

        instance = KafkaProducerSingleton.instance()

        instance.flush(timeout=10.0)

        mock_producer.flush.assert_called_once_with(10.0)

    @patch("app.services.kafka_producer.Producer")
    def test_flush_default_timeout(self, mock_producer_class):
        """Test flush method with default timeout."""
        KafkaProducerSingleton._instance = None

        mock_producer = Mock()
        mock_producer.flush = Mock()
        mock_producer_class.return_value = mock_producer

        instance = KafkaProducerSingleton.instance()

        instance.flush()

        mock_producer.flush.assert_called_once_with(5.0)
