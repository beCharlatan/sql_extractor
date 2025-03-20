"""Реализация ИИ-агента с использованием Gigachat."""
from typing import Any, Dict, Optional

from gigachat import GigaChat
from loguru import logger

from src.config.settings import settings
from src.utils.errors import GigachatAPIError, handle_exception


class GigachatAgent:
    """Реализация ИИ-агента с использованием API Gigachat."""

    def __init__(self, model: Optional[str] = None):
        """Инициализация агента Gigachat.

        Аргументы:
            model: Опциональное название модели для использования. По умолчанию используется модель, указанная в настройках.
        """
        self.model = model or settings.gigachat.model
        self.client = self._initialize_client()
        logger.info(f"Initialized GigachatAgent with model: {self.model}")

    def _initialize_client(self) -> GigaChat:
        """Инициализация клиента Gigachat.

        Возвращает:
            Инициализированный клиент Gigachat.

        Вызывает исключение:
            GigachatAPIError: Если инициализация клиента не удалась.
        """
        try:
            credentials = {}
            
            # Использовать API ключ, если он предоставлен
            if settings.gigachat.api_key:
                credentials["credentials"] = settings.gigachat.api_key
            
            # Использовать файл учетных данных, если он предоставлен
            if settings.gigachat.credentials_path:
                credentials["credentials_path"] = settings.gigachat.credentials_path
                
            if not credentials:
                raise ValueError("No Gigachat credentials provided. Set GIGACHAT_API_KEY or GIGACHAT_CREDENTIALS_PATH.")
                
            return GigaChat(**credentials, scope="GIGACHAT_API_PERS", model="GigaChat", verify_ssl_certs=False)
        except Exception as e:
            error_msg = f"Failed to initialize Gigachat client: {str(e)}"
            logger.error(error_msg)
            raise GigachatAPIError(error_msg, details={"original_error": str(e)})

    def process_query(self, query: str) -> Dict[str, Any]:
        """Обработка запроса пользователя с использованием модели Gigachat.

        Аргументы:
            query: Текст запроса пользователя.

        Возвращает:
            Словарь, содержащий ответ модели.

        Вызывает исключение:
            GigachatAPIError: Если вызов API завершается с ошибкой.
        """
        try:
            # Логируем параметры, но не используем их, так как API их не поддерживает
            logger.info(f"Processing query with temperature: {settings.gigachat.temperature}, max_tokens: {settings.gigachat.max_tokens}")
            logger.debug(f"Query text: {query}")
            
            # Вызываем API Gigachat без параметров temperature и max_tokens
            response = self.client.chat(query)
            
            logger.info("Query processed successfully")
            return response
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            handle_exception(e)
            raise GigachatAPIError(error_msg, details={"query": query, "original_error": str(e)})
