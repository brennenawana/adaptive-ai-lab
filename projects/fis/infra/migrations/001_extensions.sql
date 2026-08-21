-- Runs once, on first container init (docker-entrypoint-initdb.d).
-- Knowledge memory (runbook/policy retrieval) uses pgvector per the
-- Canonical Architecture: "PostgreSQL + pgvector rather than introducing
-- a dedicated vector database."

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid() for trace_ids

-- Schema-per-service keeps service ownership visible in code while still
-- running a single Postgres, as the guide recommends for the learning project.
CREATE SCHEMA IF NOT EXISTS customer;
CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS processor;
CREATE SCHEMA IF NOT EXISTS ledger;
CREATE SCHEMA IF NOT EXISTS risk;
CREATE SCHEMA IF NOT EXISTS webhook;
CREATE SCHEMA IF NOT EXISTS integration;
CREATE SCHEMA IF NOT EXISTS cases;
CREATE SCHEMA IF NOT EXISTS knowledge;

-- Learning plane: the canonical trajectory store lives in our own schema,
-- never only in an observability UI.
CREATE SCHEMA IF NOT EXISTS learning;

-- Ground truth is deliberately isolated. The AI's tools must never be able
-- to reach this schema — it is the answer key for the eval harness only.
CREATE SCHEMA IF NOT EXISTS ground_truth;

DO $$
BEGIN
  RAISE NOTICE 'FIS extensions and schemas initialised';
END $$;
