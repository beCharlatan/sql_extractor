"""Database schema reference tool for the AI agent."""

import psycopg2
from psycopg2 import sql
from typing import Dict, List, Optional, Any
from loguru import logger

from src.config.settings import settings
from src.utils.errors import DatabaseError


class DBSchemaReferenceTool:
    """Tool for retrieving database schema information.
    
    This tool connects to a database and retrieves table structure information,
    which can be used by the agent to understand data structure for filtering,
    sorting, and other operations.
    """

    def __init__(self, db_connection_string: Optional[str] = None):
        """Initialize the DB schema reference tool.

        Args:
            db_connection_string: Optional connection string to the PostgreSQL database. 
                                  Defaults to the one specified in settings.
        """
        self.db_connection_string = db_connection_string or settings.database.get_connection_string()
        logger.info(f"Initialized DBSchemaReferenceTool with database connection")

    def get_table_schema(self, table_name: str) -> str:
        """Get the DDL (CREATE TABLE statement) for a specific table.

        Args:
            table_name: Name of the table to get schema for.

        Returns:
            DDL statement for the table.

        Raises:
            DatabaseError: If there's an error connecting to the database or the table doesn't exist.
        """
        try:
            conn = psycopg2.connect(self.db_connection_string)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute(
                """SELECT EXISTS (SELECT 1 FROM information_schema.tables 
                   WHERE table_schema = 'public' AND table_name = %s)""", 
                (table_name,)
            )
            if not cursor.fetchone()[0]:
                raise DatabaseError(f"Table '{table_name}' does not exist", details={"table_name": table_name})
            
            # Get the CREATE TABLE statement using pg_dump-like query
            cursor.execute(
                """SELECT 'CREATE TABLE ' || relname || ' (' ||
                   array_to_string(array_agg(column_name || ' ' || data_type), ', ') || ');'
                   FROM (
                       SELECT c.relname, a.attname AS column_name,
                       pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type
                       FROM pg_catalog.pg_class c
                       JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                       JOIN pg_catalog.pg_attribute a ON a.attrelid = c.oid
                       WHERE c.relname = %s
                       AND a.attnum > 0
                       AND NOT a.attisdropped
                       AND n.nspname = 'public'
                       ORDER BY a.attnum
                   ) t
                   GROUP BY relname;""", 
                (table_name,)
            )
            result = cursor.fetchone()
            
            conn.close()
            
            if not result or not result[0]:
                raise DatabaseError(f"Failed to retrieve DDL for table '{table_name}'", 
                                  details={"table_name": table_name})
                
            return result[0]
        except psycopg2.Error as e:
            error_msg = f"Database error when retrieving schema for table '{table_name}': {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, details={"table_name": table_name, "original_error": str(e)})
        except Exception as e:
            error_msg = f"Unexpected error when retrieving schema for table '{table_name}': {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, details={"table_name": table_name, "original_error": str(e)})

    def get_table_columns(self, table_name: str) -> List[Dict[str, str]]:
        """Get detailed information about columns in a table.

        Args:
            table_name: Name of the table to get columns for.

        Returns:
            List of dictionaries containing column information (name, type, etc.).

        Raises:
            DatabaseError: If there's an error connecting to the database or the table doesn't exist.
        """
        try:
            conn = psycopg2.connect(self.db_connection_string)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute(
                """SELECT EXISTS (SELECT 1 FROM information_schema.tables 
                   WHERE table_schema = 'public' AND table_name = %s)""", 
                (table_name,)
            )
            if not cursor.fetchone()[0]:
                raise DatabaseError(f"Table '{table_name}' does not exist", details={"table_name": table_name})
            
            # Get column information
            cursor.execute(
                """SELECT 
                    ordinal_position as cid,
                    column_name as name,
                    data_type as type,
                    CASE WHEN is_nullable = 'NO' THEN 1 ELSE 0 END as notnull,
                    column_default as default_value,
                    CASE WHEN column_name IN (
                        SELECT column_name FROM information_schema.table_constraints tc
                        JOIN information_schema.constraint_column_usage ccu 
                        USING (constraint_schema, constraint_name)
                        WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_name = %s
                    ) THEN 1 ELSE 0 END as pk
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position""", 
                (table_name, table_name)
            )
            columns_info = cursor.fetchall()
            
            conn.close()
            
            if not columns_info:
                raise DatabaseError(f"Failed to retrieve columns for table '{table_name}'", 
                                  details={"table_name": table_name})
                
            # Format the column information
            columns = []
            for col in columns_info:
                columns.append({
                    "cid": col[0],
                    "name": col[1],
                    "type": col[2],
                    "notnull": col[3],
                    "default_value": col[4],
                    "pk": col[5]
                })
                
            return columns
        except psycopg2.Error as e:
            error_msg = f"Database error when retrieving columns for table '{self.table_name}': {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, details={"table_name": self.table_name, "original_error": str(e)})
        except Exception as e:
            error_msg = f"Unexpected error when retrieving columns for table '{self.table_name}': {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, details={"table_name": self.table_name, "original_error": str(e)})

    def get_parameter_info(self, parameter_name: str) -> Dict[str, Any]:
        """Get information about a specific parameter from the parameters reference table.

        Args:
            parameter_name: Name of the parameter to look up.

        Returns:
            Dictionary containing parameter information (name, description, data_type).

        Raises:
            DatabaseError: If there's an error connecting to the database or the parameter doesn't exist.
        """
        try:
            conn = psycopg2.connect(self.db_connection_string)
            cursor = conn.cursor()
            
            # Assuming there's a parameters_reference table with columns: parameter_name, description, data_type
            cursor.execute(
                "SELECT parameter_name, description, data_type FROM parameters_reference WHERE parameter_name = %s", 
                (parameter_name,)
            )
            result = cursor.fetchone()
            
            conn.close()
            
            if not result:
                raise DatabaseError(f"Parameter '{parameter_name}' not found in reference table", 
                                  details={"parameter_name": parameter_name})
                
            return {
                "parameter_name": result[0],
                "description": result[1],
                "data_type": result[2]
            }
        except psycopg2.Error as e:
            error_msg = f"Database error when retrieving parameter info for '{parameter_name}': {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, details={"parameter_name": parameter_name, "original_error": str(e)})
        except Exception as e:
            error_msg = f"Unexpected error when retrieving parameter info for '{parameter_name}': {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, details={"parameter_name": parameter_name, "original_error": str(e)})

    def search_parameters(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for parameters matching a search term.

        Args:
            search_term: Term to search for in parameter names or descriptions.

        Returns:
            List of dictionaries containing parameter information.

        Raises:
            DatabaseError: If there's an error connecting to the database.
        """
        try:
            conn = psycopg2.connect(self.db_connection_string)
            cursor = conn.cursor()
            
            # Search in both parameter_name and description
            cursor.execute(
                """
                SELECT parameter_name, description, data_type 
                FROM parameters_reference 
                WHERE parameter_name ILIKE %s OR description ILIKE %s
                """, 
                (f"%{search_term}%", f"%{search_term}%")
            )
            results = cursor.fetchall()
            
            conn.close()
            
            parameters = []
            for result in results:
                parameters.append({
                    "parameter_name": result[0],
                    "description": result[1],
                    "data_type": result[2]
                })
                
            return parameters
        except psycopg2.Error as e:
            error_msg = f"Database error when searching parameters with term '{search_term}': {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, details={"search_term": search_term, "original_error": str(e)})
        except Exception as e:
            error_msg = f"Unexpected error when searching parameters with term '{search_term}': {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, details={"search_term": search_term, "original_error": str(e)})

    def get_all_tables(self) -> List[str]:
        """Get a list of all tables in the database.

        Returns:
            List of table names.

        Raises:
            DatabaseError: If there's an error connecting to the database.
        """
        try:
            conn = psycopg2.connect(self.db_connection_string)
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """
            )
            tables = cursor.fetchall()
            
            conn.close()
            
            return [table[0] for table in tables]
        except psycopg2.Error as e:
            error_msg = f"Database error when retrieving all tables: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, details={"original_error": str(e)})
        except Exception as e:
            error_msg = f"Unexpected error when retrieving all tables: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, details={"original_error": str(e)})
