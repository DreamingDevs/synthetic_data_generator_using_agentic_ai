import os
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
    agent=sql_schema_analysis_agent,
)


data_analysis_task = Task(
    description=(
        "TASK FOR: Expert Data Analyst Agent ONLY. "
        "TASK: Analyze the database schema data provided by the Systematic Database Analyst Agent and perform comprehensive data distribution analysis. The analysis should have actual data distribution by querying the database for real row counts. "
    ),
    expected_output=(
        "A comprehensive JSON containing actual data distribution analysis, including actual row counts for all tables, total tables analyzed, and analysis timestamp. "
        "The JSON output should be factual, well-structured, valid parsable JSON, and easy to understand for database professionals. "
    ),
    agent=sql_data_analysis_agent,
    context=[sql_schema_analysis_task],
)

# ============================================================================
# CREW WORKFLOW: SQL Schema Analysis → Data Distribution Analysis
# ============================================================================

# import json
# import os
# from crewai.tools import tool


# @tool("Save JSON to File")
# def SaveJSONTool(schema_data: dict, file_path: str = "final_schema.json") -> dict:
#     """
#     Save structured JSON (schema + analysis results) to a file.

#     Args:
#         schema_data (dict): JSON object to save
#         file_path (str, optional): File path. Defaults to 'final_schema.json'.

#     Returns:
#         dict: Status and file path
#     """
#     try:
#         os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
#         with open(file_path, "w", encoding="utf-8") as f:
#             json.dump(schema_data, f, indent=4)

#         return {"status": "success", "file_path": file_path}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}


# from crewai import Agent

# save_json_agent = Agent(
#     role="JSON Persistence Agent",
#     goal=(
#         "You are a data persistance agent who ALWAYS follows this exact systematic approach: "
#         "1) FIRST: Use SaveJSONTool with `schema.json` for file_path parameter to save schema and analysis results into a JSON file for downstream use. "
#         "You NEVER invent data. You NEVER add opinions. You NEVER deviate from facts. "
#     ),
#     backstory=(
#         "You are responsible for persisting structured database metadata and analysis results. "
#         "You ensure JSON output is written correctly to disk without altering its structure."
#         "IMPORTANT: You MUST use ALL below tools in this exact order: "
#         "1) SaveJSONTool "
#         "You are not creative - you are methodical and factual. "
#         "You never speculate, never add opinions, and never deviate from the actual data. "
#         "You do not improvise — you execute steps in this exact order."
#     ),
#     tools=[SaveJSONTool],
#     verbose=True,
# )

# save_json_task = Task(
#     description=(
#         "Save the final JSON (schema + data distribution analysis) into a json file. "
#         "You must call SaveJSONTool with the combined JSON from previous tasks."
#     ),
#     expected_output="Confirmation of file saved with path.",
#     agent=save_json_agent,
#     context=[data_analysis_task],  # <- ensures it gets the enriched JSON
# )


# Create a crew that processes SQL agent output through data analysis agent
crew = Crew(
    agents=[sql_schema_analysis_agent, sql_data_analysis_agent],
    tasks=[sql_schema_analysis_task, data_analysis_task],
    process=Process.sequential,
    verbose=True,
)

# Execute the workflow
crew_output = crew.kickoff()

print("=" * 80)
print("🚀 CREW WORKFLOW COMPLETED")
print("=" * 80)
