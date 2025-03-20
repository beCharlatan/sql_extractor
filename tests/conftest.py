import os
import pytest
import allure
from unittest.mock import patch, MagicMock


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    """Hook to add extra information to test reports."""
    module_name = item.module.__name__
    class_name = item.cls.__name__ if item.cls else ""
    allure.dynamic.label("module", module_name)
    if class_name:
        allure.dynamic.label("class", class_name)
    
    if "sql_generator" in module_name:
        allure.dynamic.feature("SQL Generator")
        allure.dynamic.epic("SQL Generation")
    elif "api" in module_name:
        allure.dynamic.feature("API")
        allure.dynamic.epic("API Integration")
    elif "db" in module_name or "postgres" in module_name:
        allure.dynamic.feature("Database Integration")
        allure.dynamic.epic("Database")
    elif "agent" in module_name:
        allure.dynamic.feature("AI Agent")
        allure.dynamic.epic("AI Integration")
    elif "kafka" in module_name:
        allure.dynamic.feature("Kafka Integration")
        allure.dynamic.epic("Asynchronous Processing")
    
    yield

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to add extra information to test reports."""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call":
        if item.function.__doc__:
            allure.dynamic.description(item.function.__doc__)


@pytest.fixture(scope="session")
def test_db_connection_string():
    """Get a test database connection string.
    
    This can be configured via environment variables for CI/CD pipelines
    or use a default test database configuration.
    """
    # Use environment variables if available, otherwise use test defaults
    host = os.getenv("TEST_DB_HOST", "localhost")
    port = os.getenv("TEST_DB_PORT", "5432")
    name = os.getenv("TEST_DB_NAME", "test_parameters_db")
    user = os.getenv("TEST_DB_USER", "postgres")
    password = os.getenv("TEST_DB_PASSWORD", "postgres_password")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


@pytest.fixture
def mock_asyncpg_pool():
    """Mock the asyncpg.create_pool function.
    
    Provides mocks for the asyncpg connection pool approach.
    """
    with patch('src.db.base_db_client.asyncpg.create_pool') as mock_create_pool:
        # Create mock connection and pool
        mock_connection = MagicMock()
        mock_pool = MagicMock()
        
        # Setup mocked fetch/execute methods
        mock_connection.fetch.return_value = []
        mock_connection.execute.return_value = "OK"
        
        # Setup pool acquire/release
        async def mock_acquire():
            return mock_connection
            
        mock_pool.acquire = mock_acquire
        mock_pool.release = MagicMock()
        
        # Make create_pool return the mock pool
        async def mock_pool_coro(*args, **kwargs):
            return mock_pool
            
        mock_create_pool.return_value = mock_pool_coro()
        
        # Return the mocks for use in tests
        yield mock_create_pool, mock_pool, mock_connection


@pytest.fixture
def mock_execute_query():
    """Mock the execute_query method in BaseDBClient.
    
    This fixture allows easy mocking of the execute_query method
    without needing to mock the entire connection pool.
    """
    with patch('src.db.base_db_client.BaseDBClient.execute_query') as mock_execute:
        # Default empty result
        async def mock_execute_coro(*args, **kwargs):
            return []
            
        mock_execute.side_effect = mock_execute_coro
        
        yield mock_execute
