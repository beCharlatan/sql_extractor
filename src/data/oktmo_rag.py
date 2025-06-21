"""Модуль для работы с RAG-системой на основе кодов ОКТМО с использованием PostgreSQL и pgvector."""

import os
import csv
import pandas as pd
from typing import Dict, List, Any, Optional
from loguru import logger

from src.embeddings import EmbeddingsType
from src.vectorstore import PGVectorStore

class OktmoRAG:
    """Класс для работы с RAG-системой на основе кодов ОКТМО с использованием PostgreSQL и pgvector."""
    
    _instance = None
    
    def __init__(self, csv_path: Optional[str] = None, collection_name: str = "oktmo_collection", embeddings_type: Optional[EmbeddingsType] = None, only_search: bool = False):
        """Инициализирует RAG-систему для кодов ОКТМО.
        
        Args:
            csv_path: Путь к CSV-файлу с кодами ОКТМО. Если None, то будет использован путь по умолчанию.
            collection_name: Имя коллекции в PostgreSQL для хранения векторов
            embeddings_type: Тип эмбеддингов для использования. Если None, используется тип по умолчанию.
            only_search: Если True, то будет использоваться только для поиска без загрузки данных
        """
        self.csv_path = csv_path or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "oktmo.csv")
        self.collection_name = collection_name
        self.embeddings_type = embeddings_type
        self.data = []
        self.vector_store = None
        
        # Всегда создаем объект PGVectorStore для доступа к хранилищу
        self.vector_store = PGVectorStore(
            collection_name=self.collection_name,
            embeddings_type=self.embeddings_type
        )
        
        if not only_search:
            logger.info("Инициализация ОКТМО RAG с полной загрузкой данных")
            self._load_csv_data()
            self._create_vector_store()
            logger.info("RAG-система для кодов ОКТМО инициализирована с использованием PostgreSQL и pgvector")
        else:
            logger.info("Инициализация ОКТМО RAG только для поиска (без загрузки данных)")
    
    def _load_csv_data(self):
        """Загружает данные из CSV-файла с кодами ОКТМО."""
        try:
            data = pd.read_csv(self.csv_path, sep=';', encoding='utf-8', quotechar='"')
            
            # Преобразуем данные в нужный формат
            # Предполагаем, что структура CSV файла имеет колонки с кодами и названиями
            # Адаптируем код в зависимости от реальной структуры файла
            
            # Формируем полные коды ОКТМО и их названия
            self.data = []
            
            for _, row in data.iterrows():
                try:
                    # Предполагаем, что первые несколько колонок содержат части кода ОКТМО
                    # а одна из колонок содержит название
                    code_parts = [str(row.iloc[i]).zfill(3) for i in range(4)]  # Первые 4 колонки - части кода
                    code = ''.join(code_parts)
                    
                    # Колонка с названием (может потребоваться корректировка)
                    name = str(row.iloc[6])  # Предполагаем, что название в 7-й колонке
                    
                    if name and len(code) > 0 and name != 'nan':
                        self.data.append({
                            "code": code,
                            "name": name,
                            "text": f"{code} - {name}"  # Текст для векторизации
                        })
                except Exception as e:
                    logger.warning(f"Ошибка при обработке строки ОКТМО: {str(e)}")
            
            logger.info(f"Загружено {len(self.data)} записей ОКТМО из CSV-файла")
        
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных ОКТМО: {str(e)}")
    
    def _create_vector_store(self):
        """Создает векторное хранилище в PostgreSQL с pgvector для поиска по кодам ОКТМО."""
        try:
            texts = [item["text"] for item in self.data]
            metadatas = [{"code": item["code"], "name": item["name"]} for item in self.data]
            
            self.vector_store.create_from_texts(
                texts=texts,
                metadatas=metadatas,
            )
            
            logger.info(f"Создано векторное хранилище в PostgreSQL для {len(texts)} кодов ОКТМО")
        
        except Exception as e:
            logger.error(f"Ошибка при создании векторного хранилища ОКТМО в PostgreSQL: {str(e)}")
            raise
    

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Выполняет семантический поиск по кодам ОКТМО.
        
        Args:
            query: Строка запроса для поиска
            k: Количество результатов для возврата
            
        Returns:
            Список найденных кодов ОКТМО с их описаниями и релевантностью
        """
        try:
            results = self.vector_store.search(query, k=k)
            
            # Форматируем результаты
            formatted_results = []
            
            for doc, score in results:
                # Преобразуем score в процент релевантности (score ближе к 0 = лучше)
                # Используем экспоненциальное преобразование для получения значения от 0 до 100
                relevance = int(100 * max(0, min(1, 1 - (score / 2))))
                
                formatted_results.append({
                    "code": doc.metadata["code"],
                    "name": doc.metadata["name"],
                    "relevance": f"{relevance}%",
                    "relevance_score": relevance
                })
            
            logger.info(f"Найдено {len(formatted_results)} результатов по запросу '{query}'")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Ошибка при выполнении семантического поиска: {str(e)}")
            return []


# Синглтон для хранения экземпляра ОКТМО RAG
_oktmo_rag_instance = None

def initialize_oktmo_rag(csv_path: Optional[str] = None, collection_name: str = "oktmo_collection", embeddings_type: Optional[EmbeddingsType] = None) -> OktmoRAG:
    """Инициализирует RAG-систему для кодов ОКТМО с загрузкой данных.
    
    Эта функция должна быть вызвана один раз перед использованием get_oktmo_rag().
    
    Args:
        csv_path: Путь к CSV-файлу с кодами ОКТМО. Если None, то будет использован путь по умолчанию.
        collection_name: Имя коллекции в PostgreSQL для хранения векторов
        embeddings_type: Тип эмбеддингов для использования. Если None, используется тип по умолчанию.
        
    Returns:
        Экземпляр OktmoRAG с загруженными данными
    """
    global _oktmo_rag_instance
    
    # Создаем новый экземпляр с полной загрузкой данных
    _oktmo_rag_instance = OktmoRAG(
        csv_path=csv_path,
        collection_name=collection_name,
        embeddings_type=embeddings_type,
        only_search=False
    )
    
    return _oktmo_rag_instance

def get_oktmo_rag(collection_name: str = "oktmo_collection", embeddings_type: Optional[EmbeddingsType] = None) -> OktmoRAG:
    """Возвращает экземпляр RAG-системы для кодов ОКТМО (синглтон) только для поиска.
    
    ВАЖНО: Перед первым использованием необходимо вызвать initialize_oktmo_rag(),
    чтобы загрузить данные в векторное хранилище.
    
    Args:
        collection_name: Имя коллекции в PostgreSQL для хранения векторов
        embeddings_type: Тип эмбеддингов для использования. Если None, используется тип по умолчанию.
        
    Returns:
        Экземпляр OktmoRAG только для поиска
    """
    global _oktmo_rag_instance
    
    if _oktmo_rag_instance is None:
        _oktmo_rag_instance = OktmoRAG(
            csv_path=None,
            collection_name=collection_name,
            embeddings_type=embeddings_type,
            only_search=True
        )
    
    return _oktmo_rag_instance
