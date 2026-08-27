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

## 2026-08-22 — Opus inventory: primary measurement report received

The Opus delegation sent its primary measurement/eval report ahead of its full
per-surface deliverable. Headline facts (code-cited by the agent; to be folded
into `AI_SYSTEM_INVENTORY.md`):

- **0 of 110 AI-touching test files contain an eval** — all 47 read in depth
  are plumbing (routing, fallbacks, kill switches, prompt substrings, canned
  outputs). Real golden-corpus discipline exists only for deterministic math
  (pricing 330 / valuation 139 cases, weekly-gated) — not AI.
- **One real scored harness exists**: `app/vision/bench/` (exact-tier +
  within-1 accuracy + repair MAPE). Run twice (n=3, then n=49 prod props at
  ~55% exact / ~88% within-1, one-directional optimism bias 0/49-read-worse);
  **neither result committed as data**, labels live only in a DB table, no
  prompt version anywhere, and commit d96a822e changed the default config AND
  rewrote the rubric in the same commit — pre/post verdicts indistinguishable
  in the DB. Docs stale vs shipped default.
- **Telemetry**: the unified `app.ai.router.complete` chokepoint persists
  nothing; usage discarded by all callers except vision. Retroactive
  measurement possible for vision (fully), CIS interpret (approve/edit/reject
  labels accumulating — best instrumented), dives (raw dossiers + operator
  review status); **impossible for outreach email — cannot even tell which
  sent emails were LLM-written** (model stamped then discarded, silent
  template fallback). Agent's suggested single fix: an `ai_call` table written
  inside `router.complete`.
- **Human gates substituting for eval**: reply-draft approval queue, CIS
  triage (approve/edit/reject with edited_params = richest ground truth),
  voice hard interlock (no new live call while one is unreviewed), dossier
  lint (4 mechanical rules from 3 operator-caught hallucinations), compliance
  scrubber (46 patterns), review judge + operator calibration (architecturally
  right, flag OFF → no rows).
- **The exposed surface**: condition-analysis writes tier/confidence/repair
  band straight onto properties to clear the guardrail condition-HOLD
  **without manual review** — the only AI surface with no human gate, and its
  supporting eval is the uncommitted, version-ambiguous 49-property bench.
- Committed scored-output artifacts are narrative one-shots: FL sample run
  n=6 (underwriting materially wrong on all six) and a blind test n=1 whose
  answer key is not in the repo.

Awaiting the delegation's full per-surface inventory before writing
`AI_SYSTEM_INVENTORY.md`.

## 2026-08-22 — Opus inventory complete; AI_SYSTEM_INVENTORY.md written

The Opus delegation delivered its consolidated per-surface roster + system
spine + observed-failure facts (2 messages, ~205k subagent tokens, 121 tool
uses each pass). `AI_SYSTEM_INVENTORY.md` is now complete: 19 AI surfaces
rostered (7 LIVE in prod, incl. two with NO human gate — the xAI vision lane
auto-armed by the nightly, and the Crexi income extraction with no flag, no
budget, no kill switch), 13 candidate surfaces verified DETERMINISTIC and
excluded, measurement audit (0 evals in 110 AI-touching test files; one
partial harness with instrument defects), telemetry map, human-gate map, and
a six-item observed-failure corpus.

