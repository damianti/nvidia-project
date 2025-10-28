import os
import json
from typing import Any, Dict, Optional
from confluent_kafka import Producer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaProducerSingleton:
    _instance: Optional["KafkaProducerSingleton"] = None
    
    def __init__(self) -> None:
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        client_id = os.getenv("HOSTNAME", "orchestrator-producer")


        config = {
            "bootstrap.servers": bootstrap_servers,  
            "client.id": client_id,
            "acks": "all",
            "retry.idempotence": True,
            "retries": 5,
            "retry.backoff.ms": 200,
            "linger.ms": 10,
            "batch.size": 64_000,
            "compression.type": "lz4",
        }
        self._producer = Producer(config)

    @classmethod
    def instance(cls) -> "KafkaProducerSingleton":
        if cls._instance is None:
            cls._instance = KafkaProducerSingleton()
        return cls._instance

    def produce_json(self, data= Dict[str,str]):

        json.dumps(dict)

    def delivery_report(self, err, msg) -> None:

        if err is not None:
            logger.error(f"[KAFKA] Delivery failed: {err}")

        else:
            logger.info(f"[KAFKA] Delivered to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}")



    

    