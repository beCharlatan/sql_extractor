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
        tool = DBSchemaReferenceTool(db_connection_string=custom_conn_string)
        assert tool.db_connection_string == custom_conn_string
    
    def test_get_table_schema(self, mock_db_connection):
        """Test getting table schema."""
        _, _, mock_cursor = mock_db_connection
        
        # Mock the cursor's fetchone method to return table exists
        mock_cursor.fetchone.side_effect = [(True,), ("CREATE TABLE test_table (id INTEGER, name TEXT);",)]
        
        tool = DBSchemaReferenceTool(db_connection_string="postgresql://user:pass@localhost:5432/testdb")
        table_name = "test_table"
        
        result = tool.get_table_schema(table_name)
        
        # Check that the correct SQL was executed
        assert mock_cursor.execute.call_count == 2
        # First call should check if table exists
        assert "SELECT EXISTS" in mock_cursor.execute.call_args_list[0][0][0]
        # Second call should get the table schema
        assert "CREATE TABLE" in mock_cursor.execute.call_args_list[1][0][0]
        
        # Check the result
        assert result == "CREATE TABLE test_table (id INTEGER, name TEXT);"
    
    def test_get_table_schema_table_not_exists(self, mock_db_connection):
        """Test getting schema for non-existent table."""
        _, _, mock_cursor = mock_db_connection
        
        # Mock the cursor's fetchone method to return table does not exist
        mock_cursor.fetchone.return_value = (False,)
        
        tool = DBSchemaReferenceTool(db_connection_string="postgresql://user:pass@localhost:5432/testdb")
        table_name = "nonexistent_table"
        
        # Check that DatabaseError is raised
        with pytest.raises(DatabaseError) as excinfo:
            tool.get_table_schema(table_name)
        
        # Check error message
        assert "does not exist" in str(excinfo.value)
    
    def test_get_table_columns(self, mock_db_connection):
        """Test getting table columns."""
        _, _, mock_cursor = mock_db_connection
        
        # Mock the cursor's fetchone and fetchall methods
        mock_cursor.fetchone.return_value = (True,)
        mock_cursor.fetchall.return_value = [
            (1, "id", "integer", 1, "nextval('test_table_id_seq'::regclass)", 1),
            (2, "name", "text", 0, None, 0)
        ]
        
        tool = DBSchemaReferenceTool(db_connection_string="postgresql://user:pass@localhost:5432/testdb")
        table_name = "test_table"
        
        result = tool.get_table_columns(table_name)
        
        # Check that the correct SQL was executed
        assert mock_cursor.execute.call_count == 2
        # First call should check if table exists
        assert "SELECT EXISTS" in mock_cursor.execute.call_args_list[0][0][0]
        # Second call should get the column information
        assert "information_schema.columns" in mock_cursor.execute.call_args_list[1][0][0]
        
        # Check the result
        assert len(result) == 2
        assert result[0]["name"] == "id"
        assert result[0]["type"] == "integer"
        assert result[0]["pk"] == 1
        assert result[1]["name"] == "name"
        assert result[1]["type"] == "text"
        assert result[1]["pk"] == 0
    
    def test_get_parameter_info(self, mock_db_connection):
        """Test getting parameter information."""
        _, _, mock_cursor = mock_db_connection
        
        # Mock the cursor's fetchone method
        mock_cursor.fetchone.return_value = ("test_param", "Test parameter description", "string")
        
        tool = DBSchemaReferenceTool(db_connection_string="postgresql://user:pass@localhost:5432/testdb")
        
        result = tool.get_parameter_info("test_param")
        
        # Check that the correct SQL was executed
        assert mock_cursor.execute.call_count == 1
        assert "parameters_reference" in mock_cursor.execute.call_args[0][0]
        
        # Check the result
        assert result["parameter_name"] == "test_param"
        assert result["description"] == "Test parameter description"
        assert result["data_type"] == "string"
    
    def test_get_parameter_info_not_found(self, mock_db_connection):
        """Test getting information for non-existent parameter."""
        _, _, mock_cursor = mock_db_connection
        
        # Mock the cursor's fetchone method to return None (parameter not found)
        mock_cursor.fetchone.return_value = None
        
        tool = DBSchemaReferenceTool(db_connection_string="postgresql://user:pass@localhost:5432/testdb")
        
        # Check that DatabaseError is raised
        with pytest.raises(DatabaseError) as excinfo:
            tool.get_parameter_info("nonexistent_param")
        
        # Check error message
        assert "not found in reference table" in str(excinfo.value)
    
    def test_search_parameters(self, mock_db_connection):
        """Test searching for parameters."""
        _, _, mock_cursor = mock_db_connection
        
        # Mock the cursor's fetchall method
        mock_cursor.fetchall.return_value = [
            ("param1", "First test parameter", "string"),
            ("param2", "Second test parameter", "integer")
        ]
        
        tool = DBSchemaReferenceTool(db_connection_string="postgresql://user:pass@localhost:5432/testdb")
        
        result = tool.search_parameters("test")
        
        # Check that the correct SQL was executed
        assert mock_cursor.execute.call_count == 1
        assert "ILIKE" in mock_cursor.execute.call_args[0][0]
        
        # Check the result
        assert len(result) == 2
        assert result[0]["parameter_name"] == "param1"
        assert result[1]["parameter_name"] == "param2"
    
    def test_get_all_tables(self, mock_db_connection):
        """Test getting all tables from the database."""
        _, _, mock_cursor = mock_db_connection
        
        # Mock the cursor's fetchall method
        mock_cursor.fetchall.return_value = [("table1",), ("table2",), ("table3",)]
        
        tool = DBSchemaReferenceTool(db_connection_string="postgresql://user:pass@localhost:5432/testdb")
        
        result = tool.get_all_tables()
        
        # Check that the correct SQL was executed
        assert mock_cursor.execute.call_count == 1
        assert "information_schema.tables" in mock_cursor.execute.call_args[0][0]
        assert "table_schema = 'public'" in mock_cursor.execute.call_args[0][0]
        
        # Check the result
        assert len(result) == 3
        assert "table1" in result
        assert "table2" in result
        assert "table3" in result
