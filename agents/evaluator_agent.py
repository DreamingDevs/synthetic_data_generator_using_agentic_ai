# agents/evaluator_agent.py
from crewai import Agent
from tools.db_connection_tool import DBConnectionTool
from tools.schema_tools import GetSchemaInfoTool, GetForeignKeysTool
from tools.analysis_tools import GetRowCountsTool, GetFKDistributionsTool
from tools.yaml_tools import SaveYAMLTool
import os

def create_evaluator_agent():
    """
    Autonomous Evaluator that plans its own analysis and uses tools.
    Prompt guides it to:
      1) connect,
      2) inspect schema & row counts,
      3) inspect FKs & distributions,
      4) save YAML.
    """
    return Agent(
        name="Evaluator",
        role="Autonomous Database Evaluator",
        goal=(
            "Thoroughly analyze the connected SQL Server database in order to generate a "
            "single authoritative YAML file (`schema_analysis.yaml`). The report must include: "
            "1) all schemas, tables, and columns with datatypes and nullability; "
            "2) row counts for each table; "
            "3) foreign key relationships (parent and referenced tables/columns); "
            "4) distribution of values for foreign keys, showing the most common keys. "
            "The YAML must be accurate, structured, and ready to be consumed by downstream "
            "agents for synthetic data generation and validation."
        ),
        backstory=(
            "You are a senior database auditor and metadata analyst tasked with preparing a precise "
            "profile of an unknown SQL Server database. Your job is not to make guesses but to rely "
            "on the available tools to query live metadata. You think step-by-step, confirm each stage "
            "of the analysis, and only include verified details in the report. You understand that your "
            "analysis will guide downstream Optimizer and Validator agents in generating realistic test "
            "data, so accuracy and clarity are essential. Document results in YAML with logical structure, "
            "using clear field names and consistent formatting so that automated pipelines can consume it. "
            "Err on the side of completeness—capture everything you can about schemas, row counts, and key "
            "distributions—while keeping the YAML human-readable."
        ),
        verbose=True,
        tools=[
            DBConnectionTool(),
            GetSchemaInfoTool(),
            GetRowCountsTool(),
            GetForeignKeysTool(),
            GetFKDistributionsTool(),
            SaveYAMLTool()
        ],
        llm="azure/o4-mini",
        llm_params={
            "model": os.getenv("AZURE_OPENAI_DEPLOYMENT")
        }
    )

