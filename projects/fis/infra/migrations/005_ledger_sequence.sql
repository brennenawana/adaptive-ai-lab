-- Monotonic posting sequence.
--
-- Real ledgers separate two orderings and so must we:
--   posting_seq  the order entries were written. Immutable, monotonic, and the
--                order an operator sees when reading the account.
--   posted_at    when the underlying event actually occurred (value date).
--
-- An out-of-order arrival makes these disagree: an entry with a LOWER posted_at
-- than its predecessor but a HIGHER posting_seq. That divergence IS the S07
-- reversal-race hazard — nothing is lost, but reading in posting order misleads.
--
-- Detecting it previously ordered by entry_id, which is a random uuid hex and
-- therefore not an ordering at all. The test caught it.

ALTER TABLE ledger.entries
    ADD COLUMN IF NOT EXISTS posting_seq bigserial;

CREATE INDEX IF NOT EXISTS entries_account_seq_idx
    ON ledger.entries (account_id, posting_seq);

COMMENT ON COLUMN ledger.entries.posting_seq IS
    'Insertion order. Compare against posted_at to detect out-of-order arrival.';
