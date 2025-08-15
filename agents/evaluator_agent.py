# agents/evaluator_agent.py
from crewai import Agent
from tools.db_connection_tool import DBConnectionTool
from tools.schema_tools import GetSchemaInfoTool, GetForeignKeysTool
from tools.analysis_tools import GetRowCountsTool, GetFKDistributionsTool
from tools.yaml_tools import SaveYAMLTool

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
            "Understand an unknown SQL Server database and produce a comprehensive YAML report "
            "covering schema, row counts, foreign keys, and key FK distributions."
        ),
        backstory=(
            "A meticulous database auditor who reasons step-by-step, decides which tools to call, "
            "and documents findings clearly for downstream synthetic data generation."
        ),
        verbose=True,
        tools=[
            DBConnectionTool(),
            GetSchemaInfoTool(),
            GetRowCountsTool(),
            GetForeignKeysTool(),
            GetFKDistributionsTool(),
            SaveYAMLTool()
        ]
    )
