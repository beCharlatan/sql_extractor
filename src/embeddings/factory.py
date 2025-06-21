"""Фабрика для создания различных типов эмбеддингов."""

from typing import Dict, Optional
from loguru import logger

from src.embeddings.base import BaseEmbeddings, EmbeddingsType
from src.embeddings.huggingface_embeddings import HuggingFaceEmbeddingsWrapper
from src.embeddings.gigachat_embeddings import GigaChatEmbeddingsWrapper
from src.config.settings import settings


class EmbeddingsFactory:
    """Фабрика для создания различных типов эмбеддингов."""
    
    _instance = None
    
    def __new__(cls):
        """Реализация паттерна Singleton для фабрики эмбеддингов."""
        if cls._instance is None:
            cls._instance = super(EmbeddingsFactory, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Инициализирует фабрику эмбеддингов."""
        if self._initialized:
            return
        
        self._initialized = True
        self._default_type = EmbeddingsType.HUGGINGFACE
        self._embeddings_cache: Dict[str, BaseEmbeddings] = {}
        logger.info("Фабрика эмбеддингов инициализирована")
    
    def get_embeddings(self, embeddings_type: Optional[EmbeddingsType] = None, **kwargs) -> BaseEmbeddings:
        """Возвращает экземпляр класса эмбеддингов указанного типа.
        
        Args:
            embeddings_type: Тип эмбеддингов. Если None, используется тип из настроек.
            **kwargs: Дополнительные параметры для инициализации эмбеддингов
            
        Returns:
            Экземпляр класса эмбеддингов
        """
        # Если тип не указан, используем тип из настроек
        if embeddings_type is None:
            default_type = settings.embeddings.default_type.lower()
            if default_type == "gigachat":
                embeddings_type = EmbeddingsType.GIGACHAT
            else:
                embeddings_type = EmbeddingsType.HUGGINGFACE
        
        # Создаем ключ кэша на основе типа и параметров
        cache_key = self._create_cache_key(embeddings_type, **kwargs)
        
        # Проверяем, есть ли уже созданный экземпляр в кэше
        if cache_key in self._embeddings_cache:
            logger.debug(f"Возвращаем закэшированный экземпляр эмбеддингов типа {embeddings_type}")
            return self._embeddings_cache[cache_key]
        
        # Создаем новый экземпляр модели эмбеддингов
        embeddings = self._create_embeddings(embeddings_type, **kwargs)
        
        # Сохраняем в кэш
        self._embeddings_cache[cache_key] = embeddings
        
        return embeddings
    
    def set_default_type(self, embeddings_type: EmbeddingsType):
        """Устанавливает тип модели эмбеддингов по умолчанию.
        
        Args:
            embeddings_type: Тип модели эмбеддингов по умолчанию
        """
        self._default_type = embeddings_type
        logger.info(f"Установлен тип эмбеддингов по умолчанию: {embeddings_type}")
    
    def get_default_type(self) -> EmbeddingsType:
        """Возвращает тип модели эмбеддингов по умолчанию.
        
        Returns:
            EmbeddingsType: Тип модели эмбеддингов по умолчанию
        """
        return self._default_type
    
    def _create_embeddings(self, embeddings_type: EmbeddingsType, **kwargs) -> BaseEmbeddings:
        """Создает экземпляр модели эмбеддингов указанного типа.
        
        Args:
            embeddings_type: Тип модели эмбеддингов
            **kwargs: Дополнительные параметры для инициализации модели эмбеддингов
            
        Returns:
            BaseEmbeddings: Экземпляр модели эмбеддингов
            
        Raises:
            ValueError: Если указан неизвестный тип модели эмбеддингов
        """
        if embeddings_type == EmbeddingsType.HUGGINGFACE:
            model_name = kwargs.get("model_name", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            logger.info(f"Создание экземпляра HuggingFace эмбеддингов с моделью: {model_name}")
            return HuggingFaceEmbeddingsWrapper(model_name=model_name)
        
        elif embeddings_type == EmbeddingsType.GIGACHAT:
            logger.info("Создание экземпляра GigaChat эмбеддингов")
            return GigaChatEmbeddingsWrapper()
        
    def _create_cache_key(self, embeddings_type: EmbeddingsType, **kwargs) -> str:
        """Создает ключ для кэширования экземпляра модели эмбеддингов.
        
        Args:
            embeddings_type: Тип модели эмбеддингов
            **kwargs: Дополнительные параметры для инициализации модели эмбеддингов
            
        Returns:
            str: Ключ для кэширования
        """
        if embeddings_type == EmbeddingsType.HUGGINGFACE:
            model_name = kwargs.get("model_name", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            return f"{embeddings_type.value}:{model_name}"
        
        elif embeddings_type == EmbeddingsType.GIGACHAT:
            # Для GigaChat не используем API ключ в ключе кэша, так как он может меняться
            return f"{embeddings_type.value}"

def get_embeddings_factory() -> EmbeddingsFactory:
    """Возвращает экземпляр фабрики эмбеддингов.
    
    Returns:
        EmbeddingsFactory: Экземпляр фабрики эмбеддингов
    """
    return EmbeddingsFactory()
