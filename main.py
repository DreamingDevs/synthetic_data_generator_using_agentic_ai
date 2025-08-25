from crewai import Process, Task, Crew
from dotenv import load_dotenv

from agents import GetSqlSchemaAnalysisAgent, GetSqlDataAnalysisAgent

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
        "TASK FOR: Systematic Database Analyst Agent ONLY. "
        "TASK: Analyze the database structure and provide a comprehensive data model. "
    ),
    expected_output=(
        "A comprehensive JSON object showing the database structure, including tables, columns, data types, and relationships between tables. "
        "The JSON output must be factual, well-structured, valid parsable JSON, and easy to understand for database professionals. "
    ),
    agent=sql_schema_analysis_agent
)


data_analysis_task = Task(
    description=(
        "TASK FOR: Expert Data Analyst Agent ONLY. "
        "TASK: Analyze the database schema data provided by the Systematic Database Analyst Agent and perform comprehensive data distribution analysis. The analysis should have actual data distribution by querying the database for real row counts. "
    ),
    expected_output=(
        "A comprehensive JSON object containing actual data distribution analysis, including actual row counts for all tables, total tables analyzed, and analysis timestamp. "
        "The JSON output should be factual, well-structured, valid parsable JSON, and easy to understand for database professionals. "
    ),
    agent=sql_data_analysis_agent,
    context=[sql_schema_analysis_task]
)

# Create a crew that processes SQL agent output through data analysis agent
crew = Crew(
    agents=[sql_schema_analysis_agent, sql_data_analysis_agent],
    tasks=[sql_schema_analysis_task, data_analysis_task],
    process=Process.sequential,
    verbose=True
)

# Execute the workflow
crew_output = crew.kickoff()

print("=" * 80)
print(crew_output.raw)
print("=" * 80)

print("=" * 80)
print("🚀 CREW WORKFLOW COMPLETED")
print("=" * 80)
