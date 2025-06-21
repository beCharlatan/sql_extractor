"""Тестирование RAG-системы для кодов ОКТМО."""

import sys
from loguru import logger
from src.data.oktmo_rag import get_oktmo_rag
from src.config.settings import settings
from src.embeddings import EmbeddingsType

# Настройка логирования
logger.remove()
logger.add(sys.stdout, level="INFO")


def test_oktmo_rag():
    """Тестирование RAG-системы для кодов ОКТМО."""
    logger.info("Тестирование RAG-системы для кодов ОКТМО")
    
    # Получаем экземпляр RAG-системы
    embeddings_type = EmbeddingsType(settings.embeddings.default_type)
    oktmo_rag = get_oktmo_rag(collection_name="oktmo_collection", embeddings_type=embeddings_type)
    
    # Тестовые запросы
    test_queries = [
        "москва",
        "санкт-петербург",
        "столица",
        "якутия",
        "адыгея"
    ]
    
    # Выполняем поиск по каждому запросу
    for query in test_queries:
        logger.info(f"\nПоиск по запросу: '{query}'")
        results = oktmo_rag.search(query, k=3)
        
        logger.info(f"Найдено {len(results)} результатов:")
        for i, result in enumerate(results):
            logger.info(f"{i+1}. Код: {result['code']} - {result['name']} (релевантность: {result['relevance']})")

if __name__ == "__main__":
    test_oktmo_rag()

