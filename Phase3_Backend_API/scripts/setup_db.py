import os
import sys
import pyodbc
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    """Create the database if it doesn't exist"""
    # Load environment variables
    load_dotenv()

    # Database connection parameters
    server = os.getenv("DB_SERVER", "localhost")
    port = os.getenv("DB_PORT", "1433")
    user = os.getenv("DB_USER", "sa")
    password = os.getenv("DB_PASSWORD", "SlatePass1@")
    database = os.getenv("DB_NAME", "SlateDB")

    # Connect to SQL Server (master database) with autocommit=True
    try:
        # Use the raw connection string format with autocommit=True
        conn_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server},{port};DATABASE=master;UID={user};PWD={password};TrustServerCertificate=yes;Connection Timeout=30;"
        conn = pyodbc.connect(conn_string, autocommit=True)  # Set autocommit=True
        cursor = conn.cursor()

        # Check if database already exists
        cursor.execute(f"SELECT DB_ID('{database}')")
        db_id = cursor.fetchone()[0]
        
        if db_id:
            print(f"Database '{database}' already exists.")
        else:
            # Create database if it doesn't exist
            print(f"Creating database {database}...")
            cursor.execute(f"CREATE DATABASE [{database}]")
            print(f"Database {database} created successfully.")

        # Close connections
        cursor.close()
        conn.close()

        # Verify the database was created
        conn = pyodbc.connect(conn_string, autocommit=True)
        cursor = conn.cursor()
        cursor.execute(f"SELECT DB_ID('{database}')")
        db_id = cursor.fetchone()[0]
        
        if db_id:
            print(f"Database '{database}' is ready. (ID: {db_id})")
            cursor.close()
            conn.close()
            return True
        else:
            print(f"Failed to verify database '{database}'.")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"Error creating database: {e}")
        return False

if __name__ == "__main__":
    main()