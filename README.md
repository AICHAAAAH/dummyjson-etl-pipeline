# DummyJSON Person/Employment/Classification ETL Pipeline

An end-to-end, orchestrated ETL pipeline that ingests Person, Employment, and
Classification data from a REST API, validates and normalizes it, and loads
it incrementally into a PostgreSQL analytics warehouse — scheduled and
monitored with Apache Airflow, running fully in Docker.

Source: [DummyJSON `/users` API](https://dummyjson.com/docs/users)

## Business Question

Can we build a reliable, repeatable pipeline that keeps a Person/Employment/
Classification warehouse in sync with a live source system — without manual
intervention, without duplicating data on re-runs, and orchestrated well
enough that another engineer could pick it up without asking me anything?

## What This Project Demonstrates

- **Staging → warehouse architecture**: raw API payloads land untouched in
  PostgreSQL before any transformation, so any load can be replayed from
  source data alone.
- **Idempotent, incremental loads**: every warehouse row carries a content
  hash (MD5 of its business fields); re-running the same batch twice
  changes nothing, and only genuinely changed records are touched — proven
  with real repeat-run tests, not just claimed (see
  `docs/incremental_strategy.md`).
- **Data quality gates that actually block bad data**: null, uniqueness,
  referential integrity, and range checks run after every load and raise a
  hard failure on critical violations — tested by deliberately injecting
  bad data and confirming the pipeline actually stops
  (see `src/validate/data_quality.py`).
- **Automated transformation testing**: transformation functions are tested
  independently for normalization, required-field validation, deterministic
  hashing, change detection, and extraction of employment/classification data
  (see `tests/test_transform.py`).
- **16 passing pytest tests**: the test suite covers both transformation logic
  and data-quality validation.
- **Full orchestration with Apache Airflow**: extract → transform_load →
  validate runs as a scheduled DAG (daily at 2 AM) with automatic retries,
  running in a Dockerized Airflow deployment (CeleryExecutor, Redis,
  PostgreSQL metadata DB).
- **Cross-container networking solved from scratch**: the Airflow stack and
  the project's own PostgreSQL warehouse run as separate Docker
  environments, connected deliberately via Docker networking rather than
  running everything in one container (see "Infrastructure Notes" below).

## Project Structure

```
dummyjson-etl-pipeline/
├── README.md
├── requirements.txt
├── pytest.ini                     # pytest configuration: test discovery + src import path
├── run_pipeline.py                 # standalone runner: extract -> transform -> load -> validate
├── docker-compose-airflow.yaml     # full Airflow stack (webserver, scheduler, worker, etc.)
├── .env.example                    # DB credentials for local (Windows-side) runs
│
├── sql/
│   └── 01_schema.sql                # staging + warehouse schema
│
├── src/
│   ├── extract/
│   │   └── extract_users.py         # paginated API pull -> staging.raw_users
│   ├── transform/
│   │   └── transform_users.py       # odular transformations + content hashing
│   ├── load/
│   │   └── load_warehouse.py        # idempotent upserts into warehouse tables
│   └── validate/
│       └── data_quality.py          # null/uniqueness/referential/range checks
│
├── dags/
│   └── dummyjson_etl_dag.py         # Airflow DAG: extract >> transform_load >> validate
│
├── docs/
│   ├── data_lineage.md              # source -> transform -> target field mapping
│   └── incremental_strategy.md      # how idempotency actually works here
│
├── tests/
│   ├── test_transform.py
│   └── test_data_quality.py
│
├── config/                          # Airflow config mount (empty, required by compose)
└── plugins/                         # Airflow plugins mount (empty, required by compose)

```

## Tech Stack

- **Python** (`requests` + `SQLAlchemy`) — API extraction, transformation,
  validation, and database loading
- **pytest** — automated unit testing for transformations and data-quality checks
- **PostgreSQL** (via Docker) — staging + warehouse schemas, idempotent
  upserts via `ON CONFLICT`
- **Apache Airflow 2.9.3** (via Docker Compose, CeleryExecutor) — scheduled
  daily orchestration with retries
- **Docker & Docker Compose** — containerized database and Airflow infrastructure

## Setup & Reproduction

### 1. Create the shared Docker network and start PostgreSQL

```powershell
docker network create dummyjson-shared-net

docker run --name dummyjson-postgres `
  --network dummyjson-shared-net `
  -e POSTGRES_USER=etl_user `
  -e POSTGRES_PASSWORD=changeme `
  -e POSTGRES_DB=dummyjson_etl `
  -p 5433:5432 `
  -d postgres:16
```
> Port `5433` is used on the host to avoid colliding with any native
> Postgres install — see "Infrastructure Notes" below for why this matters.

### 2. Run the schema migration
```powershell
Get-Content sql\01_schema.sql | docker exec -i dummyjson-postgres psql -U etl_user -d dummyjson_etl
```

### 3. Set up Python and install dependencies
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Copy `.env.example` to `.env` and fill in real values
(DB host `localhost`, port `5433`, for running standalone outside Docker)

### 5. Run the pipeline standalone (without Airflow)
```powershell
python run_pipeline.py
```

### 6. Run it fully orchestrated under Airflow
```powershell
docker compose -f docker-compose-airflow.yaml --env-file .env.airflow up airflow-init
docker compose -f docker-compose-airflow.yaml --env-file .env.airflow up -d
```
Then open `http://localhost:8080` (default login: `airflow` / `airflow`),
unpause `dummyjson_etl_pipeline`, and trigger a run.
```

### Why this is better

The README then follows the actual architecture:

```text
Create shared network
        ↓
Create warehouse PostgreSQL on network
        ↓
Run schema
        ↓
Install Python
        ↓
Standalone pipeline OR Airflow

No duplicate container creation.

## Testing

The project includes automated tests covering both transformation logic
and data-quality validation.

Run the full test suite with:

```powershell
python -m pytest -v

## Infrastructure Notes (Real Issues Hit & Fixed)

This project was built and debugged from scratch, including several
genuine infrastructure problems that don't show up in tutorials:

- **Port conflict between native and containerized Postgres.** A native
  Windows Postgres service was already listening on `5432`, silently
  causing the Python app to connect to the wrong database (with no
  matching user). Diagnosed with `netstat -ano` and `tasklist`, fixed by
  remapping the Docker container to host port `5433`.

- **Windows line-ending/encoding issue in `.env` files.** A `.env` file
  created via PowerShell's `>` redirect was saved in UTF-16 with a BOM,
  which Docker Compose's env-file parser rejected outright. Fixed by
  writing the file with `[System.IO.File]::WriteAllText(...)` and explicit
  ASCII encoding, verified with `Format-Hex`.

- **Unstable large image pulls under Docker Compose's parallel download.**
  Multi-image `docker compose pull` repeatedly failed with TLS handshake
  timeouts on large layers (Redis, Postgres, and the ~1.5GB Airflow image
  itself). Resolved by pulling each image individually with `docker pull`,
  which succeeds far more reliably than a large parallel batch pull on an
  unstable connection.

- **WSL2 memory allocation.** Airflow's own resource check flagged
  insufficient memory (3.8GB available, 4GB+ recommended) because
  WSL2's default memory cap is roughly half of total system RAM. Fixed by
  setting `memory=6GB` in `%USERPROFILE%\.wslconfig` and restarting WSL.

- **Cross-network container communication — root-caused and permanently fixed, not just patched.**

  **Permanent fix:** created a dedicated, named Docker network
  (`dummyjson-shared-net`) independent of any single compose stack.
  Recreated the PostgreSQL container to join it directly via `--network`
  at creation time (reattaching the existing named volume, so no data was
  lost), and configured `docker-compose-airflow.yaml` to use that same
  external network (`networks: default: name: dummyjson-shared-net,
  external: true`) instead of letting Compose auto-generate its own.
  Verified the fix by fully restarting Docker and confirming DNS
  resolution worked immediately, with no manual reconnection step needed.

## Methodology Notes & Limitations

- **Employment history is not versioned (no SCD Type 2).** Each pipeline
  run currently upserts a single "current" employment record per person
  rather than tracking historical job changes over time. See
  `docs/incremental_strategy.md` for what a versioned v2 would require.
- **DummyJSON has no native `updated_at` field**, so incremental loading
  is achieved via content hashing (MD5 of business fields) rather than a
  true source watermark — documented explicitly rather than implied to be
  real CDC.
- **This is a portfolio project, not a production deployment**: secrets
  are stored in plain `.env` files rather than a secrets manager, and the
  Airflow deployment uses CeleryExecutor's default local setup rather than
  a distributed worker pool.

## Author

Aicha Ajdid — [LinkedIn](https://linkedin.com/in/aicha-ajdid-50836626b) · [GitHub](https://github.com/AICHAAAAH)