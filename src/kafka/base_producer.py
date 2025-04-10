"""Базовый класс Kafka-продюсера для отправки сообщений."""

import json
import asyncio
from typing import Any, Dict, Optional

from aiokafka import AIOKafkaProducer
from loguru import logger

from src.config.settings import settings
from src.utils.errors import KafkaError


class BaseKafkaProducer:
    """Базовый класс Kafka-продюсера для общей инфраструктуры отправки сообщений."""

    def __init__(
        self,
        bootstrap_servers: str = None,
        topic: str = None,
        compression_type: str = "gzip",
        acks: str = "all",
        retries: int = 3,
    ):
        """Инициализация базового Kafka-продюсера.
        
        Аргументы:
            bootstrap_servers: Серверы Kafka. По умолчанию settings.kafka.bootstrap_servers.
            topic: Тема Kafka для отправки. По умолчанию settings.kafka.topic.
            compression_type: Тип сжатия сообщений. По умолчанию "gzip".
            acks: Количество подтверждений для записи. По умолчанию "all".
            retries: Количество попыток повторной отправки. По умолчанию 3.
        """
        self.bootstrap_servers = bootstrap_servers or settings.kafka.bootstrap_servers
        self.topic = topic or settings.kafka.topic
        self.compression_type = compression_type
        self.acks = acks
        self.retries = retries
        
        # Инициализация продюсера
        self.producer = None
        
        logger.info(
            f"Initialized Kafka producer for topic {self.topic} "
            f"with bootstrap servers {self.bootstrap_servers}"
        )
    
    async def start(self, max_retries=5, retry_delay=5):
        """Запуск Kafka-продюсера.
        
        Аргументы:
            max_retries: Максимальное количество попыток подключения. По умолчанию 5.
            retry_delay: Задержка между попытками в секундах. По умолчанию 5.
        
        Вызывает исключение:
            KafkaError: Если инициализация продюсера не удалась после всех попыток.
        """
        # Инициализация Kafka-продюсера с логикой повторных попыток
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            compression_type=self.compression_type,
            acks=self.acks,
            retries=self.retries,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        
        # Попытка подключения к Kafka с повторными попытками
        retries = 0
        last_exception = None
        
        while retries < max_retries:
            try:
                logger.info(f"Attempting to connect to Kafka (attempt {retries + 1}/{max_retries})...")
                await self.producer.start()
                logger.info(f"Successfully connected to Kafka and started producer for topic {self.topic}")
                return  # Successfully connected
            except Exception as e:
                last_exception = e
                logger.warning(f"Failed to connect to Kafka (attempt {retries + 1}/{max_retries}): {str(e)}")
                retries += 1
                if retries < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
        
        # Если мы дошли до этого места, все попытки не удались
        error_msg = f"Failed to start Kafka producer after {max_retries} attempts: {str(last_exception)}"
        logger.error(error_msg)
        raise KafkaError(error_msg, details={"original_error": str(last_exception)})
    
    async def stop(self):
        """Остановка Kafka-продюсера."""
        if self.producer:
            await self.producer.stop()
            logger.info(f"Stopped Kafka producer for topic {self.topic}")
    
    async def send_message(self, message: Dict[str, Any], key: Optional[bytes] = None) -> None:
        """Отправка сообщения в тему Kafka.
        
        Аргументы:
            message: Сообщение для отправки.
            key: Опциональный ключ для партиционирования.
        
        Вызывает исключение:
            KafkaError: Если отправка сообщения не удалась.
        """
        try:
            await self.producer.send_and_wait(
                topic=self.topic,
                value=message,
                key=key
            )
            logger.info(f"Successfully sent message to topic {self.topic}")
        except Exception as e:
            error_msg = f"Error sending message to Kafka: {str(e)}"
            logger.error(error_msg)
            raise KafkaError(error_msg, details={"original_error": str(e)})
    
    async def send_messages(self, messages: list[Dict[str, Any]], keys: Optional[list[bytes]] = None) -> None:
        """Отправка нескольких сообщений в тему Kafka.
        
        Аргументы:
            messages: Список сообщений для отправки.
            keys: Опциональный список ключей для партиционирования.
        
        Вызывает исключение:
            KafkaError: Если отправка сообщений не удалась.
        """
        try:
            for i, message in enumerate(messages):
                key = keys[i] if keys and i < len(keys) else None
                await self.send_message(message, key)
            logger.info(f"Successfully sent {len(messages)} messages to topic {self.topic}")
        except Exception as e:
            error_msg = f"Error sending batch of messages to Kafka: {str(e)}"
            logger.error(error_msg)
            raise KafkaError(error_msg, details={"original_error": str(e)}) 