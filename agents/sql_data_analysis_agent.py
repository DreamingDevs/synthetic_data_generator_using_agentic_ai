import os
from dotenv import load_dotenv
from crewai import Agent
from tools import AnalyzeActualDataDistributionTool

load_dotenv()

def GetSqlDataAnalysisAgent():
    return Agent(
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
            "top_p": 0.05,  # Very low top_p for highly focused, predictable responses
            "frequency_penalty": 0.0,  # No frequency penalty for consistent terminology
            "presence_penalty": 0.0,  # No presence penalty for consistent structure
        },
    )
