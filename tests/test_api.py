"""Tests for the API endpoints."""

import pytest
import allure
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from src.api.main import app
from src.agent.agent import GigachatAgent
from src.agent.sql_generator import SQLGenerator
from src.api.routes import get_sql_generator
from src.utils.errors import GigachatAPIError, SQLGenerationError, InvalidSQLError, InvalidTableDDLError


# Create mock responses for testing
def mock_gigachat_response():
    return {"choices": [{"message": {"content": "Test response"}}]}


def mock_sql_components():
    return {
        "sql_components": {
            "where_clause": "category = 'electronics' AND price < 1000",
            "order_by_clause": "rating DESC",
            "limit_clause": "10",
            "full_sql": "SELECT * FROM products WHERE category = 'electronics' AND price < 1000 ORDER BY rating DESC LIMIT 10"
        }
    }


# Setup test client with mocked dependencies
@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with patch("src.api.routes.get_gigachat_agent") as mock_get_agent:
        # Setup mock agent
        agent = MagicMock(spec=GigachatAgent)
        agent.process_query.return_value = mock_gigachat_response()
        mock_get_agent.return_value = agent
        
        # Mock the database schema tool
        with patch("src.db.db_schema_tool.DBSchemaReferenceTool.get_table_schema") as mock_get_schema:
            # Setup mock schema response
            mock_get_schema.return_value = "CREATE TABLE products (id INT PRIMARY KEY, name VARCHAR(100), price DECIMAL(10, 2), rating DECIMAL(3, 2), category VARCHAR(50));"
            
            with patch("src.api.routes.get_sql_generator") as mock_get_generator:
                # Setup mock SQL generator
                generator = MagicMock(spec=SQLGenerator)
                generator.generate_sql_components.return_value = mock_sql_components()
                mock_get_generator.return_value = generator
                
                # Return test client
                yield TestClient(app)


class TestHealthAPI:
    """Test cases for the health check endpoint."""

    @allure.feature("Проверка доступности")
    @allure.story("Проверка работоспособности сервиса")
    @allure.title("Проверка доступности и работоспособности сервиса")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.id("TC-001")
    def test_health_check(self):
        """Test the health check endpoint."""
        client = TestClient(app)  # No need for mocks for health check
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "extract-parameter-agent"
        assert "version" in data
        assert "timestamp" in data