**Operationally urgent findings surfaced by the survey (for the operator,
outside this workstream's scope to fix):** (1) voice compliance override
ACTIVE in prod — recording-consent notice bypassed in an all-party-consent
state on the most recent live call, and the opt-out/callback lines are never
actually spoken in conversational mode (gate validates `rendered_text`, Bland
receives `conversational_task`); (2) 3 CIS voice intakes failing silently for
days on a genserver 401 (metered head unconfigured); (3) dive approvals had
silently stopped writing assessments (33 approved vs 15 written).

**Operator hypothesis received mid-session** (verbatim intent): tasks/jobs may
be too coarse — "doing too many things at once" — so there is no insight into
smaller individual tasks; operator explicitly asked for validation or
pushback, not adoption. Disposition: recorded as a pre-registered hypothesis
to TEST, not ground truth (playbook P7/P12 discipline; a hypothesis adopted
without measurement is exactly the placeholder-to-policy drift ch. 01 §9
rejects). Orchestrator's assessment against the inventory evidence is being
delivered to the operator and folded into PLAYBOOK_PATH.md as prediction
H-OP-1.

## 2026-08-22 — Intake complete: profile, routing, path (tasks 2 and 3)

`PROJECT_PROFILE.md` written (all 21 fields; approximations flagged for
re-verification before contract freeze). **Routing outcome: archetype C
(fix-what-exists), stakes Tier 2, with named Tier-3 decision carve-outs** for
anything changing live outreach/voice behavior or compliance posture (fields
3/19). Node-1 pre-check fires: no trusted eval → eval first. Modifiers:
judge-graded split + ch. 02 pulled forward for cross-lane comparisons.

`PLAYBOOK_PATH.md` written: decision statement + per-surface evaluation-claim
skeleton; surface priority (condition → dives → CIS → outreach → voice);
hard/soft constraints with the intake kill-criteria check PASSED (dated);
3 pre-registered project kill criteria; the archetype-C first three actions
(condition-surface eval rung-0 first, taxonomy classification, diagnostic
gate + first contract freeze); prediction-ledger seeds H-OP-1 (operator's
granularity hypothesis — registered to TEST), H-1, H-2; milestones M1
(committed) through M5 (gated, owner-accepted).

**Key decisions this entry records:**
- First eval target = the condition surface (no human gate, feeds pricing,
  existing harness + labels, fully retro-measurable; its instrument defects
  are a textbook rung-0 target).
- Multi-surface scoping = per-surface by task shape (method decision; the
  playbook is silent — gap to feed back at M5).
- Product-repo changes (label commit path, prompt versioning, ai_call table)
  are flagged as operator-gated wholesaling tasks, not performed by this
  workstream.
- Intake endpoint honored: this session STOPS at intake; the frozen
  EXPERIMENT_CONTRACT is M1's deliverable, next session, per the /goal frame.

## 2026-08-22 — Integration & feedback bridges defined (operator request)

Operator asked (a) how lab output gets applied INTO the wholesaling repo and
(b) how findings get back INTO the playbook. Wrote
`INTEGRATION_AND_FEEDBACK.md` (the two bridges) and seeded
`PLAYBOOK_FEEDBACK.md` (append-only ledger, 6 initial entries F-1..F-6).

Direction 1 decisions: lab decides what/why, wholesaling receives scoped
**intervention packages** (license = RC class/rung, spec, measurement,
authorization line) implemented via wholesaling's own feature→dev PR flow;
boundary rule — instruments/corpora/CI gates live in wholesaling (like the
existing pricing/valuation corpora), contracts/verdicts/ledgers live in the
lab, cross-cited by SHA. Package queue seeded: P1 condition-instrument
prerequisites, P2 ai_call telemetry floor, P3 dive output-contract (post-
diagnosis only). All operator-gated; none started.

Direction 2 decisions: capture continuously in the ledger, promote only at
milestone gates (M2/M3/M5) with the playbook's own evidence bar (frozen
executed contract, validated instrument pass, or documented incident);
promotions are owner-reviewed lab-repo PRs touching playbook/ + CHANGELOG.
Noted: executing M1/M2 contracts here directly advances the playbook's 1.0
gate (second materially-different instantiation through executed contracts).

## 2026-08-22 — Handoff protocol for wholesaling-agent sessions (operator request)

Operator asked for a clean way to feed prompts/plans/context to separate
wholesaling-repo sessions, with explicit procedure (when to start sessions,
which models) and strict context engineering (no read-this-then-six-more
link chains). Delivered:

- `HANDOFF_PROTOCOL.md` — the one rule: the wholesaling agent reads exactly
  ONE self-contained brief per session; the lab COMPILES context in, links
  out are a brief defect (firewall exception: the wholesaling codebase
  itself). Session lifecycle (one-line launch prompt, mandatory echo check,
  declared stop point, fixed RESULT format); new-session triggers (new
  package / brief amendment / context degradation / scope discovery — agent
  never improvises spec changes); model table (Opus default, Sonnet for
  tightly-specced mechanical work, never Haiku driving the prod repo);
  brief-authoring rules (≤250 lines, inlined excerpts, provenance footer
  marked do-not-read, freeze discipline DRAFT→AUTHORIZED vN).
- `packages/TEMPLATE_BRIEF.md` — the authoring template with standing rules
  inlined so the agent still reads one file.
- `packages/P1/BRIEF.md` — P1 drafted as the worked example (condition
  instrument prerequisites: prompt-version constants + persisted
  prompt_version column + deterministic label exporter + bounded doc fix).
  Status DRAFT — explicitly not authorized; awaiting operator review.

