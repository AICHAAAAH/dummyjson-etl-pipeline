import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_URL = (
    f"postgresql+psycopg2://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
)

engine = create_engine(DB_URL)


def check_no_nulls(table, column):
    query = f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL"
    with engine.connect() as conn:
        count = conn.execute(text(query)).scalar()
    passed = count == 0
    print(f"[{'PASS' if passed else 'FAIL'}] no_nulls: {table}.{column} — {count} null(s)")
    return passed

def check_uniqueness(table, column):
    query = f"""
        SELECT COUNT(*) FROM (
            SELECT {column} FROM {table}
            GROUP BY {column} HAVING COUNT(*) > 1
        ) dupes
    """
    with engine.connect() as conn:
        count = conn.execute(text(query)).scalar()
    passed = count == 0
    print(f"[{'PASS' if passed else 'FAIL'}] uniqueness: {table}.{column} — {count} duplicate group(s)")
    return passed

def check_referential_integrity(child_table, child_fk, parent_table, parent_pk):
    query = f"""
        SELECT COUNT(*) FROM {child_table} c
        LEFT JOIN {parent_table} p ON c.{child_fk} = p.{parent_pk}
        WHERE p.{parent_pk} IS NULL
    """
    with engine.connect() as conn:
        count = conn.execute(text(query)).scalar()
    passed = count == 0
    print(f"[{'PASS' if passed else 'FAIL'}] referential_integrity: {child_table}.{child_fk} -> {parent_table}.{parent_pk} — {count} orphan(s)")
    return passed

def check_range(table, column, min_val, max_val):
    query = f"""
        SELECT COUNT(*) FROM {table}
        WHERE {column} IS NOT NULL AND ({column} < :min_val OR {column} > :max_val)
    """
    with engine.connect() as conn:
        count = conn.execute(text(query), {"min_val": min_val, "max_val": max_val}).scalar()
    passed = count == 0
    print(f"[{'PASS' if passed else 'FAIL'}] range: {table}.{column} [{min_val}-{max_val}] — {count} out-of-range value(s)")
    return passed

if __name__ == "__main__":
    results = []

    results.append(check_no_nulls("warehouse.person", "email"))
    results.append(check_no_nulls("warehouse.person", "first_name"))
    results.append(check_no_nulls("warehouse.employment", "company_name"))
    results.append(check_no_nulls("warehouse.classification", "role"))

    results.append(check_uniqueness("warehouse.person", "person_id"))
    results.append(check_uniqueness("warehouse.person", "email"))

    results.append(check_referential_integrity("warehouse.employment", "person_id", "warehouse.person", "person_id"))
    results.append(check_referential_integrity("warehouse.classification", "person_id", "warehouse.person", "person_id"))

    results.append(check_range("warehouse.person", "age", 0, 120))

    if not all(results):
        raise RuntimeError("One or more data quality checks failed. See output above.")
    else:
        print("\nAll data quality checks passed.")