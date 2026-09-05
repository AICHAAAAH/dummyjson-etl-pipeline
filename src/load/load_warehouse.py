import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_URL = (
    f"postgresql+psycopg2://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
)

engine = create_engine(DB_URL)


def load_person(people):
    with engine.begin() as conn:
        for person in people:
            result = conn.execute(
                text("""
                    INSERT INTO warehouse.person (person_id, first_name, last_name, email, age, row_hash)
                    VALUES (:person_id, :first_name, :last_name, :email, :age, :row_hash)
                    ON CONFLICT (person_id) DO UPDATE SET
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        email = EXCLUDED.email,
                        age = EXCLUDED.age,
                        row_hash = EXCLUDED.row_hash
                    WHERE warehouse.person.row_hash IS DISTINCT FROM EXCLUDED.row_hash
                """),
                person
            )
            action = "changed" if result.rowcount else "unchanged"
            print(f"person_id={person['person_id']}: {action}")


def load_employment(employment):
    with engine.begin() as conn:
        for emp in employment:
            result = conn.execute(
                text("""
                    INSERT INTO warehouse.employment (person_id, company_name, department, title, row_hash)
                    VALUES (:person_id, :company_name, :department, :title, :row_hash)
                    ON CONFLICT (person_id) DO UPDATE SET
                        company_name = EXCLUDED.company_name,
                        department = EXCLUDED.department,
                        title = EXCLUDED.title,
                        row_hash = EXCLUDED.row_hash
                    WHERE warehouse.employment.row_hash IS DISTINCT FROM EXCLUDED.row_hash
                """),
                emp
            )
            action = "changed" if result.rowcount else "unchanged"
            print(f"person_id={emp['person_id']}: employment {action}")


def load_classification(classification):
    with engine.begin() as conn:
        for cls in classification:
            result = conn.execute(
                text("""
                    INSERT INTO warehouse.classification (person_id, role, department, row_hash)
                    VALUES (:person_id, :role, :department, :row_hash)
                    ON CONFLICT (person_id) DO UPDATE SET
                        role = EXCLUDED.role,
                        department = EXCLUDED.department,
                        row_hash = EXCLUDED.row_hash
                    WHERE warehouse.classification.row_hash IS DISTINCT FROM EXCLUDED.row_hash
                """),
                cls
            )
            action = "changed" if result.rowcount else "unchanged"
            print(f"person_id={cls['person_id']}: classification {action}")