Decision recorded: briefs are frozen at authorization; post-authorization
edits bump the version and force a fresh session — a lightweight mirror of
the playbook's contract-freeze discipline applied to handoffs.

## 2026-08-24 — Subscription-lane telemetry gap made first-class (operator question)

Operator asked whether the plan accounts for AI jobs running through the local
Claude Code/Claude Max subscription (mac mini genserver, dive runners) and
CLI-subscription providers (Codex/opencode-style) — flagged as important for
insight and telemetry. Assessment: the inventory documented these lanes
precisely (usage={} unconditional in both flat-rate providers; dive runner
bypasses the router; genserver hop is a visibility wall), but the plan
under-weighted them. Changes:

- **P2 expanded** (INTEGRATION_AND_FEEDBACK): flat-rate providers must
  surface real SDK/CLI usage (NULL + wall-time + quota-event flag when truly
  unavailable, never silent {}); wire-level correlation id across the
  genserver hop so mini-side and serverless-side records join; router-bypass
  lanes (dive runner) write ai_call rows directly; cost semantics split by
  supply class (USD for metered, tokens+wall-time+quota events for
  flat-rate); per-call execution-identity fields (resolved model, transport,
  host, CLI/SDK version) as the ch.-02 prerequisite.
- **PROJECT_PROFILE field 12 amended** (dated): subscription lanes named as a
  distinct supply class carrying much of the AI volume.
- **F-7 appended** to the feedback ledger: subscription-backed local
  inference as a fourth supply class the playbook's ch. 02/11 don't treat
  (neither owned compute nor managed API); promote at M2/M4 with real
  cross-lane data.

P1 unaffected (touches prompts/labels, not providers). P2 remains
operator-gated and unstarted.

## 2026-08-25 — Session prompts staged; P1 brief verified against code

Operator asked to stage the next step, push, and get launch prompts for both
repos. Delivered `SESSION_PROMPTS.md` (per-repo launch prompts, session
routing table, order of operations), a `packages/P1/RESULT.md` scaffold, and
README start-here entry points.

**Wholesaling repo needs no changes to "know how to operate"** — by design it
runs on its own CLAUDE.md plus one self-contained brief; that is the context
firewall, and it also honors this workstream's read-only constraint. The lab
repo orients via `/goal wholesaling`.

**P1 brief verified (Sonnet delegation, read-only) and corrected** — the draft
had real defects, exactly the kind the protocol exists to catch:
- ORM class is `ConditionAnalysisRequestORM` at `db/models.py:1181-1279`
  (draft said lines 1219-1249, unnamed).
- **One** write site, `services/condition_analysis.py:271` — the draft assumed
  additional bench-side write sites that do not exist.
- **Three** prompt families, not two: `vision/prompt.py` (single-pass screen),
  `vision/bench/extended.py:201` (per-batch map), `vision/bench/reduce.py:50`
  (reduce/merge); `services/condition_analysis.py` defines no prompt text, so
  the draft's instruction to check there was wrong.
- Golden-label ORM is `VisionGoldenLabelORM` (`db/models.py:2608-2627`) with
  8 columns; no export path exists anywhere (confirmed). Export spec tightened
  to exclude timestamps/`labeled_by` for determinism.
- Next migration is `0108` (head `0107_comm_fact_homes`); exact test invocation
  is `python -m ruff check .` + `python -m pytest -q -n auto` from `backend/`.
- Doc discrepancy confirmed: `Docs/IMAGE_ANALYSIS.md:220-222` says
  `singles_768`, shipped default is `grid_512_3x3` (`settings.py:1732-1733`).
- Also confirmed the F-7 evidence first-hand: `codex_cli.py:215` and
  `claude_sdk.py:168` both return `usage={}` unconditionally.

P1 remains **DRAFT** — authorization is the operator's act (flip the status
line), per the freeze discipline. Nothing has been executed in the wholesaling
repo; it remains untouched.

## 2026-08-25 — SCOPE PIVOT: go-to-market by selling leads; scope narrowed to ingestion + underwriting

**Operator directive.** Go to market by **selling high-quality leads** rather
than pursuing deals ourselves. Immediate need: full insight into the
ingestion and underwriting workflows (and the AI calls inside them). Explicitly
a speed-run — jumping into one slice, in the playbook's spirit.

**Why this is a profile amendment, not just a task** (ch. 01 §5.2, and the
template's own rule that a profile is revised when outcome/stakes change
materially): field 1 (business outcome) changes, and with it what "quality"
means. Previously the AI surfaces were *internal inputs* to our own pursuit
decisions, with operator judgment as the last line of defense. **Selling the
output makes underwriting numbers the product itself** — a third party pays
for them and acts on them, with no operator in their loop.

