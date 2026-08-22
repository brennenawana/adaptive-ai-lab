# Playbook Path — Wholesaling Instantiation

> The decision context, constraints inventory, kill criteria, first actions,
> and gated milestones for archetype C (01 → 03 eval-first → 07). Governed by
> [`PROJECT_PROFILE.md`](PROJECT_PROFILE.md) (routing) and
> [`ARCHETYPE_C_BRIEF.md`](ARCHETYPE_C_BRIEF.md) (operative digest of ch.
> 03/07). Written 2026-08-22.

## 1. The decision and its evaluation claims (01 §5.2)

**Decision:** for each AI surface in the wholesaling system, should it (a)
keep operating as configured, (b) operate behind a tightened gate, (c) be
repaired at a diagnosed ladder rung, or (d) be turned off — decided on
measured evidence, per surface, by the decision owner.

Evaluation-claim skeleton, instantiated per surface as its eval lands:
*"Surface S achieves bar Q on its real task population, verified by trusted
versioned eval E, within its cost bounds — else the pre-declared consequence
executes."* No such claim may precede its eval (P1); no eval score may precede
its instrument validation (P2).

**Surface priority order** (consequence × evidence availability):

1. **Condition (vision + OpenRouter queue)** — only surface with no human
   gate; directly sets rehab→offer math and clears the guardrail HOLD; the
   one existing harness + 49 labels + full retro-measurability make it the
   cheapest first trusted eval. Its instrument defects (uncommitted labels,
   no prompt version, rubric rewritten in the adopting commit) are a textbook
   **rung-0 / RC-1** target.
2. **Deep-dive dossiers** — richest observed failures (31% `needs_attention`,
   35% output-contract failures, hallucination corpus), operator ground truth
   accumulating, prices overwrite baselines on approval.
3. **CIS interpret** — best instrumented (prompt_version + approve/edit/reject
   labels); acceptance-rate eval is nearly free once labels accumulate.
4. **Outreach email generation** — outward-facing but human-throttled and
   allowlisted today; blocked on attribution (cannot link sent bodies to
   generations) — a telemetry prerequisite, not an eval-first target.
5. Voice — Tier-3 decision territory; the immediate items are the operator's
   compliance posture (outside this workstream), not model quality.

## 2. Constraints inventory (01 §5.3)

| Constraint | Class | Effect |
|---|---|---|
| Compliance/consent law on outreach + voice (field 19) | **Hard** | Any change to live outreach behavior = Tier-3 decision, operator-authorized; never made by this workstream |
| Wholesaling repo read-only for this workstream | **Hard** (self-imposed, recorded in GOAL.md) | Product changes (e.g. `ai_call` table, prompt versioning) are separately scoped, operator-gated tasks in that repo's own flow |
| No written PII/residency rule exists | **Hard gap** | Intake action for the operator: write the rule; until then, no NEW data flows to additional third parties for eval purposes |
| Held-out data spend semantics (P8) | Hard | Look ledger from the first eval onward |
| No standing labeling team (field 16) | Soft, consequential | Ground truth leans on accumulating operator dispositions + generator-derived checks; judge scores only behind the full calibration protocol |
| No stated recurring budget ceiling (field 14) | Soft | Operator to state one; becomes a consequence-bearing tolerance |

**Intake kill-criteria check (01 §5.3, dated 2026-08-22):** no hard constraint
eliminates every candidate — the evaluation work itself runs read-only against
existing data and flat-rate/owned compute, and every surface has at least one
admissible measurement path. Finding recorded: **PASS** (no re-scope required).

## 3. Project-level kill criteria (pre-registered)

1. If the condition-surface instrument cannot be made trustworthy (labels
   committed, prompt versioned, gates green) within **two working sessions of
   effort**, STOP and re-scope to the dive surface — do not iterate
   indefinitely on one instrument (P4).
2. If for any surface no ground-truth path exists at acceptable operator cost,
   that surface's eval is declared blocked and the finding goes to the
   operator as a **gating recommendation** (tighten/disable), not silence.
3. If prod evidence shows an AI surface actively causing compliance exposure,
   this workstream stops evaluating and escalates to the operator immediately
   (already exercised once: the voice posture findings in the inventory).

## 4. First three actions (archetype C, Tier 2)

