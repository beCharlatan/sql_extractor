"""Инструмент для работы со схемой базы данных для ИИ-агента."""

from typing import Dict, List, Optional, Any
from loguru import logger

from src.db.base_db_client import BaseDBClient
from src.utils.errors import DatabaseError
from db_response_cache import cache


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
            # Проверка существования таблицы
            exists_query = """
                SELECT EXISTS (SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = $1)
            """
            exists_result = await self.execute_query(exists_query, [table_name])
            
            if not exists_result[0]['exists']:
                raise DatabaseError(f"Table '{table_name}' does not exist", details={"table_name": table_name})
            
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
            
            if not result or not result[0][0]:
                raise DatabaseError(f"Failed to retrieve DDL for table '{table_name}'", 
                                  details={"table_name": table_name})
                
            return result[0][0]
            
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
            # Проверка существования таблицы
            exists_query = """
                SELECT EXISTS (SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = $1)
            """
            exists_result = await self.execute_query(exists_query, [table_name])
            
            if not exists_result[0]['exists']:
                raise DatabaseError(f"Table '{table_name}' does not exist", details={"table_name": table_name})
            
            # Получение информации о столбцах
            columns_query = """
                SELECT 
                    ordinal_position as cid,
                    column_name as name,
                    data_type as type,
                    CASE WHEN is_nullable = 'NO' THEN 1 ELSE 0 END as notnull,
                    column_default as default_value,
                    CASE WHEN column_name IN (
                        SELECT column_name FROM information_schema.table_constraints tc
                        JOIN information_schema.constraint_column_usage ccu 
                        USING (constraint_schema, constraint_name)
                        WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_name = $1
                    ) THEN 1 ELSE 0 END as pk
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = $1
                ORDER BY ordinal_position
            """
            columns_info = await self.execute_query(columns_query, [table_name])
            
            if not columns_info:
                raise DatabaseError(f"Failed to retrieve columns for table '{table_name}'", 
                                  details={"table_name": table_name})
                
            # Форматирование информации о столбцах
            columns = []
            for col in columns_info:
                columns.append({
                    "cid": col['cid'],
                    "name": col['name'],
                    "type": col['type'],
                    "notnull": col['notnull'],
                    "default_value": col['default_value'],
                    "pk": col['pk']
                })
                
            return columns
            
        except Exception as e:
            error_msg = f"Error when retrieving columns for table '{table_name}': {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, details={"table_name": table_name, "original_error": str(e)})

    async def get_parameter_info(self, parameter_name: str) -> Dict[str, Any]:
        """Получение информации о конкретном параметре из справочной таблицы параметров.

        Аргументы:
            parameter_name: Имя параметра для поиска.

        Возвращает:
            Словарь, содержащий информацию о параметре (имя, описание, тип данных).

        Вызывает исключение:
            DatabaseError: Если есть ошибка подключения к базе данных или параметр не существует.
        """
        try:
            # Предполагается, что существует таблица parameters_reference со столбцами: parameter_name, description, data_type
            query = """
                SELECT parameter_name, description, data_type 
                FROM parameters_reference 
                WHERE parameter_name = $1
            """
            result = await self.execute_query(query, [parameter_name])
            
            if not result:
                raise DatabaseError(f"Parameter '{parameter_name}' not found in reference table", 
                                  details={"parameter_name": parameter_name})
                
            return {
                "parameter_name": result[0]['parameter_name'],
                "description": result[0]['description'],
                "data_type": result[0]['data_type']
            }
            
        except Exception as e:
            error_msg = f"Error when retrieving parameter info for '{parameter_name}': {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, details={"parameter_name": parameter_name, "original_error": str(e)})
