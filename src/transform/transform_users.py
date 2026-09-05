import os
import hashlib
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_URL = (
    f"postgresql+psycopg2://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
)

engine = create_engine(DB_URL)

def transform_batch(batch_id):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT source_id, payload FROM staging.raw_users WHERE batch_id = :batch_id"),
            {"batch_id": batch_id}
        )
        rows = result.fetchall()

    clean_people = []

    for row in rows:
        payload = row.payload

        first_name = payload.get("firstName")
        last_name = payload.get("lastName")
        email = payload.get("email")
        age = payload.get("age")
        # Required-field check: skip this record if anything essential is missing
        if not first_name or not last_name or not email:
            print(f"SKIPPING source_id={row.source_id}: missing required field")
            continue

        row_hash = hashlib.md5(f"{first_name.strip()}|{last_name.strip()}|{email.strip().lower()}|{age}".encode()).hexdigest()
        
        clean_people.append({
          "person_id": row.source_id,
          "first_name": first_name.strip(),
          "last_name": last_name.strip(),
          "email": email.strip().lower(),
          "row_hash": row_hash,
          "age": age,
        })

    print(f"\nCleaned {len(clean_people)} of {len(rows)} rows")
    for p in clean_people:
        print(p)

    clean_employment = []

    for row in rows:
        payload = row.payload
        company = payload.get("company") or {}

        company_name = company.get("name")
        department = company.get("department")
        title = company.get("title")

        if not company_name:
            print(f"SKIPPING employment for source_id={row.source_id}: missing company name")
            continue

        row_hash = hashlib.md5(f"{company_name.strip()}|{department}|{title}".encode()).hexdigest()

        clean_employment.append({
            "person_id": row.source_id,
            "company_name": company_name.strip(),
            "department": department,
            "title": title,
            "row_hash": row_hash,
        })

    print(f"\nCleaned {len(clean_employment)} of {len(rows)} employment rows")

    clean_classification = []

    for row in rows:
        payload = row.payload
        company = payload.get("company") or {}

        role = payload.get("role")
        department = company.get("department")

        if not role:
            print(f"SKIPPING classification for source_id={row.source_id}: missing role")
            continue

        row_hash = hashlib.md5(f"{role.strip().lower()}|{department}".encode()).hexdigest()

        clean_classification.append({
            "person_id": row.source_id,
            "role": role.strip().lower(),
            "department": department,
            "row_hash": row_hash,
        })

    print(f"\nCleaned {len(clean_classification)} of {len(rows)} classification rows")

    return clean_people, clean_employment, clean_classification

if __name__ == "__main__":
    BATCH_ID = "bb60b84b-d4c0-443a-8cf7-02208b2ff5f2"
    people, employment, classification = transform_batch(BATCH_ID)
    print(f"Transformed {len(people)} people, {len(employment)} employment, {len(classification)} classification")












