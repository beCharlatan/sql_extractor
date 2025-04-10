"""Kafka producer for sending SQL generation results."""

import json
from typing import Dict, Any, Optional

from aiokafka import AIOKafkaProducer
from loguru import logger

from src.config.settings import settings
from src.utils.errors import KafkaError


class ResultProducer:
    """Kafka producer for sending SQL generation results."""

    def __init__(
        self,
        bootstrap_servers: str = None,
        topic: str = None,
    ):
        """Initialize the result producer.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers. Defaults to settings.kafka.bootstrap_servers.
            topic: Kafka topic to produce to. Defaults to settings.kafka.result_topic.
        """
        self.bootstrap_servers = bootstrap_servers or settings.kafka.bootstrap_servers
        self.topic = topic or settings.kafka.result_topic
        self.producer = None
        
        logger.info(
            f"Initialized result producer for topic {self.topic} "
            f"with bootstrap servers {self.bootstrap_servers}"
        )
    
    async def start(self):
        """Start the result producer.
        
        Raises:
            KafkaError: If producer initialization fails.
        """
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda m: json.dumps(m).encode("utf-8"),
            )
            
            await self.producer.start()
            logger.info(f"Started result producer for topic {self.topic}")
        except Exception as e:
            error_msg = f"Failed to start result producer: {str(e)}"
            logger.error(error_msg)
            raise KafkaError(error_msg, details={"original_error": str(e)})
    
    async def stop(self):
        """Stop the result producer."""
        if self.producer:
            await self.producer.stop()
            logger.info(f"Stopped result producer for topic {self.topic}")
    
    async def send_result(
        self,
        sql_components: Dict[str, Any],
        request_hash: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Send a SQL generation result to the Kafka topic.
        
        Args:
            sql_components: Generated SQL components.
            request_hash: Hash of the original request.
            headers: Optional headers to include with the message.
            
        Raises:
            KafkaError: If sending the result fails.
        """
        if not self.producer:
            raise KafkaError("Result producer not started")
        
        # Create the result message
        message = {
            "sql_components": sql_components,
            "request_hash": request_hash,
        }
        
        # Add headers if provided
        if headers:
            message["headers"] = headers
        
        try:
            # Send the result
            await self.producer.send_and_wait(
                topic=self.topic,
                value=message,
                key=request_hash
            )
            
            logger.info(f"Sent SQL generation result with request_hash {request_hash} to topic {self.topic}")
        except Exception as e:
            error_msg = f"Failed to send SQL generation result: {str(e)}"
            logger.error(error_msg)
            raise KafkaError(error_msg, details={"original_error": str(e), "request_hash": request_hash})
