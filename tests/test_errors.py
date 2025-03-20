"""Tests for error handling functionality."""

from src.utils.errors import (
    AppError, ValidationError, GigachatAPIError, SQLGenerationError, 
    InvalidTableDDLError, InvalidSQLError
)


class TestAppError:
    """Test cases for the AppError class."""

    def test_app_error_properties(self):
        """Test that AppError properties are set correctly."""
        error = AppError("Test error message", details={"key": "value"})
        assert error.message == "Test error message"
        assert error.details == {"key": "value"}

    def test_app_error_str(self):
        """Test the string representation of AppError."""
        error = AppError("Test error message")
        assert str(error) == "Test error message"

    def test_app_error_to_dict(self):
        """Test the to_dict method of AppError."""
        error = AppError("Test error message", details={"key": "value"})
        error_dict = error.to_dict()
        assert error_dict["error"] == "Test error message"
        assert error_dict["details"] == {"key": "value"}
        assert "error_code" in error_dict


class TestValidationError:
    """Test cases for the ValidationError class."""

    def test_validation_error_inheritance(self):
        """Test that ValidationError inherits from AppError."""
        error = ValidationError("Invalid input", details={"field": "filter"})
        assert isinstance(error, AppError)

    def test_validation_error_error_code(self):
        """Test that ValidationError has the correct error_code."""
        error = ValidationError("Invalid input", details={"field": "filter"})
        assert error.error_code == 400
        assert error.to_dict()["error_code"] == 400


class TestGigachatAPIError:
    """Test cases for the GigachatAPIError class."""

    def test_gigachat_api_error_inheritance(self):
        """Test that GigachatAPIError inherits from AppError."""
        error = GigachatAPIError("API connection failed", details={"status": 502})
        assert isinstance(error, AppError)

    def test_gigachat_api_error_code(self):
        """Test that GigachatAPIError has the correct error_code."""
        error = GigachatAPIError("API connection failed", details={"status": 502})
        assert error.error_code == 502
        assert error.to_dict()["error_code"] == 502


class TestSQLGenerationError:
    """Test cases for the SQLGenerationError class."""

    def test_sql_generation_error_inheritance(self):
        """Test that SQLGenerationError inherits from AppError."""
        error = SQLGenerationError("Failed to generate SQL", details={"reason": "parsing_error"})
        assert isinstance(error, AppError)

    def test_sql_generation_error_code(self):
        """Test that SQLGenerationError has the correct error_code."""
        error = SQLGenerationError("Failed to generate SQL", details={"reason": "parsing_error"})
        assert error.error_code == 500
        assert error.to_dict()["error_code"] == 500


class TestInvalidTableDDLError:
    """Test cases for the InvalidTableDDLError class."""

    def test_invalid_table_ddl_error_inheritance(self):
        """Test that InvalidTableDDLError inherits from ValidationError."""
        error = InvalidTableDDLError("Invalid table DDL", details={"field": "table_ddl"})
        assert isinstance(error, ValidationError)
        assert isinstance(error, AppError)

    def test_invalid_table_ddl_error_code(self):
        """Test that InvalidTableDDLError has the correct error_code."""
        error = InvalidTableDDLError("Invalid table DDL", details={"field": "table_ddl"})
        assert error.error_code == 400
        assert error.to_dict()["error_code"] == 400


class TestInvalidSQLError:
    """Test cases for the InvalidSQLError class."""

    def test_invalid_sql_error_inheritance(self):
        """Test that InvalidSQLError inherits from ValidationError and AppError."""
        error = InvalidSQLError("Invalid SQL syntax", details={"component": "where_clause"})
        assert isinstance(error, ValidationError)
        assert isinstance(error, AppError)

    def test_invalid_sql_error_code(self):
        """Test that InvalidSQLError has the correct error_code."""
        error = InvalidSQLError("Invalid SQL syntax", details={"component": "where_clause"})
        assert error.error_code == 400
        assert error.to_dict()["error_code"] == 400
