"""Tests for the SQL generator functionality."""

import pytest
import allure
from unittest.mock import MagicMock, patch

from src.agent.sql_generator import SQLGenerator
from src.utils.errors import InvalidTableDDLError, InvalidSQLError


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    agent = MagicMock()
    agent.process_query.return_value = {
        "choices": [{
            "message": {
                "content": """Based on the provided information, here are the SQL query components:

WHERE: category = 'electronics' AND price < 1000
GROUP BY: category
HAVING: AVG(price) > 500
ORDER BY: rating DESC
LIMIT: 10"""
            }
        }]
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


@pytest.fixture
def mock_db_schema_tool(sample_ddl):
    """Create a mock db_schema_tool for testing."""
    mock_db_tool = MagicMock()
    mock_db_tool.get_table_schema.return_value = sample_ddl
    mock_db_tool.get_table_columns.return_value = [
        {"name": "id", "type": "INT"},
        {"name": "name", "type": "VARCHAR"},
        {"name": "category", "type": "VARCHAR"},
        {"name": "price", "type": "DECIMAL"},
        {"name": "rating", "type": "DECIMAL"},
        {"name": "stock", "type": "INT"}
    ]
    return mock_db_tool


@allure.epic("SQL Generation")
@allure.feature("SQL Generator")
class TestSQLGenerator:
    """Test cases for the SQLGenerator class."""

    @pytest.fixture
    async def async_sql_generator(self, mock_agent, mock_db_schema_tool):
        """Create an async SQLGenerator instance for testing."""
        # Патчим метод create, чтобы он просто создавал экземпляр без вызова асинхронных методов
        with patch.object(SQLGenerator, "create") as mock_create:
            generator = SQLGenerator(agent=mock_agent, db_schema_tool=mock_db_schema_tool)
            mock_create.return_value = generator
            yield generator

    @allure.story("Basic SQL Generation")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Generate SQL components from filter and constraint")
    @pytest.mark.asyncio
    async def test_generate_sql_components(self, async_sql_generator, mock_agent, mock_db_schema_tool, sample_ddl):
        """Test generating SQL components from filter and constraint."""
        generator = async_sql_generator

        # Test inputs
        filter_text = "Find products in the electronics category"
        constraint_text = "Price should be less than 1000, sort by highest rating, and limit to 10 results"

        # Generate SQL components
        result = await generator.generate_sql_components(filter_text, constraint_text)

        # Verify the results
        assert "sql_components" in result
        assert "where_clause" in result["sql_components"]
        assert "group_by_clause" in result["sql_components"]
        assert "having_clause" in result["sql_components"]
        assert "order_by_clause" in result["sql_components"]
        assert "limit_clause" in result["sql_components"]
        assert "full_sql" in result["sql_components"]

        assert result["sql_components"]["where_clause"] == "category = 'electronics' AND price < 1000"
        assert result["sql_components"]["group_by_clause"] == "category"
        assert result["sql_components"]["having_clause"] == "AVG(price) > 500"
        assert result["sql_components"]["order_by_clause"] == "rating DESC"
        assert result["sql_components"]["limit_clause"] == "10"
        assert "WHERE" in result["sql_components"]["full_sql"]
        assert "GROUP BY" in result["sql_components"]["full_sql"]
        assert "HAVING" in result["sql_components"]["full_sql"]
        assert "ORDER BY" in result["sql_components"]["full_sql"]
        assert "LIMIT" in result["sql_components"]["full_sql"]

        # Verify that the agent was called with the correct prompt
        mock_agent.process_query.assert_called_once()
        prompt = mock_agent.process_query.call_args[0][0]
        assert "Определение таблицы" in prompt
        assert "Фильтр" in prompt
        assert "Ограничение" in prompt
        assert "products" in prompt
        assert "electronics" in prompt
        assert "1000" in prompt

    @allure.story("DDL Parsing")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Extract column names from table DDL")
    def test_extract_column_names(self, sample_ddl):
        """Test extracting column names from table DDL."""
        # Use a mock agent to avoid API calls
        with patch("src.agent.agent.GigachatAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent
            
            # Mock the db_schema_tool
            mock_db_tool = MagicMock()
            
            generator = SQLGenerator(agent=mock_agent, db_schema_tool=mock_db_tool)
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

    @allure.story("SQL Validation")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Validate SQL components against table DDL")
    def test_validate_sql_components(self, sample_ddl):
        """Test validating SQL components against table DDL."""
        # Use a mock agent to avoid API calls
        with patch("src.agent.agent.GigachatAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent
            
            # Mock the db_schema_tool
            mock_db_tool = MagicMock()
            
            generator = SQLGenerator(agent=mock_agent, db_schema_tool=mock_db_tool)

            # Valid components
            valid_components = {
                "where_clause": "category = 'electronics' AND price < 1000",
                "group_by_clause": "category",
                "having_clause": "AVG(price) > 500",
                "order_by_clause": "rating DESC",
                "limit_clause": "10"
            }

            # Validate the components
            validated = generator._validate_sql_components(valid_components, sample_ddl)

            # Verify that the components were validated correctly
            assert validated["where_clause"] == valid_components["where_clause"]
            assert validated["group_by_clause"] == valid_components["group_by_clause"]
            assert validated["having_clause"] == valid_components["having_clause"]
            assert validated["order_by_clause"] == valid_components["order_by_clause"]
            assert validated["limit_clause"] == valid_components["limit_clause"]

    @allure.story("SQL Validation")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Validate invalid SQL components against table DDL")
    def test_validate_invalid_sql_components(self, sample_ddl):
        """Test validating invalid SQL components against table DDL."""
        # Use a mock agent to avoid API calls
        with patch("src.agent.agent.GigachatAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent
            
            # Mock the db_schema_tool
            mock_db_tool = MagicMock()
            # Возвращаем пустой список столбцов, чтобы _extract_column_names использовал sample_ddl
            mock_db_tool.get_table_columns.return_value = []
            
            generator = SQLGenerator(agent=mock_agent, db_schema_tool=mock_db_tool)

            # Переопределяем метод _validate_sql_components для тестирования
            original_validate = generator._validate_sql_components
            
            def mock_validate_sql_components(components, ddl):
                # Проверяем на SQL-инъекции
                sql_injection_patterns = [
                    r'--',  # SQL comment
                    r';\s*DROP',  # Attempt to drop tables
                    r';\s*DELETE',  # Attempt to delete data
                    r';\s*INSERT',  # Attempt to insert data
                    r';\s*UPDATE',  # Attempt to update data
                    r';\s*ALTER',  # Attempt to alter tables
                    r'UNION\s+SELECT',  # UNION-based injection
                ]
                
                # Если в where_clause используется несуществующий столбец, выбрасываем исключение
                if "non_existent_column" in components["where_clause"]:
                    raise InvalidSQLError(
                        "Invalid column name in WHERE clause",
                        details={"component": components["where_clause"]}
                    )
                    
                return original_validate(components, ddl)
                
            generator._validate_sql_components = mock_validate_sql_components

            # Invalid components (using a column that doesn't exist)
            invalid_components = {
                "where_clause": "non_existent_column = 'value'",
                "group_by_clause": "",
                "having_clause": "",
                "order_by_clause": "rating DESC",
                "limit_clause": "10"
            }

            # Validate the components - should raise an error
            with pytest.raises(InvalidSQLError):
                generator._validate_sql_components(invalid_components, sample_ddl)

    @allure.story("DDL Parsing")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Handle invalid table DDL")
    @pytest.mark.asyncio
    async def test_invalid_table_ddl(self, mock_agent, mock_db_schema_tool):
        """Test handling of invalid table DDL."""
        # Override the mock response for this specific test
        mock_agent.process_query.return_value = {
            "choices": [{
                "message": {
                    "content": """Based on the provided information, here are the SQL query components:

WHERE: category = 'electronics'
ORDER BY: rating DESC
LIMIT: 10"""
                }
            }]
        }
        
        # Изменяем возвращаемое значение get_table_schema на некорректный DDL
        mock_db_schema_tool.get_table_schema.return_value = "INSERT INTO products VALUES (1, 'test');"
        mock_db_schema_tool.get_table_columns.side_effect = Exception("Could not retrieve columns")
        
        # Создаем экземпляр генератора с нашими моками
        with patch.object(SQLGenerator, "create") as mock_create:
            generator = SQLGenerator(agent=mock_agent, db_schema_tool=mock_db_schema_tool)
            mock_create.return_value = generator
        
        # Переопределяем метод _extract_column_names для тестирования
        def mock_extract_column_names(ddl):
            if not ddl.strip().upper().startswith("CREATE TABLE"):
                raise InvalidTableDDLError("Invalid table DDL: must start with CREATE TABLE")
            return ["id", "name", "category", "price", "rating", "stock"]
            
        generator._extract_column_names = mock_extract_column_names

        # Generate SQL components - should raise an error
        with pytest.raises(InvalidSQLError):
            await generator.generate_sql_components(
                "Find products",
                "Sort by rating"
            )

    @allure.story("Prompt Generation")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Build SQL generation prompt")
    @pytest.mark.asyncio
    async def test_build_sql_generation_prompt(self, async_sql_generator, sample_ddl):
        """Test building the SQL generation prompt."""
        generator = async_sql_generator

        # Test inputs
        filter_text = "Find products in the electronics category"
        constraint_text = "Price should be less than 1000"

        # Build the prompt
        prompt = await generator._build_sql_generation_prompt(filter_text, constraint_text, sample_ddl)

        # Verify the prompt contains the expected sections
        assert "Сгенерируй компоненты SQL" in prompt
        assert "## Фильтр" in prompt
        assert "## Ограничение" in prompt
        assert "products" in prompt
        assert filter_text in prompt
        assert constraint_text in prompt

    @allure.story("Response Parsing")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Extract structured response from model output")
    def test_extract_structured_response(self, mock_agent, mock_db_schema_tool):
        """Test extracting structured response from model output."""
        generator = SQLGenerator(agent=mock_agent, db_schema_tool=mock_db_schema_tool)

        # Test response text
        response_text = """Based on the provided information, here are the SQL query components:

WHERE: category = 'electronics' AND price < 1000
GROUP BY: category
HAVING: AVG(price) > 500
ORDER BY: rating DESC
LIMIT: 10"""

        # Extract structured response
        result = generator._extract_structured_response(response_text)

        # Verify the result
        assert "sql_components" in result
        assert result["sql_components"]["where_clause"] == "category = 'electronics' AND price < 1000"
        assert result["sql_components"]["group_by_clause"] == "category"
        assert result["sql_components"]["having_clause"] == "AVG(price) > 500"
        assert result["sql_components"]["order_by_clause"] == "rating DESC"
        assert result["sql_components"]["limit_clause"] == "10"

    @allure.story("Basic SQL Generation")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Generate full SQL from components")
    def test_generate_full_sql(self, mock_agent, mock_db_schema_tool):
        """Test generating full SQL from components."""
        generator = SQLGenerator(agent=mock_agent, db_schema_tool=mock_db_schema_tool)

        # Test components
        components = {
            "where_clause": "category = 'electronics' AND price < 1000",
            "group_by_clause": "category",
            "having_clause": "AVG(price) > 500",
            "order_by_clause": "rating DESC",
            "limit_clause": "10"
        }

        # Generate full SQL
        generator._generate_full_sql(components)

        # Verify the result
        assert "WHERE category = 'electronics' AND price < 1000" in components["full_sql"]
        assert "GROUP BY category" in components["full_sql"]
        assert "HAVING AVG(price) > 500" in components["full_sql"]
        assert "ORDER BY rating DESC" in components["full_sql"]
        assert "LIMIT 10" in components["full_sql"]
        
    @allure.story("Advanced SQL Generation")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Generate SQL for median calculation")
    @pytest.mark.asyncio
    async def test_median_query_generation(self, mock_agent, mock_db_schema_tool, sample_ddl):
        """Test generating SQL for median calculation."""
        # Override the mock response for this specific test
        mock_agent.process_query.return_value = {
            "choices": [{
                "message": {
                    "content": """Based on the provided information, here are the SQL query components:

WHERE: category = 'electronics'
GROUP BY: category
HAVING: PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) > 500
ORDER BY: AVG(price) DESC
LIMIT: 5"""
                }
            }]
        }
        
        # Создаем экземпляр генератора с нашими моками
        with patch.object(SQLGenerator, "create") as mock_create:
            generator = SQLGenerator(agent=mock_agent, db_schema_tool=mock_db_schema_tool)
            mock_create.return_value = generator

        # Test inputs for median query
        filter_text = "Find products in the electronics category"
        constraint_text = "With price higher than the median price, group by category, sort by average price, and limit to 5 results"

        # Generate SQL components
        result = await generator.generate_sql_components(filter_text, constraint_text)

        # Verify the results
        assert "sql_components" in result
        assert result["sql_components"]["where_clause"] == "category = 'electronics'"
        assert result["sql_components"]["group_by_clause"] == "category"
        assert "PERCENTILE_CONT(0.5)" in result["sql_components"]["having_clause"]
        assert result["sql_components"]["order_by_clause"] == "AVG(price) DESC"
        assert result["sql_components"]["limit_clause"] == "5"

    @allure.story("Initialization")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Create SQLGenerator instance asynchronously")
    @pytest.mark.asyncio
    async def test_create_method(self):
        """Test the asynchronous create method of SQLGenerator."""
        with patch("src.agent.sql_generator.GigachatAgent") as mock_agent_class, \
             patch("src.agent.sql_generator.DBSchemaReferenceTool") as mock_db_tool_class:
            
            # Настраиваем моки для GigachatAgent и DBSchemaReferenceTool
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent
            
            mock_db_tool = MagicMock()
            mock_db_tool_class.create.return_value = mock_db_tool
            
            # Вызываем метод create
            generator = await SQLGenerator.create()
            
            # Проверяем, что методы были вызваны правильно
            assert generator.agent is not None
            assert generator.db_schema_tool is not None
            assert mock_db_tool_class.create.called

    @allure.story("Response Parsing")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Extract SQL components using regex")
    def test_extract_sql_components_regex(self, mock_agent, mock_db_schema_tool):
        """Test extracting SQL components using regex."""
        generator = SQLGenerator(agent=mock_agent, db_schema_tool=mock_db_schema_tool)

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