Consequences of the pivot, recorded:

1. **The FL n=6 finding is promoted from "pipeline defect" to "product
   defect."** Underwriting was materially wrong on 6/6 (4 false-positive
   deals on mirage inputs, 2 false UNPRICEABLE holds). Selling that output
   to a paying buyer converts an internal miss into a delivered
   misrepresentation. This is now the single most consequential open item.
2. **Surface priority re-ordered for this workstream.** Was: condition →
   dives → CIS → outreach → voice. Now: **ingestion (coverage/freshness/
   identity) and underwriting (ARV, rehab, pricing) first**; the condition
   surface stays high because it feeds rehab→price, but it is now scoped as
   *an input to the product* rather than as an isolated first eval. Outreach
   and voice drop in priority — we are not the ones contacting sellers in the
   lead-sale model (revisit if that changes).
3. **Stakes reading.** Still Tier 2 for the evaluation work, but the Tier-3
   carve-out list gains a new member: **publishing/selling a lead whose
   numbers came from an unmeasured AI surface** is money-movement-adjacent and
   reputational, and needs its own gate before first sale.
4. **New evaluation claim shape** (ch. 01 §5.2), replacing the internal one:
   *"A lead we sell states ARV, rehab, and price within stated tolerance of
   ground truth, or declares its own uncertainty — verified by eval E on a
   representative sample of the book we would actually sell."* Note the
   second clause: for a saleable product, a declared UNKNOWN is a legitimate,
   non-defective output; a confident wrong number is the expensive failure
   (P11 silent-failure).

**Research dispatched (3 parallel delegations):** Opus × ingestion pipeline
(sources, schedules, identity/dedup, enrichment, AI calls, freshness,
data-quality controls, known failures, coverage instrumentation); Opus ×
underwriting (ARV/comps + accuracy gate, condition→rehab mapping, per-strategy
solvers and constants, strategy routing, the versioning manifest/freeze_status,
gates/holds, AI inputs that can overwrite deterministic values, the golden
corpora, buyer-visible output fields, known defects); Sonnet × live prod data
profile via read-only SQL (book size, freshness distribution, underwriting
completeness funnel, condition coverage, contact linkage, and a
"complete sellable lead" funnel with per-filter loss). The prod delegation was
given explicit read-only + no-PII constraints.

## 2026-08-25 — Leads-GTM research complete (3 surveys, ~820k subagent tokens)

Wrote `leads-gtm/` — README (synthesis), INGESTION_STATE, UNDERWRITING_TRUST,
UNDERWRITING_MECHANICS, PROD_DATA_PROFILE. Three delegations: Opus × ingestion
(214 tool uses), Opus × underwriting (105 + 105 on a follow-up for the main
body), Sonnet × read-only prod SQL profile.

**Three findings that decide the GTM:**

1. **Supply is silently dead in 6/8 markets** — 0 listings across 82 runs
   each over 3 days, every run `succeeded`. Three compounding causes make
   alerting structurally impossible: no `source_health` rows written for those
   markets, `is_volume_anomaly` returns False below baseline 20 (a market
   pinned at 0 never flags), `coverage_ratio` NULL everywhere (WAF-403 on the
   denominator). `data-discovery`: 0 successes in 1000 runs. Issue #1463 open
   since 2026-07-18 suppresses new alerts.
2. **The proven half is not the product half.** The solver suite is excellent
   (26+11+3 invariants, closed-form differential oracle sharing no code with
   prod, 9 seeds, CI structurally unable to skip) but proves obedience *given
   inputs*; the harness hands carrying costs from a hard-coded table, so
   `area_costs.py` and `HOLD_AREA_COSTS_MISSING` are never exercised and the
   FL 5×–6.7× T+I error is invisible to all 330 cases. `BACKTESTED == 0`; the
   weekly accuracy gate has no committed measurement.
3. **~100/22,026 (0.45%) complete sellable leads**, and the dominant funnel
   loss is our own buy box (`pass` 11,782 / `park` 2,959 / `conditional_pursue`
   1,420 — pricing populates only for the last). Condition completeness is
   nominal: 66% carry a tier, **1.8%** from image analysis.

**Two artifacts that shortcut eval design:**
- `services/handoff_approval.py:38-65` already defines the buyer-decision
  field set (`offer_price, assignment_fee, expected_fee, math_version, arv,
  arv_confidence, arv_source, condition_confidence`) — adopt as eval scope
  rather than inventing one.
