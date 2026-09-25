# Data Lineage: Source → Transform → Target

This document traces every warehouse column back to its source field, so
an analytics team (or another engineer) can understand the pipeline
without reading the code.

## Person (`warehouse.person`)

| Target column | Source field (DummyJSON `/users`) | Transform applied |
|---|---|---|
| `person_id` | `id` | Used as-is (natural key) |
| `first_name` | `firstName` | Whitespace-trimmed |
| `last_name` | `lastName` | Whitespace-trimmed |
| `email` | `email` | Trimmed, lowercased |
| `age` | `age` | Used as-is; validated against a 0–120 range check post-load |
| `row_hash` | *(derived)* | MD5 of first_name, last_name, email, age — used for change detection |

**Rows skipped if:** `firstName`, `lastName`, or `email` is missing.

## Employment (`warehouse.employment`)

| Target column | Source field | Transform applied |
|---|---|---|
| `person_id` | `id` | Foreign key to `warehouse.person` |
| `company_name` | `company.name` | Whitespace-trimmed |
| `department` | `company.department` | Whitespace-trimmed when present |
| `title` | `company.title` | Whitespace-trimmed when present |
| `row_hash` | *(derived)* | MD5 of company_name, department, title |

**Rows skipped if:** `company.name` is missing.

## Classification (`warehouse.classification`)

| Target column | Source field | Transform applied |
|---|---|---|
| `person_id` | `id` | Foreign key to `warehouse.person` |
| `role` | `role` | Trimmed, lowercased |
| `department` | `company.department` | Duplicated from Employment, for fast filtering without a join |
| `row_hash` | *(derived)* | MD5 of role, department |

**Rows skipped if:** `role` is missing.

## Rejected Row Handling

Rows failing a required-field check are currently skipped during transformation
and reported through console summary counts.

The pipeline does not currently persist rejected rows to a queryable table.

**Known gap, flagged intentionally:** a production version should write skipped
rows to a `staging.rejected_rows` table so the analytics team can audit exactly
what did not load, and why, without reading application logs.