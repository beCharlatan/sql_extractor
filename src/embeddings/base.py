"""Базовый класс и типы для работы с эмбеддингами."""

from enum import Enum
from typing import Dict, Any
from abc import ABC, abstractmethod
from langchain_core.embeddings import Embeddings


class EmbeddingsType(str, Enum):
    """Типы доступных моделей эмбеддингов."""
    
    HUGGINGFACE = "huggingface"
    GIGACHAT = "gigachat"


class BaseEmbeddings(ABC):
    """Базовый класс для работы с различными моделями эмбеддингов."""
    
    @abstractmethod
    def get_embeddings(self) -> Embeddings:
        """Возвращает экземпляр модели эмбеддингов.
        
        Returns:
            Embeddings: Экземпляр модели эмбеддингов, совместимый с LangChain
        """
        pass
    
    @abstractmethod
    def get_type(self) -> EmbeddingsType:
        """Возвращает тип модели эмбеддингов.
        
        Returns:
            EmbeddingsType: Тип модели эмбеддингов
        """
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию модели эмбеддингов.
        
        Returns:
            Dict[str, Any]: Конфигурация модели эмбеддингов
        """
        pass
