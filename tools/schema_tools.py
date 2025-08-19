from crewai.tools import BaseTool
from .connection_manager import ConnectionManager
from typing import Dict, List, Any

class GetSchemaInfoTool(BaseTool):
    name: str = "Get Database Schema"
    description: str = "Return all tables and columns with data types from INFORMATION_SCHEMA."

    def _run(self) -> Dict[str, List[Dict[str, Any]]]:
        conn = ConnectionManager.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
        """)
        rows = cursor.fetchall()
        result: Dict[str, List[Dict[str, Any]]] = {}
        for schema, table, col, dtype, nullable in rows:
            key = f"{schema}.{table}"
            result.setdefault(key, []).append({
                "column": col,
                "type": dtype,
                "nullable": (nullable == "YES")
            })
        return result


class GetForeignKeysTool(BaseTool):
    name: str = "Get Foreign Keys"
    description: str = "Return all foreign keys (parent_table/column -> referenced_table/column)."

    def _run(self) -> List[Dict[str, str]]:
        conn = ConnectionManager.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                fk.name AS FK_Name,
                tp.name AS ParentTable,
                cp.name AS ParentColumn,
                tr.name AS ReferencedTable,
                cr.name AS ReferencedColumn,
                s1.name AS ParentSchema,
                s2.name AS RefSchema
            FROM sys.foreign_keys AS fk
            INNER JOIN sys.foreign_key_columns AS fkc
                ON fk.object_id = fkc.constraint_object_id
            INNER JOIN sys.tables AS tp
                ON fkc.parent_object_id = tp.object_id
            INNER JOIN sys.schemas AS s1
                ON tp.schema_id = s1.schema_id
            INNER JOIN sys.columns AS cp
                ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
            INNER JOIN sys.tables AS tr
                ON fkc.referenced_object_id = tr.object_id
            INNER JOIN sys.schemas AS s2
                ON tr.schema_id = s2.schema_id
            INNER JOIN sys.columns AS cr
                ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
            ORDER BY s1.name, tp.name
        """)
        rows = cursor.fetchall()
        fks: List[Dict[str, str]] = []
        for (fk_name, p_table, p_col, r_table, r_col, p_schema, r_schema) in rows:
            fks.append({
                "fk_name": fk_name,
                "parent_schema": p_schema,
                "parent_table": p_table,
                "parent_column": p_col,
                "referenced_schema": r_schema,
                "referenced_table": r_table,
                "referenced_column": r_col
            })
        return fks
