from typing import Optional
from loguru import logger

from agent.agent import GigachatAgent
from db.db_schema_tool import DBSchemaReferenceTool


class AnalyzeQuery:
    def __init__(
        self, 
        agent: Optional[GigachatAgent] = None,
    ):
        """Инициализация генератора SQL.

        Аргументы:
            agent: Опциональный экземпляр GigachatAgent. Если не предоставлен, будет создан новый.
        """
        self.agent = agent or GigachatAgent()
        logger.info(f"Initialized EnrichedQuery")


    @classmethod
    async def create(
        cls,
    ) -> 'AnalyzeQuery':
        """Асинхронная инициализация генератора SQL.
            
        Возвращает:
            Экземпляр AnalyzeQuery с инициализированными зависимостями.
        """
        instance = cls()
        instance.db_schema_tool = await DBSchemaReferenceTool.create()
            
        return instance


    async def process(self, query: str) -> str:
        table_ddl = await self.db_schema_tool.get_table_schema(self.table_name)
        prompt = f"""
        [ROLE] Ты SQL-аналитик банка. Сгенерируй 3 разные интерпретации запроса, учитывая:

[SCHEMA]
{table_ddl}

[QUERY]
{query}

[INSTRUCTIONS]
1. Для каждой гипотезы:
   - Опиши ключевые допущения
   - Укажи неоднозначности
   - Предложи критерии проверки
2. Выбери наиболее вероятный вариант
3. Сгенерируй SQL с комментариями
        """

        try:
            response = await self.agent.process_query(prompt)
            expanded_query = response.strip('"')
            return expanded_query
        except Exception as e:
            logger.error(f"Analyze failed: {str(e)}")
            raise e