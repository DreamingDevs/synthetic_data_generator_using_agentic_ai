import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    DB_SERVER = os.getenv("DB_SERVER")  # e.g. myserver (no instance name)
    DB_NAME = os.getenv("DB_NAME")
    DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    @staticmethod
    def get_connection_string():
        server = f"tcp:{Config.DB_SERVER},1433"
        return f"DRIVER={{{Config.DB_DRIVER}}};SERVER={server};DATABASE={Config.DB_NAME};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30;UID={Config.DB_USER};PWD={Config.DB_PASSWORD};"