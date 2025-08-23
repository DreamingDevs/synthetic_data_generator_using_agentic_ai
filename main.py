import os
import pyodbc
from typing import Any, Dict, List, Optional
from crewai import Agent, Process, Task, Crew
from crewai.tools import tool
from pydantic import BaseModel
from dotenv import load_dotenv
from config import Config

# Import tools from the organized tools folder
from tools import (
    GetSchemaInfoTool,
    GetForeignKeysTool,
    AnalyzeActualDataDistributionTool
)

load_dotenv()

# ============================================================================
# SCHEMA ANALYSIS AGENT
# ============================================================================

sql_schema_analysis_agent = Agent(
    role="Systematic Database Analyzer",
    goal=(
        "You are a methodical database analyst who ALWAYS follows this exact systematic approach: "
        "1) FIRST: Use GetSchemaInfoTool to fetch complete table schemas and column information. "
        "2) SECOND: Use GetForeignKeysTool to fetch all foreign key relationships. "
        "3) THIRD: Combine both results into a data model in a single root-level deterministic JSON object as shown below. "
        "The format MUST strictly follow this structure:\n\n"
        "{\n"
        '  "database_name": "string",\n'
        '  "tables": [\n'
        "    {\n"
        '      "table_name": "string",\n'
        '      "columns": [\n'
        "        {\n"
        '          "column_name": "string",\n'
        '          "data_type": "string",\n'
        '          "is_nullable": true\n'
        "        }\n"
        "      ]\n"
        "    }\n"
        "  ],\n"
        '  "foreign_keys": [\n'
        "    {\n"
        '      "fk_name": "string",\n'
        '      "source_table": "string",\n'
        '      "source_column": "string",\n'
        '      "target_table": "string",\n'
        '      "target_column": "string"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "You NEVER deviate from this sequence. You NEVER skip steps. You NEVER invent or assume data. "
    ),
    backstory=(
        "You are a highly systematic and predictable database analyst. "
        "Your methodology is strict: always analyze schema, then foreign keys, then combine into JSON. "
        "You do not improvise — you execute steps in this exact order."
    ),
    verbose=True,
    tools=[GetSchemaInfoTool, GetForeignKeysTool],
    llm=f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT', 'o4-mini')}",
    llm_params={
        "api_key": os.getenv("AZURE_API_KEY"),
        "api_base": os.getenv("AZURE_API_BASE"),
        "api_version": os.getenv("AZURE_API_VERSION"),
        "temperature": 0.0,
        "max_tokens": 2000,
        "top_p": 0.1,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }
)

sql_schema_analysis_task = Task(
    description=(
        "TASK FOR: Systematic Database Analyzer Agent ONLY. "
        "Analyze the database structure and provide a comprehensive data model. "
        "IMPORTANT: You MUST use BOTH tools in this exact order: "
        "1) GetSchemaInfoTool, 2) GetForeignKeysTool. "
        "After fetching results, combine them into a single structured deterministic JSON output. "
        "Do not add any freeform commentary — return only the JSON."
    ),
    expected_output=(
        "A comprehensive JSON object showing the database structure, including tables, columns, "
        "data types, and relationships between tables. "
        "The JSON must be well-organized, valid parsable JSON, and easy to understand for database professionals."
    ),
    agent=sql_schema_analysis_agent
)


# ============================================================================
# DATA DISTRIBUTION ANALYSIS AGENT
# ============================================================================

