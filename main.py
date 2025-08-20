import os
import pyodbc
from typing import Any, Dict, List
from crewai import Agent, Task, Crew
from crewai.tools import tool
from pydantic import BaseModel
from dotenv import load_dotenv
from config import Config

load_dotenv()

@tool("Fetch SQL Database Schema tool")
def GetSchemaInfoTool() -> Dict[str, List[Dict[str, Any]]]:
    """
    Connects to SQL Server and returns a structured schema
    (tables with columns and datatypes).
    """
    conn = pyodbc.connect(Config.get_connection_string())
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
            "datatype": dtype,
            "nullable": nullable
        })
    return result

@tool("Fetch SQL Database Foreign Keys tool")
def GetForeignKeysTool() -> List[Dict[str, str]]:
    """
    Connects to SQL Server and returns all foreign keys
    (parent_table.column -> referenced_table.column).
    """
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


# Agent with both tools
sql_agent = Agent(
    role="Database Evaluator",
    goal=(
        "When asked for a data model, "
        "You should use the provided tools to first fetch schema, "
        "then fetch foreign keys, and combine them into one final result. "
        "Never invent tools or fabricate data. Do not use any tools apart from what are provided to you."
    ),
    backstory=(
        "You are an expert database assistant. You know how to break down "
        "a complex request into smaller steps using available tools."
    ),
    verbose=True,
    tools=[GetSchemaInfoTool, GetForeignKeysTool],
    llm=f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT', 'o4-mini')}",
    llm_params={
        "api_key": os.getenv("AZURE_API_KEY"),
        "api_base": os.getenv("AZURE_API_BASE"),
        "api_version": os.getenv("AZURE_API_VERSION")
    }
)

# High-level task (LLM decides how to execute)
sql_task = Task(
    description=(
        "The user may ask for a data model of the database. "
        "To build it, you must:\n"
        "1. Run the schema tool to get tables and columns.\n"
        "2. Run the foreign keys tool to get relationships.\n"
        "3. Merge both results into a JSON object with two keys: 'schema' and 'foreign_keys'.\n"
        "Return only this JSON."
    ),
    expected_output=(
        "JSON object with the following structure:\n"
        "{\n"
        "  'schema': { '<schema>.<table>': [ { 'column': str, 'datatype': str, 'nullable': str } ] },\n"
        "  'foreign_keys': [ { 'constraint_name': str, 'parent_table': str, 'parent_column': str, 'referenced_table': str, 'referenced_column': str } ]\n"
        "}"
    ),
    agent=sql_agent
)


# Crew with planning enabled
crew = Crew(
    agents=[sql_agent],
    tasks=[sql_task],
    verbose=True,
    planning=True,  # 🔑 lets the LLM figure out sequence,
    planning_llm="azure/o4-mini",   # 🔑 use your Azure model instead of OpenAI’s default
    planning_llm_params={
        "api_key": os.getenv("AZURE_API_KEY"),
        "api_base": os.getenv("AZURE_API_BASE"),
        "api_version": os.getenv("AZURE_API_VERSION")
    }
)

crew_output = crew.kickoff()

print("Final Output:", crew_output.raw)
