# Incremental Load Strategy

This explains how "incremental" and "idempotent" are actually implemented
in this pipeline — and where the honest limitations are.

## The core mechanism: content hashing, not a source watermark

DummyJSON has no `updated_at` field, so this pipeline cannot do a true
"give me everything changed since timestamp X" extraction the way a
production source with a reliable watermark (or a CDC stream like
Debezium) would allow.

Instead, every transformed record gets a `row_hash` — an MD5 of its
business fields, computed in `transform_users.py`. On load, the upsert
uses:

```sql
ON CONFLICT (person_id) DO UPDATE SET ...
WHERE warehouse.person.row_hash IS DISTINCT FROM EXCLUDED.row_hash
```

This means re-running the exact same extract twice results in **zero**
changed rows the second time — only records whose actual values changed
get touched.

## Proven, not just claimed

This was tested directly, not assumed:
1. Ran the full pipeline once on 208 users — all inserted as `changed`.
2. Ran it again immediately, same data — all 208 came back as
   `unchanged`, confirming the pipeline is idempotent.
3. Manually corrupted one row (`age = 999`) and re-ran the data quality
   checks — the range check correctly failed and the pipeline raised a
   `RuntimeError`, proving the failure path (not just the success path)
   actually works.

## Known limitation: Employment history is not versioned (no SCD Type 2)

`warehouse.employment` currently upserts a single "current" record per
`person_id` rather than tracking historical changes with `is_current` /
`valid_from` / `valid_to` columns. If a person's title changed between
runs, this v1 pipeline overwrites the old value rather than preserving
history.

**What a v2 would add:** on load, check if the incoming `row_hash` differs
from the current record; if so, mark the old row `is_current = FALSE` with
a `valid_to` timestamp, then insert a new row. This is standard SCD Type 2,
deliberately scoped out of v1 to ship a working pipeline first.

## What true CDC would add on top of this

If the source were a real production database (as the original job
description's PostgreSQL-source scenario describes) rather than a REST
API, this same row-hash strategy could be paired with:
- Postgres logical replication or Debezium to capture row-level changes
  directly from the write-ahead log, avoiding a full re-pull every run.
- A real `source_updated_at` watermark to make extraction itself
  incremental, rather than pulling everything and relying on hashing at
  load time.