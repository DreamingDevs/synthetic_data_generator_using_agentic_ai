import os
from crewai import Process, Task, Crew
from dotenv import load_dotenv

from agents import (
    GetSqlSchemaAnalysisAgent,
    GetSqlDataAnalysisAgent
)

load_dotenv()

# ============================================================================
# AGENT
# ============================================================================

sql_schema_analysis_agent = GetSqlSchemaAnalysisAgent()
sql_data_analysis_agent = GetSqlDataAnalysisAgent()

# ============================================================================
# Tasks
# ============================================================================

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
    agent=sql_data_analysis_agent,
    context=[sql_schema_analysis_task]
)

# ============================================================================
# CREW WORKFLOW: SQL Schema Analysis → Data Distribution Analysis
# ============================================================================

# Create a crew that processes SQL agent output through data analysis agent
crew = Crew(
    agents=[sql_schema_analysis_agent, sql_data_analysis_agent],
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
print(f"Data Analysis Agent Tools: {[tool.name for tool in sql_data_analysis_agent.tools]}")
print("\n🔧 DEBUG: Task Assignments:")
print(f"SQL Task Agent: {sql_schema_analysis_task.agent.role}")
print(f"Data Analysis Task Agent: {data_analysis_task.agent.role}")
print("=" * 80)

# Execute the workflow
crew_output = crew.kickoff()

print("=" * 80)
print("🚀 CREW WORKFLOW COMPLETED")
print("=" * 80)
