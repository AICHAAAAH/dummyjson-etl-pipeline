import os
import uuid
import json

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import requests

load_dotenv()

DB_URL = (
    f"postgresql+psycopg2://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
)

engine = create_engine(DB_URL)

BASE_URL = (
    f"{os.getenv('SOURCE_API_BASE_URL', 'https://dummyjson.com').rstrip('/')}/users"
)

PAGE_SIZE = int(os.getenv("SOURCE_API_PAGE_SIZE", "30"))


def fetch_all_users():
    all_users = []
    skip = 0

    while True:
        response = requests.get(
            BASE_URL,
            params={"limit": PAGE_SIZE, "skip": skip},
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()

        all_users.extend(data["users"])

        print(
            f"Fetched {len(data['users'])} users "
            f"(skip={skip}). "
            f"Total so far: {len(all_users)}"
        )

        skip += PAGE_SIZE

        if skip >= data["total"]:
            break

    return all_users


def run_extract():
    users = fetch_all_users()

    print("\nDONE. Total users fetched:", len(users))

    batch_id = str(uuid.uuid4())

    print("Batch ID for this run:", batch_id)

    with engine.begin() as conn:
        for user in users:
            conn.execute(
                text("""
                    INSERT INTO staging.raw_users
                        (source_id, payload, batch_id)
                    VALUES
                        (:source_id, :payload, :batch_id)
                """),
                {
                    "source_id": user["id"],
                    "payload": json.dumps(user),
                    "batch_id": batch_id,
                },
            )

    print("Inserted", len(users), "rows into staging.raw_users")

    return batch_id


if __name__ == "__main__":
    run_extract()