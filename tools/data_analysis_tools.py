"""
Data Analysis Tools
Tools for analyzing database data distribution and patterns.
"""

import datetime
from typing import Dict, Any
from crewai.tools import tool
import json
import pyodbc
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

@tool("Analyze Table Row Counts")
def AnalyzeActualDataDistributionTool(schema_data: str) -> Dict[str, Any]:
    """
    Analyzes ACTUAL data distribution by querying the database for real row counts of all tables.
    
    IMPORTANT: This tool MUST be used to get actual row counts from the database.
    It queries the actual database to count rows for each table, providing real data volume
    information that is critical for understanding database size and capacity.
    
    Args:
        schema_data: JSON string containing the database schema information
        
    Returns:
        A dictionary containing table row count analysis including:
        - table_row_counts: Actual row counts for each table
        - total_tables_analyzed: Number of tables analyzed
        - analysis_timestamp: When the analysis was performed
    """
    try:
        # Parse the schema data
        data = json.loads(schema_data) if isinstance(schema_data, str) else schema_data
        
        conn = None
        cursor = None
        
        try:
            conn = pyodbc.connect(Config.get_connection_string())
            cursor = conn.cursor()
            
            table_row_counts = {}
            for table_info in data.get("tables", []):
                table_name = table_info.get("table_name")
                if table_name:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        row_count = cursor.fetchone()[0]
                        table_row_counts[table_name] = row_count
                        table_info["row_count"] = row_count  # <-- enrich table entry
                    except Exception as e:
                        table_row_counts[table_name] = f"Error: {str(e)}"
                        table_info["row_count"] = None

            # Add metadata
            data["analysis_metadata"] = {
                "total_tables": len(table_row_counts),
                "analysis_timestamp": datetime.datetime.now().isoformat()
            }

            return data 
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
                
    except Exception as e:
        return {"error": f"Failed to analyze table row counts: {str(e)}"}

