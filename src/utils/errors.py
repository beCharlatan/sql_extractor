"""Error handling utilities for the AI agent application."""

from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from loguru import logger


class APIError(Exception):
    """Base exception class for API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary representation."""
        return {
            "error": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }

    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=self.status_code,
            detail={
                "error": self.message,
                "details": self.details,
            },
        )


class GigachatAPIError(APIError):
    """Exception for Gigachat API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code, details)


class ValidationError(APIError):
    """Exception for input validation errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, details)


class AuthenticationError(APIError):
    """Exception for authentication errors."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, details)


class NotFoundError(APIError):
    """Exception for resource not found errors."""

    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status.HTTP_404_NOT_FOUND, details)


class SQLGenerationError(APIError):
    """Exception for SQL generation errors."""

    def __init__(
        self,
        message: str = "Error generating SQL",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR, details)


class InvalidSQLError(ValidationError):
    """Exception for invalid SQL syntax."""

    def __init__(
        self,
        message: str = "Invalid SQL syntax",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)


class InvalidTableDDLError(ValidationError):
    """Exception for invalid table DDL."""

    def __init__(
        self,
        message: str = "Invalid table DDL",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)


class DatabaseError(APIError):
    """Exception for database-related errors."""

    def __init__(
        self,
        message: str = "Database error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR, details)


def handle_exception(exc: Exception) -> None:
    """Log exception with appropriate level based on type.

    Args:
        exc: The exception to handle.
    """
    if isinstance(exc, APIError):
        if exc.status_code >= 500:
            logger.error(f"API Error: {exc.message}\nDetails: {exc.details}")
        else:
            logger.warning(f"API Error: {exc.message}\nDetails: {exc.details}")
    else:
        logger.exception(f"Unhandled exception: {str(exc)}")
