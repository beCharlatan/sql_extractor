"""Tests for the database schema reference tool."""

import pytest

from src.db.db_schema_tool import DBSchemaReferenceTool
from src.utils.errors import DatabaseError


class TestDBSchemaReferenceTool:
    """Test the DBSchemaReferenceTool class."""
    
    def test_init(self):
        """Test initialization of the DBSchemaReferenceTool."""
        # Test with default connection string
        tool = DBSchemaReferenceTool()
        
        # Test with custom connection string
        custom_conn_string = "postgresql://user:pass@localhost:5432/testdb"
        tool = DBSchemaReferenceTool(connection_string=custom_conn_string)
        assert tool.master_connection_string == custom_conn_string
    
    @pytest.mark.asyncio
    async def test_create(self, mock_asyncpg_pool):
        """Test asynchronous creation of the DBSchemaReferenceTool."""
        # Test with default connection string
        tool = await DBSchemaReferenceTool.create()
        assert isinstance(tool, DBSchemaReferenceTool)
        
        # Test with custom connection string
        custom_conn_string = "postgresql://user:pass@localhost:5432/testdb"
        tool = await DBSchemaReferenceTool.create(connection_string=custom_conn_string)
        assert tool.master_connection_string == custom_conn_string
    
    @pytest.mark.asyncio
    async def test_get_table_schema(self, mock_execute_query):
        """Test getting table schema."""
        # Настройка mock для execute_query
        async def custom_query_results(*args, **kwargs):
            query = args[1] if len(args) > 1 else kwargs.get('query', '')
            if "EXISTS" in query:
                return [{"exists": True}]
            if "SELECT 'CREATE TABLE'" in query:
                return [["CREATE TABLE test_table (id INTEGER, name TEXT);"]]
            return []
            
        mock_execute_query.side_effect = custom_query_results
        
        # Создание инстанса через create
        tool = await DBSchemaReferenceTool.create(connection_string="postgresql://user:pass@localhost:5432/testdb")
        table_name = "test_table"
        
        result = await tool.get_table_schema(table_name)
        
        # Check the result
        assert result == "CREATE TABLE test_table (id INTEGER, name TEXT);"
        
        # Проверка вызовов execute_query
        assert mock_execute_query.call_count == 2
        # Первый вызов должен проверять существование таблицы
        assert "EXISTS" in mock_execute_query.call_args_list[0][0][1]
        # Второй вызов должен получать схему таблицы
        assert "CREATE TABLE" in mock_execute_query.call_args_list[1][0][1]
    
    @pytest.mark.asyncio
    async def test_get_table_schema_table_not_exists(self, mock_execute_query):
        """Test getting schema for non-existent table."""
        # Настройка mock для execute_query
        async def custom_query_results(*args, **kwargs):
            query = args[1] if len(args) > 1 else kwargs.get('query', '')
            if "EXISTS" in query:
                return [{"exists": False}]
            return []
            
        mock_execute_query.side_effect = custom_query_results
        
        # Создание инстанса через create
        tool = await DBSchemaReferenceTool.create(connection_string="postgresql://user:pass@localhost:5432/testdb")
        table_name = "nonexistent_table"
        
        # Check that DatabaseError is raised
        with pytest.raises(DatabaseError) as excinfo:
            await tool.get_table_schema(table_name)
        
        # Check error message
        assert "does not exist" in str(excinfo.value)
        
        # Проверка вызовов execute_query
        assert mock_execute_query.call_count == 1
        assert "EXISTS" in mock_execute_query.call_args[0][1]
    
    @pytest.mark.asyncio
    async def test_get_table_columns(self, mock_execute_query):
        """Test getting table columns."""
        # Настройка mock для execute_query
        async def custom_query_results(*args, **kwargs):
            query = args[1] if len(args) > 1 else kwargs.get('query', '')
            if "EXISTS" in query:
                return [{"exists": True}]
            if "information_schema.columns" in query:
                return [
                    {"cid": 1, "name": "id", "type": "integer", "notnull": 1, "default_value": "nextval('test_table_id_seq'::regclass)", "pk": 1},
                    {"cid": 2, "name": "name", "type": "text", "notnull": 0, "default_value": None, "pk": 0}
                ]
            return []
            
        mock_execute_query.side_effect = custom_query_results
        
        # Создание инстанса через create
        tool = await DBSchemaReferenceTool.create(connection_string="postgresql://user:pass@localhost:5432/testdb")
        table_name = "test_table"
        
        result = await tool.get_table_columns(table_name)
        
        # Check the result
        assert len(result) == 2
        assert result[0]["name"] == "id"
        assert result[0]["type"] == "integer"
        assert result[0]["pk"] == 1
        assert result[1]["name"] == "name"
        assert result[1]["type"] == "text"
        assert result[1]["pk"] == 0
        
        # Проверка вызовов execute_query
        assert mock_execute_query.call_count == 2
        # Первый вызов должен проверять существование таблицы
        assert "EXISTS" in mock_execute_query.call_args_list[0][0][1]
        # Второй вызов должен получать информацию о столбцах
        assert "information_schema.columns" in mock_execute_query.call_args_list[1][0][1]
    
    @pytest.mark.asyncio
    async def test_get_parameter_info(self, mock_execute_query):
        """Test getting parameter information."""
        # Настройка mock для execute_query
        async def custom_query_results(*args, **kwargs):
            query = args[1] if len(args) > 1 else kwargs.get('query', '')
            if "parameters_reference" in query:
                return [{"parameter_name": "test_param", "description": "Test parameter description", "data_type": "string"}]
            return []
            
        mock_execute_query.side_effect = custom_query_results
        
        # Создание инстанса через create
        tool = await DBSchemaReferenceTool.create(connection_string="postgresql://user:pass@localhost:5432/testdb")
        
        result = await tool.get_parameter_info("test_param")
        
        # Check the result
        assert result["parameter_name"] == "test_param"
        assert result["description"] == "Test parameter description"
        assert result["data_type"] == "string"
        
        # Проверка вызовов execute_query
        assert mock_execute_query.call_count == 1
        assert "parameters_reference" in mock_execute_query.call_args[0][1]
    
    @pytest.mark.asyncio
    async def test_get_parameter_info_not_found(self, mock_execute_query):
        """Test getting information for non-existent parameter."""
        # Настройка mock для execute_query - пустой результат
        async def custom_query_results(*args, **kwargs):
            return []
            
        mock_execute_query.side_effect = custom_query_results
        
        # Создание инстанса через create
        tool = await DBSchemaReferenceTool.create(connection_string="postgresql://user:pass@localhost:5432/testdb")
        
        # Check that DatabaseError is raised
        with pytest.raises(DatabaseError) as excinfo:
            await tool.get_parameter_info("nonexistent_param")
        
        # Check error message
        assert "not found in reference table" in str(excinfo.value)
        
        # Проверка вызовов execute_query
        assert mock_execute_query.call_count == 1
        assert "parameters_reference" in mock_execute_query.call_args[0][1]
