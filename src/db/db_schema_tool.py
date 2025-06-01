"""Инструмент для работы со схемой базы данных для ИИ-агента."""

from typing import Dict, List, Optional, Any
from loguru import logger

from src.db.base_db_client import BaseDBClient
from src.utils.errors import DatabaseError
from src.db.db_response_cache import cache


class DBSchemaReferenceTool(BaseDBClient):
    """Инструмент для получения информации о схеме базы данных.
    
    Этот инструмент подключается к базе данных и получает информацию о структуре таблиц,
    которая может быть использована агентом для понимания структуры данных для фильтрации,
    сортировки и других операций.
    """

    def __init__(self, connection_string: Optional[str] = None, slave_connection_string: Optional[str] = None, db_key: str = 'schema'):
        """Инициализация инструмента для работы со схемой базы данных.

        Аргументы:
            connection_string: Опциональная строка подключения к базе данных. 
                              По умолчанию используется строка, указанная в настройках.
            db_key: Уникальный идентификатор для этого подключения к базе данных.
                  По умолчанию 'schema'.
        """
        super().__init__(connection_string, slave_connection_string=slave_connection_string, db_key=db_key)

    @classmethod
    async def create(cls, connection_string: Optional[str] = None, slave_connection_string: Optional[str] = None, db_key: str = 'schema') -> 'DBSchemaReferenceTool':
        """Асинхронная инициализация инструмента для работы со схемой базы данных.

        Аргументы:
            connection_string: Опциональная строка подключения к базе данных.
                              По умолчанию используется строка, указанная в настройках.
            db_key: Уникальный идентификатор для этого подключения к базе данных.
                  По умолчанию 'schema'.
        """
        instance = await super().create(connection_string=connection_string, slave_connection_string=slave_connection_string, db_key=db_key)
        return instance

    @cache.cached(prefix='ddl')
    async def get_table_schema(self, table_name: str) -> str:
        """Получение DDL (оператора CREATE TABLE) для конкретной таблицы.

        Аргументы:
            table_name: Имя таблицы, для которой нужно получить схему.

        Возвращает:
            DDL-оператор для таблицы.

        Вызывает исключение:
            DatabaseError: Если есть ошибка подключения к базе данных или таблица не существует.
        """
        try:
            # Получение оператора CREATE TABLE с помощью запроса, похожего на pg_dump
            ddl_query = """
                SELECT 'CREATE TABLE ' || relname || ' (' ||
                array_to_string(array_agg(column_name || ' ' || data_type), ', ') || ');'
                FROM (
                    SELECT c.relname, a.attname AS column_name,
                    pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type
                    FROM pg_catalog.pg_class c
                    JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                    JOIN pg_catalog.pg_attribute a ON a.attrelid = c.oid
                    WHERE c.relname = $1
                    AND a.attnum > 0
                    AND NOT a.attisdropped
                    AND n.nspname = 'public'
                    ORDER BY a.attnum
                ) t
                GROUP BY relname;
            """
            result = await self.execute_query(ddl_query, [table_name])
            
            if not result:
                raise DatabaseError(f"Failed to retrieve DDL for table '{table_name}'", 
                                  details={"table_name": table_name})
            
            logger.debug(f'DDL: {result}')
                
            return result
            
        except Exception as e:
            error_msg = f"Error when retrieving schema for table '{table_name}': {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, details={"table_name": table_name, "original_error": str(e)})

    @cache.cached(prefix='row')
    async def get_table_columns(self, table_name: str) -> List[Dict[str, str]]:
        """Получение подробной информации о столбцах в таблице.

        Аргументы:
            table_name: Имя таблицы, для которой нужно получить столбцы.

        Возвращает:
            Список словарей, содержащих информацию о столбцах (имя, тип и т.д.).

        Вызывает исключение:
            DatabaseError: Если есть ошибка подключения к базе данных или таблица не существует.
        """
        try:
            # Получение информации о столбцах
            columns_query = f"SELECT attr_name, description FROM parameters_reference"
            columns = await self.execute_query(columns_query)

            logger.info(f'Columns info: {columns}')
            
            if not columns:
                raise DatabaseError(f"Failed to retrieve columns for table '{table_name}'", 
                                  details={"table_name": table_name})
                
            return columns
            
        except Exception as e:
            error_msg = f"Error when retrieving columns for table '{table_name}': {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, details={"table_name": table_name, "original_error": str(e)})
