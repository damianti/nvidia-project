import os
import json
from typing import Any, Dict, Optional
from confluent_kafka import Consumer
import logging

logger = logging.getLogger(__name__)
from app.services.container_pool import ContainerPool, ContainerData


class KafkaConsumerService:
    def __init__(self, pool: ContainerPool) -> None:
        self.pool = pool
        self.running = False
        self.consumer = None
        # Dispatch map de evento -> handler
        self._event_handlers = {
            "container.created": self._on_container_created,
            "container.started": self._on_container_started,
            "container.stopped": self._on_container_stopped,
            "container.deleted": self._on_container_deleted,
        }

    def start(self):
        """Starts the Kafka consumer"""
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

        config = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': 'load-balancers',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True
        }

        self.consumer = Consumer(config)
        self.consumer.subscribe(['container-lifecycle'])
        self.running = True

        logger.info(f"Kafka Consumer started. Connecting to: {bootstrap_servers}")
        logger.info("Waiting for messages from topic 'container-lifecycle'...")

        while self.running:
            try:
                message = self.consumer.poll(timeout=1.0)
                if message is None:
                    continue
                elif message.error():
                    logger.error(f"Consumer error: {message.error()}")
                else:
                    self.process_message(message)
            except KeyboardInterrupt:
                logger.info("Stopping consumer...")
                self.running = False
            except Exception as e:
                logger.error(f"Unexpected error in consumer: {e}")

    def stop(self):
        """Stops the Kafka consumer"""
        self.running = False
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka Consumer closed")            


    def process_message(self, message: Dict):
        """Processes a Kafka message and updates the container pool"""
        try:
            data = json.loads(message.value)
            event = data.get("event")
            if not event:
                logger.warning("Message without 'event' field received")
                return

            logger.info(f"Processing event: {event} for container {data.get('container_id', 'unknown')}")

            handler = self._event_handlers.get(event)
            if handler is None:
                logger.warning(f"Unknown event: {event}")
                return

            handler(data)

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON message: {e}")
        except KeyError as e:
            logger.error(f"Missing field in message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _extract_core_fields(self, data: Dict[str, Any]):
        image_id = data["image_id"]
        container_id = data["container_id"]
        external_port = data["port"]
        return image_id, container_id, external_port

    def _on_container_created(self, data: Dict[str, Any]) -> None:
        image_id, container_id, external_port = self._extract_core_fields(data)
        container_data = ContainerData(
            container_id=container_id,
            image_id=image_id,
            external_port=external_port,
            status="running"
        )
        self.pool.add_container(container_data)
        logger.info(f"Container {container_id} added to pool for image {image_id}")

    def _on_container_started(self, data: Dict[str, Any]) -> None:
        image_id, container_id, external_port = self._extract_core_fields(data)
        existing = self.pool.find_container(image_id, container_id)
        if not existing:
            container_data = ContainerData(
                container_id=container_id,
                image_id=image_id,
                external_port=external_port,
                status="running"
            )
            self.pool.add_container(container_data)
            logger.info(f"Container {container_id} added to pool for image {image_id}")
        else:
            self.pool.start_container(image_id, container_id)
            logger.info(f"Container {container_id} started in pool for image {image_id}")

    def _on_container_stopped(self, data: Dict[str, Any]) -> None:
        image_id, container_id, _ = self._extract_core_fields(data)
        self.pool.stop_container(image_id, container_id)
        logger.info(f"Container {container_id} stopped in pool for image {image_id}")

    def _on_container_deleted(self, data: Dict[str, Any]) -> None:
        image_id, container_id, _ = self._extract_core_fields(data)
        self.pool.remove_container(image_id, container_id)
        logger.info(f"Container {container_id} removed from pool for image {image_id}")