data_analysis_agent = Agent(
    role="Comprehensive Data Distribution Analyzer",
    goal=(
        "You are a factual data analyst who ALWAYS follows this exact systematic approach: "
        "1) FIRST: Use the json output from the SQL agent to analyze the database schema. "
        "2) SECOND: Use AnalyzeActualDataDistributionTool to query database for real data distribution. "
        "3) THIRD: Return ONLY the JSON documentation with no additional text. You must NOT repeat or restate the schema JSON — only extend it with distribution data as shown below."
        "The enriched JSON format MUST strictly follow this structure:\n\n"
        "{\n"
        '  "database_name": "string",\n'
        '  "tables": [\n'
        "    {\n"
        '      "table_name": "string",\n'
        '      "row_count": number,\n'
        '      "columns": [\n'
        "        {\n"
        '          "column_name": "string",\n'
        '          "data_type": "string",\n'
        '          "is_nullable": true\n'
        "        }\n"
        "      ]\n"
        "    }\n"
        "  ],\n"
        '  "foreign_keys": [\n'
        "    {\n"
        '      "fk_name": "string",\n'
        '      "source_table": "string",\n'
        '      "source_column": "string",\n'
        '      "target_table": "string",\n'
        '      "target_column": "string"\n'
        "    }\n"
        "  ],\n"
        '  "analysis_metadata": {\n'
        '    "total_tables": number,\n'
        '    "analysis_timestamp": "ISO8601 string"\n'
        "  }\n"
        "}\n\n"
        "You NEVER invent data. You NEVER add opinions. You NEVER deviate from facts. "
        "You MUST call ALL tools in the exact order specified."
    ),
    backstory=(
        "You are a highly factual and deterministic data analyst specializing in comprehensive database analysis. "
        "You have a proven methodology that focuses on actual data distribution analysis: "
        "always start by understanding the schema data which was given to you, then query the actual database for real data distribution, "
        "then return JSON documentation. You must NOT repeat or restate the schema JSON — only extend it with distribution data by adding `row_count` for each table."
        "You are not creative - you are methodical and factual. "
        "You never speculate, never add opinions, and never deviate from the actual data. "
        "Your analysis always includes real data characteristics. "
        "When given database schema data, you immediately apply your proven 3-step comprehensive method."
    ),
    verbose=True,
    tools=[AnalyzeActualDataDistributionTool],
    llm=f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT', 'o4-mini')}",
    llm_params={
        "api_key": os.getenv("AZURE_API_KEY"),
        "api_base": os.getenv("AZURE_API_BASE"),
        "api_version": os.getenv("AZURE_API_VERSION"),
        "temperature": 0.0,  # Zero temperature for maximum determinism
        "max_tokens": 4000,  # Control output length for consistency
        "top_p": 0.05,       # Very low top_p for highly focused, predictable responses
        "frequency_penalty": 0.0,  # No frequency penalty for consistent terminology
        "presence_penalty": 0.0    # No presence penalty for consistent structure
    }
)

# Enhanced Data Analysis Task - Generic but agent is deterministic
data_analysis_task = Task(
    description=(
        "Analyze the database schema data provided by the SQL agent and perform comprehensive data distribution analysis. "
        "This includes actual data distribution analysis by querying the database for real row counts. "
        "then return JSON documentation. You must NOT repeat or restate the schema JSON — only extend it with distribution data by adding `row_count` for each table."
        "Focus on factual analysis based on real database queries and actual data. "
        "IMPORTANT: You MUST use ALL below tools in this exact order: "
        "1) AnalyzeActualDataDistributionTool "
        "CRITICAL: You cannot complete this task without calling ALL tools. "
    ),
    expected_output=(
        "A comprehensive JSON containing actual data distribution analysis, including "
        "actual row counts for all tables, total tables analyzed, and analysis timestamp. "
        "The output should be factual, well-structured, and easy to understand for database professionals. "
    ),
    agent=data_analysis_agent
    # Removed context dependency to avoid planning conflicts
)


# ============================================================================
# CREW WORKFLOW: SQL Schema Analysis → Data Distribution Analysis
# ============================================================================

# Create a crew that processes SQL agent output through data analysis agent
crew = Crew(
    agents=[sql_schema_analysis_agent, data_analysis_agent],
    tasks=[sql_schema_analysis_task, data_analysis_task],
    process=Process.sequential,
    verbose=True,
    planning=False,  # 🔑 Disable planning to prevent agent reassignment
    planning_llm="azure/o4-mini",   # 🔑 use your Azure model instead of OpenAI’s default
    planning_llm_params={
        "api_key": os.getenv("AZURE_API_KEY"),
        "api_base": os.getenv("AZURE_API_BASE"),
        "api_version": os.getenv("AZURE_API_VERSION")
    }
)

# Debug: Print agent tools and task assignments
print("\n🔧 DEBUG: Agent Tools Available:")
print(f"SQL Agent Tools: {[tool.name for tool in sql_schema_analysis_agent.tools]}")
print(f"Data Analysis Agent Tools: {[tool.name for tool in data_analysis_agent.tools]}")
print("\n🔧 DEBUG: Task Assignments:")
print(f"SQL Task Agent: {sql_schema_analysis_task.agent.role}")
print(f"Data Analysis Task Agent: {data_analysis_task.agent.role}")
print("=" * 80)

# Execute the workflow
crew_output = crew.kickoff()

print("=" * 80)
print("🚀 CREW WORKFLOW COMPLETED")
print("=" * 80)
