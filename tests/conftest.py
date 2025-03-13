"""Common test fixtures and configuration for the test suite."""

import os
import pytest
import allure
from unittest.mock import patch, MagicMock

from src.config.settings import settings

# u041du0430u0441u0442u0440u043eu0439u043au0438 u0434u043bu044f u0438u043du0442u0435u0433u0440u0430u0446u0438u0438 u0441 Allure TestOps
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    """Hook to add extra information to test reports."""
    # u0414u043eu0431u0430u0432u043bu044fu0435u043c u0438u043du0444u043eu0440u043cu0430u0446u0438u044e u043e u043cu043eu0434u0443u043bu0435 u0438 u043au043bu0430u0441u0441u0435 u0442u0435u0441u0442u0430 u0432 u043eu0442u0447u0435u0442 Allure
    module_name = item.module.__name__
    class_name = item.cls.__name__ if item.cls else ""
    allure.dynamic.label("module", module_name)
    if class_name:
        allure.dynamic.label("class", class_name)
    
    # u0414u043eu0431u0430u0432u043bu044fu0435u043c u043cu0435u0442u043au0438 u043du0430 u043eu0441u043du043eu0432u0435 u0438u043cu0435u043du0438 u043cu043eu0434u0443u043bu044f
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
    
    yield

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to add extra information to test reports."""
    outcome = yield
    report = outcome.get_result()
    
    # u0414u043eu0431u0430u0432u043bu044fu0435u043c u0434u043eu043fu043eu043bu043du0438u0442u0435u043bu044cu043du0443u044e u0438u043du0444u043eu0440u043cu0430u0446u0438u044e u043e u0442u0435u0441u0442u0435 u0432 u043eu0442u0447u0435u0442 Allure
    if report.when == "call":
        # u0414u043eu0431u0430u0432u043bu044fu0435u043c u0434u043eu043au0441u0442u0440u0438u043du0433 u0442u0435u0441u0442u0430 u0432 u043au0430u0447u0435u0441u0442u0432u0435 u043eu043fu0438u0441u0430u043du0438u044f
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
def mock_db_connection():
    """Mock the psycopg2.connect function.
    
    This is a general-purpose mock for database connections that can be used
    across multiple test files.
    """
    with patch('psycopg2.connect') as mock_connect:
        # Create mock cursor and connection
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Return the mocks for use in tests
        yield mock_connect, mock_connection, mock_cursor
