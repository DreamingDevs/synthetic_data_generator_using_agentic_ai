"""
Database Schema Tools
Tools for connecting to and analyzing database schema information.
"""

import os
import pyodbc
from typing import Any, Dict, List
from crewai.tools import tool
from dotenv import load_dotenv
from config import Config

load_dotenv()

@tool("Get Database Schema")
def GetSchemaInfoTool() -> Dict[str, Any]:
    """
    Fetches the complete database schema including all tables, columns, and their data types.
    
    IMPORTANT: This tool MUST be used FIRST in any database analysis workflow.
    It provides the foundational table structure information that other tools depend on.
    
    Returns:
        A dictionary where keys are table names (format: 'schema.table') and values are lists of column information.
        Each column has: column name, data type, and nullable status.
        
    Usage: ALWAYS call this tool first to establish the database structure foundation.
    """
    conn = None
    cursor = None
    try:
        conn = pyodbc.connect(Config.get_connection_string())
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
        """)
        rows = cursor.fetchall()

        result: Dict[str, Any] = {
            "database_name": Config.DB_NAME,
            "tables": []
        }

        table_map: Dict[str, List[Dict[str, Any]]] = {}
        for schema, table, col, dtype, nullable in rows:
            key = f"{schema}.{table}"
            table_map.setdefault(key, []).append({
                "column_name": col,
                "data_type": dtype,
                "is_nullable": (nullable.upper() == "YES")
            })

        # Convert to list structure
        for table_name, columns in table_map.items():
            result["tables"].append({
                "table_name": table_name,
                "columns": columns
            })
        return result
    except Exception as e:
        return {"error": f"Failed to fetch schema: {str(e)}"}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@tool("Get Database Foreign Keys")
def GetForeignKeysTool() -> List[Dict[str, str]]:
    """
    Fetches all foreign key relationships in the database.
    
    IMPORTANT: This tool MUST be used SECOND in any database analysis workflow.
    It requires the schema information from GetSchemaInfoTool to be meaningful.
    
    Returns:
        A list of foreign key relationships, each containing:
        - constraint_name: Name of the foreign key constraint
        - parent_table: Table containing the foreign key
        - parent_column: Column containing the foreign key
        - referenced_table: Table being referenced
        - referenced_column: Column being referenced
        
    Usage: ALWAYS call this tool second, after GetSchemaInfoTool, to understand table relationships.
    """
    conn = None
    cursor = None
    try:
        conn = pyodbc.connect(Config.get_connection_string())
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                fk.name AS constraint_name,
                tp.name AS parent_table,
                cp.name AS parent_column,
                tr.name AS referenced_table,
                cr.name AS referenced_column
            FROM sys.foreign_keys fk
            INNER JOIN sys.foreign_key_columns fkc 
                ON fk.object_id = fkc.constraint_object_id
            INNER JOIN sys.tables tp 
                ON fkc.parent_object_id = tp.object_id
            INNER JOIN sys.columns cp 
                ON fkc.parent_object_id = cp.object_id 
               AND fkc.parent_column_id = cp.column_id
            INNER JOIN sys.tables tr 
                ON fkc.referenced_object_id = tr.object_id
            INNER JOIN sys.columns cr 
                ON fkc.referenced_object_id = cr.object_id 
               AND fkc.referenced_column_id = cr.column_id
            ORDER BY tp.name, fk.name
        """)

        rows = cursor.fetchall()

        foreign_keys: List[Dict[str, str]] = [
            {
                "constraint_name": row.constraint_name,
                "parent_table": row.parent_table,
                "parent_column": row.parent_column,
                "referenced_table": row.referenced_table,
                "referenced_column": row.referenced_column
            }
            for row in rows
        ]

        return foreign_keys
    except Exception as e:
        return [{"error": f"Failed to fetch foreign keys: {str(e)}"}]
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
