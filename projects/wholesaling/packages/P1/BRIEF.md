# Work Order P1 — Condition-instrument prerequisites (labels + prompt versioning)

Status: DRAFT (not yet authorized — do not execute)
Session model: Opus · effort high · one session, fresh context
Repo: ~/code/wholesaling · branch `feat/condition-eval-prereqs` off `origin/dev` · PR to `dev`
Stop point: PR-open (do NOT merge; the acceptance gate is external to this session)

All code references below were verified against `origin/dev` on 2026-08-25.

## Standing rules (complete — do not seek other process docs)

- This brief is your complete task context. Do NOT read documents outside the
  wholesaling repo; do not follow links except code `path:line` references.
  If something you need is missing here, that is a defect in this brief:
  STOP and report it in your final message rather than exploring or guessing.
- Echo check before any code change: restate objective, non-goals, acceptance
  criteria, and your stop point in 3–6 lines.
- Wholesaling repo rules that apply: never push `main` or `dev` directly;
  feature branch → PR to `dev`; secret-scan before push; the hermetic pytest
  suite must stay green; the new Alembic migration is `0108` (current head is
  `0107_comm_fact_homes`) and must be additive/nullable — **no backfill of
  historical rows**, whose prompt version is genuinely unknown and must stay
  NULL.
- Scope changes are not yours to make. On spec-vs-code conflict: STOP, record
  it in RESULT.md, end the session.
- At session end, append your report to
  `~/code/adaptive-ai-lab/projects/wholesaling/packages/P1/RESULT.md` using
  §7's format, then stop. Do not self-assess the acceptance gate; do not begin
  any other work.

## 1. Objective

Make the vision/condition surface's outputs attributable to a versioned
prompt, and make its golden labels exportable as a deterministic, committable
corpus — so a later evaluation can (a) tell which rubric produced any stored
verdict and (b) freeze a labeled corpus outside the database.

## 2. Why (compiled context — everything you need to know)

The condition surface writes tier/confidence/repair-band onto properties and
clears a guardrail HOLD **without human review**, but nothing records which
prompt produced a verdict: no version constant exists in any vision prompt
module, and `condition_analysis_request` has no version column. The one
benchmark run of this surface (49 properties) is therefore unreproducible — a
later commit rewrote the rubric, and pre- and post-rewrite verdicts are
indistinguishable in the database. The golden labels that would anchor any
re-measurement exist only as DB rows with no export path. This package adds
the minimal provenance to make future measurement possible. It changes **no
model behavior, no prompt content, and no defaults**.

## 3. Non-goals

- No changes to prompt/rubric *content* of any kind — versioning only.
- No re-running of any benchmark; no new or edited golden labels.
- No changes to the xAI enrichment lane's triggering, the condition queue's
  model/config defaults, or the HOLD-clearing logic.
- No backfill of `prompt_version` on existing rows.
- No unrelated doc fixes beyond §4.4.
- Do not confuse this with the existing, unrelated `prompt_version` column on
  the CIS `intake_proposal` table (`backend/app/db/models.py:1394`).

## 4. Spec

**4.1 Prompt version constants.** Three distinct prompt families exist; give
each its own module-level constant, colocated with its prompt text, plus a
one-line comment stating the rule *"any semantic edit to this prompt text
bumps this constant in the same commit"*:

| File | Prompt | Constant to add |
|---|---|---|
| `backend/app/vision/prompt.py` (`SYSTEM_PROMPT` :20-44, `USER_TEXT` :46-49) | single-pass screen/assess, used by `condition_vision.py` | `PROMPT_VERSION` |
| `backend/app/vision/bench/extended.py:201` (`SYSTEM_PROMPT`) | per-batch map rubric, used by `bench/runner.py:171` | `PROMPT_VERSION` |
| `backend/app/vision/bench/reduce.py:50` (`REDUCE_SYSTEM_PROMPT`, user text built at `:92`) | reduce/merge | `REDUCE_PROMPT_VERSION` |

Use simple opaque strings (e.g. `"screen-1"`, `"map-1"`, `"reduce-1"`). Note
`backend/app/services/condition_analysis.py` defines **no** prompt text — it
orchestrates the queue and calls the bench engine; do not add a constant there.

**4.2 Persist the version.** Add nullable `prompt_version` (String) to
`ConditionAnalysisRequestORM` (`backend/app/db/models.py:1181-1279`) via
migration `0108`. There is exactly **one** write site:
`backend/app/services/condition_analysis.py:271` (`ConditionAnalysisRequestORM(...)`
followed by `session.add`/`session.flush`). Populate it there with a composite
of the versions actually in force for that run (e.g.
`"map-1+reduce-1"` for the batched path) — derive it from the constants, never
hardcode a literal at the write site.

**4.3 Label export.** Add a deterministic exporter for `VisionGoldenLabelORM`
(`backend/app/db/models.py:2608-2627`; columns `property_id, tier, repair_low,
repair_high, labeled_by, notes, created_at, updated_at`). Existing store API
for reference: `backend/app/vision/bench/store.py` — `labels_from_db:30`,
`list_labels:373`, `label_to_dict:379` (these build in-memory dicts for the
dashboard; **no file export exists anywhere**). Requirements: output JSON
sorted by `property_id`, stable key order, one `schema_version` field, and
**no timestamps or `labeled_by` in the payload** (they make output
non-deterministic and add no evaluation value). Expose it the way the bench
CLI is already exposed (`python -m app.vision.bench` conventions). **Commit
the exporter and its test only — never a dump produced from a real database.**

**4.4 Doc correction (bounded).** `Docs/IMAGE_ANALYSIS.md:220-222` states the
`CONDITION_ANALYSIS_IMAGE_CONFIG` default as `singles_768`; the shipped
default is `grid_512_3x3` (`backend/app/config/settings.py:1732-1733`).
Correct that line and add a short note documenting the §4.1 versioning rule.
Nothing else in that file.

## 5. Acceptance criteria (agent-checkable)

1. `python -m pytest -q -n auto` green from `backend/`, and
   `python -m ruff check .` clean.
2. New tests prove: (a) a row written through
   `services/condition_analysis.py`'s enqueue path carries a non-null
   `prompt_version` derived from the constants; (b) the exporter produces
   byte-identical output across two runs over the same seeded labels.
3. Migration `0108` applies cleanly on a fresh test DB, following whatever
   pattern existing migration tests use.
4. `git grep -n "PROMPT_VERSION" -- backend/app` shows the three constants at
   their prompt sites plus the single write-site reference.
5. PR open against `dev` citing "Work Order P1"; **not merged**.

## 6. Verification commands

```bash
cd ~/code/wholesaling/backend
python -m ruff check .
python -m pytest -q -n auto
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
adaptive-ai-lab/projects/wholesaling/AI_SYSTEM_INVENTORY.md §2,
PLAYBOOK_PATH.md §4 action 1, INTEGRATION_AND_FEEDBACK.md P1.
