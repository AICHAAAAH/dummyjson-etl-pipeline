import os
import hashlib

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


def _md5(value: str) -> str:
    """Create an MD5 hash for content-change detection.

    MD5 is used here only as a deterministic content hash,
    not for security or password hashing.
    """
    return hashlib.md5(value.encode()).hexdigest()


def _normalize_optional(value):
    """Normalize optional string fields."""
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        return value if value else None

    return value


def build_person(person_id, payload):
    """
    Transform a raw DummyJSON user payload into the person dimension format.

    Returns:
        dict: cleaned person record
        None: if required fields are missing
    """

    first_name = str(payload.get("firstName") or "").strip()
    last_name = str(payload.get("lastName") or "").strip()
    email = str(payload.get("email") or "").strip().lower()
    age = payload.get("age")

    # Required fields
    if not first_name or not last_name or not email:
        return None

    row_hash = _md5(
        f"{first_name}|{last_name}|{email}|{age}"
    )

    return {
        "person_id": person_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "row_hash": row_hash,
        "age": age,
    }


def build_employment(person_id, payload):
    """
    Transform employment information from a raw user payload.

    Returns:
        dict: cleaned employment record
        None: if company information is missing
    """

    company = payload.get("company") or {}

    company_name = str(company.get("name") or "").strip()
    department = _normalize_optional(company.get("department"))
    title = _normalize_optional(company.get("title"))

    if not company_name:
        return None

    row_hash = _md5(
        f"{company_name}|{department or ''}|{title or ''}"
    )

    return {
        "person_id": person_id,
        "company_name": company_name,
        "department": department,
        "title": title,
        "row_hash": row_hash,
    }


def build_classification(person_id, payload):
    """
    Transform classification information from a raw user payload.

    Returns:
        dict: cleaned classification record
        None: if role is missing
    """

    role = str(payload.get("role") or "").strip().lower()

    company = payload.get("company") or {}
    department = _normalize_optional(company.get("department"))

    if not role:
        return None

    row_hash = _md5(
        f"{role}|{department or ''}"
    )

    return {
        "person_id": person_id,
        "role": role,
        "department": department,
        "row_hash": row_hash,
    }


def transform_batch(batch_id):
    """
    Read one staging batch and transform it into
    person, employment, and classification records.
    """

    # Create the database engine only when the batch transformation runs.
    # This keeps the module importable by unit tests without requiring
    # database credentials.
    db_url = (
        f"postgresql+psycopg2://{os.environ['DB_USER']}:"
        f"{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/"
        f"{os.environ['DB_NAME']}"
    )

    engine = create_engine(db_url)

    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT source_id, payload
                FROM staging.raw_users
                WHERE batch_id = :batch_id
                """
            ),
            {"batch_id": batch_id},
        )

        rows = result.fetchall()

    clean_people = []
    clean_employment = []
    clean_classification = []

    skipped_people = 0
    skipped_employment = 0
    skipped_classification = 0

    for row in rows:
        person = build_person(row.source_id, row.payload)

        if person:
            clean_people.append(person)
        else:
            skipped_people += 1

        employment = build_employment(row.source_id, row.payload)

        if employment:
            clean_employment.append(employment)
        else:
            skipped_employment += 1

        classification = build_classification(
            row.source_id,
            row.payload,
        )

        if classification:
            clean_classification.append(classification)
        else:
            skipped_classification += 1

    print(
        f"Batch {batch_id} transformed: "
        f"{len(clean_people)} people, "
        f"{len(clean_employment)} employment records, "
        f"{len(clean_classification)} classification records."
    )

    print(
        f"Skipped: "
        f"{skipped_people} people, "
        f"{skipped_employment} employment records, "
        f"{skipped_classification} classification records."
    )

    return (
        clean_people,
        clean_employment,
        clean_classification,
    )


if __name__ == "__main__":
    BATCH_ID = "bb60b84b-d4c0-443a-8cf7-02208b2ff5f2"

    people, employment, classification = transform_batch(BATCH_ID)

    print(f"People: {len(people)}")
    print(f"Employment: {len(employment)}")
    print(f"Classification: {len(classification)}")