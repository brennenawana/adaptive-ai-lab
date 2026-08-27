# Crexi Baseline

A reproducible, fully-observed run of the Crexi ingest→analysis lane, plus an
operator-adjudicated ground truth. Plan: `../../../..`/plan file; epic context in
[`../leads-gtm/README.md`](../leads-gtm/README.md).

## Quick start

```bash
source rig/env.sh A      # A = deterministic (AI extract off) | B = AI-on
./rig/db.sh up           # start pinned postgres:17
./rig/db.sh schema       # alembic upgrade head (0107)
./rig/preflight.sh       # MUST pass before any run
```

## Why the preflight exists

The wholesaling Crexi scripts resolve their own database URL: `--db prod` →
`DATABASE_URL`, `--db dev` → `DEV_DATABASE_URL`, read from `os.environ` **first,
then falling back to parsing `backend/.env.local`** — which holds real Supabase
URLs. An unset variable is therefore not "safe default", it is "silently use
production". Separately `backend/.env` carries `R2_*`, and pydantic-settings
loads `.env` relative to CWD, so an `--apply` ingest would upload photos to the
**production R2 bucket**.

`rig/env.sh` exports both URL vars at localhost and every `R2_*` as empty (not
unset). `rig/preflight.sh` fails closed on either hazard, on an undeclared AI
arm, and on `ANTHROPIC_BASE_URL` leaking the experiment lane's z.ai routing into
the product's own AI calls. Both hazards were adversarially tested.

## Files

| Path | Role |
|---|---|
| `rig/env.sh` | hermetic environment; **source**, never execute |
| `rig/preflight.sh` | fail-closed safety gate |
| `rig/db.sh` | postgres lifecycle: `up/schema/down/nuke/snapshot/restore/psql` |
| `runs/` | run artifacts (per-listing JSONL + manifests) |
| `runs/snapshots/` | frozen DB dumps — the corpus of record |

## Finding: a fresh Postgres cannot run the migration chain unaided

`alembic upgrade head` against a clean Postgres dies at revision
`0052_source_health_coverage_ratio` — the id is **33 chars** and
`alembic_version.version_num` defaults to `VARCHAR(32)`, so Postgres raises
`StringDataRightTruncation` the instant Alembic stamps it. SQLite ignores
`VARCHAR` length, so the hermetic CI suite never sees it.

Every live environment was widened by hand (issue #960). That step is recorded
**only in the docstring of `backend/tests/test_alembic_migrations.py`** — no
script, no runbook, no migration performs it. Standing up a new environment
therefore requires tribal knowledge. `rig/db.sh schema` widens the column
explicitly before upgrading; a durable fix belongs in the product repo.
