-- Defence in depth for the answer key.
--
-- ToolDefinition.forbidden_schemas already blocks ground_truth in Python. That is a
-- code-level check, and code-level checks are one bad refactor from silently failing.
-- This adds a database-level one: the role the tool broker connects as is never
-- granted USAGE on ground_truth, so a leak requires defeating BOTH layers.
--
-- The eval scorer connects as the owner (fis) and can read the manifests. The
-- investigator's tools cannot, whatever SQL they end up executing.

CREATE ROLE fis_tools LOGIN PASSWORD 'fis_tools_local_dev';

-- Read-only across the model-visible service schemas.
GRANT USAGE ON SCHEMA customer, identity, ledger, processor, risk, webhook,
                      integration, cases, knowledge TO fis_tools;

GRANT SELECT ON ALL TABLES IN SCHEMA customer, identity, ledger, processor, risk,
                                    webhook, integration, cases, knowledge TO fis_tools;

-- Tables created later must inherit the same grant, or a new service silently
-- becomes invisible to the broker.
ALTER DEFAULT PRIVILEGES IN SCHEMA customer, identity, ledger, processor, risk,
                                   webhook, integration, cases, knowledge
    GRANT SELECT ON TABLES TO fis_tools;

-- Explicitly NOT granted, stated for the reader rather than because it is required
-- (no grant exists by default):
REVOKE ALL ON SCHEMA ground_truth FROM fis_tools;
REVOKE ALL ON ALL TABLES IN SCHEMA ground_truth FROM fis_tools;
REVOKE ALL ON SCHEMA learning FROM fis_tools;
REVOKE ALL ON ALL TABLES IN SCHEMA learning FROM fis_tools;

-- Read-only at the connection level too: even a mistaken INSERT fails.
ALTER ROLE fis_tools SET default_transaction_read_only = on;
