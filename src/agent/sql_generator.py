"""Функциональность генерации SQL-запросов для ИИ-агента."""

from typing import Any, Dict, Optional

from loguru import logger

from src.agent.agent import Agent
from src.utils.errors import (
    SQLGenerationError,
)


class SQLGenerator:
    """Генерирует компоненты SQL-запроса на основе ввода на естественном языке."""

    def __init__(
        self,
        agent: Optional[Agent] = None,
        table_name: str = "products",
    ):
        """Инициализация генератора SQL.

        Аргументы:
            agent: Опциональный экземпляр OllamaAgent. Если не предоставлен, будет создан новый.
            table_name: Имя таблицы, для которой генерируется SQL.
        """
        self.agent = agent or Agent()
        self.table_name = table_name
        logger.info(f"Initialized SQLGenerator for table {table_name}")

    @classmethod
    async def create(
        cls, 
        agent: Optional[Agent] = None,
        table_name: str = "products",
    ) -> 'SQLGenerator':
        """Асинхронная инициализация генератора SQL.

        Аргументы:
            agent: Опциональный экземпляр OllamaAgent. Если не предоставлен, будет создан новый.
            table_name: Имя таблицы, для которой генерируется SQL.
            
        Возвращает:
            Экземпляр SQLGenerator с инициализированными зависимостями.
        """
        instance = cls(agent=agent, table_name=table_name)
        return instance

    async def generate_sql_components(
        self,
        query: str,
    ) -> Dict[str, Any]:
        try:
            # Обработка запроса с помощью агента
            response = await self.agent.process_query(query)
            return response
        except Exception as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            raise SQLGenerationError(
                f"Error calling Ollama API: {str(e)}",
                details={"original_error": str(e)}
            )