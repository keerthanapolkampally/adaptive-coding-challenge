from sqlalchemy import create_engine, MetaData, Table, select

# Database URL
DB_URL = "postgresql://polkampallykeerthana:Montu#2799@localhost/adaptive_coding_challenge"

# Connect to the database
engine = create_engine(DB_URL)
metadata = MetaData()
metadata.reflect(bind=engine)

# Load tables
challenges_table = metadata.tables['challenges']
test_cases_table = metadata.tables['test_cases']
solutions_table = metadata.tables['solutions']

# Function to verify table content
def verify_table(table, limit=10):
    print(f"Verifying table: {table.name}")
    with engine.connect() as conn:
        result = conn.execute(select(table).limit(limit)).fetchall()
        for row in result:
            print(row)

if __name__ == "__main__":
    # Verify each table
    verify_table(challenges_table)
    verify_table(test_cases_table)
    verify_table(solutions_table)
