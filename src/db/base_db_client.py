"""Асинхронный клиент базы данных с поддержкой пулов соединений и master-slave репликации."""

import asyncpg
from urllib.parse import urlparse
from typing import Optional, Dict, Any, Union, List
from loguru import logger

from src.config.settings import settings
from src.utils.errors import DatabaseError


class BaseDBClient:
    """Асинхронный клиент для работы с базой данных с использованием пулов соединений."""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        slave_connection_string: Optional[str] = None,
        db_key: str = 'default'
    ):
        """Инициализация клиента.
        
        Args:
            connection_string: Строка подключения к мастер-ноде
            slave_connection_string: Строка подключения к слейв-ноде
            db_key: Уникальный идентификатор подключения
        """
        self.db_key = db_key
        self.min_connections = settings.database.min_connections
        self.max_connections = settings.database.max_connections

        self.master_connection_string = connection_string or settings.database.get_connection_string()
        self.slave_connection_string = slave_connection_string or getattr(
            settings.database, 'get_slave_connection_string', lambda: None
        )()

        self.master_pool: Optional[asyncpg.pool.Pool] = None
        self.slave_pool: Optional[asyncpg.pool.Pool] = None
        self.master_conn_params: Dict[str, Any] = {}
        self.slave_conn_params: Dict[str, Any] = {}

        self._parse_connection_strings()
        logger.info(f"Initialized {self.__class__.__name__} with db_key={self.db_key}")

    @classmethod
    async def create(
        cls,
        connection_string: Optional[str] = None,
        slave_connection_string: Optional[str] = None,
        db_key: str = 'default'
    ) -> 'BaseDBClient':
        """Фабричный метод для асинхронной инициализации."""
        instance = cls(
            connection_string=connection_string,
            slave_connection_string=slave_connection_string,
            db_key=db_key
        )
        await instance._initialize_pools()
        return instance

    def _parse_connection_strings(self):
        """Парсинг строк подключения."""
        try:
            if self.master_connection_string:
                self.master_conn_params = self._parse_single_connection_string(self.master_connection_string)
            if self.slave_connection_string:
                self.slave_conn_params = self._parse_single_connection_string(self.slave_connection_string)
        except Exception as e:
            error_msg = f"Ошибка парсинга строк подключения: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def _parse_single_connection_string(self, connection_string: str) -> Dict[str, Any]:
        """Парсинг одной строки подключения."""
        parsed = urlparse(connection_string)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'database': parsed.path.lstrip('/')
        }

    async def _initialize_pools(self):
        """Инициализация пулов соединений."""
        try:
            if self.master_conn_params:
                self.master_pool = await asyncpg.create_pool(
                    min_size=self.min_connections,
                    max_size=self.max_connections,
                    **self.master_conn_params
                )
                logger.info(f"Инициализирован мастер-пул для {self.db_key}")

            if self.slave_conn_params:
                self.slave_pool = await asyncpg.create_pool(
                    min_size=self.min_connections,
                    max_size=self.max_connections,
                    **self.slave_conn_params
                )
                logger.info(f"Инициализирован слейв-пул для {self.db_key}")

        except Exception as e:
            error_msg = f"Ошибка инициализации пулов: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    async def get_master_connection(self) -> asyncpg.Connection:
        """Получение соединения из мастер-пула."""
        if not self.master_pool:
            raise DatabaseError("Мастер-пул не настроен")
        
        try:
            return await self.master_pool.acquire()
        except Exception as e:
            error_msg = f"Ошибка получения мастер-соединения: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    async def get_slave_connection(self) -> asyncpg.Connection:
        """Получение соединения из слейв-пула."""
        if not self.slave_pool:
            raise DatabaseError("Слейв-пул не настроен")
        
        try:
            return await self.slave_pool.acquire()
        except Exception as e:
            error_msg = f"Ошибка получения слейв-соединения: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    async def return_connection(self, conn: asyncpg.Connection, is_master: bool = True):
        """Возврат соединения в пул."""
        try:
            if is_master and self.master_pool:
                await self.master_pool.release(conn)
            elif not is_master and self.slave_pool:
                await self.slave_pool.release(conn)
        except Exception as e:
            logger.error(f"Ошибка возврата соединения: {str(e)}")
            

    async def execute_query(
        self,
        query: str,
        params: Optional[list] = None,
        use_master: bool = False
    ) -> Union[List[asyncpg.Record], str]:
        """Универсальный метод выполнения запроса"""
        conn = None
        try:
            conn = await (self.get_master_connection() if use_master else self.get_slave_connection())
            
            if use_master:
                return await conn.execute(query, *(params or []))
            return await conn.fetch(query, *(params or []))
            
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            raise DatabaseError(f"Query execution error: {str(e)}")
        finally:
            if conn:
                await self.return_connection(conn, is_master=use_master)


    async def close(self):
        """Закрытие всех соединений."""
        try:
            if self.master_pool:
                await self.master_pool.close()
            if self.slave_pool:
                await self.slave_pool.close()
            logger.info(f"Все соединения закрыты для {self.db_key}")
        except Exception as e:
            logger.error(f"Ошибка закрытия соединений: {str(e)}")