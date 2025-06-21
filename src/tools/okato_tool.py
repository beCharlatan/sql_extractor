"""Инструмент для поиска кодов ОКАТО с использованием RAG (Retrieval-Augmented Generation).
Использует векторную базу данных для семантического поиска кодов ОКАТО."""

from typing import Dict, Any
from loguru import logger
from langchain_core.tools import BaseTool
from src.data.okato_rag import get_okato_rag


class OkatoTool(BaseTool):
    """Инструмент для поиска кодов ОКАТО с использованием RAG (Retrieval-Augmented Generation)."""
    
    name: str = "okato_search"
    description: str = """Ищет коды ОКАТО с использованием семантического поиска на основе RAG. 
    Например, по запросу "москва" или "столица" вернет код Москвы."""
    
    # Определяем атрибуты класса для Pydantic
    _okato_rag = None
    
    def __init__(self):
        """Инициализация инструмента для поиска кодов ОКАТО."""
        super().__init__()
        self._okato_rag = get_okato_rag()
        logger.info("Инструмент для поиска кодов ОКАТО инициализирован")
    
    def _run(self, query: str) -> Dict[str, Any]:
        """Выполняет поиск кодов ОКАТО по запросу с использованием RAG.
        
        Args:
            query: Строка запроса для поиска кодов ОКАТО
            
        Returns:
            Словарь с найденными кодами ОКАТО и их описаниями
        """
        try:
            logger.info(f"Поиск кодов ОКАТО по запросу с использованием RAG: {query}")
            results = self._okato_rag.search(query, k=5)
            logger.info(f"Найдено {len(results)} результатов по запросу '{query}'")
            return {
                "query": query,
                "results": results
            }
        except Exception as e:
            logger.error(f"Ошибка при поиске кодов ОКАТО: {str(e)}")
            return {
                "query": query,
                "results": [],
                "error": str(e)
            }
    
    async def _arun(self, query: str) -> Dict[str, Any]:
        """Асинхронная версия _run."""
        return self._run(query)


def get_okato_tool() -> OkatoTool:
    """Создает и возвращает экземпляр инструмента поиска кодов ОКАТО."""
    return OkatoTool()
