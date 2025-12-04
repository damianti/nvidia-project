import os
import json
from typing import Any, Dict, Optional
from confluent_kafka import Producer
import logging

logger = logging.getLogger("orchestrator")

class KafkaProducerSingleton:
    _instance: Optional["KafkaProducerSingleton"] = None
    
    def __init__(self) -> None:
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        client_id = os.getenv("HOSTNAME", "orchestrator-producer")


        config = {
            "bootstrap.servers": bootstrap_servers,  
            "client.id": client_id,
            "acks": "all",
            "enable.idempotence": True,
            "retries": 5,
            "retry.backoff.ms": 200,
            "linger.ms": 10,
            "batch.size": 64000,
            "compression.type": "lz4",
            "message.timeout.ms": 10000,
        }
        self._producer = Producer(config)

    @classmethod
    def instance(cls) -> "KafkaProducerSingleton":
        if cls._instance is None:
            cls._instance = KafkaProducerSingleton()
        return cls._instance

    def produce_json(self, topic: str, key: Optional[str], value: Dict[str, Any]) -> None:
        payload = json.dumps(value)
        self._producer.produce(topic=topic, key=key, value=payload, callback=self.delivery_report)
        self._producer.poll(0)
    def delivery_report(self, err, msg) -> None:

        if err is not None:
            logger.error(
                "kafka.delivery.failed",
                extra={
                    "error": str(err),
                    "topic": msg.topic() if msg else "unknown",
                    "partition": msg.partition() if msg else None
                }
            )

        else:
            logger.info(
                "kafka.delivery.success",
                extra={
                    "topic": msg.topic(),
                    "partition": msg.partition(),
                    "offset": msg.offset()
                }
            )


    def flush(self, timeout: float = 5.0) -> None:
        self._producer.flush(timeout)

    

    