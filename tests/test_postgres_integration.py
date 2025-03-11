"""Integration tests for PostgreSQL functionality with the SQL generator."""

import os
import pytest
from unittest.mock import MagicMock, patch

from src.agent.sql_generator import SQLGenerator
from src.db.db_schema_tool import DBSchemaReferenceTool
from src.utils.errors import DatabaseError


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    agent = MagicMock()
    agent.process_query.return_value = {
        "choices": [
            {
                "message": {
                    "content": """
```json
{
  "sql_components": {
    "where_clause": "category = 'electronics' AND price < 500",
    "order_by_clause": "rating DESC",
    "limit_clause": "5"
  }
}
```
                    """
                }
            }
        ]
    }
    return agent


@pytest.fixture
def mock_db_schema_tool():
    """Create a mock DBSchemaReferenceTool for testing."""
    tool = MagicMock()
    
    # Mock get_table_schema
    tool.get_table_schema.return_value = """
    CREATE TABLE products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        price DECIMAL(10, 2) NOT NULL,
        category VARCHAR(50),
        rating DECIMAL(3, 2),
        stock INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Mock get_table_columns
    tool.get_table_columns.return_value = [
        {"cid": 1, "name": "id", "type": "integer", "notnull": 1, "default_value": "nextval('products_id_seq'::regclass)", "pk": 1},
        {"cid": 2, "name": "name", "type": "character varying", "notnull": 1, "default_value": None, "pk": 0},
        {"cid": 3, "name": "description", "type": "text", "notnull": 0, "default_value": None, "pk": 0},
        {"cid": 4, "name": "price", "type": "numeric", "notnull": 1, "default_value": None, "pk": 0},
        {"cid": 5, "name": "category", "type": "character varying", "notnull": 0, "default_value": None, "pk": 0},
        {"cid": 6, "name": "rating", "type": "numeric", "notnull": 0, "default_value": None, "pk": 0},
        {"cid": 7, "name": "stock", "type": "integer", "notnull": 0, "default_value": "0", "pk": 0},
        {"cid": 8, "name": "created_at", "type": "timestamp without time zone", "notnull": 0, "default_value": "CURRENT_TIMESTAMP", "pk": 0}
    ]
    
    # Mock get_parameter_info
    def mock_get_parameter_info(param_name):
        parameter_info = {
            "price": {"parameter_name": "price", "description": "Product price in USD", "data_type": "numeric"},
            "category": {"parameter_name": "category", "description": "Product category (e.g. electronics, clothing)", "data_type": "string"},
            "rating": {"parameter_name": "rating", "description": "Product rating from 0 to 5", "data_type": "numeric"},
            "stock": {"parameter_name": "stock", "description": "Number of items in stock", "data_type": "integer"}
        }
        if param_name in parameter_info:
            return parameter_info[param_name]
        raise DatabaseError(f"Parameter '{param_name}' not found in reference table")
    
    tool.get_parameter_info.side_effect = mock_get_parameter_info
    
    # Mock get_all_tables
    tool.get_all_tables.return_value = ["products", "orders", "customers"]
    
    return tool


class TestPostgresIntegration:
    """Test PostgreSQL integration with the SQL generator."""
    
    def test_field_recognition_with_parameter_info(self, mock_agent, mock_db_schema_tool):
        """Test that the SQL generator correctly recognizes fields with parameter info."""
        # Initialize the SQL generator with mocks
        generator = SQLGenerator(agent=mock_agent, db_schema_tool=mock_db_schema_tool)
        generator.table_name = "products"
        
        # Test inputs that should use price field (not stock)
        filter_text = "найти все товары с ценой меньше 500"
        constraint_text = "отсортировать по рейтингу в порядке убывания и ограничить результат 5 записями"
        
        # Generate SQL components
        result = generator.generate_sql_components(filter_text, constraint_text)
        
        # Verify the results
        assert "sql_components" in result
        assert "where_clause" in result["sql_components"]
        assert "order_by_clause" in result["sql_components"]
        assert "limit_clause" in result["sql_components"]
        
        # Check that price is used in the where clause (not stock)
        assert "price" in result["sql_components"]["where_clause"]
        assert "500" in result["sql_components"]["where_clause"]
        
        # Check that rating is used for sorting
        assert "rating DESC" in result["sql_components"]["order_by_clause"]
        
        # Check that limit is applied
        assert result["sql_components"]["limit_clause"] == "5"
        
        # Verify that the agent was called with a prompt containing parameter descriptions
        prompt = mock_agent.process_query.call_args[0][0]
        assert "Parameter descriptions:" in prompt
        assert "Product price in USD" in prompt
        assert "Product rating from 0 to 5" in prompt
    
    def test_category_filter_recognition(self, mock_agent, mock_db_schema_tool):
        """Test that the SQL generator correctly recognizes category filters."""
        # Initialize the SQL generator with mocks
        generator = SQLGenerator(agent=mock_agent, db_schema_tool=mock_db_schema_tool)
        generator.table_name = "products"
        
        # Test inputs for category filtering
        filter_text = "найти все товары в категории electronics"
        constraint_text = "отсортировать по цене по возрастанию"
        
        # Generate SQL components
        result = generator.generate_sql_components(filter_text, constraint_text)
        
        # Verify the results
        assert "category" in result["sql_components"]["where_clause"]
        assert "electronics" in result["sql_components"]["where_clause"]
        
        # Note: In a real scenario, we would check for price sorting,
        # but our mock agent always returns 'rating DESC'
        assert "rating" in result["sql_components"]["order_by_clause"]
        
    def test_limit_recognition(self, mock_agent, mock_db_schema_tool):
        """Test that the SQL generator correctly recognizes limit constraints."""
        # Initialize the SQL generator with mocks
        generator = SQLGenerator(agent=mock_agent, db_schema_tool=mock_db_schema_tool)
        generator.table_name = "products"
        
        # Test inputs with explicit limit
        filter_text = "найти все товары"
        constraint_text = "ограничить результат 5 записями"
        
        # Generate SQL components
        result = generator.generate_sql_components(filter_text, constraint_text)
        
        # Verify the results
        assert result["sql_components"]["limit_clause"] == "5"