class TestGenerateSQLAPI:
    """Test cases for the generate-sql endpoint."""
    
    @allure.feature("Генерация SQL")
    @allure.story("Успешная генерация SQL")
    @allure.title("Успешная генерация SQL запроса")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.id("TC-002")
    def test_generate_sql_success(self, client):
        """Test successful SQL generation."""
        # Test request data
        request_data = {
            "filter": "Find products in the electronics category with price less than 1000",
            "constraint": "Sort by highest rating and limit to 10 results"
        }
        
        # Send request
        response = client.post("/client/generate-sql", json=request_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "sql_components" in data
        assert "where_clause" in data["sql_components"]
        assert "order_by_clause" in data["sql_components"]
        assert "limit_clause" in data["sql_components"]
        assert "full_sql" in data["sql_components"]

    @allure.feature("Генерация SQL")
    @allure.story("Обработка ошибок")
    @allure.title("Обработка ошибки валидации запроса")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.id("TC-003")
    def test_validation_error(self, client):
        """Test validation error for invalid request data."""
        # Invalid request (empty filter)
        request_data = {
            "filter": "",  # Empty filter should fail validation
            "constraint": "Sort by highest rating"
        }
        
        # Send request
        response = client.post("/client/generate-sql", json=request_data)
        
        # Check response
        assert response.status_code == 422  # Unprocessable Entity
        data = response.json()
        assert "detail" in data
    
    @allure.feature("Генерация SQL")
    @allure.story("Обработка ошибок")
    @allure.title("Обработка ошибки некорректного формата DDL таблицы")
    @allure.severity(allure.severity_level.HIGH)
    @allure.id("TC-004")
    def test_invalid_table_ddl_error(self, client):
        """Test error handling for invalid table DDL."""
        # Создаем мок, который будет вызывать ошибку
        def mock_generator_with_error():
            generator = MagicMock(spec=SQLGenerator)
            generator.generate_sql_components.side_effect = InvalidTableDDLError(
                "Invalid table DDL format",
                details={"field": "table_ddl"}
            )
            return generator
        
        # Сохраняем оригинальную зависимость
        original_dependency = app.dependency_overrides.get(get_sql_generator, None)
        
        try:
            # Переопределяем зависимость для генератора SQL
            app.dependency_overrides[get_sql_generator] = mock_generator_with_error
            
            # Создаем тестовый клиент с переопределенной зависимостью
            test_client = TestClient(app)
            
            # Тестовые данные запроса
            request_data = {
                "filter": "Find products",
                "constraint": "Sort by rating"
            }
            
            # Отправляем запрос
            response = test_client.post("/client/generate-sql", json=request_data)
            
            # Проверяем ответ
            assert response.status_code == 400  # Bad Request
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]
            assert "details" in data["detail"]
        finally:
            # Восстанавливаем оригинальную зависимость
            if original_dependency is None:
                app.dependency_overrides.pop(get_sql_generator, None)
            else:
                app.dependency_overrides[get_sql_generator] = original_dependency

    @allure.feature("Генерация SQL")
    @allure.story("Обработка ошибок")
    @allure.title("Обработка ошибки генерации SQL")
    @allure.severity(allure.severity_level.HIGH)
    @allure.id("TC-005")
    def test_sql_generation_error(self, client):
        """Test error handling for SQL generation errors."""
        # Создаем мок, который будет вызывать ошибку
        def mock_generator_with_error():
            generator = MagicMock(spec=SQLGenerator)
            generator.generate_sql_components.side_effect = SQLGenerationError(
                "Failed to generate SQL",
                details={"error_type": "parsing_error"}
            )
            return generator
        
        # Сохраняем оригинальную зависимость
        original_dependency = app.dependency_overrides.get(get_sql_generator, None)
        
        try:
            # Переопределяем зависимость для генератора SQL
            app.dependency_overrides[get_sql_generator] = mock_generator_with_error
            
            # Создаем тестовый клиент с переопределенной зависимостью
            test_client = TestClient(app)
            
            # Тестовые данные запроса
            request_data = {
                "filter": "Find products with complex conditions",
                "constraint": "Sort in a way that's hard to parse"
            }
            
            # Отправляем запрос
            response = test_client.post("/client/generate-sql", json=request_data)
            
            # Проверяем ответ
            assert response.status_code == 500  # Internal Server Error
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]
            assert "details" in data["detail"]
        finally:
            # Восстанавливаем оригинальную зависимость
            if original_dependency is None:
                app.dependency_overrides.pop(get_sql_generator, None)
            else:
                app.dependency_overrides[get_sql_generator] = original_dependency

    @allure.feature("Генерация SQL")
    @allure.story("Обработка ошибок")
    @allure.title("Обработка ошибки API Gigachat")
    @allure.severity(allure.severity_level.HIGH)
    @allure.id("TC-006")
    def test_gigachat_api_error(self, client):
        """Test error handling for Gigachat API errors."""
        # Создаем мок, который будет вызывать ошибку
        def mock_generator_with_error():
            generator = MagicMock(spec=SQLGenerator)
            generator.generate_sql_components.side_effect = GigachatAPIError(
                "Failed to connect to Gigachat API",
                details={"status_code": 502}
            )
            return generator
        
        # Сохраняем оригинальную зависимость
        original_dependency = app.dependency_overrides.get(get_sql_generator, None)
        
        try:
            # Переопределяем зависимость для генератора SQL
            app.dependency_overrides[get_sql_generator] = mock_generator_with_error
            
            # Создаем тестовый клиент с переопределенной зависимостью
            test_client = TestClient(app)
            
            # Тестовые данные запроса
            request_data = {
                "filter": "Find products",
                "constraint": "Sort by rating"
            }
            
            # Отправляем запрос
            response = test_client.post("/client/generate-sql", json=request_data)
            
            # Проверяем ответ
            assert response.status_code == 502  # Bad Gateway
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]
            assert "details" in data["detail"]
        finally:
            # Восстанавливаем оригинальную зависимость
            if original_dependency is None:
                app.dependency_overrides.pop(get_sql_generator, None)
            else:
                app.dependency_overrides[get_sql_generator] = original_dependency

    @allure.feature("Генерация SQL")
    @allure.story("Обработка ошибок")
    @allure.title("Обработка ошибки некорректного SQL запроса")
    @allure.severity(allure.severity_level.HIGH)
    @allure.id("TC-007")
    def test_invalid_sql_error(self, client):
        """Test error handling for invalid SQL errors."""
        # Создаем мок, который будет вызывать ошибку
        def mock_generator_with_error():
            generator = MagicMock(spec=SQLGenerator)
            generator.generate_sql_components.side_effect = InvalidSQLError(
                "Invalid SQL syntax",
                details={"component": "where_clause"}
            )
            return generator
        
        # Сохраняем оригинальную зависимость
        original_dependency = app.dependency_overrides.get(get_sql_generator, None)
        
        try:
            # Переопределяем зависимость для генератора SQL
            app.dependency_overrides[get_sql_generator] = mock_generator_with_error
            
            # Создаем тестовый клиент с переопределенной зависимостью
            test_client = TestClient(app)
            
            # Тестовые данные запроса
            request_data = {
                "filter": "Find products with invalid conditions",
                "constraint": "Sort by rating"
            }
            
            # Отправляем запрос
            response = test_client.post("/client/generate-sql", json=request_data)
            
            # Проверяем ответ
            assert response.status_code == 400  # Bad Request
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]
            assert "details" in data["detail"]
        finally:
            # Восстанавливаем оригинальную зависимость
            if original_dependency is None:
                app.dependency_overrides.pop(get_sql_generator, None)
            else:
                app.dependency_overrides[get_sql_generator] = original_dependency
