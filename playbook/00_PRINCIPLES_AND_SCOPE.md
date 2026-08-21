# 00. Principles and Scope

> Part of the **Adaptive AI Systems Playbook** v0.1.0 ·
> [Index](README.md) · [Next →](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md)
> **Reading time:** ~15 min. **Prerequisites:** none. Read once; it binds everything.

## 1. Purpose and when to read this

This chapter is the normative core of the playbook: the principles every other
chapter instantiates. Read it once, before anything else. Every principle here is
either corroborated by external evidence, argued from first principles in place, or
explicitly labeled otherwise — and each carries an
[evidence-strength label](GLOSSARY.md#evidence-strength-labels).

The playbook exists for one job: given a concrete product or problem, candidate
models, owned or rentable compute, budgets, constraints, and a quality bar, derive a
defensible path — what to do next, why, what evidence is needed, what to measure,
what to skip, what should force a stop or change of direction, and when an expensive
intervention is justified.

## 2. Inputs required

None. This chapter is self-contained. Its outputs (the principles, the
[intervention ladder](GLOSSARY.md#intervention-ladder) in short form, and the
[rigor dial](GLOSSARY.md#rigor-dial)) are inputs to every other chapter.

## 3. Decisions this chapter supports

- Whether this playbook fits your project at all (§4.10, §9).
- Which obligations are non-negotiable at your stakes level (§6, the rigor dial).
- What may override a principle, and what that costs (§7).

## 4. Normative principles

**[PRINCIPLE] P1 — Evaluate first.** (consensus)
No selection, optimization, or training decision is made without a trusted
evaluation for the task. Building the evaluation is the first engineering act, not a
tax on the "real" work. Corroborated across vendor and practitioner guidance
[NV-AGENTICBLOGS-001], [EXT-EVAL-001], [EXT-EVAL-002], and by repeated field
experience that untrusted evals silently redirect entire projects
[CASE: CASE-004].

**[PRINCIPLE] P2 — The instrument outranks the score.** (strong-evidence)
Before believing any low score, validate the instrument: measure
[reachability ceilings](GLOSSARY.md#reachability-ceiling), check
[inversions](GLOSSARY.md#inversion-check), review cross-arm disagreement. A large
share of apparent model failures are instrument defects, and the two are initially
indistinguishable [EXT-EVAL-005], [CASE: CASE-004]. Diagnosis class RC-1 in the
[canonical failure taxonomy](GLOSSARY.md#canonical-failure-taxonomy) exists for this
reason and always ranks first.

**[PRINCIPLE] P3 — Evidence before intervention, in ladder order.**
(rung-0-first: strong-evidence, inherits P2; retrieval/prompt-before-fine-tuning on
knowledge tasks: strong-evidence [EXT-FT-001]; the full ten-rung ordering and
"never train around defects at rungs 0–4" as a general rule: inference — a cost
ordering, not an externally validated sequence)
Interventions on a measured gap follow the
[intervention ladder](GLOSSARY.md#intervention-ladder):

```
0 instrument integrity  →  1 infrastructure/runtime  →  2 evidence/retrieval/context
→  3 tool contracts & output enforcement  →  4 specification & verification
→  5 generation/reasoning budget  →  6 routing/escalation  →  7 fine-tuning
→  8 larger/different model  →  9 architectural redesign
```

Descending a rung requires evidence that cheaper rungs are exhausted or
inapplicable — a diagnosis, not impatience. Rung 0's priority rests on the same
instrument-first argument as P2. For knowledge/citation tasks specifically,
retrieval/prompt-first ahead of fine-tuning is externally corroborated by three
converging studies [EXT-FT-001]. The rest of the order — including generalizing
"never train (rung 7+) around defects at rungs 0–4" beyond knowledge tasks to tool
contracts, output enforcement, and verification gaps — is this playbook's own
cost-ordering heuristic, argued from first principles (cheaper, faster-to-diagnose
causes should be ruled out before an expensive, slow-to-diagnose one is assumed);
vendor guidance to "start lightweight, invest early in evaluation, and layer in
training-based techniques where measurement shows they're needed"
[NV-AGENTICBLOGS-001] is directionally consistent with it but does not corroborate
the specific ordering. Rungs 1–6 MAY be locally re-sequenced when a diagnosis
clearly identifies the cause class; rung 0's priority and the
never-train-around-defects rule stay normative regardless of their evidence class —
inference is why the rule is argued here, not a license to skip it. Chapter 07 is
the operational form.
*Override provision:* a documented, evidence-bearing
[method decision record](GLOSSARY.md#method-decision-record) may re-order rungs for
a project; silence may not.

**[PRINCIPLE] P4 — Decision quality over speed.**
(operator attention/measurement validity as the scarce resource: inference — first
principles; the wall-clock value of a stopping rule: case-study, scoped to the one
measured instance)
The scarce resources of a small lab are operator attention and measurement validity,
not compute. Stopping rules, tolerances, and gates exist to make decisions *priced
and chosen* rather than drifted into. In the one internally measured instance,
certainty curtailment would have recovered only about 2% of total wall clock
[CASE: CASE-001] — because that project's dominant arm happened to sit near its
qualification bar, not because a stopping rule's speed value is generically small;
on a project where hopeless arms dominate wall clock, or per-item cost is high, the
speed value can be genuinely large, and that is not itself a problem (§9). The
correct fix for an expensive failure mode is usually a consequence attached to a
tolerance, not a faster loop.

**[PRINCIPLE] P5 — Measurement validity before comparison.** (strong-evidence)
A number is comparable only within a
[frozen execution system](GLOSSARY.md#frozen-identity) and inside a *measured*
[reproducibility boundary](GLOSSARY.md#reproducibility-boundary). Runtime, provider,
harness, hardware, and configuration are part of the identity; nondeterminism is a
measured property, not an assumption [EXT-DETERM-001], [CASE: CASE-012]. Chapter 02
is the foundation; do not trust any cross-run number until you have read it.

**[PRINCIPLE] P6 — Frozen instruments, versioned change.** (strong-evidence)
Evaluation criteria drift as outputs are seen — this is an empirical finding about
humans, not a discipline failure [EXT-EVAL-004]. The response is versioned
[suite releases](GLOSSARY.md#suite-release) with
[cross-suite refusal](GLOSSARY.md#cross-suite-refusal), never silent in-place edits
[CASE: CASE-009].

**[PRINCIPLE] P7 — Pre-registration with consequences.** (consensus)
Decision-driving thresholds are fixed before data, and every tolerance names its
breach consequence in advance
([consequence-bearing tolerance](GLOSSARY.md#consequence-bearing-tolerance):
ABORT / RECALIBRATE / PROCEED-WITH-DECLARED-CEILING with the projected cost stated).
The pre-specification doctrine is clinical-trial consensus — pre-register the
adaptation rule, and let the rule execute rather than the investigator's mid-run
judgment [EXT-STOPPING-002]. A detection without a consequence is not a control
[CASE: CASE-001].

**[PRINCIPLE] P8 — Held-out evidence is consumable.**
(look-spend / overfitting-by-looking: inference — first-principles;
corpus contamination: strong-evidence [EXT-EVAL-006])
Every [look](GLOSSARY.md#look) at held-out data spends it
([spend semantics](GLOSSARY.md#spend-semantics)); exposure is recorded in a
[look ledger](GLOSSARY.md#look-ledger) and a pre-registered threshold triggers suite
refresh — repeated analyst access to the same held-out split degrades its
evidentiary value even with no leakage into the model, by the same logic as
adaptive/reusable-holdout analysis generally (argued here from first principles;
not yet corroborated by that literature directly). Corpus contamination is a
distinct, externally measured effect on scores — up to 8 percentage points of
accuracy drop has been documented on a benchmark's decontaminated successor
[EXT-EVAL-006] — and is the effect the look ledger's refresh threshold also guards
against.

**[PRINCIPLE] P9 — INCONCLUSIVE is a legitimate verdict.** (strong-evidence)
Every comparison carries a pre-computed [MDE](GLOSSARY.md#mde) on the design's
[effective N](GLOSSARY.md#effective-n); results below it are INCONCLUSIVE, never
"equivalent" or "no difference". Clustered suites can have an effective N several
times smaller than their item count, quietly voiding headline claims
[EXT-STATS-001], [CASE: CASE-002]. An experiment that cannot say INCONCLUSIVE will
eventually say something false.

**[PRINCIPLE] P10 — Fail closed, on a record of record.** (case-study + inference)
At Tier 2 and above (§6), work that lacks its prerequisites — registration, frozen
contract, integrity gates — is refused by machinery, not discouraged by convention;
results live in a tamper-evident [record of record](GLOSSARY.md#record-of-record).
First-principles argument: an unrecorded execution path will eventually be taken
exactly when it matters most, because that is when pressure is highest; mainstream
experiment-tracking tools provide lineage but not tamper evidence
[EXT-OPS-003], so the record of record is a deliberate build. Cheap tiers belong
*inside* this machinery as non-promotable states
([smoke tier](GLOSSARY.md#smoke-tier)), not beside it as relaxed lanes.

**[PRINCIPLE] P11 — Verification is part of the system.** (strong-evidence)
[Silent failure](GLOSSARY.md#silent-failure) — confident wrong output — is the most
expensive failure class. JudgeBench measures pairwise discrimination between a
correct and an incorrect response on hard knowledge/reasoning/math/coding items; a
frontier judge scored ~56.6% against a 50% pairwise-chance baseline
[EXT-JUDGE-002] — evidence that unvalidated judges are unreliable at discriminating
correctness on hard items, not a measurement of schema or exact-match grading,
which the study did not test. Wherever output is objectively checkable —
execution result, schema conformance, exact/fuzzy match — deterministic
verification is the default on determinism, cost, and auditability grounds; judges
require the calibration protocol of chapter 03 before their scores drive any
decision.

**[PRINCIPLE] P12 — Honesty about validation status.** (consensus)
Procedures this playbook prescribes but has not exercised carry
`status: doctrine — not yet exercised` — visibly. Evidence-strength labels attach to
every principle and default. A recent paper is never rendered as law; a single
project's result is never rendered as consensus.

## 5. Default procedure

The default lifecycle every project instantiates (QUICKSTART routes you into it;
chapters give each step's full procedure):

```
define the decision/problem            (01)
→ trustworthy eval substrate           (03)
→ instrument integrity / ceilings      (03)
→ simplest credible baseline           (05)
→ frozen execution-system identity     (02)
→ candidate characterization           (05, 06)
→ failure diagnosis                    (03 §taxonomy, 07)
→ intervention choice                  (07 → 08/09)
→ capability/quality evaluation        (04)
→ performance characterization         (06)
→ economics                            (11)
→ shadow/canary                        (10)
→ promote or roll back                 (10)
→ production evidence back into learning (12 → 03)
```

Two structural rules about the loop:
1. **Eval trust precedes optimization**; optimization precedes selection of
   expensive interventions; economics is consulted at intake, at capacity planning,
   and at deployment (chapter 11 is written to be entered three times).
2. The loop closes: production failures become eval candidates, then (in ladder
   order) retrieval fixes, then training data (12).

## 6. Project adaptation parameters — the rigor dial

Rigor is proportional to consequence, not to enthusiasm. The
[project profile](GLOSSARY.md#project-profile) captures a
[stakes tier](GLOSSARY.md#stakes-tier); QUICKSTART scales the mandatory artifact set
with it. *(The tier definitions and floor below are normative; the artifact mapping
is a default — calibrate it against your regulatory and contractual reality.)*

**[PRINCIPLE] The never-skippable floor.** (inference — first-principles)
At every tier, without exception:

1. State the decision the work drives and the claim to be evidenced.
2. Preserve enough execution-system/artifact provenance to identify what produced
   any result you might act on.
3. Define the evaluation/ground-truth boundary before making a quality claim.
4. Predeclare consequences for decision-driving thresholds and tolerances.
5. Treat held-out evidence as consumable; record exposure.
6. Retain outcome evidence.

Argument: each floor item is exactly the obligation whose absence cannot be repaired
after the fact. You can add statistics later; you cannot reconstruct what produced a
number, un-spend a held-out look, or retroactively attach a consequence to a
tolerance that already leaked.

**[DEFAULT] Tier artifact mapping.** (inference)

| Tier | Signature | Adds on top of the floor |
|---|---|---|
| **1 — Exploratory** | internal, reversible, low blast radius | lightweight profile; notes-grade pinned provenance; smoke-scale evals for direction (never for adoption claims) |
| **2 — Consequential** (default) | business decisions, customer-visible behavior | frozen [experiment contracts](GLOSSARY.md#experiment-contract); versioned suites + [static integrity gates](GLOSSARY.md#static-integrity-gates); MDE/effective-N statements + INCONCLUSIVE; look ledger; [prediction ledger](GLOSSARY.md#prediction-ledger); [demand ledger](GLOSSARY.md#demand-ledger) before purchases |
| **3 — High-stakes / regulated** | safety, money movement, compliance, audit | tamper-evident record of record; security/threat-model review (13); [pass^k](GLOSSARY.md#pass-at-k-vs-pass-to-the-k) reliability claims; judge calibration wherever judges are used; shadow→canary with human approval; rehearsed [rollback path](GLOSSARY.md#rollback-path); periodic methodology audit (12) |

**Boundary clarifiers:**
- Mandatory human review before an output reaches anyone does not, by itself,
  demote a project to Tier 1: an internal tool whose reviewed output drives a
  tracked business metric (efficiency, cost, staffing, throughput) is Tier 2, not
  Tier 1, whether or not a human edits or approves every item first. A Tier-1
  signature requires *both* low blast radius *and* no tracked business outcome
  riding on the output.
- When a project's signals point at different tiers — e.g., "internal-only" cuts
  toward Tier 1 while a real, measured business outcome cuts toward Tier 2 — take
  the higher tier.

**Rule of proportion:** rigor attaches to the *decision's* consequence, not the
project's prestige. A Tier-1 project making a Tier-3 decision (shipping to
production, moving money) escalates that decision to the higher tier's artifacts.

## 7. Decision gates and stopping conditions

**[DECISION GATE] Principle override.** A principle (P1–P12) may be overridden for a
project only by a written [method decision record](GLOSSARY.md#method-decision-record)
stating the evidence, the scope of the override, and the review date. Undocumented
deviation from a PRINCIPLE invalidates the affected claims at Tier 2+.

**[STOP CONDITION] Global tripwires.** Stop and re-plan when any of these fires
(QUICKSTART carries the same list; chapters add local ones):

1. A quality claim is about to be made with no trusted eval behind it (P1).
2. A stratum's measured ceiling is below its passing threshold (P2 — the instrument
   is broken; scores are meaningless).
3. A comparison is about to cross an unmeasured reproducibility boundary (P5).
4. A pre-registered tolerance was breached and the named consequence is being
   argued with instead of executed (P7).
5. A training or hardware-purchase decision is being made below the ladder's
   evidence bar (P3) or without the demand ledger/purchase trigger (11).
6. A result below the design's MDE is being read as a difference or an equivalence
   (P9).
7. Held-out exposure has hit the pre-registered refresh threshold (P8).
8. A learned or automated component is about to act on live traffic without a
   passed leakage audit and an observe-only period (08).

## 8. Metrics and formulas

N/A — this chapter defines principles; the statistics canon lives in chapter 04 and
[references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md).

## 9. Failure modes and anti-patterns

**[REJECTED]** (condition: always — these are generically wrong)

- **Unpriced escape hatches**: a tolerance whose breach clause is "record and
  proceed" at no stated cost. The failure is not detection — it is that detection
  carries no consequence [CASE: CASE-001].
- **Judges on verifiable tasks without calibration**: using an LLM judge, instead of
  a deterministic check, to grade schema conformance, exact/fuzzy match, or another
  deterministically checkable output. JudgeBench found frontier judges weak
  (~56.6% against a 50% pairwise-chance baseline) at discriminating correct from
  incorrect responses on hard knowledge/reasoning/math/coding items [EXT-JUDGE-002]
  — it did not test schema or exact-match grading, but the direction generalizes:
  where a deterministic check exists, an uncalibrated judge replaces a free,
  auditable measurement with a noisier and costlier one.
- **Promoting sub-MDE margins to decisions**: adopting or eliminating a candidate on
  a margin the design cannot resolve [CASE: CASE-002], [CASE: CASE-010].
- **Benchmark worship**: treating public leaderboard scores as evidence about your
  task, your harness, your budget, or your failure modes.
- **The relaxed lane**: a parallel "quick" execution path outside the provenance
  machinery. It recreates the unrecorded path the machinery exists to forbid; cheap
  tiers go inside as non-promotable states (P10).
- **"The model got better/worse"** when the runtime, provider, quantization,
  harness, or budget changed (P5) [CASE: CASE-006], [CASE: CASE-008].

**[REJECTED]** (condition: a stopping rule's guards are being weakened, skipped, or
argued against *because* they cost wall clock)
- **Speed rationales for stopping rules**: the rejection targets adopting or
  justifying a rule *by* a speed rationale, or trading away one of its guards to
  save time — not the possibility that a correctly-guarded rule also runs faster.
  Stopping rules purchase decision quality; a rule adopted for decision quality MAY
  incidentally save time too, and that is a welcome side effect, not the
  justification. In the one internally measured instance the recoverable wall
  clock was small — about 2% of the run [CASE: CASE-001] — but the rejection does
  not depend on that number, and does not become weaker on a project where the
  speed value is genuinely large (P4).

## 10. Vendor recipes

This playbook uses [vendor verdicts](GLOSSARY.md#vendor-verdicts) —
FOLLOW / ADAPT / REFERENCE / DEPRECATED — with as-of dates, recorded in
[references/sources.yaml](references/sources.yaml) and rendered in
[references/SOURCES.md](references/SOURCES.md). The structural finding behind them
(as of 2026-08, re-verified this release): vendor execution mechanics are strong and
current; the *decision layer* — stop, promote, select, buy, trust — is what vendors
do not publish, and it is precisely what this playbook supplies. Where a vendor
methodology is genuinely mature (inference benchmarking [NV-INFERBENCH-001]), the
verdict is FOLLOW BY THE BOOK; where mechanics are sound but decisions are missing,
ADAPT with the substitution stated.

## 11. Worked examples

- [CASE-001](examples/CASE-001_consequence-bearing-tolerances.md) — a measured 5×
  tolerance breach proceeded unpriced; what a consequence clause would have changed.
- [CASE-002](examples/CASE-002_clustered-eval-effective-n.md) — clustering silently
  collapsed a 96-item suite to ~22 effective pairs.
- [CASE-004](examples/CASE-004_harness-defects.md) — thirteen instrument defects
  initially indistinguishable from model weakness.
- [WALKTHROUGH](examples/WALKTHROUGH_rag-document-qa.md) — the full lifecycle run on
  a synthetic non-trivial project.

## 12. Outputs and artifacts

- Your project's stakes tier and mandatory-artifact set (into
  [templates/PROJECT_PROFILE.md](templates/PROJECT_PROFILE.md), chapter 01).
- Any principle overrides, as
  [method decision records](templates/METHOD_DECISION_RECORD.md).

## 13. Sources

| ID | Role here |
|---|---|
| [NV-AGENTICBLOGS-001] | Vendor corroboration of evaluate-first ordering (verified live 2026-08-21) |
| [EXT-EVAL-001], [EXT-EVAL-002] | Consensus eval-first guidance (note: the hosted OpenAI Evals platform sunsets 2026-11; the methodology stands) |
| [EXT-EVAL-004] | Criteria drift — empirical basis for frozen, versioned instruments |
| [EXT-EVAL-005], [EXT-EVAL-006] | Instrument-defect scale; contamination effects |
| [EXT-STATS-001] | Clustering/effective-N/MDE machinery |
| [EXT-STOPPING-002] | Pre-registered adaptation rules; the rule executes, not the investigator |
| [EXT-JUDGE-002] | JudgeBench: judges ~56.6% vs. 50% pairwise-chance discriminating correctness on hard items |
| [EXT-DETERM-001] | Nondeterminism as a measured property |
| [EXT-FT-001] | Retrieval/prompt-first direction for knowledge tasks |
| [EXT-OPS-003] | Lineage tools lack tamper evidence — why the record of record is built |
| [INT-CASE-001], [INT-CASE-002], [INT-CASE-004], [INT-CASE-006], [INT-CASE-008], [INT-CASE-009], [INT-CASE-010], [INT-CASE-012] | Empirical case evidence backing P2, P4–P9 |

Gap dispositions in this chapter: **G2 (rigor sizing): COVERED** (§6, with the
profile capture in 01 and the QUICKSTART application).

---

> [Index](README.md) · [Next →](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md)
