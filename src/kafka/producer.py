"""Kafka producer for sending SQL generation requests."""

import json
import uuid
from typing import Dict, Optional

from aiokafka import AIOKafkaProducer
from loguru import logger

from src.config.settings import settings
from src.utils.errors import KafkaError


class KafkaProducer:
    """Kafka producer for sending SQL generation requests."""

    def __init__(
        self,
        bootstrap_servers: str = None,
        topic: str = None,
    ):
        """Initialize the Kafka producer.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers. Defaults to settings.kafka.bootstrap_servers.
            topic: Kafka topic to produce to. Defaults to settings.kafka.topic.
        """
        self.bootstrap_servers = bootstrap_servers or settings.kafka.bootstrap_servers
        self.topic = topic or settings.kafka.topic
        self.producer = None
        
        logger.info(
            f"Initialized Kafka producer for topic {self.topic} "
            f"with bootstrap servers {self.bootstrap_servers}"
        )
    
    async def start(self):
        """Start the Kafka producer.
        
        Raises:
            KafkaError: If producer initialization fails.
        """
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda m: json.dumps(m).encode("utf-8"),
            )
            
            await self.producer.start()
            logger.info(f"Started Kafka producer for topic {self.topic}")
        except Exception as e:
            error_msg = f"Failed to start Kafka producer: {str(e)}"
            logger.error(error_msg)
            raise KafkaError(error_msg, details={"original_error": str(e)})
    
    async def stop(self):
        """Stop the Kafka producer."""
        if self.producer:
            await self.producer.stop()
            logger.info(f"Stopped Kafka producer for topic {self.topic}")
    
    async def send_message(
        self,
        filter_text: str,
        constraint_text: str,
        request_hash: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> str:
        """Send a message to the Kafka topic.
        
        Args:
            filter_text: Filter text for SQL generation.
            constraint_text: Constraint text for SQL generation.
            request_hash: Optional request hash. If not provided, a UUID will be generated.
            headers: Optional headers to include with the message.
            
        Returns:
            The request hash.
            
        Raises:
            KafkaError: If sending the message fails.
        """
        if not self.producer:
            raise KafkaError("Producer not started")
        
        # Generate a request hash if not provided
        request_hash = request_hash or str(uuid.uuid4())
        
        # Create the message
        message = {
            "filter": filter_text,
            "constraint": constraint_text,
            "request_hash": request_hash,
        }
        
        # Add headers if provided
        if headers:
            message["headers"] = headers
        
        try:
            # Send the message
            await self.producer.send_and_wait(
                topic=self.topic,
                value=message,
            )
            
            logger.info(f"Sent message with request_hash {request_hash} to topic {self.topic}")
            return request_hash
        except Exception as e:
            error_msg = f"Failed to send message to Kafka: {str(e)}"
            logger.error(error_msg)
            raise KafkaError(error_msg, details={"original_error": str(e), "request_hash": request_hash})


async def send_sql_generation_request(
    filter_text: str,
    constraint_text: str,
    request_hash: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
) -> str:
    """Send a SQL generation request to the Kafka topic.
    
    This is a convenience function that creates a producer, sends a message, and stops the producer.
    
    Args:
        filter_text: Filter text for SQL generation.
        constraint_text: Constraint text for SQL generation.
        request_hash: Optional request hash. If not provided, a UUID will be generated.
        headers: Optional headers to include with the message.
        
    Returns:
        The request hash.
        
    Raises:
        KafkaError: If sending the message fails.
    """
    producer = KafkaProducer()
    
    try:
        await producer.start()
        request_hash = await producer.send_message(
            filter_text=filter_text,
            constraint_text=constraint_text,
            request_hash=request_hash,
            headers=headers,
        )
        return request_hash
    finally:
        await producer.stop()
