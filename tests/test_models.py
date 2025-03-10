"""Tests for API data models."""

import pytest
from pydantic import ValidationError

from src.api.models import GenerateSQLRequest, SQLComponents, GenerateSQLResponse


class TestGenerateSQLRequest:
    """Test cases for the GenerateSQLRequest model."""

    def test_valid_request(self):
        """Test that a valid request passes validation."""
        request = GenerateSQLRequest(
            filter="Find products in the electronics category",
            constraint="Sort by highest rating and limit to 10 results",
            table_ddl="CREATE TABLE products (id INT PRIMARY KEY, name VARCHAR(100));"
        )
        assert request.filter == "Find products in the electronics category"
        assert request.constraint == "Sort by highest rating and limit to 10 results"
        assert request.table_ddl == "CREATE TABLE products (id INT PRIMARY KEY, name VARCHAR(100));"

    def test_empty_filter(self):
        """Test that an empty filter raises a validation error."""
        with pytest.raises(ValidationError) as exc_info:
            GenerateSQLRequest(
                filter="",
                constraint="Sort by highest rating",
                table_ddl="CREATE TABLE products (id INT PRIMARY KEY);"
            )
        errors = exc_info.value.errors()
        assert any(e["type"] == "string_too_short" for e in errors)

    def test_whitespace_filter(self):
        """Test that a whitespace-only filter raises a validation error."""
        with pytest.raises(ValidationError) as exc_info:
            GenerateSQLRequest(
                filter="   ",
                constraint="Sort by highest rating",
                table_ddl="CREATE TABLE products (id INT PRIMARY KEY);"
            )
        errors = exc_info.value.errors()
        assert any("Filter text cannot be empty" in str(e["msg"]) for e in errors)

    def test_empty_constraint(self):
        """Test that an empty constraint raises a validation error."""
        with pytest.raises(ValidationError) as exc_info:
            GenerateSQLRequest(
                filter="Find products",
                constraint="",
                table_ddl="CREATE TABLE products (id INT PRIMARY KEY);"
            )
        errors = exc_info.value.errors()
        assert any(e["type"] == "string_too_short" for e in errors)

    def test_whitespace_constraint(self):
        """Test that a whitespace-only constraint raises a validation error."""
        with pytest.raises(ValidationError) as exc_info:
            GenerateSQLRequest(
                filter="Find products",
                constraint="   ",
                table_ddl="CREATE TABLE products (id INT PRIMARY KEY);"
            )
        errors = exc_info.value.errors()
        assert any("Constraint text cannot be empty" in str(e["msg"]) for e in errors)

    def test_empty_table_ddl(self):
        """Test that an empty table DDL raises a validation error."""
        with pytest.raises(ValidationError) as exc_info:
            GenerateSQLRequest(
                filter="Find products",
                constraint="Sort by rating",
                table_ddl=""
            )
        errors = exc_info.value.errors()
        assert any(e["type"] == "string_too_short" for e in errors)

    def test_invalid_table_ddl(self):
        """Test that a table DDL not starting with 'CREATE TABLE' raises a validation error."""
        with pytest.raises(ValidationError) as exc_info:
            GenerateSQLRequest(
                filter="Find products",
                constraint="Sort by rating",
                table_ddl="INSERT INTO products VALUES (1, 'test');"
            )
        errors = exc_info.value.errors()
        assert any("Table DDL must start with 'CREATE TABLE'" in str(e["msg"]) for e in errors)

    def test_too_long_filter(self):
        """Test that a filter longer than 400 characters raises a validation error."""
        with pytest.raises(ValidationError) as exc_info:
            GenerateSQLRequest(
                filter="A" * 401,
                constraint="Sort by rating",
                table_ddl="CREATE TABLE products (id INT PRIMARY KEY);"
            )
        errors = exc_info.value.errors()
        assert any(e["type"] == "string_too_long" for e in errors)

    def test_too_long_constraint(self):
        """Test that a constraint longer than 400 characters raises a validation error."""
        with pytest.raises(ValidationError) as exc_info:
            GenerateSQLRequest(
                filter="Find products",
                constraint="A" * 401,
                table_ddl="CREATE TABLE products (id INT PRIMARY KEY);"
            )
        errors = exc_info.value.errors()
        assert any(e["type"] == "string_too_long" for e in errors)


class TestSQLComponents:
    """Test cases for the SQLComponents model."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        components = SQLComponents()
        assert components.where_clause == ""
        assert components.order_by_clause == ""
        assert components.limit_clause == ""
        assert components.full_sql == ""

    def test_custom_values(self):
        """Test that custom values are set correctly."""
        components = SQLComponents(
            where_clause="category = 'electronics'",
            order_by_clause="price DESC",
            limit_clause="10",
            full_sql="WHERE category = 'electronics'\nORDER BY price DESC\nLIMIT 10"
        )
        assert components.where_clause == "category = 'electronics'"
        assert components.order_by_clause == "price DESC"
        assert components.limit_clause == "10"
        assert components.full_sql == "WHERE category = 'electronics'\nORDER BY price DESC\nLIMIT 10"


class TestGenerateSQLResponse:
    """Test cases for the GenerateSQLResponse model."""

    def test_response_with_components(self):
        """Test that a response with SQL components is created correctly."""
        components = SQLComponents(
            where_clause="category = 'electronics'",
            order_by_clause="price DESC",
            limit_clause="10",
            full_sql="WHERE category = 'electronics'\nORDER BY price DESC\nLIMIT 10"
        )
        response = GenerateSQLResponse(sql_components=components)
        assert response.sql_components == components
        assert response.sql_components.where_clause == "category = 'electronics'"
        assert response.sql_components.order_by_clause == "price DESC"
        assert response.sql_components.limit_clause == "10"
        assert response.sql_components.full_sql == "WHERE category = 'electronics'\nORDER BY price DESC\nLIMIT 10"
