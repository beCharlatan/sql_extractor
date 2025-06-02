from typing import Optional
from loguru import logger


from src.agent.agent import GigachatAgent

class EnrichedQuery:
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


    async def process(self, filter: str, constraint: str) -> str:
        """Расширение запроса синонимами и бизнес-терминами"""
        prompt = f"""|||
        [Задача] Расширь запрос, добавляя официальные бизнес-термины и общепринятые синонимы. 

        Примеры:
        Оригинал: "клиенты с долгами"
        Расширенный: "клиенты с просроченной задолженностью (delinquent customers) или непогашенными кредитами"

        Оригинал: "Фильтр: {filter}. Ограничения: {constraint}"
        Расширенный: 
        |||"""

        try:
            response = await self.agent.process_query(prompt)
            expanded_query = response["choices"][0]["message"]["content"].strip('"')
            return expanded_query
        except Exception as e:
            logger.error(f"Synonym expansion failed: {str(e)}")
            return f'{filter} {constraint}'