1. **Build/validate the first eval — condition surface — WITHOUT changing the
   system** (ch. 03; rung 0 first). Concretely: extract + commit the golden
   labels as a versioned corpus; reconstruct which rubric each historical
   verdict used (or declare pre/post-rewrite verdicts incomparable — likely);
   define the task ontology from the real failure shapes (optimism bias,
   grid-vs-singles divergence); write the EVAL_SUITE_RELEASE_CONTRACT; run the
   integrity gates (gold-answer, determinism, saturation, inversion) before
   believing any score. Product-repo prerequisites (prompt version constant,
   label export) are operator-gated wholesaling tasks — flagged, not done here.
2. **Classify the observed-failure corpus into the canonical taxonomy**
   (inventory §6 + accumulating dispositions). Provisional reading to be
   verified, not assumed: dive JSON-tail failures → RC-5; approval ignoring
   `needs_attention` + the fail-open posture check → RC-7; CIS genserver 401 →
   RC-2/RC-4; vision eval trail → RC-1; dive hallucinations → RC-3/RC-6
   pending diagnosis.
3. **Pick the highest applicable rung per diagnosed gap with a cheap
   pre-registered diagnostic gate, then freeze the first
   EXPERIMENT_CONTRACT** (ch. 07 §5.2; contract per ch. 04 — the first-sprint
   endpoint). Candidate first contract: re-run the vision bench under a frozen
   execution-system identity on the committed corpus, one factor, MDE stated,
   GO/RE-SCOPE/DROP bands pre-registered.

## 5. Predictions (prediction-ledger seeds; scored when evals land)

- **H-OP-1 (operator, 2026-08-22): task units are too coarse — jobs "doing
  too many things at once" prevent insight into smaller individual tasks.**
  Status: registered for test, not adopted. Test: when per-surface failure
  classification lands, score whether failures concentrate at the seams of
  fused subtasks (→ RC-6 spec/decomposition or RC-12 architecture would
  confirm) versus at measurement/enforcement/verification layers (RC-1, RC-5,
  RC-7 — which would refute "granularity" as the binding constraint and
  confirm "measurement" instead). Orchestrator's prior from the inventory:
  partially supported — the dive runner and CIS interpret are genuine
  multi-task monoliths and the map-reduce REDUCE re-reasons its merge
  opaquely; but the failure evidence so far skews RC-5/RC-7/RC-2 (format
  enforcement, verification gaps, config), and NO task at ANY granularity is
  measured today, so decomposition without instrumentation would produce more
  unmeasured units, not insight.
- **H-1 (orchestrator): the condition surface's post-rewrite prompt performs
  differently from the ~55%/88% measured pre-rewrite** — direction unknown;
  the point of the rung-0 re-run.
- **H-2 (orchestrator): dive `needs_attention` rate is reducible below 10% at
  rung 3/4 (output contract + spec) without model change.**

## 6. Gated milestones (committed sprint = M1 only; the rest are gated, not scheduled)

| M | Deliverable | Gate to proceed (accepted by owner, never self-assessed) |
|---|---|---|
| **M1 (committed)** | Actions 1–3 above → frozen first EXPERIMENT_CONTRACT | Contract passes the 8-item freeze gate (04 §7) |
| M2 | Executed first contract → verdict (CONFIRMED/REFUTED/INCONCLUSIVE) on the condition instrument | Owner accepts verdict + consequence executes as pre-declared |
| M3 | Dive-surface eval from operator dispositions + failure taxonomy | M2 verdict recorded; owner prioritizes dive vs CIS |
| M4 | Telemetry-floor recommendation package for the wholesaling repo (`ai_call` table, prompt versioning, dive cost persistence) as a scoped PR plan | Owner authorizes product-repo work explicitly |
| M5 | Multi-surface scoping method decision (per-surface vs system eval) fed back to the playbook (the ch. 03/07 doctrine gap) | Two surface evals exist to generalize from |

## 7. Standing method notes

- Ch. 02 before any cross-lane/cross-session comparison (many execution
  surfaces: serverless, genserver, SDK subprocess, cron runners).
- Deterministic grading wherever checkable (tier match, JSON contract,
  attestation presence); judges only behind the 8-step calibration protocol —
  and note the review-judge + operator-calibration machinery already in the
  tree is architecturally aligned with it but flag-off and unwired.
- Multi-surface doctrine gap (ARCHETYPE_C_BRIEF §8): scoping decision recorded
  here as **per-surface by task shape** — a method decision to be revisited at
  M5 and fed back to the playbook.
