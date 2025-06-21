"""Модуль для работы с RAG-системой на основе кодов ОКВЭД."""

import os
import pandas as pd
from typing import List, Dict, Any, Optional
from loguru import logger

from src.embeddings import EmbeddingsType
from src.vectorstore import PGVectorStore

class OkvedRAG:
    """Класс для работы с данными ОКВЭД с использованием RAG и PostgreSQL с pgvector."""
    
    def __init__(self, csv_path: str = None, collection_name: str = "okved_collection", embeddings_type: Optional[EmbeddingsType] = None, only_search: bool = False):
        """Инициализирует класс для работы с ОКВЭД через RAG.
        
        Args:
            csv_path: Путь к CSV-файлу с кодами ОКВЭД (требуется только если only_search=False)
            collection_name: Имя коллекции в PostgreSQL для хранения векторов
            embeddings_type: Тип эмбеддингов для использования. Если None, используется тип по умолчанию.
            only_search: Если True, то будет использоваться только для поиска без загрузки данных
        """
        self.csv_path = csv_path
        self.collection_name = collection_name
        self.embeddings_type = embeddings_type
        self.df = None
        
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
            logger.info(f"Инициализирован OkvedRAG с загрузкой данных из CSV-файла: {csv_path}")
        else:
            logger.info("Инициализирован OkvedRAG только для поиска (без загрузки данных)")
    
    def _load_csv_data(self):
        """Загружает данные из CSV-файла."""
        try:
            logger.info(f"Загрузка данных ОКВЭД из файла: {self.csv_path}")
            # Загружаем CSV-файл с кодировкой UTF-8
            self.df = pd.read_csv(self.csv_path, sep=';', encoding='utf-8', header=None, quotechar='"')
            
            # Удаляем кавычки из строк
            self.df = self.df.applymap(lambda x: x.strip('"') if isinstance(x, str) else x)
            
            # Присваиваем имена столбцам
            self.df.columns = ['section', 'code', 'name']
            
            # Создаем полный текст для индексирования (код + название)
            self.df['text'] = self.df['code'] + ' ' + self.df['name']
            
            logger.info(f"Загружено {len(self.df)} записей ОКВЭД")
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных ОКВЭД: {str(e)}")
            raise

    
    def _create_vector_store(self) -> bool:
        """Создает векторную базу данных PostgreSQL с pgvector из загруженных данных.
        
        Returns:
            bool: True, если создание прошло успешно, иначе False
        """
        try:
            logger.info("Создание векторной базы данных PostgreSQL для ОКВЭД")
            
            texts = self.df['text'].tolist()
            metadatas = self.df.apply(
                lambda row: {
                    'section': row['section'],
                    'code': row['code'],
                    'name': row['name']
                }, 
                axis=1
            ).tolist()
            
            self.vector_store.create_from_texts(texts, metadatas)
            
            logger.info(f"Векторная база данных PostgreSQL для ОКВЭД успешно создана")
            return True
        except Exception as e:
            logger.error(f"Ошибка при создании векторной базы данных PostgreSQL для ОКВЭД: {str(e)}")
            return False
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Выполняет семантический поиск по кодам ОКВЭД в PostgreSQL с pgvector.
        
        Args:
            query: Строка запроса для поиска
            k: Количество результатов для возврата
            
        Returns:
            Список словарей с найденными кодами ОКВЭД и их описаниями
        """
        try:            
            # Выполняем поиск в векторной базе данных PostgreSQL
            docs_and_scores = self.vector_store.search(query, k=k)
            
            # Формируем результаты
            results = []
            for doc, score in docs_and_scores:
                # Преобразуем оценку сходства в процент релевантности (чем ниже расстояние, тем выше релевантность)
                # Нормализуем оценку, чтобы она была в диапазоне от 0 до 100
                relevance = max(0, min(100, 100 * (1 - score / 2)))
                
                results.append({
                    "code": doc.metadata["code"],
                    "name": doc.metadata["name"],
                    "section": doc.metadata["section"],
                    "relevance": round(relevance, 2)
                })
            
            logger.info(f"Найдено {len(results)} результатов по запросу '{query}'")
            return results
        except Exception as e:
            logger.error(f"Ошибка при поиске кодов ОКВЭД: {str(e)}")
            raise


# Singleton для экземпляра OkvedRAG
_okved_rag_instance = None

def initialize_okved_rag(csv_path: Optional[str] = None, collection_name: str = "okved_collection", embeddings_type: Optional[EmbeddingsType] = None) -> OkvedRAG:
    """Инициализирует RAG-систему для кодов ОКВЭД с загрузкой данных из CSV.
    
    Args:
        csv_path: Путь к CSV-файлу с кодами ОКВЭД. Если None, используется путь по умолчанию
        collection_name: Имя коллекции векторов
        embeddings_type: Тип эмбеддингов для использования
        
    Returns:
        OkvedRAG: Экземпляр RAG-системы для кодов ОКВЭД с загруженными данными
    """
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "okved.csv")
    
    return OkvedRAG(csv_path=csv_path, collection_name=collection_name, embeddings_type=embeddings_type, only_search=False)


def get_okved_rag(collection_name: str = "okved_collection", embeddings_type: Optional[EmbeddingsType] = None) -> OkvedRAG:
    """Возвращает синглтон-экземпляр RAG-системы для кодов ОКВЭД только для поиска (без загрузки данных).
    
    Args:
        collection_name: Имя коллекции векторов
        embeddings_type: Тип эмбеддингов для использования
        
    Returns:
        OkvedRAG: Экземпляр RAG-системы для кодов ОКВЭД только для поиска
    """
    global _okved_rag_instance
    
    if _okved_rag_instance is None:
        _okved_rag_instance = OkvedRAG(collection_name=collection_name, embeddings_type=embeddings_type, only_search=True)
    
    return _okved_rag_instance
