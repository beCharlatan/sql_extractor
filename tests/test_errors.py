"""Tests for error handling functionality."""

from fastapi import HTTPException, status

from src.utils.errors import (
    APIError, ValidationError, GigachatAPIError, SQLGenerationError, 
    InvalidTableDDLError, InvalidSQLError
)


class TestAPIError:
    """Test cases for the APIError class."""

    def test_api_error_properties(self):
        """Test that APIError properties are set correctly."""
        error = APIError("Test error message", details={"key": "value"})
        assert error.message == "Test error message"
        assert error.details == {"key": "value"}

    def test_api_error_str(self):
        """Test the string representation of APIError."""
        error = APIError("Test error message")
        assert str(error) == "Test error message"

    def test_api_error_to_dict(self):
        """Test the to_dict method of APIError."""
        error = APIError("Test error message", details={"key": "value"})
        error_dict = error.to_dict()
        assert error_dict["error"] == "Test error message"
        assert error_dict["details"] == {"key": "value"}
        assert "status_code" in error_dict


class TestValidationError:
    """Test cases for the ValidationError class."""

    def test_validation_error_inheritance(self):
        """Test that ValidationError inherits from APIError."""
        error = ValidationError("Invalid input", details={"field": "filter"})
        assert isinstance(error, APIError)

    def test_validation_error_to_http_exception(self):
        """Test the to_http_exception method of ValidationError."""
        error = ValidationError("Invalid input", details={"field": "filter"})
        http_exc = error.to_http_exception()
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == status.HTTP_400_BAD_REQUEST
        assert http_exc.detail["error"] == error.message
        assert http_exc.detail["details"] == error.details


class TestGigachatAPIError:
    """Test cases for the GigachatAPIError class."""

    def test_gigachat_api_error_inheritance(self):
        """Test that GigachatAPIError inherits from APIError."""
        error = GigachatAPIError("API connection failed", details={"status": 502})
        assert isinstance(error, APIError)

    def test_gigachat_api_error_to_http_exception(self):
        """Test the to_http_exception method of GigachatAPIError."""
        error = GigachatAPIError("API connection failed", details={"status": 502})
        http_exc = error.to_http_exception()
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == status.HTTP_502_BAD_GATEWAY
        assert http_exc.detail["error"] == error.message
        assert http_exc.detail["details"] == error.details


class TestSQLGenerationError:
    """Test cases for the SQLGenerationError class."""

    def test_sql_generation_error_inheritance(self):
        """Test that SQLGenerationError inherits from APIError."""
        error = SQLGenerationError("Failed to generate SQL", details={"reason": "parsing_error"})
        assert isinstance(error, APIError)

    def test_sql_generation_error_to_http_exception(self):
        """Test the to_http_exception method of SQLGenerationError."""
        error = SQLGenerationError("Failed to generate SQL", details={"reason": "parsing_error"})
        http_exc = error.to_http_exception()
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert http_exc.detail["error"] == error.message
        assert http_exc.detail["details"] == error.details


class TestInvalidTableDDLError:
    """Test cases for the InvalidTableDDLError class."""

    def test_invalid_table_ddl_error_inheritance(self):
        """Test that InvalidTableDDLError inherits from ValidationError."""
        error = InvalidTableDDLError("Invalid table DDL", details={"field": "table_ddl"})
        assert isinstance(error, ValidationError)

    def test_invalid_table_ddl_error_to_http_exception(self):
        """Test the to_http_exception method of InvalidTableDDLError."""
        error = InvalidTableDDLError("Invalid table DDL", details={"field": "table_ddl"})
        http_exc = error.to_http_exception()
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == status.HTTP_400_BAD_REQUEST
        assert http_exc.detail["error"] == error.message
        assert http_exc.detail["details"] == error.details


class TestInvalidSQLError:
    """Test cases for the InvalidSQLError class."""

    def test_invalid_sql_error_inheritance(self):
        """Test that InvalidSQLError inherits from ValidationError."""
        error = InvalidSQLError("Invalid SQL syntax", details={"component": "where_clause"})
        assert isinstance(error, ValidationError)

    def test_invalid_sql_error_to_http_exception(self):
        """Test the to_http_exception method of InvalidSQLError."""
        error = InvalidSQLError("Invalid SQL syntax", details={"component": "where_clause"})
        http_exc = error.to_http_exception()
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == status.HTTP_400_BAD_REQUEST
        assert http_exc.detail["error"] == error.message
        assert http_exc.detail["details"] == error.details
