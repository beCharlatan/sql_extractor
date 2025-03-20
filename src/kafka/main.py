"""Основная точка входа для сервиса Kafka-потребителя."""

import asyncio
import signal
import sys
from pathlib import Path

# Добавление корня проекта в путь Python
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from loguru import logger

from src.config.settings import settings
from src.kafka.consumer import KafkaConsumer
from src.utils.logging import setup_logging


# Обработчик сигнала для корректного завершения
async def shutdown(consumer, signal=None):
    """Корректное завершение работы Kafka-потребителя.
    
    Аргументы:
        consumer: Kafka-потребитель, который нужно остановить.
        signal: Сигнал, который вызвал завершение работы.
    """
    if signal:
        logger.info(f"Received exit signal {signal.name}...")
    
    logger.info("Shutting down Kafka consumer...")
    await consumer.stop()
    logger.info("Kafka consumer has been shut down.")


# Функция обратного вызова для обработки результатов
def process_result(message, result):
    """Обработка результата сообщения Kafka.
    
    Аргументы:
        message: Исходное сообщение Kafka.
        result: Результат обработки.
    """
    message_id = message.get("message_id", "unknown")
    
    if "error" in result:
        logger.error(f"Error processing message {message_id}: {result['error']['message']}")
    else:
        logger.info(f"Successfully processed message {message_id}")
        logger.debug(f"SQL components: {result.get('sql_components', {})}")


async def main():
    """Основная точка входа для сервиса Kafka-потребителя."""
    # Настройка логирования
    setup_logging()
    logger.info("Starting Kafka consumer service...")
    
    # Создание и запуск Kafka-потребителя
    consumer = KafkaConsumer(
        bootstrap_servers=settings.kafka.bootstrap_servers,
        topic=settings.kafka.topic,
        group_id=settings.kafka.group_id,
        auto_offset_reset=settings.kafka.auto_offset_reset,
        enable_auto_commit=settings.kafka.enable_auto_commit,
        consumer_timeout_ms=settings.kafka.consumer_timeout_ms,
    )
    
    # Настройка обработчиков сигналов для корректного завершения
    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_event_loop().add_signal_handler(
            sig, lambda sig=sig: asyncio.create_task(shutdown(consumer, sig))
        )
    
    try:
        # Запуск потребителя
        await consumer.start()
        
        # Обработка сообщений
        await consumer.process_messages(callback=process_result)
    except Exception as e:
        logger.exception(f"Error in Kafka consumer service: {str(e)}")
    finally:
        # Гарантируем остановку потребителя
        await shutdown(consumer)


if __name__ == "__main__":
    asyncio.run(main())
