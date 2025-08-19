# tools/analysis_tools.py
from typing import List, Dict, Optional
from pydantic import BaseModel
from crewai.tools import BaseTool
from .connection_manager import ConnectionManager


# ---------- Pydantic Models for Structured Outputs ----------
class TableRowCount(BaseModel):
    table: str
    rows: int


class FKParentRef(BaseModel):
    schema_name: str
    table: str
    column: str


class FKDistributionEntry(BaseModel):
    ref_value: Optional[str]
    count: int


class FKDistribution(BaseModel):
    fk_name: str
    parent: FKParentRef
    referenced: FKParentRef
    top: List[FKDistributionEntry]


# ---------- Tool Implementations ----------
class GetRowCountsTool(BaseTool):
    name: str = "Get Table Row Counts"
    description: str = "Return row counts for all base tables (clustered/heap partitions)."

    def _run(self) -> List[TableRowCount]:
        conn = ConnectionManager.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.name AS SchemaName, t.name AS TableName, SUM(p.rows) AS RowCounts
            FROM sys.tables t
            JOIN sys.schemas s ON s.schema_id = t.schema_id
            JOIN sys.partitions p ON t.object_id = p.object_id
            WHERE p.index_id IN (0,1)
            GROUP BY s.name, t.name
            ORDER BY RowCounts DESC, s.name, t.name
        """)
        rows = cursor.fetchall()
        return [TableRowCount(table=f"{r[0]}.{r[1]}", rows=int(r[2])) for r in rows]


class GetFKDistributionsTool(BaseTool):
    name: str = "Get Foreign Key Distributions"
    description: str = (
        "For each foreign key, compute how many parent rows reference each referenced key value. "
        "Returns a dict keyed by 'parent_schema.parent_table -> ref_schema.ref_table'."
    )

    def _run(self, top_n_per_relationship: int = 50, include_zeroes: bool = True) -> Dict[str, FKDistribution]:
        conn = ConnectionManager.get_connection()
        cursor = conn.cursor()

        # Discover foreign keys
        cursor.execute("""
            SELECT
                fk.name AS FK_Name,
                s1.name AS ParentSchema,
                tp.name AS ParentTable,
                cp.name AS ParentColumn,
                s2.name AS RefSchema,
                tr.name AS RefTable,
                cr.name AS RefColumn
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
        fks = cursor.fetchall()

        distributions: Dict[str, FKDistribution] = {}

        for (fk_name, p_schema, p_table, p_col, r_schema, r_table, r_col) in fks:
            rel_key = f"{p_schema}.{p_table}->{r_schema}.{r_table}"

            base_query = f"""
                SELECT ref.[{r_col}] AS RefValue, COUNT(parent.[{p_col}]) AS RefCount
                FROM [{r_schema}].[{r_table}] AS ref
                LEFT JOIN [{p_schema}].[{p_table}] AS parent
                  ON ref.[{r_col}] = parent.[{p_col}]
                GROUP BY ref.[{r_col}]
                ORDER BY RefCount DESC
            """
            final_query = base_query
            if top_n_per_relationship and int(top_n_per_relationship) > 0:
                final_query += f" OFFSET 0 ROWS FETCH NEXT {int(top_n_per_relationship)} ROWS ONLY"

            cursor.execute(final_query)
            rows = cursor.fetchall()
            vals = [FKDistributionEntry(ref_value=r[0], count=int(r[1])) for r in rows]

            if not include_zeroes:
                vals = [v for v in vals if v.count > 0]

            distributions[rel_key] = FKDistribution(
                fk_name=fk_name,
                parent=FKParentRef(schema_name=p_schema, table=p_table, column=p_col),
                referenced=FKParentRef(schema_name=r_schema, table=r_table, column=r_col),
                top=vals
            )

        return distributions