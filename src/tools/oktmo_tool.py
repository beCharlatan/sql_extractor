from typing import Dict, Any
from loguru import logger
from langchain_core.tools import BaseTool
from src.data.oktmo_rag import get_oktmo_rag


class OktmoTool(BaseTool):
    """Инструмент для поиска кодов ОКТМО с использованием RAG (Retrieval-Augmented Generation)."""
    
    name: str = "oktmo_search"
    description: str = """Ищет коды ОКТМО с использованием семантического поиска на основе RAG. 
    Например, по запросу "москва" или "столица" вернет код 45000000."""
    
    # Определяем атрибуты класса для Pydantic
    _oktmo_rag = None
    
    def __init__(self):
        """Инициализация инструмента для поиска кодов ОКТМО."""
        super().__init__()
        self._oktmo_rag = get_oktmo_rag()
        logger.info("Инструмент для поиска кодов ОКТМО инициализирован")
    
    def _run(self, query: str) -> Dict[str, Any]:
        """Выполняет поиск кодов ОКТМО по запросу с использованием RAG.
        
        Args:
            query: Строка запроса для поиска кодов ОКТМО
            
        Returns:
            Словарь с найденными кодами ОКТМО и их описаниями
        """
        try:
            logger.info(f"Поиск кодов ОКТМО по запросу с использованием RAG: {query}")
            results = self._oktmo_rag.search(query, k=5)
            logger.info(f"Найдено {len(results)} результатов по запросу '{query}'")
            return {
                "query": query,
                "results": results
            }
        except Exception as e:
            logger.error(f"Ошибка при поиске кодов ОКТМО: {str(e)}")
            return {
                "query": query,
                "results": [],
                "error": str(e)
            }
    
    async def _arun(self, query: str) -> Dict[str, Any]:
        """Асинхронная версия _run."""
        return self._run(query)


def get_oktmo_tool() -> OktmoTool:
    """Создает и возвращает экземпляр инструмента поиска кодов ОКТМО."""
    return OktmoTool()
