# Wholesaling Playbook Instantiation — Process Log

> APPEND-ONLY. Task-specific log of how the Adaptive AI Systems Playbook is being
> instantiated for the wholesaling project (`~/code/wholesaling`,
> `Thrasher66099/wholesaling`). New entries go at the bottom; existing entries are
> never edited. Each entry records what was done, key decisions, and summaries of
> subagent delegations.

---

## 2026-08-22 — Session 1: orientation, prerequisites, intake kickoff

**Operator request.** Understand the playbook at a high level, check its
prerequisites, execute the first two or three high-level tasks against the
wholesaling project, delegating to Haiku/Sonnet/Opus subagents by complexity.
Work on a branch (`project/wholesaling-intake`), commit/push at checkpoints,
keep this append-only log, and create + invoke a `/goal` prompt to establish a
goal session.

**Orchestrator's playbook understanding (read directly, not delegated).** Read
`playbook/README.md`, `QUICKSTART.md`, `00_PRINCIPLES_AND_SCOPE.md`,
`01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md`, `templates/PROJECT_PROFILE.md`,
`docs/LAB_CHARTER.md`, and both existing instantiations (`projects/fis/`
mature, `projects/millwork-estimating/` early-stage). Distilled spine:

1. Fill the 21-field PROJECT_PROFILE (fields 3, 4, 6, 19, 21 always mandatory).
2. Set the rigor tier from consequence (Tier 2 is the default for anything a
   business decision rides on; tier attaches to the *decision*, not the project).
3. Route to an archetype via QUICKSTART's decision tree (facts, not vibes);
   node 1 pre-check: no trusted eval → "eval first" whatever the letter.
4. Execute the archetype's first three actions; the first sprint ends at a
   frozen EXPERIMENT_CONTRACT (Tier 2+) or a written lightweight plan (Tier 1).
5. Never-skippable floor at every tier: name the decision/claim, provenance,
   eval boundary before quality claims, pre-declared consequences, held-out
   spend accounting, retained outcome evidence.

**Prerequisites check.** Chapter 00 declares no inputs. Chapter 01's inputs are
satisfied: decision owner = Brennen (operator, reachable); access to the
incumbent system = the wholesaling repo + its prod/dev environments; chapter 00
read. Lab-level: `docs/LAB_DECISIONS.md` is owner-append-only — creating
`projects/wholesaling/` follows the same pattern as `millwork-estimating`
(added without a decision row); flagged for the owner to append a row if they
want the lab record to note the third instantiation. `make playbook-check`
validates the playbook itself, not projects — not a gate here.

**Decision: where the instantiation lives.** In `adaptive-ai-lab` under
`projects/wholesaling/`, NOT in the wholesaling product repo. Rationale: the
lab charter's loop explicitly places project implementations in
`projects/<name>/`; the playbook's 1.0 gate wants a second/third materially
different instantiation adjacent to the methodology; and the wholesaling repo's
strict branch/PR flow is for product code, not lab-methodology artifacts. The
wholesaling repo is read-only for this task.

**Decision: the first three high-level tasks** (mapped from QUICKSTART/ch. 01):

1. **Incumbent inventory** — a code-verified survey of every AI surface in the
   wholesaling system as it operates today (what runs, what decisions ride on
   outputs, observed failures, existing eval/telemetry, costs). This is the
   evidence base for profile field 20 and the routing tree. → `AI_SYSTEM_INVENTORY.md`.
2. **Intake** — fill the PROJECT_PROFILE, set the stakes tier, run the archetype
   routing with the routing facts recorded. → `PROJECT_PROFILE.md`.
3. **Decision context + path** — name the decision(s) and evaluation claims,
   hard/soft constraints inventory, kill criteria, the archetype's first three
   actions and gated (not scheduled) milestones. → `PLAYBOOK_PATH.md`.

**Subagent delegation plan** (model by complexity, per operator instruction —
overrides the standing always-Opus memory rule for this task):

- **Opus**: deep incumbent AI-surface inventory of `~/code/wholesaling`
  (judgment-heavy; "code is authority" — verify against code, not docs/memory).
- **Sonnet**: digest playbook chapters 03 (Evaluation Foundation) + 07
  (Intervention Ladder) into an operative brief for archetype-C first actions
  (expected route: C — existing system underperforming, no trusted eval).
