import os
import pyodbc
from typing import Any, Dict, List, Optional
from crewai import Agent, Task, Crew
from crewai.tools import tool
from pydantic import BaseModel
from dotenv import load_dotenv
from config import Config

load_dotenv()

@tool("Get Database Schema")
def GetSchemaInfoTool() -> Dict[str, List[Dict[str, Any]]]:
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

        result: Dict[str, List[Dict[str, Any]]] = {}
        for schema, table, col, dtype, nullable in rows:
            key = f"{schema}.{table}"
            result.setdefault(key, []).append({
                "column": col,
                "datatype": dtype,
                "nullable": nullable
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


# Agent with both tools - Deterministic by design
sql_agent = Agent(
    role="Systematic Database Analyzer",
    goal=(
        "You are a methodical database analyst who ALWAYS follows this exact systematic approach: "
        "1) FIRST: Use GetSchemaInfoTool to fetch complete table schemas and column information. "
        "2) SECOND: Use GetForeignKeysTool to fetch all foreign key relationships. "
        "3) THIRD: Combine both results into a comprehensive data model. "
        "4) FOURTH: Present results in a structured, organized format. "
        "You NEVER deviate from this sequence. You NEVER skip steps. You NEVER invent data. "
        "You ONLY use the provided tools in the exact order specified."
    ),
    backstory=(
        "You are a highly systematic and predictable database analyst. "
        "You have developed a proven methodology that you follow religiously: "
        "always start with schema analysis, then examine relationships, then combine results. "
        "This systematic approach has never failed you, so you stick to it rigidly. "
        "You are not creative in your approach - you are methodical and consistent. "
        "When given any database analysis task, you immediately apply your proven 4-step method."
    ),
    verbose=True,
    tools=[GetSchemaInfoTool, GetForeignKeysTool],
    llm=f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT', 'o4-mini')}",
    llm_params={
        "api_key": os.getenv("AZURE_API_KEY"),
        "api_base": os.getenv("AZURE_API_BASE"),
        "api_version": os.getenv("AZURE_API_VERSION"),
        "temperature": 0.0,  # Zero temperature for maximum determinism
        "max_tokens": 2000,  # Control output length for consistency
        "top_p": 0.1,        # Low top_p for focused, predictable responses
        "frequency_penalty": 0.0,  # No frequency penalty for consistent terminology
        "presence_penalty": 0.0    # No presence penalty for consistent structure
    }
)

# Generic task - Agent determines the approach
sql_task = Task(
    description=(
        "Analyze the database structure and provide a comprehensive data model. "
        "Present the information in a clear, organized format that would be useful for "
        "database analysis, documentation, or understanding the data relationships."
    ),
    expected_output=(
        "A comprehensive data model showing the database structure, including tables, columns, "
        "data types, and relationships between tables. The information should be well-organized "
        "and easy to understand for database professionals."
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
