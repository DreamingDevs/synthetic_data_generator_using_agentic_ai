# tools/connection_manager.py
import pyodbc
from typing import Optional

class ConnectionManager:
    """
    Singleton-style connection holder that other tools can use.
    """
    _conn: Optional[pyodbc.Connection] = None
    _conn_info: Optional[dict] = None

    @classmethod
    def set_connection(cls, conn: pyodbc.Connection, info: dict):
        cls._conn = conn
        cls._conn_info = info

    @classmethod
    def get_connection(cls) -> pyodbc.Connection:
        if cls._conn is None:
            raise RuntimeError("No active database connection. Call the DBConnectionTool first.")
        return cls._conn

    @classmethod
    def get_info(cls) -> Optional[dict]:
        return cls._conn_info

    @classmethod
    def clear(cls):
        try:
            if cls._conn is not None:
                cls._conn.close()
        finally:
            cls._conn = None
            cls._conn_info = None
