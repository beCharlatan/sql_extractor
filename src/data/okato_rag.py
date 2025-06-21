"""
Модуль для создания и управления RAG (Retrieval-Augmented Generation) системой для кодов ОКАТО.
Преобразует CSV-файл с кодами ОКАТО в векторную базу данных для семантического поиска.
"""

import os
import csv
from typing import List, Dict, Any, Optional
from loguru import logger
from langchain_core.documents import Document

from src.embeddings import EmbeddingsType
from src.vectorstore import PGVectorStore

class OkatoRAG:
    """
    Класс для работы с кодами ОКАТО через RAG-систему.
    Загружает данные из CSV-файла, создает векторное хранилище и выполняет семантический поиск.
    """
    
    def __init__(self, csv_path: str = None, collection_name: str = "okato_collection", embeddings_type: Optional[EmbeddingsType] = None, only_search: bool = False):
        """
        Инициализирует RAG-систему для кодов ОКАТО.
        
        Args:
            csv_path: Путь к CSV-файлу с кодами ОКАТО (требуется только если only_search=False)
            collection_name: Имя коллекции в PostgreSQL
            embeddings_type: Тип эмбеддингов для использования. По умолчанию None (будет использоваться значение по умолчанию)
            only_search: Если True, то будет использоваться только для поиска без загрузки данных
        """
        self.csv_path = csv_path
        self.collection_name = collection_name
        self.embeddings_type = embeddings_type
        self.df = []
        self.vector_store = None
        
        # Создаем объект PGVectorStore для доступа к хранилищу
        self.vector_store = PGVectorStore(
            collection_name=self.collection_name,
            embeddings_type=self.embeddings_type
        )
        
        # Если требуется только поиск, не загружаем данные
        if not only_search and csv_path:
            # Загружаем данные и создаем векторное хранилище
            self._load_csv_data()
            self._create_vector_store()
            logger.info(f"Инициализирован OkatoRAG с загрузкой данных из CSV-файла: {csv_path}")
        else:
            logger.info("Инициализирован OkatoRAG только для поиска (без загрузки данных)")

    def _create_vector_store(self) -> bool:
        """
        Загружает документы в векторное хранилище.
        
        Returns:
            bool: True, если создание прошло успешно, иначе False
        """
        try:
            # Загружаем документы в векторное хранилище
            logger.info("Создание векторной базы данных PostgreSQL для ОКАТО")
            self.vector_store.create_from_documents(self.df)
            logger.info(f"Векторная база данных PostgreSQL для ОКАТО успешно создана, загружено {len(self.df)} документов")
            return True
        except Exception as e:
            logger.error(f"Ошибка при создании векторной базы данных для ОКАТО: {str(e)}")
            return False


    def _load_csv_data(self):
        """
        Загружает данные из CSV-файла с кодами ОКАТО.
        """
        try:
            # Чтение CSV-файла с правильной кодировкой
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=';', quotechar='"')
                
                self.df = []
                for row in reader:
                    if len(row) >= 6:  # Проверяем, что в строке достаточно данных
                        # Формируем код ОКАТО из первых нескольких колонок
                        code_parts = [row[0], row[1], row[2], row[3]]
                        code = "".join([part.strip() for part in code_parts if part.strip() != "000"])
                        
                        # Получаем название объекта
                        name = row[5].strip() if row[5] else ""
                        
                        # Добавляем дополнительную информацию, если она есть
                        additional_info = row[6].strip() if len(row) > 6 and row[6] else ""
                        
                        # Формируем полное описание
                        description = f"{name} {additional_info}".strip()
                        
                        if code and description:
                            doc = Document(
                                page_content=f"Код ОКАТО: {code}. {description}",
                                metadata={
                                    "code": code,
                                    "name": name,
                                    "description": description
                                }
                            )
                            self.df.append(doc)
            
            logger.info(f"Загружено {len(self.df)} записей ОКАТО из CSV-файла")
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных из CSV-файла: {str(e)}")

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Выполняет семантический поиск по кодам ОКАТО.
        
        Args:
            query: Текст запроса для поиска
            k: Количество результатов для возврата
            
        Returns:
            List[Dict[str, Any]]: Список найденных кодов ОКАТО с метаданными
        """
        try:
            # Выполняем поиск через векторное хранилище
            results = self.vector_store.search(query, k=k)
            
            # Преобразуем результаты в удобный формат
            formatted_results = []
            for doc, score in results:
                result = doc.metadata.copy()
                result["score"] = score
                result["content"] = doc.page_content
                formatted_results.append(result)
            
            return formatted_results
        except Exception as e:
            logger.error(f"Ошибка при выполнении поиска по ОКАТО: {str(e)}")
            return []


# Singleton-экземпляр для использования в приложении
_okato_rag_instance = None

def initialize_okato_rag(csv_path: Optional[str] = None, collection_name: str = "okato_collection", embeddings_type: Optional[EmbeddingsType] = None) -> OkatoRAG:
    """Инициализирует RAG-систему для кодов ОКАТО с загрузкой данных из CSV.
    
    Args:
        csv_path: Путь к CSV-файлу с кодами ОКАТО. Если None, используется путь по умолчанию
        collection_name: Имя коллекции векторов
        embeddings_type: Тип эмбеддингов для использования
        
    Returns:
        OkatoRAG: Экземпляр RAG-системы для кодов ОКАТО с загруженными данными
    """
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "okato.csv")
    
    return OkatoRAG(csv_path=csv_path, collection_name=collection_name, embeddings_type=embeddings_type, only_search=False)


def get_okato_rag(collection_name: str = "okato_collection", embeddings_type: Optional[EmbeddingsType] = None) -> OkatoRAG:
    """Возвращает синглтон-экземпляр RAG-системы для кодов ОКАТО только для поиска (без загрузки данных).
    
    Args:
        collection_name: Имя коллекции векторов
        embeddings_type: Тип эмбеддингов для использования
        
    Returns:
        OkatoRAG: Экземпляр RAG-системы для кодов ОКАТО только для поиска
    """
    global _okato_rag_instance
    
    if _okato_rag_instance is None:
        _okato_rag_instance = OkatoRAG(collection_name=collection_name, embeddings_type=embeddings_type, only_search=True)
    
    return _okato_rag_instance