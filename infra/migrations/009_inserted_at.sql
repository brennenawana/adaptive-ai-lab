-- inserted_at: a statement-time write timestamp, correcting the transaction-frozen
-- `now()` defect (R6 autopsy §13 DB row, NEXT_STEP_M0.md §6-D,
-- docs/current/M_STAT_IMPLEMENTATION_MAP.md §14).
--
-- learning.trajectories, learning.case_scores, learning.model_outputs and
-- learning.routing_decisions all stamp `created_at timestamptz NOT NULL DEFAULT now()`.
-- Postgres resolves `now()` to `transaction_timestamp()` — frozen once, at the start of
-- the enclosing transaction — not re-evaluated per statement. A transaction that inserts
-- several rows over real elapsed time (or is itself part of a longer-running write path)
-- gives every one of those rows the SAME created_at regardless of the order they were
-- actually written in: the observed symptom was case 1's created_at predating its own
-- insert. `clock_timestamp()` is the non-transaction-frozen wall clock (re-evaluated on
-- every call), which is what an honest "when was this row written" field needs.
--
-- `created_at` is left untouched — other code and historical reports read it, and
-- silently redefining its semantics after the fact is exactly what the R-series
-- provenance discipline exists to prevent. `inserted_at` is a new, additive column.
--
-- Ordering is load-bearing, and is two SEPARATE statements per table:
--   1. ADD COLUMN IF NOT EXISTS inserted_at timestamptz     -- NULLABLE, NO DEFAULT
--   2. ALTER COLUMN inserted_at SET DEFAULT clock_timestamp()   -- AFTERWARDS
-- Putting a volatile default (clock_timestamp()) directly inside ADD COLUMN would have
-- Postgres evaluate it ONCE and backfill that single value onto every existing row as of
-- migration time — stamping every historical row with "when this migration ran" under a
-- column named "when this row was inserted". That is forbidden here: historical rows
-- must stay inserted_at IS NULL forever, meaning "not recorded". Doing the SET DEFAULT
-- as a second statement, after the column already exists (NULL on every existing row),
-- means the default applies only to rows inserted from this point forward.
--
-- Idempotent: IF NOT EXISTS guards the ADD COLUMN, and SET DEFAULT is safe to re-run
-- (it just re-sets the same default). No backfill of existing rows, ever.

ALTER TABLE learning.trajectories
    ADD COLUMN IF NOT EXISTS inserted_at timestamptz;
ALTER TABLE learning.trajectories
    ALTER COLUMN inserted_at SET DEFAULT clock_timestamp();

ALTER TABLE learning.case_scores
    ADD COLUMN IF NOT EXISTS inserted_at timestamptz;
ALTER TABLE learning.case_scores
    ALTER COLUMN inserted_at SET DEFAULT clock_timestamp();

ALTER TABLE learning.model_outputs
    ADD COLUMN IF NOT EXISTS inserted_at timestamptz;
ALTER TABLE learning.model_outputs
    ALTER COLUMN inserted_at SET DEFAULT clock_timestamp();

ALTER TABLE learning.routing_decisions
    ADD COLUMN IF NOT EXISTS inserted_at timestamptz;
ALTER TABLE learning.routing_decisions
    ALTER COLUMN inserted_at SET DEFAULT clock_timestamp();

COMMENT ON COLUMN learning.trajectories.inserted_at IS
    'Statement-time (clock_timestamp()) row-write timestamp, added by migration 009. '
    'NULL on every row written before this migration ran (historical = not recorded, '
    'never backfilled). created_at is transaction-frozen (now()) and unaffected.';
COMMENT ON COLUMN learning.case_scores.inserted_at IS
    'Statement-time (clock_timestamp()) row-write timestamp, added by migration 009. '
    'NULL on every row written before this migration ran (historical = not recorded, '
    'never backfilled). created_at is transaction-frozen (now()) and unaffected.';
COMMENT ON COLUMN learning.model_outputs.inserted_at IS
    'Statement-time (clock_timestamp()) row-write timestamp, added by migration 009. '
    'NULL on every row written before this migration ran (historical = not recorded, '
    'never backfilled). created_at is transaction-frozen (now()) and unaffected.';
COMMENT ON COLUMN learning.routing_decisions.inserted_at IS
    'Statement-time (clock_timestamp()) row-write timestamp, added by migration 009. '
    'NULL on every row written before this migration ran (historical = not recorded, '
    'never backfilled). created_at is transaction-frozen (now()) and unaffected.';
