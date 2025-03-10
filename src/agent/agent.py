"""AI Agent implementation using Gigachat."""
from typing import Any, Dict, Optional

from gigachat import GigaChat
from loguru import logger

from src.config.settings import settings
from src.utils.errors import GigachatAPIError, handle_exception


class GigachatAgent:
    """AI Agent implementation using Gigachat API."""

    def __init__(self, model: Optional[str] = None):
        """Initialize the Gigachat agent.

        Args:
            model: Optional model name to use. Defaults to the one specified in settings.
        """
        self.model = model or settings.gigachat.model
        self.client = self._initialize_client()
        logger.info(f"Initialized GigachatAgent with model: {self.model}")

    def _initialize_client(self) -> GigaChat:
        """Initialize the Gigachat client.

        Returns:
            Initialized Gigachat client.

        Raises:
            GigachatAPIError: If client initialization fails.
        """
        try:
            credentials = {}
            
            # Use API key if provided
            if settings.gigachat.api_key:
                credentials["credentials"] = settings.gigachat.api_key
            
            # Use credentials file if provided
            if settings.gigachat.credentials_path:
                credentials["credentials_path"] = settings.gigachat.credentials_path
                
            if not credentials:
                raise ValueError("No Gigachat credentials provided. Set GIGACHAT_API_KEY or GIGACHAT_CREDENTIALS_PATH.")
                
            return GigaChat(**credentials, scope="GIGACHAT_API_PERS", model="GigaChat", verify_ssl_certs=False)
        except Exception as e:
            error_msg = f"Failed to initialize Gigachat client: {str(e)}"
            logger.error(error_msg)
            raise GigachatAPIError(error_msg, details={"original_error": str(e)})

    def process_query(self, query: str, **kwargs) -> Dict[str, Any]:
        """Process a user query using the Gigachat model.

        Args:
            query: The user's query text.
            **kwargs: Additional parameters to pass to the Gigachat API.

        Returns:
            Dictionary containing the model's response and any extracted parameters.

        Raises:
            GigachatAPIError: If the API call fails.
        """
        try:
            # Log parameters but don't use them as API doesn't support them
            logger.info(f"Processing query with temperature: {settings.gigachat.temperature}, max_tokens: {settings.gigachat.max_tokens}")
            logger.debug(f"Query text: {query}")
            
            # Call the Gigachat API without temperature and max_tokens parameters
            response = self.client.chat(query)
            
            logger.info("Query processed successfully")
            return response
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            handle_exception(e)
            raise GigachatAPIError(error_msg, details={"query": query, "original_error": str(e)})
