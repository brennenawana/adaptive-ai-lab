-- FIS domain model.
--
-- Two deliberate deviations from the guide's §13 table, both for eval integrity:
--
-- 1. The guide lists `injected_root_cause` as a field on Case. It is NOT here.
--    A case row is model-visible through get_case; storing the answer there would
--    let the investigator read the label instead of deriving it. Root cause lives
--    in ground_truth.scenario_manifest, which no tool can reach.
--
-- 2. Every entity carries BOTH a provider-native id and a normalized internal id.
--    Cross-system id mapping is a realistic source of operational error and, per
--    the guide, makes for good evaluation scenarios — S09 depends on it.

-- ======================================================================== customer
CREATE TABLE customer.customers (
    customer_id      text PRIMARY KEY,
    display_name     text NOT NULL,
    dob              date NOT NULL,
    country          text NOT NULL,
    onboarding_state text NOT NULL CHECK (onboarding_state IN
                       ('applied','kyc_pending','kyc_failed','active','restricted','closed')),
    created_at       timestamptz NOT NULL,
    scenario_id      text NOT NULL
);
CREATE INDEX ON customer.customers (scenario_id);

-- ======================================================================== identity
CREATE TABLE identity.verifications (
    verification_id     text PRIMARY KEY,
    provider_ref        text NOT NULL,          -- vendor-native id
    customer_id         text NOT NULL REFERENCES customer.customers(customer_id),
    vendor              text NOT NULL,
    check_type          text NOT NULL CHECK (check_type IN
                          ('document','liveness','sanctions','address','pep')),
    status              text NOT NULL CHECK (status IN
                          ('pending','approved','failed','expired','vendor_timeout')),
    reason_code         text,
    event_time          timestamptz NOT NULL,
    scenario_id         text NOT NULL
);
CREATE INDEX ON identity.verifications (customer_id);
CREATE INDEX ON identity.verifications (scenario_id);

-- ========================================================================== ledger
CREATE TABLE ledger.accounts (
    account_id        text PRIMARY KEY,
    customer_id       text NOT NULL REFERENCES customer.customers(customer_id),
    status            text NOT NULL CHECK (status IN ('pending','active','restricted','closed')),
    currency          char(3) NOT NULL,
    available_balance bigint NOT NULL,   -- minor units. never floats for money.
    ledger_balance    bigint NOT NULL,
    opened_at         timestamptz NOT NULL,
    scenario_id       text NOT NULL
);
CREATE INDEX ON ledger.accounts (customer_id);

CREATE TABLE ledger.entries (
    entry_id       text PRIMARY KEY,
    account_id     text NOT NULL REFERENCES ledger.accounts(account_id),
    direction      text NOT NULL CHECK (direction IN ('debit','credit')),
    amount         bigint NOT NULL CHECK (amount > 0),
    currency       char(3) NOT NULL,
    reference_type text NOT NULL CHECK (reference_type IN
                     ('authorization','settlement','reversal','fee','adjustment')),
    reference_id   text,
    posted_at      timestamptz NOT NULL,
    scenario_id    text NOT NULL
);
CREATE INDEX ON ledger.entries (account_id, posted_at);
CREATE INDEX ON ledger.entries (reference_id);

-- ======================================================================= processor
CREATE TABLE processor.cards (
    card_id     text PRIMARY KEY,
    provider_ref text NOT NULL,
    customer_id text NOT NULL REFERENCES customer.customers(customer_id),
    account_id  text NOT NULL REFERENCES ledger.accounts(account_id),
    status      text NOT NULL CHECK (status IN ('not_issued','active','frozen','cancelled')),
    pan_token   text NOT NULL,            -- placeholder token, never a real PAN
    issued_at   timestamptz,
    scenario_id text NOT NULL
);

CREATE TABLE processor.authorizations (
    auth_id         text PRIMARY KEY,
    provider_ref    text NOT NULL,
    card_id         text NOT NULL REFERENCES processor.cards(card_id),
    amount          bigint NOT NULL,
    currency        char(3) NOT NULL,
    merchant        text NOT NULL,
    mcc             text,
    processor_state text NOT NULL CHECK (processor_state IN
                      ('approved','declined','reversed','settled','expired')),
    decline_code    text,
    authorized_at   timestamptz NOT NULL,
    reversed_at     timestamptz,
    scenario_id     text NOT NULL
);
CREATE INDEX ON processor.authorizations (card_id, authorized_at);

CREATE TABLE processor.settlements (
    settlement_id text PRIMARY KEY,
    provider_ref  text NOT NULL,
    auth_id       text REFERENCES processor.authorizations(auth_id),
    amount        bigint NOT NULL,
    currency      char(3) NOT NULL,
    settled_at    timestamptz NOT NULL,
    scenario_id   text NOT NULL
);
CREATE INDEX ON processor.settlements (auth_id);

