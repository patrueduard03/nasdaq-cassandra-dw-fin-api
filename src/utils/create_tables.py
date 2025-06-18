import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.connect_database import session

# List accessible keyspaces
print("Accessible keyspaces:")
rows = session.execute("SELECT keyspace_name FROM system_schema.keyspaces")
for row in rows:
    print("-", row.keyspace_name)

# Set the working keyspace here
KEYSPACE = "lectures"
session.execute(f"USE {KEYSPACE}")

# CQL statements for table creation
CREATE_ASSET = '''
CREATE TABLE IF NOT EXISTS asset (
    id int,
    name text,
    description text,
    system_date timestamp,
    is_deleted boolean,
    valid_from timestamp,
    valid_to timestamp,
    attributes map<text, text>,
    PRIMARY KEY (id, valid_from)
) WITH CLUSTERING ORDER BY (valid_from DESC);
'''

CREATE_DATA_SOURCE = '''
CREATE TABLE IF NOT EXISTS data_source (
    id int,
    name text,
    description text,
    system_date timestamp,
    provider text,
    attributes map<text, text>,
    is_deleted boolean,
    valid_from timestamp,
    valid_to timestamp,
    PRIMARY KEY (id, valid_from)
) WITH CLUSTERING ORDER BY (valid_from DESC);
'''

CREATE_DATA = '''
CREATE TABLE IF NOT EXISTS data (
    asset_id int,
    data_source_id int,
    business_date date,
    system_date timestamp,
    values_double map<text, double>,
    values_int map<text, int>,
    values_text map<text, text>,
    is_deleted boolean,
    valid_from timestamp,
    valid_to timestamp,
    PRIMARY KEY ((asset_id, data_source_id), business_date, system_date)
) WITH CLUSTERING ORDER BY (business_date DESC, system_date DESC);
'''

def create_tables():
    print(f"Using keyspace: {KEYSPACE}")
    session.execute(CREATE_ASSET)
    session.execute(CREATE_DATA_SOURCE)
    session.execute(CREATE_DATA)
    print("Tables created successfully.")

if __name__ == "__main__":
    create_tables() 