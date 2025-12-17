import json
import asyncio
from typing import Dict
from confluent_kafka import Consumer
import logging
from pydantic import ValidationError


from app.schemas.container_data import ContainerEventData
from app.services import consul_client 
from app.utils.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_CONSUMER_GROUP, SERVICE_NAME
logger = logging.getLogger(SERVICE_NAME)

# TODO implement event: image deleted, change url from image.
class KafkaConsumerService:
    def __init__(self) -> None:
        self.running = False
        self.consumer = None
        self.message_count = 0 
        self.registration_success = 0
        self.registration_failures = 0
        
        # Dispatch map of event -> handler (all async now)
        self._event_handlers = {
            "container.created": self._on_container_created,
            "container.started": self._on_container_started,
            "container.stopped": self._on_container_stopped,
            "container.deleted": self._on_container_deleted,
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
            
            # All handlers are async now
            await handler(container_data)

        except json.JSONDecodeError as e:
            logger.error(
                "kafka.json_decode_error",
                extra={
                    "error": str(e),
                    "raw_message": message.value()[:200]
                }
            )
        except ValidationError as e:
            logger.error(
                "kafka.validation_error",
                extra={
                    "error": str(e),
                    "errors": e.errors(),
                    "raw_data": raw_data
                }
            )
        except Exception as e:
            logger.error(
                "kafka.process_message_error",
                extra={"error": str(e), "error_type": type(e).__name__}
            )

    async def _on_container_created(self, data: ContainerEventData) -> None:
        logger.info(
            "kafka.container_created",
            extra={
                "container_id": data.container_id,
                "container_name": data.container_name,
                "image_id": data.image_id,
                "app_hostname": data.app_hostname,
            }
        )
        success = await consul_client.register_service(data)

        self.message_count += 1
        if success:
            self.registration_success += 1
            logger.info(
                "consul.registration_success",
                extra={
                    "container_id": data.container_id,
                    "container_name": data.container_name
                }
            )
        else:
            self.registration_failures += 1
            logger.error(
                "consul.registration_failed",
                extra={
                    "container_id": data.container_id,
                    "container_name": data.container_name
                }
            )
      
      
    async def _on_container_deleted(self, data: ContainerEventData) -> None:
        logger.info(
            "kafka.container_deleted",
            extra={
                "container_id": data.container_id,
                "container_name": data.container_name,
                "image_id": data.image_id,
                "app_hostname": data.app_hostname,
            }
        )
        success = await consul_client.deregister_service(data.container_id)
        if success:
            logger.info(
                "consul.deregistration_success",
                extra={"container_id": data.container_id}
            )
        else:
            logger.error(
                "consul.deregistration_failed",
                extra={"container_id": data.container_id}
            )

    async def _on_container_started(self, data: ContainerEventData) -> None:
        logger.info(
            "kafka.container_started",
            extra={
                "container_id": data.container_id,
                "container_name": data.container_name,
                "note": "Consul will detect via health check"
            }
        )

    async def _on_container_stopped(self, data: ContainerEventData) -> None:
        logger.info(
            "kafka.container_stopped",
            extra={
                "container_id": data.container_id,
                "container_name": data.container_name,
                "note": "Consul will detect via health check"
            }
        )
