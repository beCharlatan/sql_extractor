"""Утилита логирования для приложения AI-агента."""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from src.config.settings import settings


def setup_logging(log_file: Optional[str] = None) -> None:
    """Настройка логирования приложения.

    Аргументы:
        log_file: Опциональный путь к файлу лога. Если не указан, будет использовано значение из настроек.
    """
    # Удаление логгера по умолчанию
    logger.remove()

    # Получение уровня логирования из настроек
    log_level = settings.logging.level

    # Добавление обработчика консоли
    logger.add(
        sys.stderr,
        format=settings.logging.format,
        level=log_level,
        colorize=True,
    )

    # Добавление обработчика файла, если файл лога указан
    log_file = log_file or settings.logging.log_file
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_path,
            format=settings.logging.format,
            level=log_level,
            rotation="10 MB",
            compression="zip",
            retention="1 month",
        )

    logger.info(f"Logging initialized with level: {log_level}")


# Инициализация логирования с настройками по умолчанию
setup_logging()
