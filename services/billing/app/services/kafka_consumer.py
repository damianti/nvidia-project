import json
import asyncio
from typing import Dict
from confluent_kafka import Consumer
import logging
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.schemas.billing import ContainerEventData
from app.services.billing_service import process_container_started, process_container_stopped
from app.utils.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_CONSUMER_GROUP, SERVICE_NAME
from app.database.config import SessionLocal

logger = logging.getLogger(SERVICE_NAME)


class KafkaConsumerService:
    def __init__(self) -> None:
        self.running = False
        self.consumer = None
        self.message_count = 0
        self.processed_success = 0
        self.processed_failures = 0
        
        # Dispatch map of event -> handler
        self._event_handlers = {
            "container.created": self._on_container_started,  # Treat created as started
            "container.started": self._on_container_started,
            "container.stopped": self._on_container_stopped,
            "container.deleted": self._on_container_stopped,  # Treat deleted as stopped
        }

    async def start(self):
        """
        Start the Kafka consumer in an async loop.
        
        Runs indefinitely until stop() is called.
        Uses asyncio.to_thread() to run the blocking consumer.poll() without blocking the event loop.
        """
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
                # Run the blocking poll() in a separate thread to not block the event loop
                message = await asyncio.to_thread(self.consumer.poll, 1.0)
                
                if message is None:
                    continue
                elif message.error():
                    logger.error(
                        "kafka.consumer_error",
                        extra={"error": str(message.error())}
                    )
                else:
                    await self.process_message(message)
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

    async def process_message(self, message: Dict):
        """Processes a Kafka message and dispatch to event handler"""
        try:
            raw_data = json.loads(message.value())
            container_data = ContainerEventData(**raw_data)
            
            logger.info(
                "kafka.processing_event",
                extra={
                    "event": container_data.event,
                    "container_id": container_data.container_id,
                }
            )

            handler = self._event_handlers.get(container_data.event)
            
            if handler:
                await handler(container_data)
                self.message_count += 1
                self.processed_success += 1
            else:
                logger.warning(
                    "kafka.unknown_event",
                    extra={
                        "event": container_data.event,
                        "container_id": container_data.container_id
                    }
                )

        except json.JSONDecodeError as e:
            logger.error(
                "kafka.json_decode_error",
                extra={
                    "error": str(e),
                    "raw_message": message.value()[:200] if hasattr(message, 'value') else None
                }
            )
            self.processed_failures += 1
        except ValidationError as e:
            logger.error(
                "kafka.validation_error",
                extra={
                    "error": str(e),
                    "errors": e.errors(),
                    "raw_data": raw_data if 'raw_data' in locals() else None
                }
            )
            self.processed_failures += 1
        except Exception as e:
            logger.error(
                "kafka.process_message_error",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True
            )
            self.processed_failures += 1

    async def _on_container_started(self, data: ContainerEventData) -> None:
        """Handle container.started or container.created events"""
        # Create a new DB session for this event
        db = SessionLocal()
        try:
            process_container_started(db, data)
            logger.info(
                "billing.container_started_processed",
                extra={
                    "container_id": data.container_id,
                    "user_id": data.user_id,
                    "image_id": data.image_id
                }
            )
        except Exception as e:
            logger.error(
                "billing.container_started_failed",
                extra={
                    "container_id": data.container_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            # Don't re-raise - we want to continue processing other messages
        finally:
            db.close()

    async def _on_container_stopped(self, data: ContainerEventData) -> None:
        """Handle container.stopped or container.deleted events"""
        # Create a new DB session for this event
        db = SessionLocal()
        try:
            process_container_stopped(db, data)
            logger.info(
                "billing.container_stopped_processed",
                extra={
                    "container_id": data.container_id,
                    "user_id": data.user_id,
                    "image_id": data.image_id
                }
            )
        except Exception as e:
            logger.error(
                "billing.container_stopped_failed",
                extra={
                    "container_id": data.container_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            # Don't re-raise - we want to continue processing other messages
        finally:
            db.close()

