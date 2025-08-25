import os
from dotenv import load_dotenv
from crewai import Agent
from tools import (
    GetSchemaInfoTool,
    GetForeignKeysTool
)

load_dotenv()

def GetSqlSchemaAnalysisAgent():
    return Agent(
        role="Systematic Database Analyst",
        goal=(
            "You are an expert database analyst who ALWAYS follows a systematic approach which is defined below: "
            "1) FIRST: You use GetSchemaInfoTool to fetch complete table schemas and column information. "
            "2) SECOND: You use GetForeignKeysTool to fetch all foreign key relationships. "
            "3) THIRD: You strictly follow below structure to combine both results into a data model in a single root-level deterministic JSON object as shown below. "
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
            "If there is an error in the sequence, you return the error and stop the process."
        ),
        backstory=(
            "YOUR ROLE: You are a highly systematic and predictable database analyst. "
            "YOUR STYLE: Your methodology is strict: always analyze schema, then foreign keys, then combine into JSON. "
            "YOUR RULES: You NEVER invent or assume data. You execute steps in this exact order. "
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