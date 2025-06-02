"""Функциональность генерации SQL-запросов для ИИ-агента."""

import json
import re
from typing import Any, Dict, Optional

# from src.agent.enriched_query import EnrichedQuery
from src.db.db_schema_tool import DBSchemaReferenceTool

from loguru import logger

from src.agent.agent import GigachatAgent
from src.utils.errors import (
    GigachatAPIError,
    InvalidSQLError,
    SQLGenerationError,
)


class SQLGenerator:
    """Генерирует компоненты SQL-запроса на основе ввода на естественном языке."""

    def __init__(
        self, 
        agent: Optional[GigachatAgent] = None, 
        db_schema_tool: Optional[DBSchemaReferenceTool] = None, 
        table_name: str = "products"
    ):
        """Инициализация генератора SQL.

        Аргументы:
            agent: Опциональный экземпляр GigachatAgent. Если не предоставлен, будет создан новый.
            db_schema_tool: Опциональный экземпляр DBSchemaReferenceTool. Если не предоставлен, будет создан новый.
            table_name: Имя таблицы, для которой генерируется SQL.
        """
        self.agent = agent or GigachatAgent()
        # self.enriched_query = EnrichedQuery()
        self.db_schema_tool = db_schema_tool
        self.table_name = table_name
        logger.info(f"Initialized SQLGenerator for table {table_name}")

    @classmethod
    async def create(
        cls, 
        agent: Optional[GigachatAgent] = None, 
        db_schema_tool: Optional[DBSchemaReferenceTool] = None, 
        table_name: str = "products"
    ) -> 'SQLGenerator':
        """Асинхронная инициализация генератора SQL.

        Аргументы:
            agent: Опциональный экземпляр GigachatAgent. Если не предоставлен, будет создан новый.
            db_schema_tool: Опциональный экземпляр DBSchemaReferenceTool. Если не предоставлен, будет создан новый.
            table_name: Имя таблицы, для которой генерируется SQL.
            
        Возвращает:
            Экземпляр SQLGenerator с инициализированными зависимостями.
        """
        instance = cls(agent=agent, db_schema_tool=None, table_name=table_name)
        
        # Создание инстанса DBSchemaReferenceTool, если не был передан
        if db_schema_tool is None:
            instance.db_schema_tool = await DBSchemaReferenceTool.create()
        else:
            instance.db_schema_tool = db_schema_tool
            
        return instance

    async def generate_sql_components(
        self,
        filter_text: str,
        constraint_text: str,
    ) -> Dict[str, Any]:
        """Генерация компонентов SQL-запроса на основе текста фильтра и ограничения.

        Аргументы:
            filter_text: Описание фильтра на естественном языке.
            constraint_text: Описание ограничения на естественном языке.

        Возвращает:
            Словарь, содержащий:
            - sql_components: Сгенерированные компоненты SQL
              - where_clause: Условие WHERE (без ключевого слова 'WHERE')
              - order_by_clause: Условие ORDER BY (без ключевого слова 'ORDER BY')
              - limit_clause: Условие LIMIT (без ключевого слова 'LIMIT')
              - full_sql: Объединенные компоненты SQL
            
        Вызывает исключения:
            ValidationError: Если проверка входных данных не пройдена
            DatabaseError: Если таблица не существует или есть ошибка базы данных
            GigachatAPIError: Если есть ошибка с API Gigachat
            SQLGenerationError: Если генерация SQL не удалась
        """
        try:
            table_ddl = await self.db_schema_tool.get_table_schema(self.table_name)
            logger.debug(f"Retrieved table schema for {self.table_name}")
            
            logger.info("Generating SQL components from natural language input")
            logger.debug(f"Filter: {filter_text}")
            logger.debug(f"Constraint: {constraint_text}")

            # Создание промпта для модели
            # enriched_query = await self.enriched_query.process(filter=filter_text, constraint=constraint_text)
            prompt = await self._build_sql_generation_prompt(filter=filter_text, constraint=constraint_text, table_ddl=table_ddl)

            try:
                # Обработка запроса с помощью агента
                response = await self.agent.process_query(prompt)
                
                # Извлекаем текст ответа в зависимости от структуры ответа API
                if isinstance(response, dict) and "choices" in response:
                    # Новый формат ответа от Gigachat API
                    response_text = response["choices"][0]["message"]["content"]
                elif hasattr(response, "choices") and hasattr(response.choices[0], "message"):
                    # Объект ChatCompletion
                    response_text = response.choices[0].message.content
                else:
                    # Старый формат или другой формат
                    response_text = str(response)
                    logger.warning(f"Unexpected response format: {type(response)}")
            except Exception as e:
                logger.error(f"Error calling Gigachat API: {str(e)}")
                raise GigachatAPIError(
                    f"Error calling Gigachat API: {str(e)}",
                    details={"original_error": str(e)}
                )

            # Извлечение структурированного ответа (компоненты SQL)
            try:
                result = self._extract_structured_response(response_text)
            except Exception as e:
                logger.error(f"Error extracting structured response: {str(e)}")
                raise SQLGenerationError(
                    f"Error extracting structured response: {str(e)}",
                    details={"original_error": str(e), "response_text": response_text[:100] + "..."}
                )
            
            # Проверка сгенерированных SQL-компонентов
            try:
                result["sql_components"] = self._validate_sql_components(result["sql_components"], table_ddl)
            except Exception as e:
                logger.error(f"Error validating SQL components: {str(e)}")
                raise InvalidSQLError(
                    f"Error validating SQL components: {str(e)}",
                    details={"original_error": str(e), "sql_components": result.get("sql_components", {})}
                )

            logger.info("Successfully generated SQL components")
            logger.debug(f"SQL components: {result['sql_components']}")
            
            return result
        
        except Exception as e:
            # Перехват любых других неожиданных исключений
            logger.exception(f"Unexpected error in SQL generation: {str(e)}")
            raise SQLGenerationError(
                f"Unexpected error in SQL generation: {str(e)}",
                details={"original_error": str(e)}
            )

    async def _build_sql_generation_prompt(self, filter: str, constraint: str, table_ddl: str) -> str:
        """Создание промпта для генерации SQL.

        Аргументы:
            query: Запрос на естественном языке.
            table_ddl: DDL-определение таблицы для запроса.

        Возвращает:
            Отформатированный промпт для модели.
        """
        # Получение дополнительной информации о столбцах из базы данных
        column_info = ""
        try:
            columns = await self.db_schema_tool.get_table_columns(self.table_name)
            column_info = ""
            
            try:
                for col in columns:
                    column_info += f"{col['attr_name']}: {col['description']}\n"
            except Exception as e:
                logger.warning(f"Could not retrieve parameter descriptions: {str(e)}")
        except Exception as e:
            logger.warning(f"Could not retrieve column information: {str(e)}")
        
        return f"""Ты SQL-агент. Сгенерируй компоненты SQL-запроса на основе следующей информации:
   
[DDL таблицы данных]
```sql
{table_ddl}
```
[Бизнесовое определение атрибутов данных]
{column_info}

[Запрос]
{filter.lower()}
{constraint.lower()}

[Инструкции]
На основе определения таблицы и предоставленного фильтра и ограничения, сгенерируй следующие компоненты SQL-запроса:
1. WHERE - для фильтрации данных в соответствии с описанием фильтра
2. GROUP BY - для группировки данных, если требуется агрегация или вычисление статистических показателей (например, медианы)
3. HAVING - для фильтрации сгруппированных данных, если требуется
4. ORDER BY - для сортировки данных в соответствии с ограничением
5. LIMIT - если в ограничении указан лимит результатов

Предоставь свой ответ в следующем JSON-формате:

```json
{{
  "sql_components": {{
    "where_clause": "<условие_where>",
    "group_by_clause": "<условие_group_by>",
    "having_clause": "<условие_having>",
    "order_by_clause": "<условие_order_by>",
    "limit_clause": "<условие_limit>"
  }}
}}
```

[Правила для обработки строковых значений]
1. Для игнорирования окончаний слов:
   - Всегда используй оператор `ILIKE` (регистронезависимый поиск)
   - Добавляй символы `%` только ПОСЛЕ основы слова
   - Основу слова определяй как:
     * Для слов >6 букв: отсекай последние 2-3 символа
     * Для слов 4-6 букв: отсекай последний 1 символ
     * Для слов <4 букв: используй полное слово

2. Примеры преобразования:
   - "производство" → "производств%" (12 букв >6 → отсекли 2)
   - "компании" → "компани%" (8 букв >6 → отсекли 2)
   - "поле" → "пол%" (4 буквы → отсекли 1)
   - "IT" → "IT" (2 буквы <4 → полное слово)

3. Для фраз из нескольких слов:
   - Разбивай запрос на отдельные слова
   - Для каждого слова применяй правила выше
   - Объединяй условия через `OR`:
     ```sql
     WHERE column ILIKE 'основа1%' 
       OR column ILIKE 'основа2%'
     ```

4. Для точных совпадений (если нужно):
   - Если пользователь указывает кавычки: "текст"
   - Используй точное сравнение: `= 'текст'`

[Правила обработки географических названий]
1. Извлекай ТОЛЬКО ядро названия, удаляя типы объектов:
   - Автоматически удаляй слова: район, область, поселок, город, деревня, село, р-н, обл, пгт, г, д, п 
   - Учитывай все падежи (например: района, области, поселка, городской)
   - В остальном пользуйся правилами для обработки строковых значений

[ПРОВЕРКА]
- Не включай ключевые слова 'WHERE', 'GROUP BY', 'HAVING', 'ORDER BY' или 'LIMIT' в свои условия
- Убедись, что используешь правильные имена столбцов из определения таблицы
- Используй правильный синтаксис SQL с соответствующими операторами (=, <, >, LIKE, IN и т.д.)
- Если требуется вычисление медианы, используй соответствующие функции (например, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY column) для PostgreSQL)
- Если компонент не применим, оставь его как пустую строку
- Для сложных запросов с медианой, можешь использовать подзапросы или оконные функции
"""

    def _extract_structured_response(self, response_text: str) -> Dict[str, Any]:
        """Извлечение структурированного ответа из вывода модели.

        Аргументы:
            response_text: Текстовый ответ от модели.

        Возвращает:
            Словарь, содержащий извлеченные компоненты SQL.
        """
        # Инициализация структуры результата
        result = {
            "sql_components": {
                "where_clause": "",
                "group_by_clause": "",
                "having_clause": "",
                "order_by_clause": "",
                "limit_clause": "",
                "full_sql": ""
            }
        }
        
        # Попытка извлечь JSON из ответа
        try:
            # Поиск JSON-содержимого между тройными обратными кавычками
            json_match = re.search(r'```json\s*(.+?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                parsed_data = json.loads(json_str)
                
                # Извлечение компонентов SQL
                if "sql_components" in parsed_data:
                    result["sql_components"].update(parsed_data["sql_components"])
                    
                logger.info("Successfully extracted structured response from JSON")
                
                # Генерация полного SQL, если он отсутствует
                if "full_sql" not in result["sql_components"] or not result["sql_components"]["full_sql"]:
                    self._generate_full_sql(result["sql_components"])
                    
                return result
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from response: {e}")
        except Exception as e:
            logger.warning(f"Error extracting structured response: {e}")
        
        # Запасной вариант - извлечение с помощью регулярных выражений, если разбор JSON не удался
        logger.info("Falling back to regex extraction")
        sql_components = self._extract_sql_components_regex(response_text)
        result["sql_components"] = sql_components
        
        return result
        
    def _extract_sql_components_regex(self, response_text: str) -> Dict[str, str]:
        """Извлечение компонентов SQL из ответа модели с использованием регулярных выражений.

        Аргументы:
            response_text: Текстовый ответ от модели.

        Возвращает:
            Словарь, содержащий извлеченные компоненты SQL.
        """
        components = {
            "where_clause": "",
            "group_by_clause": "",
            "having_clause": "",
            "order_by_clause": "",
            "limit_clause": "",
        }

        # Извлечение условия WHERE
        where_match = re.search(r'WHERE:\s*(.+?)(?=\nGROUP BY:|\nHAVING:|\nORDER BY:|\nLIMIT:|$)', response_text, re.DOTALL)
        if where_match:
            components["where_clause"] = where_match.group(1).strip()

        # Извлечение условия GROUP BY
        group_by_match = re.search(r'GROUP BY:\s*(.+?)(?=\nHAVING:|\nORDER BY:|\nLIMIT:|$)', response_text, re.DOTALL)
        if group_by_match:
            components["group_by_clause"] = group_by_match.group(1).strip()
            
        # Извлечение условия HAVING
        having_match = re.search(r'HAVING:\s*(.+?)(?=\nORDER BY:|\nLIMIT:|$)', response_text, re.DOTALL)
        if having_match:
            components["having_clause"] = having_match.group(1).strip()

        # Извлечение условия ORDER BY
        order_by_match = re.search(r'ORDER BY:\s*(.+?)(?=\nLIMIT:|$)', response_text, re.DOTALL)
        if order_by_match:
            components["order_by_clause"] = order_by_match.group(1).strip()

        # Извлечение условия LIMIT
        limit_match = re.search(r'LIMIT:\s*(.+?)(?=\n|$)', response_text, re.DOTALL)
        if limit_match:
            components["limit_clause"] = limit_match.group(1).strip()

        # Generate full SQL
        self._generate_full_sql(components)
        
        return components
        
    def _generate_full_sql(self, components: Dict[str, str]) -> None:
        """Генерация полного SQL из компонентов и добавление его в словарь компонентов.

        Аргументы:
            components: Словарь компонентов SQL для обновления с full_sql.
        """
        full_sql = ""
        if components["where_clause"]:
            full_sql += f"WHERE {components['where_clause']}"
        if components["group_by_clause"]:
            full_sql += f"\nGROUP BY {components['group_by_clause']}"
        if components["having_clause"]:
            full_sql += f"\nHAVING {components['having_clause']}"
        if components["order_by_clause"]:
            full_sql += f"\nORDER BY {components['order_by_clause']}"
        if components["limit_clause"]:
            full_sql += f"\nLIMIT {components['limit_clause']}"

        components["full_sql"] = full_sql

    def _validate_sql_components(self, components: Dict[str, str], table_ddl: str) -> Dict[str, str]:
        """Проверка сгенерированных компонентов SQL на соответствие DDL таблицы.

        Аргументы:
            components: Извлеченные компоненты SQL.
            table_ddl: DDL таблицы для проверки.

        Возвращает:
            Проверенные компоненты SQL.
            
        Вызывает исключение:
            InvalidSQLError: Если компоненты SQL недействительны и не могут быть исправлены.
        """
        if not components:
            raise InvalidSQLError(
                "No SQL components were generated",
                details={"components": components}
            )
            
        # Проверка наличия необходимых ключей
        required_keys = ["where_clause", "group_by_clause", "having_clause", "order_by_clause", "limit_clause"]
        for key in required_keys:
            if key not in components:
                components[key] = ""  # Initialize missing keys with empty strings
                logger.warning(f"Missing SQL component: {key}. Initialized with empty string.")

        # Проверка на наличие шаблонов SQL-инъекций
        sql_injection_patterns = [
            r'--',  # SQL comment
            r';\s*DROP',  # Attempt to drop tables
            r';\s*DELETE',  # Attempt to delete data
            r';\s*INSERT',  # Attempt to insert data
            r';\s*UPDATE',  # Attempt to update data
            r';\s*ALTER',  # Attempt to alter tables
            r'UNION\s+SELECT',  # UNION-based injection
        ]
        
        for component_name in ["where_clause", "group_by_clause", "having_clause", "order_by_clause", "limit_clause"]:
            component = components[component_name]
            if component:
                for pattern in sql_injection_patterns:
                    if re.search(pattern, component, re.IGNORECASE):
                        raise InvalidSQLError(
                            f"Potential SQL injection detected in {component_name}",
                            details={"component": component, "pattern": pattern}
                        )

        # Проверка, что условие LIMIT является числом или пустым
        limit = components["limit_clause"]
        if limit:
            if not re.match(r'^\d+$', limit):
                logger.warning(f"Invalid LIMIT clause: {limit}. Setting to empty.")
                components["limit_clause"] = ""
                # Обновление полного SQL соответственно, если он существует
                if "full_sql" in components:
                    components["full_sql"] = components["full_sql"].replace(f"\nLIMIT {limit}", "")
        
        # Генерация полного SQL, если он не существует или требует обновления
        self._generate_full_sql(components)

        return components