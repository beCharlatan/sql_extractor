"""Tests for the GigachatAgent class."""

import pytest
from unittest.mock import MagicMock, patch

from src.agent.agent import GigachatAgent
from src.utils.errors import GigachatAPIError


class TestGigachatAgent:
    """Test cases for the GigachatAgent class."""

    def test_process_query_success(self):
        """Test successful query processing."""
        # Mock the GigaChat client
        with patch("src.agent.agent.GigaChat") as mock_gigachat_class:
            mock_client = MagicMock()
            mock_client.chat.return_value = {"choices": [{"message": {"content": "Test response"}}]}
            mock_gigachat_class.return_value = mock_client
            
            # Create agent with mocked client
            with patch("src.agent.agent.settings") as mock_settings:
                mock_settings.gigachat.api_key = "test_key"
                mock_settings.gigachat.credentials_path = None
                mock_settings.gigachat.temperature = 0.1
                mock_settings.gigachat.max_tokens = 1000
                
                agent = GigachatAgent()
                
                # Process a query
                result = agent.process_query("Test query")
                
                # Verify the result
                assert "response" in result
                assert result["response"] == "Test response"
                
                # Verify the client was called correctly
                mock_client.chat.assert_called_once()
                call_args = mock_client.chat.call_args[1]
                assert call_args["messages"][0]["content"] == "Test query"
                assert call_args["temperature"] == 0.1
                assert call_args["max_tokens"] == 1000

    def test_process_query_error(self):
        """Test error handling during query processing."""
        # Mock the GigaChat client to raise an exception
        with patch("src.agent.agent.GigaChat") as mock_gigachat_class:
            mock_client = MagicMock()
            mock_client.chat.side_effect = Exception("Test error")
            mock_gigachat_class.return_value = mock_client
            
            # Create agent with mocked client
            with patch("src.agent.agent.settings") as mock_settings:
                mock_settings.gigachat.api_key = "test_key"
                mock_settings.gigachat.credentials_path = None
                
                agent = GigachatAgent()
                
                # Process a query - should raise GigachatAPIError
                with pytest.raises(GigachatAPIError) as exc_info:
                    agent.process_query("Test query")
                
                # Verify the error details
                assert "Error processing query" in str(exc_info.value)
                assert "Test error" in str(exc_info.value.details)

    def test_initialize_client_with_api_key(self):
        """Test initializing client with API key."""
        with patch("src.agent.agent.GigaChat") as mock_gigachat_class:
            mock_client = MagicMock()
            mock_gigachat_class.return_value = mock_client
            
            # Create settings with API key
            with patch("src.agent.agent.settings") as mock_settings:
                mock_settings.gigachat.api_key = "test_api_key"
                mock_settings.gigachat.credentials_path = None
                
                # Initialize agent
                agent = GigachatAgent()
                
                # Verify GigaChat was initialized with correct credentials
                mock_gigachat_class.assert_called_once_with(credentials="test_api_key")

    def test_initialize_client_with_credentials_path(self):
        """Test initializing client with credentials path."""
        with patch("src.agent.agent.GigaChat") as mock_gigachat_class:
            mock_client = MagicMock()
            mock_gigachat_class.return_value = mock_client
            
            # Create settings with credentials path
            with patch("src.agent.agent.settings") as mock_settings:
                mock_settings.gigachat.api_key = None
                mock_settings.gigachat.credentials_path = "/path/to/credentials"
                
                # Initialize agent
                agent = GigachatAgent()
                
                # Verify GigaChat was initialized with correct credentials
                mock_gigachat_class.assert_called_once_with(credentials_path="/path/to/credentials")

    def test_initialize_client_no_credentials(self):
        """Test error when no credentials are provided."""
        with patch("src.agent.agent.GigaChat") as mock_gigachat_class:
            # Create settings with no credentials
            with patch("src.agent.agent.settings") as mock_settings:
                mock_settings.gigachat.api_key = None
                mock_settings.gigachat.credentials_path = None
                
                # Initialize agent - should raise GigachatAPIError
                with pytest.raises(GigachatAPIError) as exc_info:
                    GigachatAgent()
                
                # Verify the error message
                assert "No Gigachat credentials provided" in str(exc_info.value)
                
                # Verify GigaChat was not called
                mock_gigachat_class.assert_not_called()
