import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    DB_SERVER = os.getenv("DB_SERVER")
    DB_NAME = os.getenv("DB_NAME")
    DB_DRIVER = os.getenv("DB_DRIVER")

    @staticmethod
    def get_connection_string():
        return f"DRIVER={{{Config.DB_DRIVER}}};SERVER={Config.DB_SERVER};DATABASE={Config.DB_NAME};Trusted_Connection=yes;TrustServerCertificate=yes;"
