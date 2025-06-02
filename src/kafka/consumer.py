"""Реализация Kafka-потребителя для обработки запросов на генерацию SQL."""

from typing import Any, Dict, Optional
from loguru import logger

from src.kafka.base_consumer import BaseKafkaConsumer
from src.services.request_processor import RequestProcessor
from src.utils.errors import KafkaError


class KafkaConsumer(BaseKafkaConsumer):
    """Специализированный Kafka-потребитель для обработки запросов на генерацию SQL."""

    def __init__(
        self,
        bootstrap_servers: str = None,
        topic: str = None,
        group_id: str = None,
        auto_offset_reset: str = "earliest",
        enable_auto_commit: bool = True,
        consumer_timeout_ms: int = 1000,
        request_processor: Optional[RequestProcessor] = None,
    ):
        """Инициализация специализированного Kafka-потребителя для генерации SQL.
        
        Аргументы:
            bootstrap_servers: Серверы Kafka. По умолчанию settings.kafka.bootstrap_servers.
            topic: Тема Kafka для потребления. По умолчанию settings.kafka.topic.
            group_id: ID группы потребителей. По умолчанию settings.kafka.group_id.
            auto_offset_reset: Стратегия сброса смещения. По умолчанию "earliest".
            enable_auto_commit: Включить автоматическую фиксацию. По умолчанию True.
            consumer_timeout_ms: Тайм-аут потребителя в миллисекундах. По умолчанию 1000.
            request_processor: Опциональный экземпляр RequestProcessor. Если не указан, будет создан новый.
        """
        # Вызов инициализатора базового класса для настройки Kafka
        super().__init__(
            bootstrap_servers=bootstrap_servers,
            topic=topic,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=enable_auto_commit,
            consumer_timeout_ms=consumer_timeout_ms
        )
        
        self.request_processor = request_processor
    
    async def start(self, max_retries=5, retry_delay=5):
        """Расширенный запуск, включающий подключение к Kafka и инициализацию компонентов.
        
        Аргументы:
            max_retries: Максимальное количество попыток подключения. По умолчанию 5.
            retry_delay: Задержка между попытками в секундах. По умолчанию 5.
        
        Вызывает исключение:
            KafkaError: Если инициализация потребителя не удалась после всех попыток.
        """
        # Инициализация процессора запросов, если он не был предоставлен
        if self.request_processor is None:
            self.request_processor = RequestProcessor()
            await self.request_processor.start()
            
        # Вызов метода start базового класса для подключения к Kafka
        await super().start(max_retries=max_retries, retry_delay=retry_delay)
    
    async def stop(self):
        """Расширенная остановка, включающая отключение от Kafka и закрытие компонентов."""
        # Вызов метода stop базового класса для остановки Kafka-потребителя
        await super().stop()
        
        # Остановка процессора запросов
        if self.request_processor is not None:
            await self.request_processor.stop()
            logger.info("Stopped request processor")

    async def _process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка одного сообщения из Kafka.
        
        Аргументы:
            message: Сообщение из Kafka.
            
        Возвращает:
            Результат обработки.
            
        Вызывает исключение:
            KafkaError: Если обработка сообщения не удалась.
        """
        try:
            # Обработка сообщения через процессор запросов
            return await self.request_processor.process_request(message)
        except Exception as e:
            error_msg = f"Failed to process Kafka message: {str(e)}"
            logger.error(error_msg)
            raise KafkaError(error_msg, details={"original_error": str(e)})
