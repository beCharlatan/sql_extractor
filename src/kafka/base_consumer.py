"""Базовый класс Kafka-потребителя для обработки сообщений."""

import json
import asyncio
from typing import Any, Callable, Dict, Optional

from aiokafka import AIOKafkaConsumer
from loguru import logger

from src.config.settings import settings
from src.utils.errors import KafkaError


class BaseKafkaConsumer:
    """Базовый класс Kafka-потребителя для общей инфраструктуры обработки сообщений."""

    def __init__(
        self,
        bootstrap_servers: str = None,
        topic: str = None,
        group_id: str = None,
        auto_offset_reset: str = "earliest",
        enable_auto_commit: bool = True,
        consumer_timeout_ms: int = 1000,
    ):
        """Инициализация базового Kafka-потребителя.
        
        Аргументы:
            bootstrap_servers: Серверы Kafka. По умолчанию settings.kafka.bootstrap_servers.
            topic: Тема Kafka для потребления. По умолчанию settings.kafka.topic.
            group_id: ID группы потребителей. По умолчанию settings.kafka.group_id.
            auto_offset_reset: Стратегия сброса смещения. По умолчанию "earliest".
            enable_auto_commit: Включить автоматическую фиксацию. По умолчанию True.
            consumer_timeout_ms: Тайм-аут потребителя в миллисекундах. По умолчанию 1000.
        """
        self.bootstrap_servers = bootstrap_servers or settings.kafka.bootstrap_servers
        self.topic = topic or settings.kafka.topic
        self.group_id = group_id or settings.kafka.group_id
        self.auto_offset_reset = auto_offset_reset
        self.enable_auto_commit = enable_auto_commit
        self.consumer_timeout_ms = consumer_timeout_ms
        
        # Инициализация потребителя
        self.consumer = None
        
        logger.info(
            f"Initialized Kafka consumer for topic {self.topic} "
            f"with group ID {self.group_id} "
            f"and bootstrap servers {self.bootstrap_servers}"
        )
    
    async def start(self, max_retries=5, retry_delay=5):
        """Запуск Kafka-потребителя.
        
        Аргументы:
            max_retries: Максимальное количество попыток подключения. По умолчанию 5.
            retry_delay: Задержка между попытками в секундах. По умолчанию 5.
        
        Вызывает исключение:
            KafkaError: Если инициализация потребителя не удалась после всех попыток.
        """
        # Инициализация Kafka-потребителя с логикой повторных попыток
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            auto_offset_reset=self.auto_offset_reset,
            enable_auto_commit=self.enable_auto_commit,
            consumer_timeout_ms=self.consumer_timeout_ms,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        
        # Попытка подключения к Kafka с повторными попытками
        retries = 0
        last_exception = None
        
        while retries < max_retries:
            try:
                logger.info(f"Attempting to connect to Kafka (attempt {retries + 1}/{max_retries})...")
                await self.consumer.start()
                logger.info(f"Successfully connected to Kafka and started consumer for topic {self.topic}")
                return  # Successfully connected
            except Exception as e:
                last_exception = e
                logger.warning(f"Failed to connect to Kafka (attempt {retries + 1}/{max_retries}): {str(e)}")
                retries += 1
                if retries < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
        
        # Если мы дошли до этого места, все попытки не удались
        error_msg = f"Failed to start Kafka consumer after {max_retries} attempts: {str(last_exception)}"
        logger.error(error_msg)
        raise KafkaError(error_msg, details={"original_error": str(last_exception)})
    
    async def stop(self):
        """Остановка Kafka-потребителя."""
        if self.consumer:
            await self.consumer.stop()
            logger.info(f"Stopped Kafka consumer for topic {self.topic}")
    
    async def process_messages(self, callback: Optional[Callable[[Dict[str, Any], Dict[str, Any]], None]] = None):
        """Обработка сообщений из темы Kafka.
        
        Аргументы:
            callback: Опциональная функция обратного вызова для обработки результата.
                     Функция получает исходное сообщение и результат.
        
        Вызывает исключение:
            KafkaError: Если обработка сообщения не удалась.
        """
        try:
            async for message in self.consumer:
                logger.info(f"Received message from topic {self.topic} at partition {message.partition}, offset {message.offset}")
                
                try:
                    # Обработка сообщения
                    result = await self._process_message(message.value)
                    
                    # Вызов функции обратного вызова, если она предоставлена
                    if callback:
                        callback(message.value, result)
                    
                    logger.info(f"Successfully processed message from topic {self.topic}")
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    # Продолжаем обработку остальных сообщений, даже если одно не удалось
        except Exception as e:
            error_msg = f"Error consuming messages from Kafka: {str(e)}"
            logger.error(error_msg)
            raise KafkaError(error_msg, details={"original_error": str(e)})
    
    async def _process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка одного сообщения из Kafka.
        
        Этот метод должен быть переопределен в дочерних классах для реализации конкретной бизнес-логики.
        
        Аргументы:
            message: Сообщение из Kafka.
            
        Возвращает:
            Результат обработки.
            
        Вызывает исключение:
            NotImplementedError: Если метод не переопределен в дочернем классе.
        """
        raise NotImplementedError("_process_message must be implemented in a subclass")
