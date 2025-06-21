"""Обертка для DBSchemaReferenceTool для использования в качестве инструмента LangChain."""

from typing import Optional
from langchain.tools import Tool
from loguru import logger

from src.db.db_schema_tool import DBSchemaReferenceTool


def get_table_schema_tool(
    connection_string: Optional[str] = None,
    slave_connection_string: Optional[str] = None,
    db_key: str = 'schema'
) -> Tool:
    """Создает инструмент LangChain для получения схемы таблицы.

    Аргументы:
        connection_string: Опциональная строка подключения к базе данных.
        slave_connection_string: Опциональная строка подключения к реплике базы данных.
        db_key: Уникальный идентификатор для этого подключения к базе данных.

    Возвращает:
        Инструмент LangChain для получения схемы таблицы.
    """
    async def _get_table_schema(table_name: str) -> str:
        """Получает DDL-оператор CREATE TABLE для указанной таблицы.

        Аргументы:
            table_name: Имя таблицы, для которой нужно получить схему.

        Возвращает:
            DDL-оператор для таблицы.
        """
        try:
            schema_tool = await DBSchemaReferenceTool.create(
                connection_string=connection_string,
                slave_connection_string=slave_connection_string,
                db_key=db_key
            )
            return await schema_tool.get_table_schema(table_name)
        except Exception as e:
            logger.error(f"Ошибка при получении схемы таблицы: {str(e)}")
            return f"Ошибка: {str(e)}"

    return Tool(
        name="get_table_schema",
        description="Получает DDL (оператор CREATE TABLE) для указанной таблицы. Используйте этот инструмент, когда вам нужно узнать структуру таблицы.",
        func=_get_table_schema,
        args_schema={
            "table_name": {
                "type": "string",
                "description": "Имя таблицы, для которой нужно получить схему"
            }
        },
        return_direct=False,
        coroutine=_get_table_schema
    )


def get_table_columns_tool(
    connection_string: Optional[str] = None,
    slave_connection_string: Optional[str] = None,
    db_key: str = 'schema'
) -> Tool:
    """Создает инструмент LangChain для получения информации о столбцах таблицы.

    Аргументы:
        connection_string: Опциональная строка подключения к базе данных.
        slave_connection_string: Опциональная строка подключения к реплике базы данных.
        db_key: Уникальный идентификатор для этого подключения к базе данных.

    Возвращает:
        Инструмент LangChain для получения информации о столбцах таблицы.
    """
    async def _get_table_columns(table_name: str) -> str:
        """Получает подробную информацию о столбцах в таблице.

        Аргументы:
            table_name: Имя таблицы, для которой нужно получить столбцы.

        Возвращает:
            Строковое представление списка словарей с информацией о столбцах.
        """
        try:
            schema_tool = await DBSchemaReferenceTool.create(
                connection_string=connection_string,
                slave_connection_string=slave_connection_string,
                db_key=db_key
            )
            columns = await schema_tool.get_table_columns(table_name)
            return str(columns)
        except Exception as e:
            logger.error(f"Ошибка при получении столбцов таблицы: {str(e)}")
            return f"Ошибка: {str(e)}"

    return Tool(
        name="get_table_columns",
        description="Получает подробную информацию о столбцах в указанной таблице. Используйте этот инструмент, когда вам нужно узнать имена и типы столбцов таблицы.",
        func=_get_table_columns,
        args_schema={
            "table_name": {
                "type": "string",
                "description": "Имя таблицы, для которой нужно получить информацию о столбцах"
            }
        },
        return_direct=False,
        coroutine=_get_table_columns
    )
