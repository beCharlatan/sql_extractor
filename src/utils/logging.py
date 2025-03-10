"""Logging utility for the AI agent application."""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from src.config.settings import settings


def setup_logging(log_file: Optional[str] = None) -> None:
    """Configure application logging.

    Args:
        log_file: Optional path to log file. If not provided, will use the value from settings.
    """
    # Remove default logger
    logger.remove()

    # Get log level from settings
    log_level = settings.logging.level

    # Add console handler
    logger.add(
        sys.stderr,
        format=settings.logging.format,
        level=log_level,
        colorize=True,
    )

    # Add file handler if log file is specified
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


# Initialize logging with default settings
setup_logging()
