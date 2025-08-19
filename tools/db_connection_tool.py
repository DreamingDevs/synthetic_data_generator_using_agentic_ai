# tools/db_connection_tool.py
import pyodbc
from crewai.tools import BaseTool
from .connection_manager import ConnectionManager
from config import Config

class DBConnectionTool(BaseTool):
    name: str = "Connect to SQL Server Database"
    description: str = (
        "Establish a SQL Server connection and store it for other tools to use. "
        "Args: server (e.g., 'localhost\\SQLEXPRESS'), database (e.g., 'MovieReviews'), "
        "username (optional), password (optional), driver (optional). "
        "If username/password are omitted, uses Windows Authentication."
    )

    def _run(self) -> str:
        conn = pyodbc.connect(Config.get_connection_string())
        conn.autocommit = True
        ConnectionManager.set_connection(conn, {
            "server": Config.DB_SERVER, "database": Config.DB_NAME, "auth":  "windows"
        })
        return f"✅ Connected to '{Config.DB_NAME}' on '{Config.DB_SERVER}'. Stored connection for subsequent tools."
