# Project Profile — Wholesaling AI Surfaces

> Intake against
> [`../../playbook/templates/PROJECT_PROFILE.md`](../../playbook/templates/PROJECT_PROFILE.md),
> filled 2026-08-22 from the code-verified [`AI_SYSTEM_INVENTORY.md`](AI_SYSTEM_INVENTORY.md)
> plus standing project context. Values marked *(approx.)* come from project
> memory and must be re-verified against the prod DB before any experiment
> contract freezes on them. Decision owner: Brennen.

## 1. Business outcome

Close real-estate deals (cash wholesale, seller-finance, income-hold) sourced
and worked by the automated pipeline, without the AI surfaces inside that
pipeline causing compliance incidents, mispriced offers, or wasted operator
attention. Stated as the decision this instantiation drives: **which of the
system's AI surfaces may be trusted to act (or keep acting) autonomously, at
what measured quality bar, and which must be repaired, gated, or turned off.**

## 2. Task population & volume

Property book *(approx.)*: ~14.4k MI + ~1.2k FL single-family, plus
multi-state Crexi multifamily (~2k listings ingested; ~860 held cards). AI
task volumes observed in prod: 29 LLM emails sent / 17 replied
(46-address allowlist); CIS interpret budget 60/day (66 proposals, 112
actions so far); vision condition on 336 properties + a 105-property
condition-analysis batch; 94 deep dives (58 approved); 9 live voice calls.
Task space spans generation (email/voice copy), extraction (rent, 19
post-call fields), classification (condition tier, reply intent), and
diagnose-and-act (CIS interpret, dives).

## 3. Criticality / failure cost

Enumerated by failure class (all observed, see inventory §6):

- **Compliance/legal** — highest: outreach and voice touch real
  counterparties under telemarketing/recording-consent and
  wholesaling-practice rules; two voice incidents (2026-08-12/13) already
  occurred; the compliance override is active in prod today.
- **Financial (mispricing)** — vision tier sets `estimate_rehab` → offer
  price; extracted rent feeds the CoC solver; dive-authored
  target/concession/walk prices overwrite the computed baseline. FL n=6
  sample: materially wrong 6/6.
- **Pipeline integrity** — a wrong condition verdict clears the guardrail
  HOLD with no human review; a wrong CIS action proposal can advance
  lifecycle/suppress contacts (human-gated today).
- **Operator attention** — 31% of dives flagged `needs_attention`; silent
  failures (CIS 401, unwritten dive assessments) burn trust and time.

## 4. Quality/reliability target

