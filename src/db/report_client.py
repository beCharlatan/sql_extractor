"""Клиент отчетов для хранения результатов генерации SQL в базе данных."""

from typing import Dict, Any, Optional
from loguru import logger

from src.db.base_db_client import BaseDBClient
from src.utils.errors import DatabaseError


class ReportClient(BaseDBClient):
    """Клиент для хранения отчетов о генерации SQL в базе данных."""

    def __init__(self, connection_string: Optional[str] = None, db_key: str = 'report'):
        """Инициализация клиента отчетов.
        
        Аргументы:
            connection_string: Опциональная строка подключения к базе данных.
                              По умолчанию используется строка, указанная в настройках.
            db_key: Уникальный идентификатор для этого подключения к базе данных.
                  По умолчанию 'report'.
        """
        super().__init__(connection_string, db_key=db_key)
        
    @classmethod
    async def create(cls, connection_string: Optional[str] = None, db_key: str = 'report') -> 'ReportClient':
        """Асинхронная инициализация клиента отчетов.
        
        Аргументы:
            connection_string: Опциональная строка подключения к базе данных.
                              По умолчанию используется строка, указанная в настройках.
            db_key: Уникальный идентификатор для этого подключения к базе данных.
                  По умолчанию 'report'.
        """
        instance = await super().create(connection_string=connection_string, db_key=db_key)
        # После создания инстанса и инициализации пулов, проверяем таблицу результатов
        await instance.ensure_results_table()
        return instance
    
    async def ensure_results_table(self):
        """Проверка существования таблицы результатов генерации SQL.
        
        Вызывает исключение:
            DatabaseError: Если создание таблицы не удалось.
        """
        try:
            create_table_query = """
                CREATE TABLE IF NOT EXISTS organization_filters (
                    id SERIAL PRIMARY KEY,
                    message_id TEXT,
                    request_hash TEXT,
                    filter_text TEXT NOT NULL,
                    constraint_text TEXT NOT NULL,
                    where_clause TEXT,
                    group_by_clause TEXT,
                    having_clause TEXT,
                    order_by_clause TEXT,
                    limit_clause TEXT,
                    full_sql TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    status TEXT NOT NULL DEFAULT 'success',
                    error_message TEXT
                )
            """
            await self.execute_query(create_table_query, use_master=True)
            logger.info(f"Ensured organization_filters table exists in database with db_key={self.db_key}")
        except Exception as e:
            error_msg = f"Failed to create organization_filters table: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, details={"original_error": str(e)})
    
    async def store_result(self, filter_text: str, constraint_text: str, 
                    sql_components: Dict[str, Any], message_id: Optional[str] = None,
                    request_hash: Optional[str] = None):
        """Сохранение результата генерации SQL в базе данных.
        
        Аргументы:
            filter_text: Текст фильтра, использованный для генерации SQL.
            constraint_text: Текст ограничений, использованный для генерации SQL.
            sql_components: Сгенерированные компоненты SQL.
            message_id: Опциональный ID сообщения из Kafka.
            request_hash: Опциональный хеш-идентификатор запроса.
            
        Вызывает исключение:
            DatabaseError: Если сохранение результата не удалось.
        """
        try:
            insert_query = """
                INSERT INTO organization_filters (
                    message_id, request_hash, filter_text, constraint_text, 
                    where_clause, group_by_clause, having_clause, 
                    order_by_clause, limit_clause, full_sql
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """
            params = [
                message_id,
                request_hash,
                filter_text,
                constraint_text,
                sql_components.get("where_clause", ""),
                sql_components.get("group_by_clause", ""),
                sql_components.get("having_clause", ""),
                sql_components.get("order_by_clause", ""),
                sql_components.get("limit_clause", ""),
                sql_components.get("full_sql", "")
            ]
            
            await self.execute_query(insert_query, params, use_master=True)
            logger.info(f"Stored SQL generation result in database with db_key={self.db_key}, message_id: {message_id}")
        except Exception as e:
            error_msg = f"Failed to store SQL generation result: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, details={"original_error": str(e)})
    
    async def store_error(self, filter_text: str, constraint_text: str, 
                  error_message: str, message_id: Optional[str] = None,
                  request_hash: Optional[str] = None):
        """Сохранение ошибки генерации SQL в базе данных.
        
        Аргументы:
            filter_text: Текст фильтра, использованный для генерации SQL.
            constraint_text: Текст ограничений, использованный для генерации SQL.
            error_message: Сообщение об ошибке.
            message_id: Опциональный ID сообщения из Kafka.
            request_hash: Опциональный хеш-идентификатор запроса.
            
        Вызывает исключение:
            DatabaseError: Если сохранение ошибки не удалось.
        """
        try:
            insert_error_query = """
                INSERT INTO organization_filters (
                    message_id, request_hash, filter_text, constraint_text, 
                    status, error_message
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """
            params = [
                message_id,
                request_hash,
                filter_text,
                constraint_text,
                "error",
                error_message
            ]
            
            await self.execute_query(insert_error_query, params, use_master=True)
            logger.info(f"Stored SQL generation error in database with db_key={self.db_key}, message_id: {message_id}")
        except Exception as e:
            error_msg = f"Failed to store SQL generation error: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, details={"original_error": str(e)})
