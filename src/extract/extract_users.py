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

BASE_URL = "https://dummyjson.com/users"
PAGE_SIZE = 30

def fetch_all_users():
    all_users = []
    skip = 0

    while True:
        response = requests.get(BASE_URL, params={"limit": PAGE_SIZE, "skip": skip})
        data = response.json()

        all_users.extend(data["users"])
        skip += PAGE_SIZE

        print(f"Fetched {len(data['users'])} users (skip={skip - PAGE_SIZE}). Total so far: {len(all_users)}")

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
                            INSERT INTO staging.raw_users (source_id, payload, batch_id)
                            VALUES (:source_id, :payload, :batch_id)
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
