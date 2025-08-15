# tools/db_connection_tool.py
import pyodbc
from crewai_tools import BaseTool
from .connection_manager import ConnectionManager

def _try_connect(conn_strs):
    last_exc = None
    for cs in conn_strs:
        try:
            conn = pyodbc.connect(cs)
            conn.autocommit = True
            return conn
        except Exception as e:
            last_exc = e
    raise last_exc

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
        database: str,
        username: str = None,
        password: str = None,
        driver: str = "{ODBC Driver 18 for SQL Server}",
        trust_server_certificate: bool = True
    ):
        tsc = "yes" if trust_server_certificate else "no"
        conn_strs = []
        if username and password:
            conn_strs.append(
                f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate={tsc};"
            )
            # fallback to Driver 17
            conn_strs.append(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate={tsc};"
            )
        else:
            conn_strs.append(
                f"DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate={tsc};"
            )
            # fallback to Driver 17
            conn_strs.append(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate={tsc};"
            )

        conn = _try_connect(conn_strs)
        ConnectionManager.set_connection(conn, {
            "server": server, "database": database, "driver": driver,
            "auth": "sql" if (username and password) else "windows"
        })
        return f"✅ Connected to '{database}' on '{server}'. Stored connection for subsequent tools."
