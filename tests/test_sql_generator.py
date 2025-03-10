"""Tests for the SQL generator functionality."""

import pytest
from unittest.mock import MagicMock, patch

from src.agent.sql_generator import SQLGenerator
from src.utils.errors import InvalidTableDDLError, InvalidSQLError


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    agent = MagicMock()
    agent.process_query.return_value = {
        "response": """Based on the provided information, here are the SQL query components:

WHERE: category = 'electronics' AND price < 1000
ORDER BY: rating DESC
LIMIT: 10"""
    }
    return agent


@pytest.fixture
def sample_ddl():
    """Sample table DDL for testing."""
    return """
CREATE TABLE products (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10, 2),
    rating DECIMAL(3, 2),
    stock INT DEFAULT 0
);
"""


class TestSQLGenerator:
    """Test cases for the SQLGenerator class."""

    def test_generate_sql_components(self, mock_agent, sample_ddl):
        """Test generating SQL components from filter and constraint."""
        # Initialize the SQL generator with the mock agent
        generator = SQLGenerator(agent=mock_agent)

        # Test inputs
        filter_text = "Find products in the electronics category"
        constraint_text = "Price should be less than 1000, sort by highest rating, and limit to 10 results"

        # Generate SQL components
        result = generator.generate_sql_components(filter_text, constraint_text, sample_ddl)

        # Verify the results
        assert "sql_components" in result
        assert "where_clause" in result["sql_components"]
        assert "order_by_clause" in result["sql_components"]
        assert "limit_clause" in result["sql_components"]
        assert "full_sql" in result["sql_components"]

        assert result["sql_components"]["where_clause"] == "category = 'electronics' AND price < 1000"
        assert result["sql_components"]["order_by_clause"] == "rating DESC"
        assert result["sql_components"]["limit_clause"] == "10"
        assert "WHERE" in result["sql_components"]["full_sql"]
        assert "ORDER BY" in result["sql_components"]["full_sql"]
        assert "LIMIT" in result["sql_components"]["full_sql"]

        # Verify that the agent was called with the correct prompt
        mock_agent.process_query.assert_called_once()
        prompt = mock_agent.process_query.call_args[0][0]
        assert "Table Definition" in prompt
        assert "Filter" in prompt
        assert "Constraint" in prompt
        assert "products" in prompt
        assert "electronics" in prompt
        assert "1000" in prompt

    def test_extract_column_names(self, sample_ddl):
        """Test extracting column names from table DDL."""
        # Use a mock agent to avoid API calls
        with patch("src.agent.agent.GigachatAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent
            
            generator = SQLGenerator(agent=mock_agent)
            column_names = generator._extract_column_names(sample_ddl)

            # Verify that all columns were extracted
            assert "id" in column_names
            assert "name" in column_names
            assert "category" in column_names
            assert "price" in column_names
            assert "rating" in column_names
            assert "stock" in column_names

            # Verify that SQL keywords were not extracted as column names
            assert "CREATE" not in column_names
            assert "TABLE" not in column_names
            assert "PRIMARY" not in column_names
            assert "KEY" not in column_names

    def test_validate_sql_components(self, sample_ddl):
        """Test validating SQL components against table DDL."""
        # Use a mock agent to avoid API calls
        with patch("src.agent.agent.GigachatAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent
            
            generator = SQLGenerator(agent=mock_agent)

            # Valid components
            valid_components = {
                "where_clause": "category = 'electronics' AND price < 1000",
                "order_by_clause": "rating DESC",
                "limit_clause": "10"
            }

            # Validate the components
            validated = generator._validate_sql_components(valid_components, sample_ddl)

            # Verify that the components were validated correctly
            assert validated["where_clause"] == valid_components["where_clause"]
            assert validated["order_by_clause"] == valid_components["order_by_clause"]
            assert validated["limit_clause"] == valid_components["limit_clause"]

    def test_validate_invalid_sql_components(self, sample_ddl):
        """Test validating invalid SQL components against table DDL."""
        # Use a mock agent to avoid API calls
        with patch("src.agent.agent.GigachatAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent
            
            generator = SQLGenerator(agent=mock_agent)

            # Invalid components (using a column that doesn't exist)
            invalid_components = {
                "where_clause": "non_existent_column = 'value'",
                "order_by_clause": "rating DESC",
                "limit_clause": "10"
            }

            # Validate the components - should raise an error
            with pytest.raises(InvalidSQLError):
                generator._validate_sql_components(invalid_components, sample_ddl)

    def test_invalid_table_ddl(self, mock_agent):
        """Test handling of invalid table DDL."""
        generator = SQLGenerator(agent=mock_agent)

        # Invalid table DDL (not starting with CREATE TABLE)
        invalid_ddl = "INSERT INTO products VALUES (1, 'test');"

        # Generate SQL components - should raise an error
        with pytest.raises(InvalidTableDDLError):
            generator.generate_sql_components(
                "Find products",
                "Sort by rating",
                invalid_ddl
            )

    def test_build_sql_generation_prompt(self, mock_agent, sample_ddl):
        """Test building the SQL generation prompt."""
        generator = SQLGenerator(agent=mock_agent)

        # Test inputs
        filter_text = "Find products in the electronics category"
        constraint_text = "Price should be less than 1000"

        # Build the prompt
        prompt = generator._build_sql_generation_prompt(filter_text, constraint_text, sample_ddl)

        # Verify the prompt contains the expected sections
        assert "Table Definition:" in prompt
        assert "Filter:" in prompt
        assert "Constraint:" in prompt
        assert sample_ddl in prompt
        assert filter_text in prompt
        assert constraint_text in prompt

    def test_extract_structured_response(self, mock_agent):
        """Test extracting structured response from model output."""
        generator = SQLGenerator(agent=mock_agent)

        # Test response text
        response_text = """Based on the provided information, here are the SQL query components:

WHERE: category = 'electronics' AND price < 1000
ORDER BY: rating DESC
LIMIT: 10"""

        # Extract structured response
        result = generator._extract_structured_response(response_text)

        # Verify the result
        assert "sql_components" in result
        assert "parameters" in result
        assert result["sql_components"]["where_clause"] == "category = 'electronics' AND price < 1000"
        assert result["sql_components"]["order_by_clause"] == "rating DESC"
        assert result["sql_components"]["limit_clause"] == "10"

    def test_generate_full_sql(self, mock_agent):
        """Test generating full SQL from components."""
        generator = SQLGenerator(agent=mock_agent)

        # Test components
        components = {
            "where_clause": "category = 'electronics'",
            "order_by_clause": "price DESC",
            "limit_clause": "10"
        }

        # Generate full SQL
        generator._generate_full_sql(components)

        # Verify the result
        assert "full_sql" in components
        assert "WHERE category = 'electronics'" in components["full_sql"]
        assert "ORDER BY price DESC" in components["full_sql"]
        assert "LIMIT 10" in components["full_sql"]

    def test_initialization_without_agent(self):
        """Test initializing SQLGenerator without providing an agent."""
        # Mock the GigachatAgent class to avoid actual API calls
        with patch("src.agent.agent.GigachatAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent
            
            # Initialize without providing an agent
            generator = SQLGenerator()
            
            # Verify that a new agent was created
            assert generator.agent is not None
            assert mock_agent_class.called

    def test_extract_sql_components_regex(self, mock_agent):
        """Test extracting SQL components using regex."""
        generator = SQLGenerator(agent=mock_agent)

        # Test response text
        response_text = """Based on the provided information, here are the SQL query components:

WHERE: category = 'electronics' AND price < 1000
ORDER BY: rating DESC
LIMIT: 10"""

        # Extract SQL components using regex
        components = generator._extract_sql_components_regex(response_text)

        # Verify the result
        assert components["where_clause"] == "category = 'electronics' AND price < 1000"
        assert components["order_by_clause"] == "rating DESC"
        assert components["limit_clause"] == "10"