- `services/deal_review.py:103-151` trust labels: `_REAL_COMP_PROVIDERS =
  {"rentcast"}` only, `_RECORDED_MORTGAGE_SOURCES` empty → on the free path
  **every ARV/rent already labels ESTIMATED and every mortgage figure
  is_estimate=True**. The system already knows it is estimating nearly
  everything; the product question is whether a buyer is told.

**Notable risk found in the display layer:** dive-authored `target_price`
overwrites the deterministic `router_baseline` (~16,032/16,108 deals carry
it), is validated **type-only with no cross-check against the router's solve**,
and `DealPanel.tsx:775` shows it *instead of* `offer_price` — the LLM number
is what a human (or buyer) sees, with the proven solve demoted to Diagnostics.

**Operator-relevant, outside lab scope:** the ingestion outage is a live prod
incident and belongs to normal product work, not a lab package.

## 2026-08-25 — Method decision: eval corpus = pinned fresh pull, not the existing book

**Operator hypothesis:** evaluate from fresh data pulls; the DB is in disarray
because properties were processed under many different code versions.

**Confirmed by the codebase's own measurement** — `underwriting_version.py`'s
docstring records the 2026-08-04 prod finding: **8 coexisting underwriting
versions, 8.7% of the book at head**. The stored book is not one instrument
but a mixture of unknown instruments; scoring it would cross an unmeasured
reproducibility boundary (P5 / ch. 02 / global tripwire 3). Supporting: two
versioning schemes stamping concurrently, `rehab_as_of` frozen at 2025-01-01,
and the material fixes (T+I defaults removed, AFR floor, 5-tier income ladder,
credibility floors, freshness fix) all shipped after most rows were written.

**Decision recorded** (`leads-gtm/EVAL_CORPUS_DESIGN.md`), amending
PLAYBOOK_PATH §4 action 1: the first eval's corpus is a **pinned fresh pull
over a stratified sample from currently-live lanes**, not a query over the
existing book.

**Qualification the orchestrator added (pushback):** a fresh pull yields a
valid *instrument*, not *ground truth*. Re-running current code tells you what
the system outputs under a known identity; it cannot say whether the output is
right — that is precisely how the existing goldens ended up pinning drift
rather than correctness (self-derived by construction). Every sold number needs
an **independent reference** gathered outside the pipeline; the FL n=6 method
(independent desk research vs pipeline output) is the template to scale.

**The old book is retained for two valid uses**: error-analysis/failure
harvesting (ch. 03 §5.1 requires real observed failures) and
coverage/completeness facts. Rule: the old book says what goes wrong; the fresh
pull says how often, under a known instrument.

**Design constraints recorded**: pin the execution system (commit SHA, 4-layer
version vector, both AI model ids, REFDATA digests) before pulling; **isolate
from the crons** — 4 concurrent property writers (`cloud-nightly` */5 despite
its "disabled" header, discovery */15, enrich 5,20,35,50, crexi 6h) will mutate
a corpus mid-measurement, with INC-001 lock contention still open on the ingest
side; use the reunderwrite freeze path (captures/restores status +
lifecycle_stage, so nothing reaches a send queue); **supply constrains scope** —
only Detroit, Grand Rapids, and the Crexi MF lane can currently produce fresh
rows; stratify by market/type/condition-source/ARV-source (the FL JV lane
yields a visible ARV at confidence 0.036 that can never price); size for a
stated MDE; ledger the look.

**Ordering consequence:** first *AI* target stays condition; first *product*
target is **carrying costs (T+I)** — the one measured error, and the one the
entire 330-case suite is structurally blind to.

## 2026-08-27 — BACKFILL: checkpoints 12–19 (logged late; see walk-test finding)

Append-only discipline failed between 2026-08-25 and 2026-08-27: eight
checkpoints were committed without process-log entries. This entry backfills
them as a single retrospective record (it is appended, not back-dated; the gap
itself is the finding).

- **12** `INFERENCE_ECONOMICS.md` — ch.11 note on open-weight models. Initial
  framing argued inference cost is not the binding constraint (the dominant
  T+I error is deterministic).
- **13** **Operator correction**: the expensive workload is the *experiment/
  analysis agent*, not the pipeline's internal AI calls, and it competes with
  the operator's Claude Code weekly limit — which their daily work depends on.
  Framing corrected; researched Aug-2026 pricing added (DeepSeek V4, Qwen3.x,
  GLM-5.2, coding plans, Alibaba free quota). Recorded the largest cost lever:
  script the harness; don't spend an agent turn per iteration step.
