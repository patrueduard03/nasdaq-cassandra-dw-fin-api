import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.connect_database import session

# Set correct keyspace here
KEYSPACE = "lectures"
session.execute(f"USE {KEYSPACE}")

# Truncate tables in correct order (respecting dependencies)
TRUNCATE_TABLES = [
    "TRUNCATE data",
    "TRUNCATE asset", 
    "TRUNCATE data_source"
]

def clear_tables():
    print(f"Using keyspace: {KEYSPACE}")
    for query in TRUNCATE_TABLES:
        try:
            session.execute(query)
            table_name = query.split()[1]
            print(f"Cleared table: {table_name}")
        except Exception as e:
            print(f"Error clearing table with query '{query}': {e}")
    print("Tables cleared successfully.")

if __name__ == "__main__":
    clear_tables()