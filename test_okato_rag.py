"""
Тестовый скрипт для проверки работы RAG-системы для кодов ОКАТО.
"""

import os
from src.data.okato_rag import get_okato_rag
from loguru import logger
from src.config.settings import settings
from src.embeddings.base import EmbeddingsType

def main():
    """Основная функция для тестирования RAG-системы для кодов ОКАТО."""
    try:
        # Получаем путь к CSV-файлу с кодами ОКАТО
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(base_dir, "okato.csv")
        
        logger.info(f"Используем CSV-файл: {csv_path}")
        
        # Инициализируем RAG-систему
        embeddings_type = EmbeddingsType(settings.embeddings.default_type)
        okato_rag = get_okato_rag(collection_name="okato_collection", embeddings_type=embeddings_type)
        
        # Тестируем поиск
        test_queries = [
            "Москва",
            "Санкт-Петербург",
            "Алтайский край",
            "столица России",
            "город на Неве"
        ]
        
        for query in test_queries:
            logger.info(f"Поиск по запросу: {query}")
            results = okato_rag.search(query, k=3)
            
            logger.info(f"Найдено {len(results)} результатов:")
            for i, result in enumerate(results, 1):
                logger.info(f"{i}. Код: {result['code']}, Название: {result['name']}, Релевантность: {result['score']:.4f}")
            
            logger.info("---")
    
    except Exception as e:
        logger.error(f"Ошибка при тестировании RAG-системы: {str(e)}")

if __name__ == "__main__":
    main()
