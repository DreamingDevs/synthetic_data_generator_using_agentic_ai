# tools/db_connection_tool.py
import pyodbc
from crewai_tools import BaseTool
from .connection_manager import ConnectionManager

class DBConnectionTool(BaseTool):
    name = "Connect to SQL Server Database"
    description = (
        "Establish a SQL Server connection and store it for other tools to use. "
        "Args: server (e.g., 'localhost\\SQLEXPRESS'), database (e.g., 'MovieReviews'), "
        "username (optional), password (optional), driver (optional). "
        "If username/password are omitted, uses Windows Authentication."
    )

    def _run(
        self,
        server: str,
        database: str
    ):
        conn = pyodbc.connect(f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;")
        conn.autocommit = True
        ConnectionManager.set_connection(conn, {
            "server": server, "database": database, "auth":  "windows"
        })
        return f"✅ Connected to '{database}' on '{server}'. Stored connection for subsequent tools."
