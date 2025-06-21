"""Реализация эмбеддингов на основе HuggingFace."""

from typing import Dict, Any, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings as LangchainHuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings
from loguru import logger

from src.embeddings.base import BaseEmbeddings, EmbeddingsType


class HuggingFaceEmbeddingsWrapper(BaseEmbeddings):
    """Класс-обертка для работы с эмбеддингами HuggingFace."""
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """Инициализирует модель эмбеддингов HuggingFace.
        
        Args:
            model_name: Название модели HuggingFace для эмбеддингов
        """
        self.model_name = model_name
        self._embeddings: Optional[LangchainHuggingFaceEmbeddings] = None
        logger.info(f"Инициализирована обертка для HuggingFace эмбеддингов с моделью: {model_name}")
    
    def get_embeddings(self) -> Embeddings:
        """Возвращает экземпляр модели эмбеддингов HuggingFace.
        
        Returns:
            Embeddings: Экземпляр модели эмбеддингов HuggingFace
        """
        if self._embeddings is None:
            logger.info(f"Загрузка модели эмбеддингов HuggingFace: {self.model_name}")
            self._embeddings = LangchainHuggingFaceEmbeddings(model_name=self.model_name)
        return self._embeddings
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Метод для создания эмбеддингов для списка текстов.
        
        Args:
            texts: Список текстов для создания эмбеддингов
            
        Returns:
            Список векторов эмбеддингов для каждого текста
        """
        embeddings = self.get_embeddings()
        return embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> list[float]:
        """Метод для создания эмбеддинга для одиночного запроса.
        
        Args:
            text: Текст запроса для создания эмбеддинга
            
        Returns:
            Вектор эмбеддинга для запроса
        """
        embeddings = self.get_embeddings()
        return embeddings.embed_query(text)
    
    def get_type(self) -> EmbeddingsType:
        """Возвращает тип модели эмбеддингов.
        
        Returns:
            EmbeddingsType: Тип модели эмбеддингов (HUGGINGFACE)
        """
        return EmbeddingsType.HUGGINGFACE
    
    def get_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию модели эмбеддингов HuggingFace.
        
        Returns:
            Dict[str, Any]: Конфигурация модели эмбеддингов HuggingFace
        """
        return {
            "model_name": self.model_name,
            "type": self.get_type().value
        }
