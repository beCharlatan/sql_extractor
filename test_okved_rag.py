"""Тестирование RAG-системы для кодов ОКВЭД."""

from loguru import logger
from src.data.okved_rag import get_okved_rag
from src.config.settings import settings
from src.embeddings import EmbeddingsType

def test_okved_rag():
    """Тестирует RAG-систему для кодов ОКВЭД."""
    logger.info("Тестирование RAG-системы для кодов ОКВЭД")
    
    # Получаем экземпляр RAG для ОКВЭД
    embeddings_type = EmbeddingsType(settings.embeddings.default_type)
    okved_rag = get_okved_rag(collection_name="okved_collection", embeddings_type=embeddings_type)
    
    # Тестовые запросы
    test_queries = [
        "образование",
        "школа",
        "разработка программного обеспечения",
        "медицина",
        "строительство дорог"
    ]
    
    # Выполняем поиск для каждого запроса
    for query in test_queries:
        logger.info(f"\nПоиск по запросу: '{query}'")
        results = okved_rag.search(query, k=3)
        
        logger.info(f"Найдено {len(results)} результатов:")
        for i, result in enumerate(results, 1):
            logger.info(f"{i}. Код: {result['code']} - {result['name']} (релевантность: {result['relevance']}%)")

if __name__ == "__main__":
    test_okved_rag()
