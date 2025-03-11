"""Common test fixtures and configuration for the test suite."""

import os
import pytest
from unittest.mock import patch, MagicMock

from src.config.settings import settings


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
