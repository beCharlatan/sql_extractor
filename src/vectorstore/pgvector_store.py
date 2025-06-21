"""
Модуль для работы с векторным хранилищем на основе PostgreSQL + pgvector.
Предоставляет класс для создания, настройки и работы с векторными хранилищами.
"""

import asyncpg
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
from langchain_community.vectorstores import PGVector
from langchain_core.documents import Document

from src.config.settings import settings
from src.embeddings import EmbeddingsType
from src.embeddings.factory import get_embeddings_factory


class PGVectorStore:
    """
    Класс для работы с векторным хранилищем на основе PostgreSQL + pgvector.
    Предоставляет методы для настройки расширения pgvector, создания коллекций и поиска.
    """
    
    def __init__(self, collection_name: str, embeddings_type: Optional[EmbeddingsType] = None):
        """
        Инициализирует экземпляр класса PGVectorStore.
        
        Args:
            collection_name: Имя коллекции в PostgreSQL для хранения векторов
            embeddings_type: Тип эмбеддингов для использования. Если None, используется тип по умолчанию.
        """
        self.collection_name = collection_name
        self.connection_string = settings.database.get_connection_string()
        
        # Инициализируем эмбеддинги через фабрику
        embeddings_factory = get_embeddings_factory()
        self.embeddings = embeddings_factory.get_embeddings(embeddings_type)
        
        # Векторное хранилище будет создано при первом использовании
        self._vector_store = None
        
        logger.info(f"Инициализирован PGVectorStore для коллекции {collection_name}")
    
    @staticmethod
    async def setup_pgvector():
        """
        Настраивает расширение pgvector в базе данных PostgreSQL.
        Эту функцию следует вызвать перед первым использованием векторного хранилища.
        
        Returns:
            bool: True, если расширение успешно настроено, иначе False.
        """
        try:
            # Подключаемся к базе данных
            conn = await asyncpg.connect(settings.database.get_connection_string())
            
            # Создаем расширение pgvector, если оно еще не создано
            await conn.execute('CREATE EXTENSION IF NOT EXISTS vector;')
            
            logger.info("Расширение pgvector успешно настроено в базе данных PostgreSQL")
            await conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка при настройке расширения pgvector: {str(e)}")
            return False
    
    def create_from_texts(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> PGVector:
        """
        Создает векторное хранилище из списка текстов и метаданных.
        
        Args:
            texts: Список текстов для векторизации
            metadatas: Список метаданных для каждого текста
            
        Returns:
            PGVector: Экземпляр векторного хранилища
        """
        try:
            self._vector_store = PGVector.from_texts(
                texts=texts,
                embedding=self.embeddings,
                collection_name=self.collection_name,
                connection_string=self.connection_string,
                metadatas=metadatas
            )
            logger.info(f"Векторное хранилище для коллекции {self.collection_name} успешно создано")
            return self._vector_store
        except Exception as e:
            logger.error(f"Ошибка при создании векторного хранилища: {str(e)}")
            raise
    
    def create_from_documents(self, documents: List[Document]) -> PGVector:
        """
        Создает векторное хранилище из списка документов.
        
        Args:
            documents: Список документов для векторизации
            
        Returns:
            PGVector: Экземпляр векторного хранилища
        """
        try:
            self._vector_store = PGVector.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name=self.collection_name,
                connection_string=self.connection_string
            )
            logger.info(f"Векторное хранилище для коллекции {self.collection_name} успешно создано из документов")
            return self._vector_store
        except Exception as e:
            logger.error(f"Ошибка при создании векторного хранилища из документов: {str(e)}")
            raise
    
    def get_vector_store(self) -> PGVector:
        """
        Возвращает существующее векторное хранилище или создает новое.
        
        Returns:
            PGVector: Экземпляр векторного хранилища
        """
        if self._vector_store is None:
            self._vector_store = PGVector(
                collection_name=self.collection_name,
                connection_string=self.connection_string,
                embedding_function=self.embeddings
            )
            logger.info(f"Получено существующее векторное хранилище для коллекции {self.collection_name}")
        return self._vector_store
    
    def search(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """
        Выполняет семантический поиск по векторному хранилищу.
        
        Args:
            query: Текст запроса для поиска
            k: Количество результатов для возврата
            
        Returns:
            List[Tuple[Document, float]]: Список пар (документ, релевантность)
        """
        try:
            vector_store = self.get_vector_store()
            logger.info(f"Выполнение семантического поиска в PostgreSQL по запросу: {query}")
            results = vector_store.similarity_search_with_score(query, k=k)
            return results
        except Exception as e:
            logger.error(f"Ошибка при выполнении поиска: {str(e)}")
            return []
