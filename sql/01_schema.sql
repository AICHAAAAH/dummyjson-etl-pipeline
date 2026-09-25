CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.raw_users (
    id           BIGSERIAL PRIMARY KEY,
    source_id    INTEGER NOT NULL,
    payload      JSONB NOT NULL,
    extracted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    batch_id     UUID NOT NULL
);

CREATE SCHEMA IF NOT EXISTS warehouse;

CREATE TABLE IF NOT EXISTS warehouse.person (
    person_id    INTEGER PRIMARY KEY,
    first_name   TEXT NOT NULL,
    last_name    TEXT NOT NULL,
    email        TEXT NOT NULL,
    age          INTEGER,
    row_hash     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.employment (
    employment_id BIGSERIAL PRIMARY KEY,
    person_id     INTEGER NOT NULL UNIQUE REFERENCES warehouse.person (person_id),
    company_name  TEXT NOT NULL,
    department    TEXT,
    title         TEXT,
    row_hash      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.classification (
    classification_id BIGSERIAL PRIMARY KEY,
    person_id          INTEGER NOT NULL UNIQUE REFERENCES warehouse.person (person_id),
    role                TEXT NOT NULL,
    department          TEXT,
    row_hash            TEXT NOT NULL
);
