-- Routing-decision telemetry (R5, contract § 15).
--
-- One row per routing decision a policy made about a local answer — offline replay
-- (DEV; TEST at unlock) now, live cascade later. Deliberately holds NOTHING the scorer
-- knows: no gold, no outcome, no split, no class. Outcomes are joined afterwards in the
-- analysis layer on (run_id, scenario_id) / trace_id. `production_observable_only`
-- is asserted true by the writer; a future policy that reads anything else must say
-- so here, in a column a query can filter on.

CREATE TABLE IF NOT EXISTS learning.routing_decisions (
    id                        bigserial PRIMARY KEY,
    routing_policy            text NOT NULL,   -- e.g. 'r4-verifier', 'r5-qwen-lr_full-v1'
    local_model               text NOT NULL,   -- canonical local model the answer came from
    router_artifact_digest    text,            -- sha256 of the frozen artifact; NULL for R4
    feature_schema_version    text,            -- RoutingFeatureSnapshot schema; NULL for R4
    feature_snapshot_digest   text,            -- sha256 of the canonical snapshot
    risk_score                double precision,
    threshold                 double precision,
    decision                  text NOT NULL CHECK (decision IN ('local', 'escalate')),
    r4_decision               text NOT NULL CHECK (r4_decision IN ('local', 'escalate')),
    production_observable_only boolean NOT NULL DEFAULT true,
    run_id                    text NOT NULL,   -- the local run replayed / lived
    scenario_id               text NOT NULL,   -- join key only; never a feature
    trace_id                  uuid,
    replay                    boolean NOT NULL DEFAULT true,
    created_at                timestamptz NOT NULL DEFAULT now(),
    UNIQUE (routing_policy, run_id, scenario_id)
);

CREATE INDEX IF NOT EXISTS routing_decisions_policy_idx ON learning.routing_decisions (routing_policy, run_id);

COMMENT ON TABLE learning.routing_decisions IS
    'Routing decisions (R5+). Production-observable inputs only; gold/outcomes join later.';
