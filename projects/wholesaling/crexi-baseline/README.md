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

## The guard rule: assert the OUTCOME, never the inputs

The first version of this preflight **passed while the hazard was live**. It
checked that every `R2_*` was "exported empty" and printed
`PASS  photo mirror inert`. Measured reality:

| CWD | `R2_BUCKET` env | `settings.r2_bucket` | mirror enabled |
|---|---|---|---|
| `backend/` | `""` (exported empty) | `'media'` | **True** |
| `backend/` | unset | `'media'` | **True** |
| elsewhere (no `.env`) | unset | `None` | **False** |

`Settings` sets `env_ignore_empty=True` (`settings.py:124`), so an empty env var
reads as *unset* and `backend/.env` supplies the production bucket anyway. The
only thing that neutralizes the mirror is **a CWD with no `.env` adjacent**.

That is the same fail-open shape as the 2026-08-12 voice incident — a check
printing SAFE one line above a live override. So every check in `preflight.py`
now resolves the **real object the product code will use**
(`build_crexi_mirror(settings).enabled`, `providers_for(AiTask(kind=extract))`,
`scripts.crexi_ingest._db_url`) rather than inspecting the environment that is
supposed to produce it.

`preflight.sh.RETIRED` is kept as the specimen.

## Why the preflight exists

The wholesaling Crexi scripts resolve their own database URL: `--db prod` →
`DATABASE_URL`, `--db dev` → `DEV_DATABASE_URL`, read from `os.environ` **first,
then falling back to parsing `backend/.env.local`** — which holds real Supabase
URLs. An unset variable is therefore not "safe default", it is "silently use
production". Separately `backend/.env` carries `R2_*`, and pydantic-settings
loads `.env` relative to CWD, so an `--apply` ingest would upload photos to the
**production R2 bucket**.

`rig/env.sh` points **both** URL vars at the rig (so `--db prod` and `--db dev`
are equally harmless — the flag becomes semantically inert) and runs everything
from `runs/work`, a directory with no `.env`.

**Host is not proof of locality on this machine.** An ssh tunnel listens on
`127.0.0.1:25432` and forwards to a remote Postgres, so the gate requires
host **+ port + database + an in-DB `rig_marker` sentinel** that prod and dev do
not have.

### Adversarial verification (all three previously slipped through)

| Test | Result |
|---|---|
| Arm B declared | discriminates — `providers_for(extract)=['claude_sdk']` |
| `DATABASE_URL` → the ssh tunnel `127.0.0.1:25432` | **FAIL** on port; the connection reached a *real remote Postgres* that rejected our password |
| Run from `backend/` (where `.env` lives) | **FAIL** — `r2_bucket='media'`, mirror would have been live |

## Files

| Path | Role |
|---|---|
| `rig/env.sh` | hermetic environment; **source**, never execute |
| `rig/preflight.sh` | fail-closed safety gate |
| `rig/db.sh` | postgres lifecycle: `up/schema/down/nuke/snapshot/restore/psql` |
| `rig/run.sh` | **the only sanctioned way to invoke anything** (preflight + exec, one CWD) |
| `rig/trace.py` | per-listing seam capture -> one JSONL record + its provenance ledger |
| `rig/provenance.py` | the ledger model, its derivation, and the producer-mix aggregate |
| `rig/defects.py` | stable defect-class registry (F-B1…F-B8) |
| `rig/cassette.py` | record/replay for both non-deterministic boundaries: Crexi HTTP + the LLM |
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
