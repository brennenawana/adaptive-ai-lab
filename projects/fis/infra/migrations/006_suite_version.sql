-- Suite identity on the rows that need it (Suite v3, contract § 2E).
--
-- Scenario ids are seed-derived and identical across suite versions, so nothing in
-- the schema said which corpus a manifest belonged to or which suite a score was
-- measured against: a v2 score row would silently join a v3 manifest, and the only
-- non-comparability marker was a hard-coded run-id set in compare.py.
--
-- Backfill, fixed at migration time: the four suite-1 run ids (fis_platform/suite.py
-- SUITE_V1_RUNS) are '1'; every other score row that exists before this migration was
-- measured on suite 2; the manifests in the database at that point are the suite-2
-- corpus. Rows written afterwards carry their version from code. Idempotent: the
-- UPDATEs touch NULLs only, and no code path writes a NULL.

ALTER TABLE ground_truth.scenario_manifests
    ADD COLUMN IF NOT EXISTS suite_version text;

ALTER TABLE learning.case_scores
    ADD COLUMN IF NOT EXISTS suite_version text;

UPDATE learning.case_scores
   SET suite_version = '1'
 WHERE suite_version IS NULL
   AND run_id IN ('E2-local-96', 'E2-local-specialist-test',
                  'E4-claude-frontier-test', 'SMOKE-local-specialist-dev');

UPDATE learning.case_scores
   SET suite_version = '2'
 WHERE suite_version IS NULL;

UPDATE ground_truth.scenario_manifests
   SET suite_version = '2'
 WHERE suite_version IS NULL;

CREATE INDEX IF NOT EXISTS case_scores_suite_run_idx
    ON learning.case_scores (suite_version, run_id);

COMMENT ON COLUMN learning.case_scores.suite_version IS
    'Eval suite the score was measured against. Never compare across values.';
COMMENT ON COLUMN ground_truth.scenario_manifests.suite_version IS
    'Suite the corpus was generated for; the runner refuses a corpus/code mismatch.';