-- ============================================================================ risk
CREATE TABLE risk.alerts (
    alert_id       text PRIMARY KEY,
    customer_id    text NOT NULL REFERENCES customer.customers(customer_id),
    transaction_id text,
    rule_code      text NOT NULL,
    severity       text NOT NULL CHECK (severity IN ('low','medium','high','critical')),
    status         text NOT NULL CHECK (status IN ('open','investigating','cleared','confirmed')),
    raised_at      timestamptz NOT NULL,
    scenario_id    text NOT NULL
);
CREATE INDEX ON risk.alerts (customer_id);

-- ========================================================================= webhook
CREATE TABLE webhook.deliveries (
    delivery_id       text PRIMARY KEY,
    provider_event_id text NOT NULL,       -- NOT unique: duplicate delivery is S01/S02
    event_type        text NOT NULL,
    payload_hash      text NOT NULL,
    idempotency_key   text,                -- absent in S02, by design
    attempt           int  NOT NULL CHECK (attempt >= 1),
    status            text NOT NULL CHECK (status IN
                        ('received','processed','deduplicated','failed','retrying')),
    received_at       timestamptz NOT NULL,
    scenario_id       text NOT NULL
);
CREATE INDEX ON webhook.deliveries (provider_event_id);

-- ===================================================================== integration
CREATE TABLE integration.events (
    event_id          text PRIMARY KEY,
    provider_event_id text NOT NULL,
    delivery_id       text REFERENCES webhook.deliveries(delivery_id),
    normalized_type   text NOT NULL,
    mapping_version   int  NOT NULL,
    raw_payload       jsonb NOT NULL,      -- what the provider actually sent
    normalized_state  text NOT NULL,       -- what we turned it into. S09 diverges here.
    created_at        timestamptz NOT NULL,
    scenario_id       text NOT NULL
);
CREATE INDEX ON integration.events (provider_event_id);

-- =========================================================================== cases
-- Model-visible. Deliberately contains NO root cause.
CREATE TABLE cases.cases (
    case_id      text PRIMARY KEY,
    category     text NOT NULL,
    subject_ids  jsonb NOT NULL DEFAULT '{}'::jsonb,
    summary      text NOT NULL,
    status       text NOT NULL CHECK (status IN ('open','investigating','resolved','closed')),
    opened_at    timestamptz NOT NULL,
    scenario_id  text NOT NULL
);
CREATE INDEX ON cases.cases (scenario_id);

-- ======================================================================= knowledge
CREATE TABLE knowledge.documents (
    document_id text PRIMARY KEY,
    version     text NOT NULL,
    doc_type    text NOT NULL CHECK (doc_type IN ('runbook','policy','escalation_rule')),
    title       text NOT NULL,
    body        text NOT NULL,
    categories  text[] NOT NULL DEFAULT '{}',
    embedding   vector(1024)
);

-- ==================================================================== ground_truth
-- The answer key. No tool in the broker may route here — enforced in code by
-- ToolDefinition.forbidden_schemas, and by this schema having no service that owns it.
CREATE TABLE ground_truth.scenario_manifests (
    scenario_id             text PRIMARY KEY,
    seed                    bigint NOT NULL,
    split                   text NOT NULL CHECK (split IN ('train','dev','test')),
    category                text NOT NULL,
    root_cause              text NOT NULL,
    required_evidence       text[] NOT NULL,
    acceptable_next_actions text[] NOT NULL,
    forbidden_claims        text[] NOT NULL DEFAULT '{}',
    distractor_event_ids    text[] NOT NULL DEFAULT '{}',
    case_id                 text NOT NULL,
    subject_ids             jsonb NOT NULL DEFAULT '{}'::jsonb,
    generated_at            timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON ground_truth.scenario_manifests (split);
CREATE INDEX ON ground_truth.scenario_manifests (category);

-- ======================================================================== learning
CREATE TABLE learning.trajectories (
    trace_id        uuid PRIMARY KEY,
    scenario_id     text,
    case_id         text,
    experiment_arm  text,
    workflow        text NOT NULL,
    workflow_version text NOT NULL,
    payload         jsonb NOT NULL,        -- full Trajectory model
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON learning.trajectories (scenario_id);
CREATE INDEX ON learning.trajectories (experiment_arm);

CREATE TABLE learning.case_scores (
    id             bigserial PRIMARY KEY,
    run_id         text NOT NULL,
    scenario_id    text NOT NULL,
    trace_id       uuid,
    experiment_arm text NOT NULL,
    payload        jsonb NOT NULL,         -- full CaseScore model
    all_pass       boolean NOT NULL,
    created_at     timestamptz NOT NULL DEFAULT now(),
    UNIQUE (run_id, scenario_id)           -- makes the eval runner idempotent on resume
);
CREATE INDEX ON learning.case_scores (run_id);