**No AI surface has an established quality bar today — that absence is the
routing fact.** Bars must be derived per surface from harvested failures and
operator dispositions (ch. 03), not asserted here. Behavioral compatibility:
required for outreach copy (must stay inside the compliance scrubber's
constraints and the operator's voice); required for condition verdicts
(consumed by the deterministic rehab→offer math in the incumbent's shape).
Repetition reliability (pass^k) applies to the agentic dive surface (stochastic
multi-turn) before its numbers overwrite baselines.

## 5. Latency/throughput/SLA

Almost entirely batch/cron (15-min enrichment ticks, 6h value-route, nightly
generation); no contractual SLA. Interactive paths: UI draft generation
(seconds-tolerant) and Bland's hosted real-time voice (provider-managed). No
hard latency floor eliminates any candidate surface.

## 6. Privacy/security/data residency

Counterparty PII (names, phones, emails, transcripts) currently flows into
metered third-party APIs (Anthropic, xAI, OpenRouter→Google, Bland) and
self-hosted lanes. **No written residency/PII rule exists.** Per playbook
QUICKSTART node-5 guidance, an unwritten rule is itself an intake action:
the operator should write one (even one line) before it silently re-routes
decisions. Call recordings in all-party-consent states are a live, named
exposure (inventory §6).

## 7. Data & knowledge availability

Rich and accumulating: raw dossiers + operator `review_status` (94 dives),
CIS approve/edit/reject with `edited_params`, voice transcripts + provider
analysis, sent-email outcomes (opens/replies), `vision_golden_label` (49+
labels, uncommitted), the FL n=6 desk-research comparison, deterministic
golden corpora (pricing 330 / valuation 139) proving corpus discipline exists
in-house. Gaps: outreach generation unattributable to model/prompt; no prompt
versioning anywhere except CIS.

## 8. Tool/action permissions

- Dive runner: Crexi MCP toolbelt behind per-dive call budgets; writes only
  via operator approval (defect: approval ignores `needs_attention`).
- CIS interpret: propose-only; every action human approve/edit/reject.
- Condition analysis: **direct write** of tier/confidence/repair band to
  properties (clears the HOLD, no human gate).
- Send paths: guardrail gate + kill switch + allowlist + throttles; voice
  additionally operator-confirmed per call + unreviewed-call interlock.

## 9. Model candidates

In service today (seeds, not a shortlist): claude-opus-5 (metered Anthropic),
Claude Max via Agent SDK (flat-rate, genserver/dives — dives pin
claude-opus-4-8), Codex CLI (flat-rate ChatGPT plan), grok-4.3 (xAI vision +
judges), gemini-3.1-flash-lite-preview (OpenRouter condition queue), Bland
hosted LLM (voice). Selection (ch. 05) is premature until diagnosis — archetype
C explicitly defers it.

## 10. Owned compute

Mac mini (genserver + message generator), `cron-mini` runner, Windows runner,
clawdbot-server (:8790 lane) — all shared with production duties, zero
marginal cost, no GPUs relevant to training.

## 11. Rentable compute

Not currently needed; OpenRouter serves as metered burst capacity. No
procurement constraints identified.

## 12. Managed APIs

Contracted/active: Anthropic (metered + Claude Max), OpenAI/ChatGPT plan
(Codex), xAI, OpenRouter, Bland.ai, Crexi (data). Known constraint: several
runners lack the metered-head secrets their routes assume (live CIS 401).

## 13. Capex budget

None pre-approved. No hardware purchase is in scope; the demand-ledger
machinery applies only if that changes.

## 14. Recurring budget

No stated monthly ceiling `[unknown — operator to state one]`. Observed spend
is small and capped per-run ($5/condition drain; daily voice caps; flat-rate
subscriptions carry most volume). A stated ceiling becomes a
consequence-bearing tolerance once surfaces are measured.

## 15. Utilization/growth expectations

Multi-state expansion intent (MI → FL done; more Crexi states planned);
AI-call volume grows with book size and with any arming of currently-idle
surfaces. No committed trajectory `[unknown]`.

## 16. Staffing/time

Brennen (operator/decision owner, part-time) + partner; execution is
agent-orchestrated (this lab's sessions + wholesaling's own agents). Rigor
must be executable at that staffing: automation-heavy, no standing human
labeling team — dual-labeling capacity is scarce (relevant to the judge
modifier).

## 17. Deployment environment

Prod: Vercel serverless (FastAPI) + Supabase Postgres + GitHub Actions
self-hosted runners + the Mac-mini/clawdbot self-hosted lanes. Dev mirrors it
on separate projects/DB. Many distinct execution surfaces → ch. 02
(execution-system identity) is pulled forward before any cross-surface or
cross-lane comparison.

## 18. Observability constraints

No external prohibition; the constraint is internal: the router chokepoint
persists nothing, usage is discarded, per-lane telemetry is denormalized
(inventory §3). The telemetry floor (ch. 12) is a build item, and the
single-table `ai_call` fix is already identified. No retention limits stated.

## 19. Regulatory/compliance

Real and already breached once: telemarketing/calling-window norms,
call-recording consent (all-party-consent states), AI-disclosure choices,
CAN-SPAM for email, state wholesaling-practice rules (committed guardrail
pattern list encodes these). **These force Tier-3 artifacts for any decision
that changes live outreach/voice behavior.**

## 20. Existing evidence

**[`AI_SYSTEM_INVENTORY.md`](AI_SYSTEM_INVENTORY.md) is this field's value** —
the incumbent exists (19 AI surfaces, 7 live in prod), its observed failures
are enumerated (§6), and **no trusted measurement exists for any AI surface**
(§2): 0 evals in 110 AI-touching test files; the one scored harness fails
instrument-integrity basics. Operator hypothesis registered this session
(H-OP-1, see PLAYBOOK_PATH §"Predictions"): task units may be too coarse for
per-task insight — recorded to test, not adopted.

## 21. Stakes / consequence tolerance

**Tier 2 (Consequential) for this instantiation's evaluation work** — business
decisions (trust/repair/disable per surface, pricing inputs) ride on its
results; nothing about it is Tier-1-exploratory. **Named Tier-3 decisions**
(rule of proportion — tier attaches to the decision): anything that changes
live outreach/voice behavior or compliance posture, arms a surface, or lets an
AI output move money — these take Tier-3 artifacts (human-approval gates,
rehearsed rollback, record of record) and explicit operator authorization.
Driven by fields 3 and 19.

## Derived outputs

- **Archetype: C — existing system underperforming** (fix-what-exists).
  Routing facts: field 20 — an incumbent automated system exists; it has no
  established quality bar and no trusted measurement of its gaps (QUICKSTART
  node 2 fires on both clauses). Node 1 pre-check: no trusted eval → **eval
  first** (ch. 03 before any optimization or selection). Node 4 considered:
  compliance obligations are real but do not dominate the evaluation
  workstream's requirements; they are carried as the named Tier-3 decisions in
  field 21 rather than re-routing to E. Modifiers applied: **judge-graded
  outputs** (outreach copy is partly open-ended → split the bar, keep every
  checkable dimension deterministic, full judge-calibration protocol before
  any judged quality claim); **cross-surface comparisons planned** → ch. 02
  read before trusting any cross-lane number.
- **Stakes tier: 2**, with the named Tier-3 decision carve-outs of field 21.
- **Mandatory artifact set (Tier 2, archetype C):** PROJECT_PROFILE ·
  EXPERIMENT_CONTRACT · TEST_LOOK_LEDGER · PREDICTION_LEDGER ·
  PERFORMANCE_AUTOPSY · EVAL_SUITE_RELEASE_CONTRACT (implied — ch. 03 is in
  the entry path).
- **First three actions:** see [`PLAYBOOK_PATH.md`](PLAYBOOK_PATH.md) —
  (1) build/validate the first eval from harvested failures without changing
  the system, starting at the condition surface (rung 0: the instrument);
  (2) classify the observed-failure corpus into the canonical taxonomy;
  (3) pick the highest applicable ladder rung via a cheap pre-registered
  diagnostic gate and freeze the first experiment contract.