- **Haiku**: mechanical sweep — enumerate AI/LLM provider references, config
  flags, env keys, and model IDs across the wholesaling backend.

Next entries will record delegation outcomes and the goal-session establishment.

## 2026-08-22 — Goal session established (first invocation of /goal)

`/goal` was created this session (`.claude/commands/goal.md`, also installed to
`~/.claude/commands/`) and invoked by the orchestrator executing its steps
directly (the harness's skill registry does not pick up commands created
mid-session; future sessions can type `/goal`).

- **Goal (one sentence):** bring every wholesaling AI surface that a business
  decision rides on under the playbook's discipline — named decision, trusted
  eval, pre-declared consequences, auditable evidence.
- **Success criteria status:** (1) intake — IN PROGRESS this session; (2) frozen
  first experiment contract — NOT STARTED; (3) trusted eval for one production
  surface — NOT STARTED; (4) one full demonstrated loop — NOT STARTED; (5)
  owner-accepted gates — standing rule, applies from criterion 2 onward.
- **Next gated action:** complete intake (tasks 1–3: inventory → profile/routing
  → path doc), governed by playbook ch. 01 + QUICKSTART. Three subagents are in
  flight (Opus: code-verified AI-surface inventory; Sonnet: ch. 03/07
  archetype-C operative brief; Haiku: mechanical provider/flag sweep).
- **Out of scope this session:** anything past the intake endpoint — no eval
  construction, no experiment contract freeze, no change to the wholesaling
  repo, nothing armed.
- **Frame verified:** branch `project/wholesaling-intake` (pushed, checkpoint 1
  = commit 71db0e3); wholesaling repo read-only; hard constraints in GOAL.md
  uncontradicted.

## 2026-08-22 — Delegations returned: Haiku sweep + Sonnet brief

**Haiku (mechanical AI sweep of wholesaling backend) — complete.** Key facts for
the inventory: a unified `app/ai` router with 5 provider transports (metered
Anthropic API, local Claude Agent SDK, Codex CLI, genserver HTTP hop,
OpenAI-compatible covering xAI/Grok + OpenRouter); AI lanes far beyond the
priors — LLM email generation, voice (Bland) **plus a voice auto-improve
call-grading judge**, vision condition (xAI/Grok) **and** a separate
OpenRouter condition-analysis queue, LLM reply triage, inbound relevance,
deal digest, **Layer-2 deep-dive runner** (Agent SDK sessions with skeptic +
evidence-audit passes and tool budgets), CIS interpret, **a cross-channel
review judge with calibration/dual-grade settings** (`REVIEW_DUAL_GRADE_RATE`,
`test_review_calibration.py`), sales-engine cadence, SF candidate detector.
392 test files; eval-adjacent assets to weigh: `Docs/deal-evaluation/
VALIDATION_BLIND_TEST.md`, `sf_eval_rubric.yaml`, vision `test_bench_runner.py`
/`test_bench_pricing.py`. Full flag/kill-switch surface captured (KILL_SWITCH
default-on, FORCE_DRY_RUN_SENDS, per-channel arming switches, budget caps).

**Sonnet (archetype-C operative brief from ch. 03/07/14 + templates) —
complete; persisted as `ARCHETYPE_C_BRIEF.md`.** Spine: eval-first from
harvested real failures (never an imagined taxonomy); 12-class canonical
failure taxonomy with RC-1 (instrument defect) always first; 8 integrity gates
before any score is trusted; deterministic grading wherever checkable, judges
only behind the 8-step calibration protocol (`doctrine — not yet exercised`);
intervention ladder with entry-vs-exit evidence bars and cheap pre-registered
diagnostic gates; 18-section experiment contract with consequence-bearing
tolerances and MDE/INCONCLUSIVE discipline. **Notable finding: the playbook
has no doctrine for multi-surface systems** (per-surface vs system-level
evals) — ch. 03/07/14 are silent; scoping must be decided explicitly at intake
(likely per-surface by task shape) and recorded as a method decision, or
escalated via ch. 02/08. This gap is also candidate feedback INTO the playbook
(the lab loop's whole point).

Opus inventory delegation still in flight.
