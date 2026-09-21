# DummyJSON Person/Employment/Classification ETL Pipeline

An end-to-end, orchestrated ETL pipeline that ingests Person, Employment, and Classification data from a REST API, validates and normalizes it, and loads it incrementally into a PostgreSQL analytics warehouse — scheduled and orchestrated with Apache Airflow, running in Docker.

**Source:** [DummyJSON `/users` API](https://dummyjson.com/docs/users)

---

## Business Question

Can we build a reliable, repeatable pipeline that keeps a Person/Employment/Classification warehouse synchronized with a REST API source — without manual intervention, without duplicating data on re-runs, and orchestrated well enough that another engineer could understand and reproduce it?

---

## What This Project Demonstrates

- **Staging → warehouse architecture**
- **Idempotent, incremental warehouse loading** using deterministic content hashes and PostgreSQL `UPSERT` logic
- **Data quality gates** for nulls, uniqueness, referential integrity, and value ranges
- **Automated transformation testing** with pytest
- **22 passing pytest tests**
- **Apache Airflow orchestration** with `extract → transform_load → validate`
- **CeleryExecutor + Redis** for Airflow task execution
- **Docker networking and service integration**
- PostgreSQL hosting both the Airflow metadata database and the `dummyjson_etl` warehouse database

---

## Project Structure

```text
dummyjson-etl-pipeline/
│
├── README.md
├── requirements.txt
├── pytest.ini
├── run_pipeline.py
├── docker-compose-airflow.yaml
├── .env.example
│
├── sql/
│   └── 01_schema.sql
│
├── src/
│   ├── extract/
│   │   └── extract_users.py
│   ├── transform/
│   │   └── transform_users.py
│   ├── load/
│   │   └── load_warehouse.py
│   └── validate/
│       └── data_quality.py
│
├── dags/
│   └── dummyjson_etl_dag.py
│
├── docs/
│   ├── data_lineage.md
│   └── incremental_strategy.md
│
├── tests/
│   ├── test_transform.py
│   ├── test_data_quality.py
│   └── test_incremental.py
│
├── config/
└── plugins/
```

---

## Architecture

```text
                         DummyJSON REST API
                                │
                                │ HTTP
                                ▼
                     ┌─────────────────────┐
                     │  Extract / Ingest   │
                     │ extract_users.py    │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │ PostgreSQL Staging  │
                     │ staging.raw_users   │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │     Transform       │
                     │ normalize fields    │
                     │ validate fields     │
                     │ calculate row_hash  │
                     └──────────┬──────────┘
                                │
                                ▼
              ┌──────────────────────────────────┐
              │      PostgreSQL Warehouse         │
              │      dummyjson_etl database       │
              │                                  │
              │ warehouse.person                 │
              │ warehouse.employment             │
              │ warehouse.classification         │
              └───────────────┬──────────────────┘
                              │
                              ▼
                     Data Quality Gates
                              │
                              ▼
                       Pipeline Success

                    Apache Airflow
                          │
                          ▼
              extract → transform_load → validate
```

---

## Tech Stack

- **Python** — extraction, transformation, validation, and loading
- **Requests** — REST API communication
- **SQLAlchemy** — PostgreSQL interaction
- **pytest** — automated testing
- **PostgreSQL** — staging and warehouse storage
- **Apache Airflow 2.9.3** — orchestration and scheduling
- **CeleryExecutor** — distributed Airflow task execution
- **Redis** — Celery message broker
- **Docker & Docker Compose** — containerized infrastructure

---

# Setup & Reproduction

## Prerequisites

- Docker Desktop
- Python 3.x
- Git

The commands below are written for PowerShell on Windows.

---

## 1. Create the shared Docker network

```powershell
docker network create dummyjson-shared-net
```

If the network already exists, no additional action is required.

---

## 2. Start PostgreSQL

PostgreSQL is defined as part of the Airflow Docker Compose deployment.

```powershell
docker compose -f docker-compose-airflow.yaml --env-file .env.airflow up -d postgres
```

The PostgreSQL service hosts two databases:

```text
airflow
    ↓
Airflow metadata

dummyjson_etl
    ↓
ETL staging + warehouse
```

PostgreSQL listens on `5432` inside Docker and is exposed as `5433` on the Windows host.

---

## 3. Apply the database schema

Apply the committed schema to the ETL database:

```powershell
Get-Content .\sql\01_schema.sql -Raw | docker compose -f docker-compose-airflow.yaml exec -T postgres psql -U etl_user -d dummyjson_etl
```

The schema creates:

```text
staging.raw_users

warehouse.person
warehouse.employment
warehouse.classification
```

---

## 4. Set up Python

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## 5. Configure environment variables

Copy `.env.example` to `.env` and configure standalone execution:

```text
SOURCE_API_BASE_URL=https://dummyjson.com
SOURCE_API_PAGE_SIZE=30

DB_HOST=localhost
DB_PORT=5433
DB_NAME=dummyjson_etl
DB_USER=etl_user
DB_PASSWORD=changeme
```

Standalone Python uses:

```text
localhost:5433
```

Airflow containers use:

```text
postgres:5432
```

Both paths access the same `dummyjson_etl` database.

---

# Running the Pipeline

## Standalone execution

The standalone runner executes:

```text
Extract
   ↓
Transform
   ↓
Load
   ↓
Validate
```

Run:

```powershell
python run_pipeline.py
```

---

# Airflow Orchestration

The Airflow deployment includes:

- Airflow webserver
- Airflow scheduler
- Airflow worker
- Airflow triggerer
- Redis
- PostgreSQL
- CeleryExecutor

The DAG is located at:

```text
dags/dummyjson_etl_dag.py
```

The workflow is:

```text
extract
   ↓
transform_load
   ↓
validate
```

The DAG is scheduled daily at **2:00 AM** and includes automatic retries.

## Start Airflow

Initialize Airflow:

```powershell
docker compose -f docker-compose-airflow.yaml --env-file .env.airflow up airflow-init
```

Then start the stack:

```powershell
docker compose -f docker-compose-airflow.yaml --env-file .env.airflow up -d
```

Open:

```text
http://localhost:8080
```

Local development credentials:

```text
Username: airflow
Password: airflow
```

Then open `dummyjson_etl_pipeline`, confirm it is unpaused, trigger a manual run, and verify that `extract → transform_load → validate` succeeds.

---

# Why This Architecture?

The project uses a single PostgreSQL service inside the Docker Compose deployment.

It contains:

```text
airflow
```

for Airflow metadata, and:

```text
dummyjson_etl
```

for the ETL staging and warehouse.

Airflow and PostgreSQL communicate through:

```text
dummyjson-shared-net
```

The same ETL database can also be accessed from Windows through `localhost:5433`.

---

# Testing

The project includes automated pytest coverage for transformation logic, data-quality validation, deterministic hashing, and incremental change detection.

Run:

```powershell
pytest -v
```

Current result:

```text
22 passed in 1.60s
```

The tests are distributed across:

```text
tests/test_transform.py
tests/test_data_quality.py
tests/test_incremental.py
```

Run the incremental tests alone:

```powershell
pytest tests/test_incremental.py -v
```

Result:

```text
6 passed
```

The automated tests are unit-level tests. PostgreSQL loading behavior was additionally verified through controlled database tests.

---

# Incremental Loading & Idempotency

DummyJSON does not provide a reliable source-side `updated_at` field for this dataset, so the project uses deterministic content hashing.

The transformation layer generates an MD5 hash from relevant business fields. PostgreSQL `ON CONFLICT` logic then prevents duplicate warehouse rows and updates rows only when the content hash changes.

Conceptually:

```text
Source record
     ↓
Normalize business fields
     ↓
Generate content hash
     ↓
Compare with warehouse row_hash
     ↓
Same hash?
   /      \\
 YES       NO
  ↓         ↓
No change  Update
```

## Repeat-Run Verification

Initial warehouse counts:

```text
person:          208
employment:      208
classification:  208
```

Two additional full pipeline executions were performed against unchanged source data.

The staging table increased:

```text
raw_users:
624 → 832 → 1040
```

The warehouse remained:

```text
person:          208
employment:      208
classification:  208
```

All 208 records were reported as `unchanged` during both repeated runs.

This demonstrates idempotent warehouse loading for unchanged source content.

---

# Controlled Source-Change Verification

A controlled source change was tested using the actual staging, transformation, and PostgreSQL loading logic.

For `person_id = 1`, the original record was:

```text
Emily Johnson
age = 29
```

A controlled staging batch changed only the age:

```text
29 → 30
```

The person hash changed from:

```text
7b07c9e3ad0b124f509012fc31f3dc6c
```

to:

```text
dc618257c27d5c5cdcc1f2776b41228b
```

The actual warehouse loader reported:

```text
person_id=1: changed
```

Verification showed:

```text
total_people            = 208
other_people            = 207
changed_person_verified  = 1
```

The source record was subsequently restored through the same transformation and loading logic:

```text
30 → 29
```

and the original hash was restored:

```text
7b07c9e3ad0b124f509012fc31f3dc6c
```

This confirms that unchanged source content leaves the warehouse unchanged, while changed source content updates the affected warehouse row.

Detailed documentation is available in [`docs/incremental_strategy.md`](docs/incremental_strategy.md).

---

# Data Quality

Data-quality validation runs after the warehouse load.

The validation layer checks:

- Null values
- Uniqueness
- Referential integrity
- Value ranges

A failed critical check raises a `RuntimeError`, causing the pipeline to fail rather than silently accepting invalid warehouse data.

Implementation:

```text
src/validate/data_quality.py
```

Tests:

```text
tests/test_data_quality.py
```

Current validation includes:

```text
warehouse.person
    ├── email not null
    ├── first_name not null
    ├── person_id unique
    ├── email unique
    └── age between 0 and 120

warehouse.employment
    ├── company_name not null
    └── person_id references warehouse.person

warehouse.classification
    ├── role not null
    └── person_id references warehouse.person
```

---

# Data Lineage

```text
DummyJSON /users
       │
       ▼
staging.raw_users
       │
       ▼
Transformation layer
       │
       ├──────────────► warehouse.person
       ├──────────────► warehouse.employment
       └──────────────► warehouse.classification
                              │
                              ▼
                       Data quality checks
```

Detailed field-level mapping is available in [`docs/data_lineage.md`](docs/data_lineage.md).

---

# Infrastructure Issues & Fixes

This project involved several real infrastructure and configuration issues during development.

## 1. PostgreSQL Port Conflict

A native Windows PostgreSQL service was already using port `5432`, causing the Python application to connect to the wrong PostgreSQL instance.

The issue was diagnosed using:

```powershell
netstat -ano
tasklist
```

The Docker PostgreSQL service was therefore exposed on host port `5433` while PostgreSQL continues to listen on `5432` inside the container.

Final connection paths:

```text
Windows: localhost:5433
Docker:  postgres:5432
```

## 2. Windows `.env` Encoding Issue

A `.env` file created through PowerShell redirection was saved with incompatible UTF-16/BOM encoding. Docker Compose rejected the environment file. The file was recreated using compatible encoding.

## 3. Docker Image Pull Timeouts

Large Docker image downloads repeatedly encountered TLS handshake timeouts. The issue was mitigated by pulling images individually rather than relying only on a large parallel Compose pull.

## 4. WSL2 Memory Allocation

Airflow's resource check reported insufficient available memory. The WSL2 memory limit was increased through `%USERPROFILE%\.wslconfig` and WSL was restarted.

## 5. Docker Networking

Airflow and PostgreSQL communicate through the dedicated external network:

```text
dummyjson-shared-net
```

The Compose configuration declares:

```yaml
networks:
  default:
    name: dummyjson-shared-net
    external: true
```

Inside Docker, Airflow reaches PostgreSQL through the service hostname `postgres`. From Windows, the ETL warehouse is available through `localhost:5433`.

---

# Methodology & Limitations

## Employment History Is Not Versioned

The current warehouse stores the current employment state for each person. It does not implement Slowly Changing Dimension Type 2 (SCD Type 2), so historical employment changes are not preserved as separate versions.

A future implementation could introduce:

```text
effective_from
effective_to
is_current
version_number
```

## Content Hashing Is Not True CDC

DummyJSON does not provide a reliable source-side `updated_at` field or CDC mechanism for this dataset. The project therefore uses content hashing instead.

The MD5 hash is used only as a deterministic content-change detector and should not be described as true Change Data Capture (CDC).

## Incremental Loading Does Not Mean Incremental Extraction

The pipeline detects changes after retrieving source records:

```text
DummyJSON API
     ↓
Retrieve records
     ↓
Transform
     ↓
Calculate row_hash
     ↓
Compare with warehouse
     ↓
Update changed warehouse rows
```

Therefore, the project implements incremental **warehouse loading**, not true incremental **source extraction**.

## Rejected Records Are Not Persisted

Invalid records are currently skipped and counted/logged during transformation.

A production implementation could add `staging.rejected_rows` containing the batch ID, source record ID, rejection reason, raw payload, and timestamp.

## Portfolio Project, Not Production Deployment

This project is a portfolio demonstration of ETL, orchestration, data quality, database loading, testing, Docker infrastructure, and technical documentation. It is not presented as production-ready.

Current limitations include:

- Secrets are supplied through environment files rather than a dedicated secrets manager
- Airflow is configured for local development
- No cloud deployment
- No production monitoring platform
- No full CI/CD deployment pipeline
- DummyJSON is a demonstration API rather than a production source
- Employment history is not implemented as SCD Type 2
- Source extraction is not true CDC

---

# What This Project Demonstrates

The project covers the complete data pipeline:

```text
REST API
   ↓
Data ingestion
   ↓
PostgreSQL staging
   ↓
Data transformation
   ↓
Content hashing
   ↓
Incremental / idempotent warehouse loading
   ↓
Warehouse modeling
   ↓
Data quality validation
   ↓
Automated testing
   ↓
Airflow orchestration
   ↓
Docker infrastructure
   ↓
Technical documentation
```

Key technologies and skills demonstrated:

- ETL pipeline design
- REST API ingestion
- Python
- SQL
- PostgreSQL
- SQLAlchemy
- Data transformation
- Data validation
- Incremental warehouse loading
- Idempotent processing
- Content-based change detection
- Automated testing
- Apache Airflow
- CeleryExecutor
- Redis
- Docker
- Docker networking
- Infrastructure troubleshooting
- Technical documentation

---

# Future Improvements

Possible future improvements include:

- GitHub Actions CI
- Persistent rejected-record/error tables
- SCD Type 2 employment history
- Expanded PostgreSQL integration-test coverage
- Production-grade secrets management
- Cloud deployment
- Monitoring and alerting
- More detailed Airflow observability
- Additional warehouse dimensions and facts
- Source-side incremental extraction when a reliable watermark becomes available
- CDC integration for a database-backed production source

These improvements are intentionally treated as future work rather than adding unnecessary infrastructure complexity to the current portfolio version.

---

# Author

**Aicha Ajdid**

[LinkedIn](https://linkedin.com/in/aicha-ajdid) · [GitHub](https://github.com/AICHAAAAH)

