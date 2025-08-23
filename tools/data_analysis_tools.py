"""
Data Analysis Tools
Tools for analyzing database schema patterns and actual data distribution.
"""

import os
import pyodbc
from typing import Any, Dict, List
from crewai.tools import tool
from dotenv import load_dotenv
from config import Config

load_dotenv()

@tool("Analyze Schema Patterns")
def AnalyzeSchemaPatternsTool(schema_data: str) -> Dict[str, Any]:
    """
    Analyzes database schema metadata to identify structural patterns and characteristics.
    
    IMPORTANT: This tool MUST be used to analyze the output from the SQL agent.
    It processes the schema information to identify patterns in data types, relationships,
    and structural characteristics that indicate data distribution patterns.
    
    Args:
        schema_data: JSON string containing the database schema and foreign key information
        
    Returns:
        A dictionary containing analyzed schema patterns including:
        - data_type_distribution: Count of each data type
        - relationship_patterns: Analysis of foreign key relationships
        - table_complexity: Analysis of table structures
        - data_volume_indicators: Patterns suggesting data volume characteristics
        - normalization_level: Assessment of database normalization
    """
    try:
        import json
        from collections import Counter
        
        # Parse the schema data
        data = json.loads(schema_data) if isinstance(schema_data, str) else schema_data
        
        # Analyze data type distribution
        data_types = []
        for table_name, columns in data.get('schema', {}).items():
            for column in columns:
                data_types.append(column.get('datatype', 'unknown'))
        
        data_type_distribution = dict(Counter(data_types))
        
        # Analyze relationship patterns
        foreign_keys = data.get('foreign_keys', [])
        relationship_patterns = {
            'total_relationships': len(foreign_keys),
            'referenced_tables': list(set(fk['referenced_table'] for fk in foreign_keys)),
            'parent_tables': list(set(fk['parent_table'] for fk in foreign_keys)),
            'relationship_types': {}
        }
        
        # Analyze table complexity
        table_complexity = {}
        for table_name, columns in data.get('schema', {}).items():
            table_complexity[table_name] = {
                'column_count': len(columns),
                'primary_key_candidates': [col['column'] for col in columns if col['column'].lower().endswith('id')],
                'nullable_columns': len([col for col in columns if col['nullable'] == 'YES']),
                'required_columns': len([col for col in columns if col['nullable'] == 'NO'])
            }
        
        # Analyze data volume indicators
        data_volume_indicators = {
            'high_volume_indicators': [],
            'low_volume_indicators': [],
            'moderate_volume_indicators': []
        }
        
        for table_name, columns in data.get('schema', {}).items():
            col_count = len(columns)
            if col_count > 10:
                data_volume_indicators['high_volume_indicators'].append(table_name)
            elif col_count < 5:
                data_volume_indicators['low_volume_indicators'].append(table_name)
            else:
                data_volume_indicators['moderate_volume_indicators'].append(table_name)
        
        # Assess normalization level
        normalization_level = "normalized"
        if len(foreign_keys) < len(data.get('schema', {})) * 0.3:
            normalization_level = "denormalized"
        elif len(foreign_keys) > len(data.get('schema', {})) * 0.7:
            normalization_level = "highly_normalized"
        
        return {
            "data_type_distribution": data_type_distribution,
            "relationship_patterns": relationship_patterns,
            "table_complexity": table_complexity,
            "data_volume_indicators": data_volume_indicators,
            "normalization_level": normalization_level,
            "analysis_timestamp": "2025-01-22T00:00:00Z"
        }
        
    except Exception as e:
        return {"error": f"Failed to analyze schema patterns: {str(e)}"}

