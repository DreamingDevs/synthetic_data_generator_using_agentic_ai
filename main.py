import os
import pyodbc
from typing import Any, Dict, List, Optional
from crewai import Agent, Task, Crew
from crewai.tools import tool
from pydantic import BaseModel
from dotenv import load_dotenv
from config import Config

# Import tools from the organized tools folder
from tools import (
    GetSchemaInfoTool,
    GetForeignKeysTool,
    AnalyzeSchemaPatternsTool,
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
        "3) THIRD: Combine both results into a comprehensive data model. "
        "4) FOURTH: Present results in a structured, organized JSONformat. "
        "4) FIFTH: Save the JSON output to a file called 'database_schema_analysis.json' "
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

sql_schema_analysis_task = Task(
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
    agent=sql_schema_analysis_agent
)

# ============================================================================
# DATA DISTRIBUTION ANALYSIS AGENT
# ============================================================================

data_analysis_agent = Agent(
    role="Comprehensive Data Distribution Analyzer",
    goal=(
        "You are a factual data analyst who ALWAYS follows this exact systematic approach: "
        "1) FIRST: Use the database_schema_analysis.json file to analyze the database schema. "
        "2) SECOND: Use AnalyzeSchemaPatternsTool to analyze schema metadata patterns. "
        "3) THIRD: Use AnalyzeActualDataDistributionTool to query database for real data distribution. "
        "4) FOURTH: Return ONLY the JSON documentation with no additional text. "
        "5) FIFTH: Save the JSON output to a file called 'database_data_distribution_analysis.json' "
        "You NEVER invent data. You NEVER add opinions. You NEVER deviate from facts. "
        "You ONLY work with the actual data provided and documented analysis results. "
        "You ALWAYS analyze both schema patterns AND actual data distribution for complete insights."
    ),
    backstory=(
        "You are a highly factual and deterministic data analyst specializing in comprehensive database analysis. "
        "You have a proven methodology that combines schema analysis with actual data distribution analysis: "
        "always start with schema patterns, then query the actual database for real data distribution, "
        "then combine both analyses into comprehensive documentation. "
        "You are not creative - you are methodical and factual. "
        "You never speculate, never add opinions, and never deviate from the actual data. "
        "Your analysis always includes both structural patterns and real data characteristics. "
        "When given database schema data, you immediately apply your proven 5-step comprehensive method."
    ),
    verbose=True,
    tools=[AnalyzeSchemaPatternsTool, AnalyzeActualDataDistributionTool],
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
        "This includes both schema pattern analysis AND actual data distribution analysis by querying the database. "
        "Generate json output that captures schema patterns, actual row counts,"
        "foreign key cardinality, data distribution patterns, relationship health, and performance indicators. "
        "Focus on factual analysis based on real database queries and actual data."
    ),
    expected_output=(
        "A comprehensive JSON document containing both schema analysis and actual data distribution analysis, including "
        "data type patterns, relationship analysis, table complexity, actual row counts, foreign key cardinality, "
        "data distribution patterns, relationship health, performance indicators, and critical insights. "
        "The output should be factual and based on both schema metadata and actual database queries."
    ),
    agent=data_analysis_agent
)


# ============================================================================
# CREW WORKFLOW: SQL Schema Analysis → Data Distribution Analysis
# ============================================================================

# Create a crew that processes SQL agent output through data analysis agent
crew = Crew(
    agents=[sql_schema_analysis_agent, data_analysis_agent],
    tasks=[sql_schema_analysis_task, data_analysis_task],
    verbose=True,
    planning=True,  # 🔑 lets the LLM figure out sequence,
    planning_llm="azure/o4-mini",   # 🔑 use your Azure model instead of OpenAI’s default
    planning_llm_params={
        "api_key": os.getenv("AZURE_API_KEY"),
        "api_base": os.getenv("AZURE_API_BASE"),
        "api_version": os.getenv("AZURE_API_VERSION")
    }
)

# Execute the workflow
crew_output = crew.kickoff()

print("=" * 80)
print("🚀 CREW WORKFLOW COMPLETED")
print("=" * 80)