- **14** Flash-tier update: GLM-5.3-Flash promo verified ($0.075/$0.015/$0.25,
  ends 2026-09-09; list $0.15/$0.03/$0.50), multimodal, 1M ctx, **weights not
  yet published so not open-weight today**. Per-turn cost model + promo-cliff
  warning + cheap-vs-strong routing caution.
- **15** z.ai coding-plan vs pay-go comparison (credit formula, 5h/weekly
  buckets).
- **16** **Correction to 15**: priced at standard credit rates and monthly
  billing, which was wrong. Two distinct discounts exist (Flash API promo vs a
  50% *off-peak credit* discount that applies to plan usage); peak is only
  Mon–Fri 06:00–10:00 UTC, so the US workday is half-credit. With yearly
  billing plans beat pay-go 2–3x during the promo, 4–6x after. **Operator
  purchased the z.ai plan.**
- **17** Qwen Coding Plan evaluated (~$10 Lite / ~$50 Pro, 90k requests/mo,
  request-based rather than credit-based billing — structurally favorable to a
  token-heavy loop). Recommendation: not yet; free 1M-per-model Alibaba quota
  funds the bake-off; two-week trigger prefers *adding* Qwen over upgrading GLM
  at equal price.
- **18** `HARNESS_SELECTION.md` — the harness effect (same model, 16–36 point
  swings by scaffold; DeepCode 0.85 vs Claude Code 0.59 on the same base
  model). Consequences: harness is part of the frozen execution identity, so
  swapping breaks comparability; "GLM in DeepSeek Harness" is a two-factor
  change needing a 3-arm design; the same lesson applies to the product's own
  prompt scaffolds. Logged F-8.
- **19** `ICM_ASSESSMENT.md` — ICM-Architect (arXiv:2603.16021, citation
  verified) is convergent with this workspace; adopt the **walk test**, decline
  the in-place restructure (it would silently break provenance citations),
  and note ICM does **not** apply to wholesaling's ETL orchestration. Logged
  F-9.

## 2026-08-27 — Walk test executed; instrument was contaminated; four defects fixed

Ran ICM's walk test against `projects/wholesaling/` with a Sonnet subagent.

**Operator caught an instrument defect before the result was believed** (P2 in
action): a subagent spawned from a session whose cwd is `~/code/wholesaling`
is **not** memoryless. Disclosure confirmed it received, before opening any
file: the product repo's `CLAUDE.md` (branch-flow rules, environments, Alembic
heads, gotchas), the ~50-entry `MEMORY.md` index (including specific prior
claims about the very AI surfaces this workstream evaluates — "AI Router Module
SHIPPED", "Underwriting Versioning RELEASED TO PROD"), and an `<env>` block
with the product repo's branch and recent commits.

**Validity ruling:** answers to *"what is the project"*, *"current state"*, and
*"could you execute"* are **contaminated — directional only**. The agent noted
it could not certify that prior memory claims didn't shape which findings felt
"already known." The **friction log stands**, because its findings are
*relational* claims about contradictions *between files inside the workspace* —
nothing ambient could supply those.

**Four real defects found and fixed this session:**
1. `PROCESS_LOG.md` stale by two days while `GOAL.md` instructs sessions to
   "read the tail first" → backfilled (entry above).
2. `PLAYBOOK_PATH.md` still ranked the condition surface first post-pivot with
   nothing marking it superseded → supersession banner added.
3. `PROJECT_PROFILE.md` field 1 never amended although the pivot entry said
   explicitly that it changes → amendment added.
4. `SESSION_PROMPTS.md` "order of operations" still said *authorize P1 first*,
   which post-pivot points a session at a deprioritized surface → rewritten;
   P1 marked QUEUED BUT NOT NEXT, and the real gap named (no brief exists yet
   for ingestion instrumentation / carrying-cost eval).

**Design tension surfaced (unresolved):** a lab session is forbidden to read
the product repo, yet a work-order brief must inline that repo's rules for the
executing session. The walk-test agent only had those rules *ambiently*. Authoring
briefs may require a scoped, explicit exception to the read-only rule (reading
is not writing) — flagged for the operator.

**Verdict: the walk test paid for itself on its first run**, even contaminated.
ICM's contribution to this project is now evidenced, not assumed.
