-- The investigator's answer body, kept beside its trajectory (R5).
--
-- Every run before R5 persisted the trajectory (tool calls, invocations, verifier
-- verdict) and the score, and only a sha256 of the model's text — so the answer's
-- own structure (facts, cited ids, hypotheses, confidence) was unrecoverable after
-- the fact for the frozen Suite v3 DEV/TEST arms. Learned routing over
-- production-observable answer features needs the answer; from R5's TRAIN
-- acquisition onward the parsed InvestigationResult is stored here.
--
-- Not a suite change: nothing here is read by the scorer, the verifier, the
-- generator or the model. The eval runner writes it best-effort after scoring.
-- Rows exist only for cases that produced a schema-valid object.

CREATE TABLE IF NOT EXISTS learning.model_outputs (
    trace_id     uuid PRIMARY KEY REFERENCES learning.trajectories(trace_id),
    run_id       text NOT NULL,
    scenario_id  text NOT NULL,
    output       jsonb NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS model_outputs_run_idx ON learning.model_outputs (run_id);

COMMENT ON TABLE learning.model_outputs IS
    'Parsed InvestigationResult per trajectory (R5+). Absent for pre-R5 runs and for no-output cases.';
