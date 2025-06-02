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


class GigachatAPIError(AppError):
    """Исключение для ошибок Gigachat API."""

    def __init__(
        self,
        message: str,
        error_code: int = 502,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, details)


class ValidationError(AppError):
    """Исключение для ошибок валидации ввода."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, 400, details)


class AuthenticationError(AppError):
    """Исключение для ошибок аутентификации."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, 401, details)


class NotFoundError(AppError):
    """Исключение для ошибок отсутствия ресурса."""

    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, 404, details)


class SQLGenerationError(AppError):
    """Исключение для ошибок генерации SQL."""

    def __init__(
        self,
        message: str = "Error generating SQL",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, 500, details)


class InvalidSQLError(ValidationError):
    """Исключение для неверного синтаксиса SQL."""

    def __init__(
        self,
        message: str = "Invalid SQL syntax",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)


class InvalidTableDDLError(ValidationError):
    """Исключение для неверного DDL таблицы."""

    def __init__(
        self,
        message: str = "Invalid table DDL",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)


class DatabaseError(AppError):
    """Исключение для ошибок, связанных с базой данных."""

    def __init__(
        self,
        message: str = "Database error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, 500, details)


class KafkaError(AppError):
    """Исключение для ошибок, связанных с Kafka."""

    def __init__(
        self,
        message: str = "Kafka error",
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
