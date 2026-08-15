-- Dedupe ledger for the integration consumer.
--
-- This table is what makes S01 vs S02 a real behavioural difference rather than
-- two hand-written row sets: with a safe idempotency key the consumer can prove a
-- redelivery and skip it; without one it cannot, and processes the event twice.
--
-- Deliberately NOT keyed on provider_event_id alone. A provider may legitimately
-- reuse an event id for a retry AND for a genuine second occurrence; treating them
-- as the same thing would paper over exactly the ambiguity S02 is about.

CREATE TABLE IF NOT EXISTS integration.dedupe_ledger (
    dedupe_key        text PRIMARY KEY,
    provider_event_id text NOT NULL,
    scenario_id       text NOT NULL,
    first_seen_at     timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS dedupe_ledger_scenario_idx
    ON integration.dedupe_ledger (scenario_id);

-- The tool role must be able to read it: "was this deduplicated?" is legitimate
-- investigative evidence, and get_webhook_history should be able to show it.
GRANT SELECT ON integration.dedupe_ledger TO fis_tools;
