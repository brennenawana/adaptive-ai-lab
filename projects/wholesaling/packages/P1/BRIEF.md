# Work Order P1 — Condition-instrument prerequisites (labels + prompt versioning)

Status: DRAFT (not yet authorized — do not execute)
Session model: Opus · effort high · one session, fresh context
Repo: ~/code/wholesaling · branch `feat/condition-eval-prereqs` off `origin/dev` · PR to `dev`
Stop point: PR-open (do NOT merge; acceptance gate is external)

## Standing rules (complete — do not seek other process docs)

- This brief is your complete task context. Do NOT read documents outside the
  wholesaling repo; do not follow links except code `path:line` references.
  If something you need is missing here, that is a defect in this brief:
  STOP and report it in your final message rather than exploring or guessing.
- Echo check before any code change: restate objective, non-goals, acceptance
  criteria, and your stop point in 3–6 lines.
- Wholesaling repo rules that apply: never push `main` or `dev` directly;
  feature branch → PR to `dev`; secret-scan before push; the hermetic pytest
  suite must stay green; Alembic migrations get the next free number and must
  be additive/nullable (no backfill of historical rows — their prompt version
  is genuinely unknown and must stay NULL).
- Scope changes are not yours to make. On spec-vs-code conflict: STOP, record
  it in RESULT.md, end the session.
- At session end, append your report to
  `~/code/adaptive-ai-lab/projects/wholesaling/packages/P1/RESULT.md` using
  §7's format, then stop.

## 1. Objective

Make the vision/condition surface's outputs attributable to a versioned
prompt, and make its golden labels an exportable, versionable corpus — so a
later evaluation can (a) tell which rubric produced any stored verdict and
(b) freeze a labeled corpus outside the database.

## 2. Why (compiled context)

The condition surface writes tier/confidence/repair-band onto properties and
clears a guardrail HOLD without human review, but today nothing records which
prompt/rubric produced a verdict: there is no version constant in any vision
prompt file and no version column on the analysis-request table. The one
benchmark run of this surface (49 properties) cannot be reproduced or compared
against, because a later commit rewrote the rubric and pre/post verdicts are
indistinguishable in the DB, and the golden labels exist only as DB rows. This
package adds the minimal provenance so future measurement is possible. It
deliberately changes NO model behavior, NO prompts' content, and NO defaults.

## 3. Non-goals

- No prompt/rubric content changes of any kind (versioning only).
- No re-running of any benchmark; no new golden labels.
- No changes to the xAI enrichment lane's triggering, the OpenRouter queue's
  defaults, or the HOLD-clearing logic.
- No backfill of `prompt_version` on existing rows (stays NULL = unknown).
- Do not fix unrelated stale docs beyond §4.4.

## 4. Spec

1. **Prompt version constants.** In the vision prompt module(s) (start at
   `backend/app/vision/prompt.py`; check for prompt text also used by
   `backend/app/services/condition_analysis.py` and
   `backend/app/vision/bench/reduce.py`), add a module-level
   `PROMPT_VERSION` string (e.g. `"cv-2"`) per distinct prompt family
   (screen/assess vs reduce/merge), colocated with the prompt text, with a
   one-line comment stating the rule: any semantic edit to the prompt text
   bumps the version in the same commit.
2. **Persist it.** Add nullable `prompt_version` (String) to the
   condition-analysis request model (`backend/app/db/models.py` — the
   `condition_analysis_request` table, around lines 1219–1249) via a new
   Alembic migration (next free number). Write the current constant into
   every NEW row at each write site (find them in
   `backend/app/services/condition_analysis.py` and the bench code under
   `backend/app/vision/bench/`).
3. **Label export.** Add a CLI entry point (pattern-match the existing
   `python -m app.vision.bench` module conventions) that dumps all
   `vision_golden_label` rows (`backend/app/vision/bench/store.py:31`;
   fields per `runner.py:51`: property_id, tier, repair_low, repair_high —
   verify actual columns in the model) to a deterministic, sorted JSON file
   (stable key order, one schema-version field, no timestamps) suitable for
   committing. Do NOT commit a dump produced against any real DB; commit only
   the exporter + a unit test using a seeded in-memory/session DB.
4. **Doc touch-up (bounded).** In `Docs/IMAGE_ANALYSIS.md`, correct the
   stated default image config to match `settings.py` (`grid_512_3x3`) and
   document the new `PROMPT_VERSION` rule. No other doc edits.

## 5. Acceptance criteria (agent-checkable)

1. Full hermetic backend test suite green.
2. New/updated tests prove: (a) a condition-analysis request row written
   through the service carries the current `PROMPT_VERSION`; (b) the exporter
   produces byte-identical output for the same seeded labels across two runs.
3. Alembic migration up-head applies cleanly on a fresh test DB (however the
   existing migration tests exercise this — follow the repo's pattern).
4. `git grep -n "PROMPT_VERSION"` shows the constant(s) colocated with prompt
   text and referenced at every write site found in §4.2.
5. PR open against `dev`, body citing "Work Order P1"; not merged.

## 6. Verification commands

```bash
cd ~/code/wholesaling/backend && python -m pytest -q          # or the repo's documented invocation
git grep -n "PROMPT_VERSION" -- backend/app | sort
```

## 7. RESULT.md format

```markdown
## P1 result — <date>
- Branch / PR: <branch> / #<PR>
- Spec deviations: <none | list, with reasons>
- Acceptance output: <pasted raw>
- Discovered en route (not acted on): <list>
- Stopped at: <stop point honored>
```

---
Provenance (do not read — for audit only):
adaptive-ai-lab/projects/wholesaling/AI_SYSTEM_INVENTORY.md §2 (instrument
defects), PLAYBOOK_PATH.md §4 action 1, INTEGRATION_AND_FEEDBACK.md P1.
