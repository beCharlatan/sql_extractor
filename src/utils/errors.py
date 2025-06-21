"""Утилиты обработки ошибок для приложения SQL-экстрактора."""

from typing import Any, Dict, Optional

from loguru import logger


class AppError(Exception):
    """Базовый класс исключений для ошибок приложения."""

    def __init__(
        self,
        message: str,
        error_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование ошибки в словарное представление."""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }


class ValidationError(AppError):
    """Исключение для ошибок валидации ввода."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, 400, details)


class SQLGenerationError(AppError):
    """Исключение для ошибок генерации SQL."""

    def __init__(
        self,
        message: str = "Error generating SQL",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, 500, details)


class DatabaseError(AppError):
    """Исключение для ошибок, связанных с базой данных."""

    def __init__(
        self,
        message: str = "Database error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, 500, details)


def handle_exception(exc: Exception) -> None:
    """Запись исключения в лог с соответствующим уровнем в зависимости от типа.

    Аргументы:
        exc: Исключение для обработки.
    """
    if isinstance(exc, AppError):
        if exc.error_code >= 500:
            logger.error(f"Application Error: {exc.message}\nDetails: {exc.details}")
        else:
            logger.warning(f"Application Error: {exc.message}\nDetails: {exc.details}")
    else:
        logger.exception(f"Unhandled exception: {str(exc)}")
