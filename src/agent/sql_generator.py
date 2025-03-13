"""SQL query generation functionality for the AI agent."""

import json
import re
from typing import Any, Dict, List, Optional

from src.db.db_schema_tool import DBSchemaReferenceTool

from loguru import logger

from src.agent.agent import GigachatAgent
from src.utils.errors import (
    GigachatAPIError,
    InvalidSQLError,
    InvalidTableDDLError,
    SQLGenerationError,
    ValidationError,
)


class SQLGenerator:
    """Generates SQL query components based on natural language input."""

    def __init__(self, agent: Optional[GigachatAgent] = None, db_schema_tool: Optional[DBSchemaReferenceTool] = None, table_name: str = "products"):
        """Initialize the SQL generator.

        Args:
            agent: Optional GigachatAgent instance. If not provided, a new one will be created.
            db_schema_tool: Optional DBSchemaReferenceTool instance. If not provided, a new one will be created.
            table_name: Name of the table to generate SQL for. Defaults to "products".
        """
        self.agent = agent or GigachatAgent()
        self.db_schema_tool = db_schema_tool or DBSchemaReferenceTool()
        self.table_name = table_name
        logger.info(f"Initialized SQLGenerator for table {table_name}")

    def generate_sql_components(
        self,
        filter_text: str,
        constraint_text: str,
    ) -> Dict[str, Any]:
        """Generate SQL query components based on filter and constraint text.

        Args:
            filter_text: Human-readable filter description.
            constraint_text: Human-readable constraint description.

        Returns:
            Dictionary containing:
            - sql_components: The generated SQL components
              - where_clause: The WHERE clause (without the 'WHERE' keyword)
              - order_by_clause: The ORDER BY clause (without the 'ORDER BY' keyword)
              - limit_clause: The LIMIT clause (without the 'LIMIT' keyword)
              - full_sql: The combined SQL components
            
        Raises:
            ValidationError: If input validation fails
            DatabaseError: If the table doesn't exist or there's a database error
            GigachatAPIError: If there's an error with the Gigachat API
            SQLGenerationError: If SQL generation fails
        """
        try:
            # Validate inputs
            if not filter_text or not filter_text.strip():
                raise ValidationError(
                    "Filter text cannot be empty",
                    details={"field": "filter"}
                )
                
            if not constraint_text or not constraint_text.strip():
                raise ValidationError(
                    "Constraint text cannot be empty",
                    details={"field": "constraint"}
                )
                
            if len(filter_text) > 400:
                raise ValidationError(
                    "Filter text exceeds maximum length of 400 characters",
                    details={"field": "filter", "value": len(filter_text)}
                )
                
            if len(constraint_text) > 400:
                raise ValidationError(
                    "Constraint text exceeds maximum length of 400 characters",
                    details={"field": "constraint", "value": len(constraint_text)}
                )
                
            # Get table DDL from database
            try:
                table_ddl = self.db_schema_tool.get_table_schema(self.table_name)
                logger.debug(f"Retrieved table schema for {self.table_name}")
            except Exception as e:
                logger.error(f"Error retrieving table schema for {self.table_name}: {str(e)}")
                raise
            
            logger.info("Generating SQL components from natural language input")
            logger.debug(f"Filter: {filter_text}")
            logger.debug(f"Constraint: {constraint_text}")

            # Construct a prompt for the model
            prompt = self._build_sql_generation_prompt(filter_text, constraint_text, table_ddl)

            try:
                # Process the query with the agent
                response = self.agent.process_query(prompt)
                
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

            # Extract structured response (SQL components)
            try:
                result = self._extract_structured_response(response_text)
            except Exception as e:
                logger.error(f"Error extracting structured response: {str(e)}")
                raise SQLGenerationError(
                    f"Error extracting structured response: {str(e)}",
                    details={"original_error": str(e), "response_text": response_text[:100] + "..."}
                )
            
            # Validate the generated SQL components
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
            
        except (ValidationError, InvalidTableDDLError, GigachatAPIError, SQLGenerationError, InvalidSQLError):
            # Re-raise known exceptions for proper handling upstream
            raise
        except Exception as e:
            # Catch any other unexpected exceptions
            logger.exception(f"Unexpected error in SQL generation: {str(e)}")
            raise SQLGenerationError(
                f"Unexpected error in SQL generation: {str(e)}",
                details={"original_error": str(e)}
            )

    def _build_sql_generation_prompt(self, filter_text: str, constraint_text: str, table_ddl: str) -> str:
        """Build a prompt for SQL generation.

        Args:
            filter_text: Human-readable filter description.
            constraint_text: Human-readable constraint description.
            table_ddl: DDL definition of the table to query.

        Returns:
            Formatted prompt for the model.
        """
        # Get additional column information from database
        column_info = ""
        try:
            columns = self.db_schema_tool.get_table_columns(self.table_name)
            column_names = [col["name"] for col in columns]
            column_info = f"\n\n## Информация о столбцах\nТаблица: {self.table_name}\nИмена столбцов: {', '.join(column_names)}"
            
            # Add data types for better context
            column_types = [f"{col['name']} ({col['type']})" for col in columns]
            column_info += f"\nТипы столбцов: {', '.join(column_types)}"
            
            # Try to get parameter descriptions if available
            parameter_descriptions = []
            try:
                for col in columns:
                    try:
                        param_info = self.db_schema_tool.get_parameter_info(col["name"])
                        if param_info and "description" in param_info:
                            parameter_descriptions.append(f"{col['name']}: {param_info['description']}")
                    except Exception:
                        pass
                if parameter_descriptions:
                    column_info += f"\n\nОписания параметров:\n{chr(10).join(parameter_descriptions)}"
            except Exception as e:
                logger.warning(f"Could not retrieve parameter descriptions: {str(e)}")
        except Exception as e:
            logger.warning(f"Could not retrieve column information: {str(e)}")
            # Fallback to extracting from DDL
            try:
                column_names = self._extract_column_names(table_ddl)
                if column_names:
                    column_info = f"\n\n## Информация о столбцах\nИмена столбцов: {', '.join(column_names)}"
            except Exception as e:
                logger.warning(f"Could not extract column names from DDL: {str(e)}")
        
        return f"""Сгенерируй компоненты SQL-запроса на основе следующей информации:

## Определение таблицы
```sql
{table_ddl}
```
{column_info}

## Фильтр
{filter_text}

## Ограничение
{constraint_text}

## Инструкции
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

Для SQL-компонентов:
- Не включай ключевые слова 'WHERE', 'GROUP BY', 'HAVING', 'ORDER BY' или 'LIMIT' в свои условия
- Убедись, что используешь правильные имена столбцов из определения таблицы
- Используй правильный синтаксис SQL с соответствующими операторами (=, <, >, LIKE, IN и т.д.)
- Если требуется вычисление медианы, используй соответствующие функции (например, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY column) для PostgreSQL)
- Если компонент не применим, оставь его как пустую строку
- Для сложных запросов с медианой, можешь использовать подзапросы или оконные функции
"""

    def _extract_structured_response(self, response_text: str) -> Dict[str, Any]:
        """Extract structured response from the model's output.

        Args:
            response_text: The text response from the model.

        Returns:
            Dictionary containing the extracted SQL components.
        """
        # Initialize the result structure
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
        
        # Try to extract JSON from the response
        try:
            # Find JSON content between triple backticks
            json_match = re.search(r'```json\s*(.+?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                parsed_data = json.loads(json_str)
                
                # Extract SQL components
                if "sql_components" in parsed_data:
                    result["sql_components"].update(parsed_data["sql_components"])
                    
                logger.info("Successfully extracted structured response from JSON")
                
                # Generate full SQL if not present
                if "full_sql" not in result["sql_components"] or not result["sql_components"]["full_sql"]:
                    self._generate_full_sql(result["sql_components"])
                    
                return result
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from response: {e}")
        except Exception as e:
            logger.warning(f"Error extracting structured response: {e}")
        
        # Fallback to regex extraction if JSON parsing fails
        logger.info("Falling back to regex extraction")
        sql_components = self._extract_sql_components_regex(response_text)
        result["sql_components"] = sql_components
        
        return result
        
    def _extract_sql_components_regex(self, response_text: str) -> Dict[str, str]:
        """Extract SQL components from the model's response using regex.

        Args:
            response_text: The text response from the model.

        Returns:
            Dictionary containing the extracted SQL components.
        """
        components = {
            "where_clause": "",
            "group_by_clause": "",
            "having_clause": "",
            "order_by_clause": "",
            "limit_clause": "",
        }

        # Extract WHERE clause
        where_match = re.search(r'WHERE:\s*(.+?)(?=\nGROUP BY:|\nHAVING:|\nORDER BY:|\nLIMIT:|$)', response_text, re.DOTALL)
        if where_match:
            components["where_clause"] = where_match.group(1).strip()

        # Extract GROUP BY clause
        group_by_match = re.search(r'GROUP BY:\s*(.+?)(?=\nHAVING:|\nORDER BY:|\nLIMIT:|$)', response_text, re.DOTALL)
        if group_by_match:
            components["group_by_clause"] = group_by_match.group(1).strip()
            
        # Extract HAVING clause
        having_match = re.search(r'HAVING:\s*(.+?)(?=\nORDER BY:|\nLIMIT:|$)', response_text, re.DOTALL)
        if having_match:
            components["having_clause"] = having_match.group(1).strip()

        # Extract ORDER BY clause
        order_by_match = re.search(r'ORDER BY:\s*(.+?)(?=\nLIMIT:|$)', response_text, re.DOTALL)
        if order_by_match:
            components["order_by_clause"] = order_by_match.group(1).strip()

        # Extract LIMIT clause
        limit_match = re.search(r'LIMIT:\s*(.+?)(?=\n|$)', response_text, re.DOTALL)
        if limit_match:
            components["limit_clause"] = limit_match.group(1).strip()

        # Generate full SQL
        self._generate_full_sql(components)
        
        return components
        
    def _generate_full_sql(self, components: Dict[str, str]) -> None:
        """Generate full SQL from components and add it to the components dict.

        Args:
            components: Dictionary of SQL components to update with full_sql.
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
        """Validate the generated SQL components against the table DDL.

        Args:
            components: The extracted SQL components.
            table_ddl: The table DDL to validate against.

        Returns:
            Validated SQL components.
            
        Raises:
            InvalidSQLError: If the SQL components are invalid and cannot be fixed.
        """
        if not components:
            raise InvalidSQLError(
                "No SQL components were generated",
                details={"components": components}
            )
            
        # Check required keys exist
        required_keys = ["where_clause", "group_by_clause", "having_clause", "order_by_clause", "limit_clause"]
        for key in required_keys:
            if key not in components:
                components[key] = ""  # Initialize missing keys with empty strings
                logger.warning(f"Missing SQL component: {key}. Initialized with empty string.")
        
        # Extract column names from the table DDL
        try:
            column_names = self._extract_column_names(table_ddl)
            if not column_names:
                raise InvalidTableDDLError(
                    "Could not extract any column names from the table DDL",
                    details={"table_ddl": table_ddl[:100] + "..."}
                )
            logger.debug(f"Extracted column names: {column_names}")
        except Exception as e:
            raise InvalidTableDDLError(
                f"Error extracting column names from table DDL: {str(e)}",
                details={"table_ddl": table_ddl[:100] + "...", "error": str(e)}
            )

        # Check if the generated SQL uses valid column names
        for component_name in ["where_clause", "group_by_clause", "having_clause", "order_by_clause"]:
            component = components[component_name]
            if component:
                # Basic validation - check if the component contains valid column names
                valid = False
                for column in column_names:
                    if column.lower() in component.lower():
                        valid = True
                        break

                if not valid:
                    logger.warning(f"Generated {component_name} does not contain any valid column names")
                    # We're not fixing it automatically, but we're warning about it
                    # This could be a false positive if the component uses aliases or functions
        
        # Check for SQL injection patterns
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

        # Validate LIMIT clause is a number or empty
        limit = components["limit_clause"]
        if limit:
            if not re.match(r'^\d+$', limit):
                logger.warning(f"Invalid LIMIT clause: {limit}. Setting to empty.")
                components["limit_clause"] = ""
                # Update the full SQL accordingly if it exists
                if "full_sql" in components:
                    components["full_sql"] = components["full_sql"].replace(f"\nLIMIT {limit}", "")
        
        # Generate full SQL if it doesn't exist or needs to be updated
        self._generate_full_sql(components)

        return components

    def _extract_column_names(self, table_ddl: str) -> List[str]:
        """Extract column names from the table DDL.

        Args:
            table_ddl: The table DDL to extract column names from.

        Returns:
            List of column names.
        """
        column_names = []
        
        # Use regex to extract column definitions
        # This is a simplified approach and might need to be adjusted for complex DDLs
        column_pattern = r'\s*([\w_]+)\s+([\w\(\)]+)'  # Matches "column_name data_type"
        matches = re.finditer(column_pattern, table_ddl)
        
        for match in matches:
            column_name = match.group(1)
            # Skip if the match is a SQL keyword
            if column_name.upper() not in ["CREATE", "TABLE", "PRIMARY", "KEY", "FOREIGN", "REFERENCES", "NOT", "NULL", "DEFAULT", "AUTO_INCREMENT"]:
                column_names.append(column_name)
        
        return column_names
