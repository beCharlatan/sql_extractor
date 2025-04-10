"""Сервис для обработки SQL запросов к таблице организаций."""

from typing import Dict, Any, List, Optional
from loguru import logger

from src.db.base_db_client import BaseDBClient
from src.utils.errors import DatabaseError


class OrganizationProcessor(BaseDBClient):
    """Сервис для обработки SQL запросов к таблице организаций."""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        slave_connection_string: Optional[str] = None,
        db_key: str = 'organizations'
    ):
        """Инициализация процессора организаций.
        
        Args:
            connection_string: Опциональная строка подключения к базе данных.
            slave_connection_string: Опциональная строка подключения к слейв-ноде.
            db_key: Уникальный идентификатор для этого подключения к базе данных.
        """
        super().__init__(connection_string, slave_connection_string=slave_connection_string, db_key=db_key)

    async def process_sql_components(
        self, 
        sql_components: Dict[str, str],
        gosb_id: Optional[str] = None,
        tb_id: Optional[str] = None,
        pers_number: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Обработка SQL компонентов и получение списка организаций.
        
        Args:
            sql_components: Словарь с компонентами SQL запроса.
            gosb_id: Идентификатор ГОСБ для фильтрации.
            tb_id: Идентификатор ТБ для фильтрации.
            pers_number: Табельный номер для фильтрации.
            
        Returns:
            Список организаций, соответствующих условиям запроса.
            
        Raises:
            DatabaseError: Если произошла ошибка при выполнении запроса.
        """
        try:
            # Формирование полного SQL запроса
            full_query = self._build_full_query(
                sql_components,
                gosb_id=gosb_id,
                tb_id=tb_id,
                pers_number=pers_number
            )
            
            # Выполнение запроса
            logger.info("Executing SQL query for organizations")
            logger.debug(f"Full query: {full_query}")
            
            organizations = await self.execute_query(full_query)
            
            # Преобразование результатов в список словарей
            result = []
            for org in organizations:
                result.append(dict(org))
                
            logger.info(f"Retrieved {len(result)} organizations")
            return result
            
        except Exception as e:
            error_msg = f"Error processing SQL components: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, details={"original_error": str(e)})

    def _build_system_filters(
        self,
        gosb_id: Optional[str] = None,
        tb_id: Optional[str] = None,
        pers_number: Optional[str] = None
    ) -> str:
        """Построение системных фильтров для запроса.
        
        Args:
            gosb_id: Идентификатор ГОСБ для фильтрации.
            tb_id: Идентификатор ТБ для фильтрации.
            pers_number: Табельный номер для фильтрации.
            
        Returns:
            Строка с условиями системной фильтрации.
        """
        filters = []
        
        # Фильтр по gosb_id
        if gosb_id:
            filters.append(f"(role_14_gosb_id = '{gosb_id}' OR role_73_gosb_id = '{gosb_id}')")
            
        # Фильтр по tb_id
        if tb_id:
            filters.append(f"(role_14_tb_id = '{tb_id}' OR role_73_tb_id = '{tb_id}')")
            
        # Фильтр по pers_number
        if pers_number:
            filters.append(f"(role_14_boss_saphr_id = '{pers_number}' OR role_73_boss_saphr_id = '{pers_number}')")
            
        return " AND ".join(filters) if filters else ""

    def _build_system_sorting(self) -> str:
        """Построение системной сортировки для запроса.
        
        Returns:
            Строка с условиями системной сортировки.
        """
        return "fl_amt_potential DESC, last_activity_dt DESC"

    def _build_full_query(
        self,
        sql_components: Dict[str, str],
        gosb_id: Optional[str] = None,
        tb_id: Optional[str] = None,
        pers_number: Optional[str] = None
    ) -> str:
        """Построение полного SQL запроса с учетом всех компонентов.
        
        Args:
            sql_components: Словарь с компонентами SQL запроса.
            gosb_id: Идентификатор ГОСБ для фильтрации.
            tb_id: Идентификатор ТБ для фильтрации.
            pers_number: Табельный номер для фильтрации.
            
        Returns:
            Полный SQL запрос.
        """
        # Добавление системных фильтров
        system_filters = self._build_system_filters(gosb_id, tb_id, pers_number)
        
        # Добавление пользовательских фильтров
        user_filters = sql_components.get('where', '')
        limit_clause = sql_components.get('limit_clause', '30')
        order_by_clause = f'ORDER BY {self._build_system_sorting()}{', ' + sql_components.get('order_by_clause', '') if sql_components.get('order_by_clause') else ''}'
        
        # Объединение фильтров
        where_clause = ''
        if system_filters and user_filters:
            where_clause = f"WHERE {system_filters} AND {user_filters}"
        elif system_filters:
            where_clause = f"WHERE {system_filters}"
        elif user_filters:
            where_clause = f"WHERE {user_filters}"
        
        # Формирование подзапроса с ранжированием по менеджерам
        subquery = f"""
        WITH ranked_orgs AS (
            SELECT 
                epk_id,
                org_name,
                oktmo,
                role_6_fio,
                is_salary_agreement,
                is_military,
                holding_name,
                sector_name,
                industry_name,
                fl_amt_potential,
                avg_fot_amt,
                avg_fl_amt,
                avg_salary_amt,
                segment_id,
                inn,
                COALESCE(role_14_saphr_id, role_73_saphr_id) as employee_number,
                COALESCE(role_14_boss_saphr_id, role_73_boss_saphr_id) as owner_number,
                ROW_NUMBER() OVER (
                    PARTITION BY 
                        CASE 
                            WHEN role_14_saphr_id IS NOT NULL THEN role_14_saphr_id 
                            ELSE role_73_saphr_id 
                        END
                    {order_by_clause}
                ) as manager_rank
            FROM organizations
            {where_clause}
        )
        SELECT * FROM ranked_orgs
        WHERE manager_rank <= LEAST({limit_clause}, 30)
        """
        
        return subquery 