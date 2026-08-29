# Experiment Contract

The frozen, pre-registered document that defines an
[experiment contract](../GLOSSARY.md#experiment-contract) before any data is collected
or acted on. It is the primary instrument of
[pre-registration](../GLOSSARY.md#pre-registration) in this playbook: it exists so
that thresholds, tolerances, and analysis choices are fixed *before* anyone has seen
an outcome, and so a reviewer can tell, after the fact, whether the run that produced
a claim actually followed the rules it was bound by.

> Index: [../README.md](../README.md) · Governing chapter: [04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md) (also [02. Execution System Model](../02_EXECUTION_SYSTEM_MODEL.md), [07. Optimization and Intervention Ladder](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md))

## When to use / when not to use

- **MUST** use this template for any comparison, selection, or adoption decision
  whose outcome will be acted on outside the lab (shipped, presented as a result,
  used to eliminate a candidate, or used to justify spend) — i.e. any Tier 2 or
  Tier 3 decision under the [rigor dial](../GLOSSARY.md#rigor-dial). See
  [Rigor-tier applicability](#rigor-tier-applicability) below.
- **SHOULD** use a lightweight subset (§1, §2, §5, §6, §11) for Tier 1 exploratory
  work where you still want a written record of what you tried and why — completing
  the full contract is optional at Tier 1 but the six
  [never-skippable floor](../GLOSSARY.md#never-skippable-floor) obligations still
  apply regardless of tier.
- **Do not** use this template for a diagnostic probe that only decides whether a
  full experiment is worth running — that is a [diagnostic gate](../GLOSSARY.md#diagnostic-gate)
  and is deliberately cheaper; it still gets a short written pre-registration of its
  decision bands, but not this document's full apparatus.
- **Do not** use this template for routine regression checks against an already-frozen
  [suite release](../GLOSSARY.md#suite-release) — that is ordinary CI, not an
  experiment; use it only when a *comparison* or *decision* is being made.
- One contract per experiment. A candidate that fails and returns with a changed
  hypothesis is a new contract, not an edit to this one — edits to a frozen contract
  are governed by §18 Amendment Log, not by rewriting sections above it.

## Rigor-tier applicability

| Tier | Requirement |
|---|---|
| Tier 1 — Exploratory | Not required in full. The lightweight subset above is recommended. Smoke-scale or informal comparisons from this tier **MUST NOT** be cited as adoption evidence — see [smoke tier](../GLOSSARY.md#smoke-tier). |
| Tier 2 — Consequential (default) | **MUST** be completed and frozen (§"Freeze Checklist") before any [iterate-split](../GLOSSARY.md#screening-vs-inference) evidence is used for a decision. This is the default tier and the default use of this template. |
| Tier 3 — High-stakes/regulated | **MUST** be completed as Tier 2, plus: pass^k reliability plan is mandatory wherever any arm is stochastic (§10), provenance in §3/§14 binds into the tamper-evident [record of record](../GLOSSARY.md#record-of-record), and any judge used is calibration-gated before its output can qualify a candidate (chapter 13). |

Rigor attaches to the *decision's* consequence, not the project's declared tier: a
Tier 1 project whose result will drive a Tier 3 decision (e.g., "ship to production")
completes this contract at Tier 3 rigor for that decision. See chapter 00 §(rigor
dial) and [PROJECT_PROFILE.md](PROJECT_PROFILE.md).

---

## The Contract

*Fill every section below for the experiment being registered. Placeholders in
`[brackets]` carry inline guidance in italics — replace the placeholder, keep or
delete the guidance. No section may be silently omitted; see
["Delete no section"](#delete-no-section) at the end of this document.*

### 1. Question, Decision, and Prediction Register

- **Question:** [the single question this experiment answers, stated so a stranger
  could grade the outcome without asking you anything else]
- **Decision this experiment drives:** [the concrete action taken on each possible
  outcome — "if the primary metric improves by ≥X we ship variant B", not "we'll see
  what the data says"]
- **Non-goals:** [what this experiment explicitly does not attempt to answer —
  scope creep during analysis is a common source of post-hoc rationalization]
- **Prediction register** *(filled before the first call is made; scored after —
  feeds [PREDICTION_LEDGER.md](PREDICTION_LEDGER.md))*:

  | Primary metric | Predicted point estimate | Predicted interval | Rationale (1 line) |
  |---|---|---|---|
  | [metric] | [value] | [low, high] | [why you expect this] |

### 2. Frozen Scientific Baseline

- **Suite version:** [the exact [suite release](../GLOSSARY.md#suite-release)
  identifier this experiment runs against — never "latest"]
- **Corpus identity:** [content digest or generation-determinism statement]
- **Scorer/verifier identity:** [deterministic scorer version; judge + calibration
  record if any judge is used — chapter 13]
- **Incumbent(s) that must not move during this experiment:** [name the baseline
  arm(s) and state the guarantee that they are not being simultaneously modified —
  a moving baseline invalidates every comparison against it]

### 3. Artifacts

*Every model artifact by content hash + upstream identity; every self-produced
artifact by its training-provenance record. An artifact identified only by a
human-readable name (e.g. a model family and a release date) is not pinned — the
upstream provider can redeploy under that name and silently break comparability.*

*Managed-API arm: no content hash is obtainable in principle (the weights are not
exposed). Pin instead by provider model-version string + endpoint/region + as-of
timestamp, plus a recorded
[provider-redeploy probe](../02_EXECUTION_SYSTEM_MODEL.md) result (02 §5 Step 2) —
and write into §4's reproducibility boundary that this arm's identity is the
weaker, probed-not-hashed form; the comparability claim is scoped to the probed
window, not assumed to hold indefinitely. See 02 §6: a managed-API-only project
needs the provider-redeploy probe and nothing else from this list.*

| Arm | Artifact | Content hash / digest | Upstream identity (provider, version, as-of date) | Provenance record (if self-produced) |
|---|---|---|---|---|
| [A] | [artifact] | [hash] | [identity] | [link or N/A] |
| [B] | [artifact] | [hash] | [identity] | [link or N/A] |
| [managed-API arm, if any] | [model name] | N/A — no digest obtainable; see managed-API pinning note above | [provider], [model-version string], [endpoint/region], as-of [date] | [provider-redeploy probe result + date, 02 §5 Step 2] |

### 4. Execution Systems and Node Placement

*State the full [execution system](../GLOSSARY.md#execution-system) per arm — model +
artifact/quantization/adapter + runtime/provider + hardware/host + harness + context
policy + retrieval/knowledge + tools + workflow + generation/reasoning budget +
verifier/grader + environment. Never collapse these into one ambiguous label.*

- **Per-arm execution-system identity:** [table or list, one row per arm — pinned
  builds/config/hosts]
- **Node placement:** [which arm runs on which host/node; if arms run on different
  hardware, state whether the comparison is intended to isolate the manipulated
  variable (§5) or whether hardware is itself part of what is being compared]
- **Rented-node rules** *(if any arm runs on rented/ephemeral compute)*: single
  session per arm for the duration of the run; artifact digests verified
  post-transfer, on the remote node, before the run starts — not assumed from the
  upload step. See [reproducibility boundary](../GLOSSARY.md#reproducibility-boundary),
  [SCENARIO-12](../examples/SCENARIO-12_restart-instability-paired-controls.md).
- **Reproducibility boundary declared:** [same session / across restarts / across
  hosts / under concurrency — state which boundary this experiment's claims are
  scoped to; measured, not assumed [EXT-DETERM-001]]

### 5. Manipulated Variable and Controlled Variables

- **Manipulated variable:** [the ONE factor that differs between arms, precisely
  named]. **MUST** be a single factor per arm unless a factorial design is
  pre-registered explicitly (state the factorial structure if so).
- **Controlled variables:** [everything else, and how each is held fixed — this list
  should be long; anything not listed here and not the manipulated variable is a
  latent confound]

  *Manipulated-variable examples by experiment type (generic — substitute your own):*

  | Experiment type | Typical manipulated variable | Typical controlled variables |
  |---|---|---|
  | Model selection | model artifact | prompt, runtime, context policy, tools, budget |
  | Quantization | quantization/precision format | model weights identity, runtime, hardware |
  | Prompt/workflow | prompt text or workflow structure | model, runtime, tools, budget |
  | Retrieval | retrieval strategy or corpus | model, prompt, verifier, tools |
  | Reasoning/generation budget | token or turn budget | model, prompt, tools |
  | Routing/cascade | gate rule or escalation policy | tier artifacts, verifier |
  | Fine-tuning | base vs. fine-tuned adapter | eval suite, decoding config, prompt |
  | Hardware/runtime | host, device, or serving stack | model artifact, prompt, budget |

### 6. Split Protocol

- **Iterate split:** [role — free exploration, calibration (§7), screening (§8); not
  used for any inference claim]
- **Qualification split:** [role — one read per candidate per
  [one-look discipline](../GLOSSARY.md#one-look-discipline); selection decisions only]
- **Confirmation split:** [role — one read for the final verdict; see §13]
- **Execution ordering:** [MUST be] [stratum-interleaved / 
  [round-robin](../GLOSSARY.md#round-robin-ordering) across strata] so that any
  prefix of the run is representative — stratum-blocked execution order is the worst
  case for any interim decision rule.
- **Screening rungs (if any):** [stratum-balanced; state the rung schedule; screening
  produces ranks, never significance claims — see
  [screening vs inference](../GLOSSARY.md#screening-vs-inference)]
- **Look-ledger entry planned at freeze:** [the row(s) this experiment will add to
  [TEST_LOOK_LEDGER.md](TEST_LOOK_LEDGER.md) — split, expected item count, expected
  date — committed now, filled in after execution]

### 7. Calibration Rules

*Iterate split only. Every calibrated parameter gets a
[consequence-bearing tolerance](../GLOSSARY.md#consequence-bearing-tolerance) — a
tolerance without a named consequence is an unpriced escape hatch and fails contract
review.*

| Parameter | Calibration procedure | Tolerance | Consequence on breach | Projected cost if PROCEED |
|---|---|---|---|---|
| [parameter] | [how it is measured/derived] | [e.g. "≤k violations in n items"] | ABORT / RECALIBRATE / PROCEED-WITH-DECLARED-CEILING | [cost stated in writing, only if PROCEED is the chosen consequence] |

Evaluated by [curtailed exact counting](../GLOSSARY.md#curtailed-exact-counting):
halt the calibration phase at violation k+1 and escalate to the named consequence.
This is a count, not a hypothesis test, and carries no error-rate claim — it is not
subject to the clustering caveats that affect i.i.d.-calibrated sequential rules
(see §10).

### 8. Candidate Selection and Elimination Rules

- **Selection metric:** [the single metric that decides which candidate(s) advance
  from the qualification split]
- **Pilot MDE:** [the [MDE](../GLOSSARY.md#mde) computed on the pilot/iterate-split
  data — this number gates the elimination rule below]
- **Elimination rule:** No candidate is withdrawn on a margin smaller than the pilot
  MDE stated above. See [elimination rule](../GLOSSARY.md#elimination-rule).
- **Sub-MDE handling** *(choose one, pre-registered)*:
  - [ ] Both candidates proceed to confirmation under a pre-registered budget.
  - [ ] The decision defers to the confirmation split's own read.
  - [ ] The selection metric changes to one the pilot data can resolve — [state the
    replacement metric now, not after seeing which one favors which candidate].

### 9. Feasibility Probes

*Cheap pre-flight checks that a candidate can physically complete the experiment at
all — run before spending qualification/confirmation splits.*

- **Stability probe:** [does the execution system produce consistent output across
  repeated identical calls within the declared reproducibility boundary (§4)?]
- **Context-fit probe:** [does the largest expected input, plus tool/retrieval
  overhead, fit the candidate's context budget with the declared generation budget
  still available?]
- **Memory/capacity probe:** [does the candidate fit the target hardware/serving
  configuration at the intended concurrency without degrading below the operating
  point chapter 06 requires?]
- Each probe: [pass/fail threshold] → [action if failed — typically ABORT before any
  split is spent]

### 10. Statistical Plan

- **Clustering unit:** [the grouping within which outcomes correlate — stratum,
  document, template, session; see
  [clustering unit](../GLOSSARY.md#clustering-unit)]
- **Expected discordance:** [estimated share of items where arms disagree, from
  pilot data — feeds the MDE calculation]
- **ICC estimate and source:** [value and how it was estimated, e.g. ANOVA on
  per-cluster indicators — never assumed zero]
- **Design effect and effective N:** DEFF = 1 + (m − 1) × ICC; N_eff = N / DEFF.
  [computed values]. See
  [design effect](../GLOSSARY.md#design-effect),
  [effective N](../GLOSSARY.md#effective-n),
  [references/STATISTICS_FORMULAS.md](../references/STATISTICS_FORMULAS.md).
- **MDE at α = .05, power = .80:** [computed value, using N_eff above]. Reported
  regardless of outcome; margins below MDE are
  [INCONCLUSIVE](../GLOSSARY.md#inconclusive), never "equivalent" or "no
  difference" [EXT-STATS-001].
- **Primary inference:** cluster-robust paired inference (t-test on per-cluster
  paired means, df = clusters − 1).
- **Secondary inference:** McNemar exact on discordant pairs, labeled
  anti-conservative under clustering [NV-EVALSDK-001], [EXT-AMAZON-LLMSTATS-001].
- **Verdict readings, written before data:** [state, for each primary metric, what
  result maps to CONFIRMED / REFUTED / INCONCLUSIVE — see
  [verdict vocabulary](../GLOSSARY.md#verdict-vocabulary)]
- **pass^k plan** *(required if any arm is stochastic)*: [k value, declared subset,
  and the claim it supports — pass^k measures reliability under repetition, not
  pass@k capability under retry [EXT-AGENT-001]]

  **[REJECTED]** (condition: outcomes cluster within stratum-ordered execution) —
  i.i.d.-calibrated sequential tests (SPRT, always-valid confidence sequences)
  inflate their nominal error rate under clustered, ordered execution. Use curtailed
  exact counting (§7, §13) instead, or verify independence of the execution order
  first. See [sequential-rule admissibility](../GLOSSARY.md#sequential-rule-admissibility).

### 11. Generation and Runtime Configuration per Arm

*Frozen for the duration of the experiment — a mid-run change to any of these
values creates a new execution system (§4) and voids comparability to data already
collected under the old one.*

| Arm | Decoding params (temp, top-p, etc.) | Max generation/reasoning budget | Tool/retrieval budget | Concurrency/operating point |
|---|---|---|---|---|
| [A] | [values] | [value] | [value] | [value] |
| [B] | [values] | [value] | [value] | [value] |

### 12. Qualification Gates

*Numeric, fixed from historical (iterate-split) data only — never derived from the
qualification split itself. Each gate names its consequence.*

| Gate | Threshold (from historical data) | Consequence on failure |
|---|---|---|
| [e.g. minimum reachability ceiling on the stratum used] | [value] | [candidate does not advance to confirmation] |
| [gate] | [value] | [consequence] |

### 13. Confirmation Protocol

- **One look:** the confirmation split is read exactly once per candidate for the
  final verdict — see [one-look discipline](../GLOSSARY.md#one-look-discipline).
- **Certainty-curtailment clause:** **default-on.** Stop the confirmation arm early
  under [certainty curtailment](../GLOSSARY.md#certainty-curtailment) when
  `passes + items_remaining < ⌈bar × N⌉` — the remaining items cannot change the
  outcome. Carries three mandatory guards, copied in from the definition:
  1. **Spend semantics:** the split is spent at the first executed item, not the
     last — no peeking and re-running. See [spend semantics](../GLOSSARY.md#spend-semantics).
  2. **Interval-only partial reporting:** a curtailed arm reports its result as an
     interval bound, never as a point estimate presented as if the full N had run.
  3. **Paired-comparison firewall:** a curtailed arm's items **MUST NOT** enter any
     paired comparison — curtailing deletes items non-randomly by stratum
     composition and can flip a paired test outcome compositionally. See
     [paired-comparison firewall](../GLOSSARY.md#paired-comparison-firewall).
  - **Disabling this clause** requires a written justification in §18 (Amendment
    Log) recorded *before* the confirmation run starts, not after seeing partial
    results.
- **Human-approval gate** *(mandatory at Tier 3 — shadow→canary with human
  approval, chapter 00 §6; add wherever a human sign-off gates the confirmed
  verdict's production consequence, whatever the tier)*: [who approves — a named
  role, not "the team" — before this experiment's verdict is allowed to drive
  production action]; [at what stage — after the confirmation-split read, before
  promotion/shipping]; [what happens on rejection — hold at current state /
  RE-SCOPE / escalate to the decision owner named in
  [PROJECT_PROFILE.md](PROJECT_PROFILE.md) field 21]. This is distinct from §17's
  scientific-owner/executor roles: those govern the experiment's *execution*; this
  gate governs whether the experiment's *output* is allowed to act on production.

### 14. Run States and Integrity Controls

- **Fail-closed requirements:** [work lacking its prerequisites — frozen contract,
  registration, integrity gates — is refused by machinery, not convention. See
  [fail-closed](../GLOSSARY.md#fail-closed).]
- **Contract binding:** this contract is bound to the run by [content hash / stated
  binding mechanism] — a run whose contract hash does not match this document's
  frozen hash is not a run of this experiment.
- **Ground-truth isolation:** [statement that gold labels are structurally
  unreachable from any model-facing surface for the duration of this run — see
  [ground-truth isolation](../GLOSSARY.md#ground-truth-isolation)]
- **Diagnostic run kinds:** [any diagnostic/smoke runs associated with this
  experiment are recorded under a non-promotable
  [diagnostic run kind](../GLOSSARY.md#diagnostic-run-kind) — they inform, they
  cannot qualify a candidate]

### 15. Telemetry Requirements

- **Dual-clock stamps:** [realtime + monotonic on every measured span — see
  [dual-clock telemetry](../GLOSSARY.md#dual-clock-telemetry)]
- **Authoritative clock per metric:** [state which clock each published metric is
  computed from — see [authoritative clock](../GLOSSARY.md#authoritative-clock)]
- **Lifecycle events:** [run start/end, per-arm start/end, per-item start/end —
  minimum event set]
- **Per-invocation stats:** [tokens, latency, finish reason, cost — minimum field
  set per call]
- **Logs preserved:** [server/engine logs retained for the run's duration, not
  rotated away before the analysis in §16 can use them]
- **Resource sampler threshold:** [sampling interval for GPU/CPU/memory telemetry,
  if applicable]

This is the [telemetry floor](../GLOSSARY.md#telemetry-floor); post-run forensics
cannot be retrofitted onto a run that did not collect it.

### 16. Analysis Plan

- **Tables/reports produced:** [list the exact tables this experiment will produce
  — decided now, not chosen after seeing which framing favors the preferred arm]
- **Replays planned:** [any offline replay of stored outputs against a re-scored
  suite — counts as a [look](../GLOSSARY.md#look), enter it in §6's look-ledger plan]
- **Economics:** [cost accounting per arm, feeding
  [COMPUTE_DEMAND_LEDGER.md](COMPUTE_DEMAND_LEDGER.md); if a routing/cascade claim
  is made, state the [break-even](../GLOSSARY.md#break-even) formula and inputs here]

### 17. Roles

- **Scientific owner:** [name/role] — interprets results, owns the verdict, is the
  only role authorized to invoke §18 amendments.
- **Executor:** [name/role] — runs the contract's rules as written; does not
  improvise thresholds, ordering, or stopping decisions mid-run.
- The contract executes. Deviation from a frozen rule during a run is not a judgment
  call available to the executor — it is either within a pre-registered adaptation
  rule (§18) or it invalidates the run for this contract's purposes.
- These two roles govern the experiment's *execution* and its scientific verdict
  only. Whether that verdict is then allowed to act on production is a separate,
  mandatory-at-Tier-3 gate — see the Human-approval gate in §13.

### 18. Amendment Log

*Append-only after freeze. An amendment is legitimate only if: the amendment
procedure itself was pre-registered; it derives only from iterate-split evidence via
formulas fixed at freeze; it is committed before any qualification/confirmation
execution; its direction of benefit is disclosed; and any amendment that moves
toward permitting a pass carries a mandatory skeptical-reader note. See
[amendment legitimacy](../GLOSSARY.md#amendment-legitimacy).*

| # | Date | Section amended | Reason | Direction of benefit disclosed | Skeptical-reader note (if applicable) |
|---|---|---|---|---|---|
| [1] | [date] | [§n] | [reason] | [favors A / favors B / neutral] | [note or N/A] |

---

## Freeze Checklist

**All of the following MUST be true before any qualification/confirmation-split
item executes, and before any iterate-split evidence is used for inference.** This
section is itself frozen once checked — see [freeze](../GLOSSARY.md#freeze). This
is an exact restatement of the canonical eight-item freeze gate defined in
[04 §7](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md) (Decision gates and stopping
conditions); [14 §6.1](../14_DECISION_TREES_AND_CHECKLISTS.md) condenses the same
eight items and adds no items of its own.

- [ ] **Contract committed, content-hash bound** — before any
  qualification/confirmation execution, and before any iterate-split evidence is
  used for inference. *Cold-start path:* freeze MAY carry a declared prior ICC
  (§10) plus a pre-registered re-estimation procedure; the re-estimation MUST
  complete before the qualification look.
- [ ] Every calibrated parameter's tolerance (§7) names ABORT / RECALIBRATE /
  PROCEED-WITH-DECLARED-CEILING, with the projected PROCEED cost pre-registered
  now — not written after a breach is observed.
- [ ] Statistical plan (§10) is written: clustering unit, ICC (measured, or a
  declared prior with its re-estimation procedure), DEFF, N_eff, MDE, and the
  verdict-reading table.
- [ ] Prediction-ledger entry (§1) is filled.
- [ ] Look ledger (§6) is updated with the planned look(s).
- [ ] Execution-system identity and authoritative clock are declared per arm, and
  node placement is pre-registered (§4, §15).
- [ ] Elimination-rule threshold (§8 pilot MDE) is stated.
- [ ] Curtailment clause and its three guards are stated (§13), or the clause is
  disabled with a written justification recorded in §18.

**Template-implementation checks** *(this template's own additions, tied to its
own sections — not part of 04 §7's normative eight; do not read these into other
contracts or into 14 §6.1's condensation)*:

- [ ] Smoke/integrity pass recorded — harness, schema, and tool-contract integrity
  checked before real spend (§9 Feasibility Probes; §14 fail-closed requirements).
- [ ] Stratum-interleaved round-robin execution ordering declared (§6).

## Delete No Section

Every numbered section above **MUST** appear in a filled contract. If a section
genuinely does not apply to this experiment, write the section header with the body
`N/A — [reason]` rather than omitting it. Absence is a decision, and a reviewer
needs to see that the decision was made rather than skipped.

---

## Miniature Filled Example

*Illustrative example — synthetic. Invented project: an invoice-triage assistant
that reads incoming vendor invoices and routes each to one of three approval
queues. Tier 2 (business decision, customer-visible routing behavior). Condensed —
a real contract fills every field in every section above; this shows the shape.*

**§1 Question/decision:** Does a structured-extraction-first prompt (extract fields
to JSON, then classify) reduce misrouted invoices versus the current
free-text-reasoning prompt? Decision: adopt the new prompt if misrouting drops by
≥3pp with no throughput-cost increase >15%. Prediction: −4pp misrouting, interval
[−7pp, −1pp].

**§2 Baseline:** Suite `invoice-triage-eval v4`. Verifier: deterministic
field-match scorer v4. Incumbent: current free-text prompt, frozen, not modified
during this experiment.

**§3 Artifacts:** Both arms use the same underlying model artifact
(`sha256:3f9a…`); only the prompt template differs.

**§5 Manipulated variable:** prompt structure (free-text vs. extract-then-classify).
Controlled: model, decoding params, tools, retrieval, budget.

**§6 Split protocol:** Iterate = 400 historical invoices (calibration only).
Qualify = 600, stratum-interleaved by vendor-category. Confirm = 600, one look.

**§7 Calibration:** JSON-parse failure rate on iterate split; tolerance ≤2 in 50;
breach → RECALIBRATE (add one-shot example) once, else ABORT.

**§8 Selection:** Pilot MDE = 2.1pp. Misrouting-rate delta is the selection metric;
sub-MDE handling: defer to confirmation split.

**§10 Statistics:** Clustering unit = vendor-category. ICC estimated at 0.09 from
iterate data. m ≈ 12 → DEFF ≈ 1.99 → N_eff ≈ 302 on N=600. MDE at α=.05/power=.80 ≈
2.8pp. Primary: cluster-robust paired t-test on per-category means. Secondary:
McNemar exact (anti-conservative, reported alongside).

**§12 Qualification gate:** Reachability ceiling on the "missing-PO-number" stratum
must be ≥90% (measured on iterate data) or that stratum is excluded from scoring.

**§13 Confirmation:** Certainty curtailment default-on; bar = 55% pass rate
required to beat incumbent by the pre-registered margin.

**Freeze checklist:** all eight canonical items plus both template-implementation
checks (10 total) checked 2026-03-02, before qualification-split execution began.

---

**Governing chapters:** [04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md)
· [02. Execution System Model](../02_EXECUTION_SYSTEM_MODEL.md)
· [07. Optimization and Intervention Ladder](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md)

**Related templates:** [PROJECT_PROFILE.md](PROJECT_PROFILE.md) ·
[EVAL_SUITE_RELEASE_CONTRACT.md](EVAL_SUITE_RELEASE_CONTRACT.md) ·
[TEST_LOOK_LEDGER.md](TEST_LOOK_LEDGER.md) ·
[PREDICTION_LEDGER.md](PREDICTION_LEDGER.md) ·
[COMPUTE_DEMAND_LEDGER.md](COMPUTE_DEMAND_LEDGER.md) ·
[METHOD_DECISION_RECORD.md](METHOD_DECISION_RECORD.md)

[Index](../README.md) · [Glossary](../GLOSSARY.md)
