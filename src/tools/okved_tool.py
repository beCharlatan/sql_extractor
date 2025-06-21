from typing import Dict, Any
from loguru import logger
from langchain_core.tools import BaseTool
from src.data.okved_rag import get_okved_rag


class OkvedTool(BaseTool):
    """Инструмент для поиска кодов ОКВЭД с использованием RAG (Retrieval-Augmented Generation)."""
    
    name: str = "okved_search"
    description: str = """Ищет коды ОКВЭД с использованием семантического поиска на основе RAG. 
    Например, по запросу "образование" или "школа" вернет код 85."""
    
    # Определяем атрибуты класса для Pydantic
    _okved_rag = None
    
    def __init__(self):
        """Инициализация инструмента для поиска кодов ОКВЭД."""
        super().__init__()
        self._okved_rag = get_okved_rag()
        logger.info("Инструмент для поиска кодов ОКВЭД инициализирован")
    
    def _run(self, query: str) -> Dict[str, Any]:
        """Выполняет поиск кодов ОКВЭД по запросу с использованием RAG.
        
        Args:
            query: Строка запроса для поиска кодов ОКВЭД
            
        Returns:
            Словарь с найденными кодами ОКВЭД и их описаниями
        """
        try:
            logger.info(f"Поиск кодов ОКВЭД по запросу с использованием RAG: {query}")
            results = self._okved_rag.search(query, k=5)
            logger.info(f"Найдено {len(results)} результатов по запросу '{query}'")
            return {
                "query": query,
                "results": results
            }
        except Exception as e:
            logger.error(f"Ошибка при поиске кодов ОКВЭД: {str(e)}")
            return {
                "query": query,
                "results": [],
                "error": str(e)
            }
    
    async def _arun(self, query: str) -> Dict[str, Any]:
        """Асинхронная версия _run."""
        return self._run(query)


def get_okved_tool() -> OkvedTool:
    """Создает и возвращает экземпляр инструмента поиска кодов ОКВЭД."""
    return OkvedTool()
