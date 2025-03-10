"""SQL query generation functionality for the AI agent."""

import json
import re
from typing import Any, Dict, List, Optional

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

    def __init__(self, agent: Optional[GigachatAgent] = None):
        """Initialize the SQL generator.

        Args:
            agent: Optional GigachatAgent instance. If not provided, a new one will be created.
        """
        self.agent = agent or GigachatAgent()
        logger.info("Initialized SQLGenerator")

    def generate_sql_components(
        self,
        filter_text: str,
        constraint_text: str,
        table_ddl: str,
    ) -> Dict[str, Any]:
        """Generate SQL query components and structured parameters based on filter and constraint text.

        Args:
            filter_text: Human-readable filter description.
            constraint_text: Human-readable constraint description.
            table_ddl: DDL definition of the table to query.

        Returns:
            Dictionary containing:
            - sql_components: The generated SQL components
              - where_clause: The WHERE clause (without the 'WHERE' keyword)
              - order_by_clause: The ORDER BY clause (without the 'ORDER BY' keyword)
              - limit_clause: The LIMIT clause (without the 'LIMIT' keyword)
              - full_sql: The combined SQL components
            - parameters: Structured parameters extracted from the input
            
        Raises:
            ValidationError: If input validation fails
            InvalidTableDDLError: If the table DDL is invalid
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
                
            if not table_ddl or not table_ddl.strip():
                raise InvalidTableDDLError(
                    "Table DDL cannot be empty",
                    details={"field": "table_ddl"}
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
                
            # Validate table DDL format
            if not table_ddl.lower().strip().startswith("create table"):
                raise InvalidTableDDLError(
                    "Table DDL must start with 'CREATE TABLE'",
                    details={"field": "table_ddl", "value": table_ddl[:20] + "..."}
                )
            
            logger.info("Generating SQL components and structured parameters from natural language input")
            logger.debug(f"Filter: {filter_text}")
            logger.debug(f"Constraint: {constraint_text}")
            logger.debug(f"Table DDL: {table_ddl}")

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

            # Extract structured response (SQL components and parameters)
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

            logger.info("Successfully generated SQL components and structured parameters")
            logger.debug(f"SQL components: {result['sql_components']}")
            logger.debug(f"Parameters: {result['parameters']}")
            
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
        return f"""Generate SQL query components based on the following information:

## Table Definition
```sql
{table_ddl}
```

## Filter
{filter_text}

## Constraint
{constraint_text}

## Instructions
Based on the table definition and the provided filter and constraint, generate the following SQL query components:
1. WHERE clause - to filter the data according to the filter description
2. ORDER BY clause - to sort the data according to the constraint
3. LIMIT clause - if any limit is specified in the constraint

In addition, extract structured parameters from the filter and constraint text.

Provide your answer in the following JSON format:

```json
{{
  "sql_components": {{
    "where_clause": "<where_clause>",
    "order_by_clause": "<order_by_clause>",
    "limit_clause": "<limit_clause>"
  }},
  "parameters": {{
    "<parameter_name>": "<parameter_value>",
    ...
  }}
}}
```

For the SQL components:
- Do not include the keywords 'WHERE', 'ORDER BY', or 'LIMIT' in your clauses
- Make sure to use the correct column names from the table definition
- Use proper SQL syntax with appropriate operators (=, <, >, LIKE, IN, etc.)
- If a component is not applicable, leave it as an empty string

For the parameters:
- Extract all relevant parameters mentioned in the filter and constraint
- Use meaningful parameter names (e.g., category, price_min, sort_by, limit)
- Convert values to appropriate types where possible (numbers for numeric values, etc.)
- Include all parameters that would be useful for understanding the query
"""

    def _extract_structured_response(self, response_text: str) -> Dict[str, Any]:
        """Extract structured response from the model's output.

        Args:
            response_text: The text response from the model.

        Returns:
            Dictionary containing the extracted SQL components and parameters.
        """
        # Initialize the result structure
        result = {
            "sql_components": {
                "where_clause": "",
                "order_by_clause": "",
                "limit_clause": "",
                "full_sql": ""
            },
            "parameters": {}
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
                
                # Extract parameters
                if "parameters" in parsed_data:
                    result["parameters"] = parsed_data["parameters"]
                    
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
        
        # Try to extract parameters using regex
        result["parameters"] = self._extract_parameters_regex(response_text)
        
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
            "order_by_clause": "",
            "limit_clause": "",
        }

        # Extract WHERE clause
        where_match = re.search(r'WHERE:\s*(.+?)(?=\nORDER BY:|\nLIMIT:|$)', response_text, re.DOTALL)
        if where_match:
            components["where_clause"] = where_match.group(1).strip()

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
        if components["order_by_clause"]:
            full_sql += f"\nORDER BY {components['order_by_clause']}"
        if components["limit_clause"]:
            full_sql += f"\nLIMIT {components['limit_clause']}"

        components["full_sql"] = full_sql
        
    def _extract_parameters_regex(self, response_text: str) -> Dict[str, Any]:
        """Extract parameters from the model's response using regex.

        Args:
            response_text: The text response from the model.

        Returns:
            Dictionary containing the extracted parameters.
        """
        parameters = {}
        
        # Try to find parameter sections
        param_section_match = re.search(r'Parameters:\s*(.+?)(?=\n\n|$)', response_text, re.DOTALL)
        if param_section_match:
            param_section = param_section_match.group(1)
            # Extract key-value pairs
            param_matches = re.finditer(r'(\w+)\s*:\s*(.+?)(?=\n\w+\s*:|$)', param_section, re.DOTALL)
            for match in param_matches:
                key = match.group(1).strip()
                value = match.group(2).strip()
                parameters[key] = value
        
        # Look for key-value pairs in the entire response
        if not parameters:
            # Try to extract from JSON-like structures
            json_like_match = re.search(r'\{\s*"parameters"\s*:\s*\{(.+?)\}\s*\}', response_text, re.DOTALL)
            if json_like_match:
                param_content = json_like_match.group(1)
                param_matches = re.finditer(r'"(\w+)"\s*:\s*"(.+?)"', param_content)
                for match in param_matches:
                    key = match.group(1).strip()
                    value = match.group(2).strip()
                    parameters[key] = value
        
        return parameters

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
        required_keys = ["where_clause", "order_by_clause", "limit_clause"]
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
        for component_name in ["where_clause", "order_by_clause"]:
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
        
        for component_name in ["where_clause", "order_by_clause", "limit_clause"]:
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
