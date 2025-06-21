#!/usr/bin/env python
"""CLI-утилита для тестирования генерации SQL без использования Kafka."""

import argparse
import asyncio
import json
import sys
from typing import Dict, Any, Optional

from loguru import logger

from src.agent.agent import Agent
from src.agent.sql_generator import SQLGenerator
from src.utils.errors import SQLGenerationError, handle_exception


class CLIProcessor:
    """Процессор для CLI-интерфейса генерации SQL."""

    def __init__(
        self,
        sql_generator: Optional[SQLGenerator] = None,
    ):
        """Инициализация CLI-процессора.
        
        Args:
            sql_generator: Опциональный экземпляр SQLGenerator. Если не указан, будет создан новый.
        """
        self.sql_generator = sql_generator

    async def _create_sql_generator(self) -> SQLGenerator:
        """Асинхронное создание нового экземпляра генератора SQL."""
        try:
            agent = Agent()
            # db_schema_tool теперь интегрирован в агента через инструменты
            return await SQLGenerator.create(agent=agent)
        except Exception as e:
            error_msg = f"Failed to initialize SQL generator: {str(e)}"
            logger.error(error_msg)
            raise SQLGenerationError(error_msg, details={"original_error": str(e)})

    async def start(self):
        """Запуск CLI-процессора и инициализация компонентов."""
        logger.info("Starting CLI processor")
        
        if self.sql_generator is None:
            self.sql_generator = await self._create_sql_generator()

    async def process_request(self, query: str) -> Dict[str, Any]:
        """Обработка запроса на генерацию SQL.
        
        Args:
            query: Текст запроса для генерации SQL.
            
        Returns:
            Результат обработки запроса.
        """
        try:
            # Генерация SQL компонентов
            logger.info("Generating SQL components from request")
            
            generator_result = await self.sql_generator.generate_sql_components(
                query=query,
            )
            
            logger.debug(f"SQL components: {generator_result}")
            
            return generator_result

        except Exception as e:
            handle_exception(e)
            return {"error": str(e)}


async def main():
    """Основная функция CLI-утилиты."""
    parser = argparse.ArgumentParser(description="SQL Generator CLI")
    parser.add_argument("query", help="Текст запроса для генерации SQL")
    parser.add_argument("--output", "-o", help="Файл для сохранения результата в формате JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Подробный вывод")
    
    args = parser.parse_args()
    
    # Настройка логирования
    log_level = "DEBUG" if args.verbose else "INFO"
    logger.remove()
    logger.add(sys.stderr, level=log_level, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
    
    # Создание и запуск процессора
    processor = CLIProcessor()
    await processor.start()
    
    # Обработка запроса
    result = await processor.process_request(
        query=args.query
    )
    
    # Вывод результата
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"Result saved to {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
