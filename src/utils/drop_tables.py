import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.connect_database import session

# Set correct keyspace here
KEYSPACE = "lectures"
session.execute(f"USE {KEYSPACE}")

# Drop tables in correct order (respecting dependencies)
DROP_TABLES = [
    "DROP TABLE IF EXISTS data",
    "DROP TABLE IF EXISTS asset",
    "DROP TABLE IF EXISTS data_source"
]

def drop_tables():
    print(f"Using keyspace: {KEYSPACE}")
    for query in DROP_TABLES:
        session.execute(query)
    print("Tables dropped successfully.")

if __name__ == "__main__":
    drop_tables()