@tool("Analyze Actual Data Distribution")
def AnalyzeActualDataDistributionTool(schema_data: str) -> Dict[str, Any]:
    """
    Analyzes ACTUAL data distribution patterns by querying the database for real row counts
    and distribution across foreign key relationships.
    
    IMPORTANT: This tool MUST be used to analyze real data distribution patterns.
    It queries the actual database to count rows, analyze foreign key cardinality,
    and identify real data distribution characteristics that are critical for understanding
    data volume and relationship patterns.
    
    Args:
        schema_data: JSON string containing the database schema and foreign key information
        
    Returns:
        A dictionary containing actual data distribution analysis including:
        - table_row_counts: Actual row counts for each table
        - foreign_key_cardinality: Analysis of relationship cardinality (1:1, 1:many, many:many)
        - data_distribution_patterns: Real patterns in data distribution
        - relationship_health: Analysis of referential integrity and data consistency
        - performance_indicators: Patterns suggesting performance characteristics
    """
    try:
        import json
        
        # Parse the schema data
        data = json.loads(schema_data) if isinstance(schema_data, str) else schema_data
        
        conn = None
        cursor = None
        
        try:
            conn = pyodbc.connect(Config.get_connection_string())
            cursor = conn.cursor()
            
            # Get actual row counts for all tables
            table_row_counts = {}
            for table_name in data.get('schema', {}).keys():
                # Extract just the table name (remove schema prefix)
                table_only = table_name.split('.')[-1] if '.' in table_name else table_name
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    table_row_counts[table_name] = row_count
                except Exception as e:
                    table_row_counts[table_name] = f"Error: {str(e)}"
            
            # Analyze foreign key cardinality and distribution
            foreign_key_cardinality = {}
            data_distribution_patterns = {}
            relationship_health = {}
            
            for fk in data.get('foreign_keys', []):
                parent_table = fk['parent_table']
                parent_column = fk['parent_column']
                referenced_table = fk['referenced_table']
                referenced_column = fk['referenced_column']
                
                # Get row counts for parent and referenced tables
                parent_count = table_row_counts.get(f"dbo.{parent_table}", 0)
                referenced_count = table_row_counts.get(f"dbo.{referenced_table}", 0)
                
                # Analyze cardinality
                if isinstance(parent_count, int) and isinstance(referenced_count, int):
                    if referenced_count == 0:
                        cardinality = "undefined"
                    elif parent_count == 0:
                        cardinality = "undefined"
                    elif referenced_count == 1 and parent_count == 1:
                        cardinality = "1:1"
                    elif referenced_count == 1 and parent_count > 1:
                        cardinality = "1:many"
                    elif referenced_count > 1 and parent_count == 1:
                        cardinality = "many:1"
                    else:
                        cardinality = "many:many"
                    
                    # Calculate distribution ratios
                    if referenced_count > 0:
                        distribution_ratio = parent_count / referenced_count
                    else:
                        distribution_ratio = 0
                    
                    foreign_key_cardinality[fk['constraint_name']] = {
                        'parent_table': parent_table,
                        'parent_column': parent_column,
                        'referenced_table': referenced_table,
                        'referenced_column': referenced_column,
                        'parent_row_count': parent_count,
                        'referenced_row_count': referenced_count,
                        'cardinality': cardinality,
                        'distribution_ratio': round(distribution_ratio, 2),
                        'relationship_type': 'normal' if distribution_ratio >= 0.5 else 'sparse'
                    }
                    
                    # Analyze data distribution patterns
                    if cardinality == "1:many":
                        if distribution_ratio > 10:
                            pattern = "high_fanout"
                        elif distribution_ratio > 3:
                            pattern = "moderate_fanout"
                        else:
                            pattern = "low_fanout"
                    elif cardinality == "many:1":
                        if distribution_ratio < 0.1:
                            pattern = "high_concentration"
                        elif distribution_ratio < 0.5:
                            pattern = "moderate_concentration"
                        else:
                            pattern = "low_concentration"
                    else:
                        pattern = "balanced"
                    
                    data_distribution_patterns[fk['constraint_name']] = {
                        'pattern': pattern,
                        'description': f"{cardinality} relationship with {pattern} distribution"
                    }
                    
                    # Analyze relationship health
                    if isinstance(parent_count, int) and isinstance(referenced_count, int):
                        if parent_count > 0 and referenced_count == 0:
                            health = "orphaned_references"
                        elif parent_count == 0 and referenced_count > 0:
                            health = "unused_references"
                        elif parent_count > 0 and referenced_count > 0:
                            health = "healthy"
                        else:
                            health = "empty_relationship"
                    else:
                        health = "error_analyzing"
                    
                    relationship_health[fk['constraint_name']] = {
                        'health_status': health,
                        'data_consistency': 'consistent' if health == 'healthy' else 'inconsistent'
                    }
            
            # Analyze performance indicators based on data distribution
            performance_indicators = {
                'high_fanout_tables': [],
                'concentration_tables': [],
                'balanced_tables': [],
                'potential_bottlenecks': []
            }
            
            for fk_name, fk_data in foreign_key_cardinality.items():
                if fk_data['cardinality'] == '1:many' and fk_data['distribution_ratio'] > 10:
                    performance_indicators['high_fanout_tables'].append({
                        'table': fk_data['parent_table'],
                        'ratio': fk_data['distribution_ratio'],
                        'risk': 'high'
                    })
                elif fk_data['cardinality'] == 'many:1' and fk_data['distribution_ratio'] < 0.1:
                    performance_indicators['concentration_tables'].append({
                        'table': fk_data['referenced_table'],
                        'ratio': fk_data['distribution_ratio'],
                        'risk': 'medium'
                    })
                elif fk_data['cardinality'] in ['1:1', 'many:many']:
                    performance_indicators['balanced_tables'].append({
                        'parent_table': fk_data['parent_table'],
                        'referenced_table': fk_data['referenced_table'],
                        'ratio': fk_data['distribution_ratio']
                    })
            
            # Identify potential bottlenecks
            for fk_name, fk_data in foreign_key_cardinality.items():
                if (fk_data['cardinality'] == '1:many' and fk_data['distribution_ratio'] > 50) or \
                   (fk_data['cardinality'] == 'many:1' and fk_data['distribution_ratio'] < 0.01):
                    performance_indicators['potential_bottlenecks'].append({
                        'constraint': fk_name,
                        'parent_table': fk_data['parent_table'],
                        'referenced_table': fk_data['referenced_table'],
                        'issue': 'extreme_distribution_ratio',
                        'ratio': fk_data['distribution_ratio']
                    })
            
            return {
                "table_row_counts": table_row_counts,
                "foreign_key_cardinality": foreign_key_cardinality,
                "data_distribution_patterns": data_distribution_patterns,
                "relationship_health": relationship_health,
                "performance_indicators": performance_indicators,
                "analysis_timestamp": "2025-01-22T00:00:00Z",
                "total_tables_analyzed": len(table_row_counts),
                "total_relationships_analyzed": len(foreign_key_cardinality)
            }
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
                
    except Exception as e:
        return {"error": f"Failed to analyze actual data distribution: {str(e)}"}

