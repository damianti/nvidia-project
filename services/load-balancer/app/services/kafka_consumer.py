import json
from typing import Any, Dict
from confluent_kafka import Consumer
import logging

from app.services.container_pool import ContainerPool, ContainerData
from app.services.website_mapping import WebsiteMapping
from app.utils.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_CONSUMER_GROUP, SERVICE_NAME
logger = logging.getLogger(SERVICE_NAME)

# TODO implement event: image deleted, change url from image.
class KafkaConsumerService:
    def __init__(self, pool: ContainerPool, website_map: WebsiteMapping) -> None:
        self.pool = pool
        self.running = False
        self.consumer = None
        self.website_map = website_map
        # Dispatch map de evento -> handler
        self._event_handlers = {
            "container.created": self._on_container_created,
            "container.started": self._on_container_started,
            "container.stopped": self._on_container_stopped,
            "container.deleted": self._on_container_deleted,
        }

    def start(self):
        """Starts the Kafka consumer"""
        
        config = {
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'group.id': KAFKA_CONSUMER_GROUP,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True
        }

        self.consumer = Consumer(config)
        self.consumer.subscribe(['container-lifecycle'])
        self.running = True

        logger.info(
            "kafka.consumer_started",
            extra={"bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS}
        )
        logger.info(
            "kafka.waiting_for_messages",
            extra={"topic": "container-lifecycle"}
        )

        while self.running:
            try:
                message = self.consumer.poll(timeout=1.0)
                if message is None:
                    continue
                elif message.error():
                    logger.error(
                        "kafka.consumer_error",
                        extra={"error": str(message.error())}
                    )
                else:
                    self.process_message(message)
            except KeyboardInterrupt:
                logger.info("kafka.stopping_consumer")
                self.running = False
            except Exception as e:
                logger.error(
                    "kafka.unexpected_error",
                    extra={"error": str(e), "error_type": type(e).__name__}
                )

    def stop(self):
        """Stops the Kafka consumer"""
        self.running = False
        if self.consumer:
            self.consumer.close()
            logger.info("kafka.consumer_closed")            


    def process_message(self, message: Dict):
        """Processes a Kafka message and updates the container pool"""
        try:
            data = json.loads(message.value())
            event = data.get("event")
            if not event:
                logger.warning("kafka.message_missing_event")
                return

            logger.info(
                "kafka.processing_event",
                extra={
                    "event": event,
                    "container_id": data.get("container_id", "unknown"),
                }
            )

            handler = self._event_handlers.get(event)
            if handler is None:
                logger.warning(
                    "kafka.unknown_event",
                    extra={"event": event}
                )
                return

            handler(data)

        except json.JSONDecodeError as e:
            logger.error(
                "kafka.json_decode_error",
                extra={"error": str(e)}
            )
        except KeyError as e:
            logger.error(
                "kafka.missing_field",
                extra={"field": str(e)}
            )
        except Exception as e:
            logger.error(
                "kafka.process_message_error",
                extra={"error": str(e), "error_type": type(e).__name__}
            )

    def _extract_core_fields(self, data: Dict[str, Any]):
        image_id = data["image_id"]
        container_id = data["container_id"]
        external_port = data.get("port")
        website_url = data.get("website_url")
        container_name = data.get("container_name")  # Container name (optional)
        return image_id, container_id, external_port, website_url, container_name

    def _on_container_created(self, data: Dict[str, Any]) -> None:
        image_id, container_id, external_port, website_url, container_name = self._extract_core_fields(data)
        logger.info(
            "kafka.container_created",
            extra={
                "container_id": container_id,
                "container_name": container_name,
                "image_id": image_id,
                "website_url": website_url,
            }
        )
        container_data = ContainerData(
            container_id=container_id,
            image_id=image_id,
            external_port=external_port,
            status="running",
            container_name=container_name
        )
        if website_url:
            self.website_map.add(website_url, image_id)
        else:
            logger.warning(
                "kafka.created_missing_website_url",
                extra={"container_id": container_id}
            )
        self.pool.add_container(container_data)
        logger.info(
            "pool.container_added",
            extra={"container_id": container_id, "image_id": image_id}
        )

    def _on_container_started(self, data: Dict[str, Any]) -> None:
        image_id, container_id, external_port, website_url, container_name = self._extract_core_fields(data)
        logger.info(
            "kafka.container_started",
            extra={
                "container_id": container_id,
                "container_name": container_name,
                "image_id": image_id,
                "website_url": website_url,
            }
        )
        existing = self.pool.find_container(image_id, container_id)
        if not existing:
            container_data = ContainerData(
                container_id=container_id,
                image_id=image_id,
                external_port=external_port,
                status="running",
                container_name=container_name
            )
            if website_url:
                self.website_map.add(website_url, image_id)
            else:
                logger.warning(
                    "kafka.started_missing_website_url",
                    extra={"container_id": container_id}
                )
            self.pool.add_container(container_data)
            logger.info(
                "pool.container_added",
                extra={"container_id": container_id, "image_id": image_id}
            )
        else:
            self.pool.start_container(image_id, container_id)
            logger.info(
                "pool.container_started",
                extra={"container_id": container_id, "image_id": image_id}
            )

    def _on_container_stopped(self, data: Dict[str, Any]) -> None:
        image_id, container_id, external_port, website_url, container_name = self._extract_core_fields(data)
        self.pool.stop_container(image_id, container_id)
        logger.info(
            "pool.container_stopped",
            extra={
                "container_id": container_id,
                "container_name": container_name,
                "image_id": image_id
            }
        )

    def _on_container_deleted(self, data: Dict[str, Any]) -> None:
        image_id, container_id, external_port, website_url, container_name = self._extract_core_fields(data)
        self.pool.remove_container(image_id, container_id)
        # Si no quedan contenedores para la imagen, limpiar mapping (si se recibió website_url)
        if not self.pool.get_containers(image_id) and website_url:
            self.website_map.remove_image(website_url, image_id)
        logger.info(
            "pool.container_removed",
            extra={
                "container_id": container_id,
                "container_name": container_name,
                "image_id": image_id
            }
        )






