import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database settings
DB_SERVER = os.getenv("DB_SERVER", "localhost")
DB_PORT = os.getenv("DB_PORT", "1433")
DB_USER = os.getenv("DB_USER", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "SlatePass1@")
DB_NAME = os.getenv("DB_NAME", "SlateDB")

# Use the raw ODBC connection string format that worked
ODBC_CONNECTION_STR = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_SERVER},{DB_PORT};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD};TrustServerCertificate=yes;Connection Timeout=30;"
DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={ODBC_CONNECTION_STR}"

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# API settings
API_V1_STR = "/api"
PROJECT_NAME = "Slate"