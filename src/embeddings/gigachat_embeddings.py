"""Реализация эмбеддингов на основе GigaChat."""

from typing import Dict, Any, Optional, List
from langchain_core.embeddings import Embeddings
from loguru import logger
from langchain_gigachat.embeddings import GigaChatEmbeddings

from src.embeddings.base import BaseEmbeddings, EmbeddingsType
from src.config.settings import settings


class GigaChatEmbeddingsWrapper(BaseEmbeddings):
    """Класс-обертка для работы с эмбеддингами GigaChat."""
    
    def __init__(self):
        """Инициализирует модель эмбеддингов GigaChat."""
        self.api_key = settings.gigachat.api_key
        self._embeddings: Optional[GigaChatEmbeddings] = None
        logger.info("Инициализирована обертка для GigaChat эмбеддингов")
    
    def get_embeddings(self) -> Embeddings:
        """Возвращает экземпляр модели эмбеддингов GigaChat.
        
        Returns:
            Embeddings: Экземпляр модели эмбеддингов GigaChat
        """
        if self._embeddings is None:
            logger.info("Инициализация модели эмбеддингов GigaChat")
            # Используем стандартные настройки GigaChat API со Sber AI API
            self._embeddings = GigaChatEmbeddings(
                credentials=self.api_key,
                base_url="https://gigachat.devices.sberbank.ru/api/v1",
                scope="GIGACHAT_API_PERS",
                verify_ssl_certs=False
            )
        return self._embeddings
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Создает эмбеддинги для списка текстов.
        
        Args:
            texts: Список текстов для создания эмбеддингов
            
        Returns:
            List[List[float]]: Список векторов эмбеддингов
        """
        return self.get_embeddings().embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """Создает эмбеддинг для одного текста запроса.
        
        Args:
            text: Текст для создания эмбеддинга
            
        Returns:
            List[float]: Вектор эмбеддинга
        """
        return self.get_embeddings().embed_query(text)
        
    def get_type(self) -> EmbeddingsType:
        """Возвращает тип модели эмбеддингов.
        
        Returns:
            EmbeddingsType: Тип модели эмбеддингов (GIGACHAT)
        """
        return EmbeddingsType.GIGACHAT
    
    def get_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию модели эмбеддингов GigaChat.
        
        Returns:
            Dict[str, Any]: Конфигурация модели эмбеддингов GigaChat
        """
        return {
            "type": self.get_type().value,
        }
