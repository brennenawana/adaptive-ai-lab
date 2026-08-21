# 08. Retrieval, Tools, Workflows, and Routing

> Part of the **Adaptive AI Systems Playbook** v0.1.1 ·
> [← Previous](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md) · [Index](README.md) · [Next →](09_TRAINING_AND_DATA.md)
> **Reading time:** ~24 min. **Prerequisites:** [00](00_PRINCIPLES_AND_SCOPE.md), [02](02_EXECUTION_SYSTEM_MODEL.md), [03](03_EVALUATION_FOUNDATION.md), [07](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md).

## 1. Purpose and when to read this

This chapter covers rungs 2, 3, and 6 of the [intervention ladder](GLOSSARY.md#intervention-ladder): what the system can *know* (retrieval, tools, context) and what it does with an escalation decision (routing, cascades). Read it when a diagnosis from [chapter 07](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md) lands on RC-3 (missing/unreachable evidence), RC-4 (tool/API contract defect), or RC-9 (routing/escalation mismatch) in the [canonical failure taxonomy](GLOSSARY.md#canonical-failure-taxonomy) — or before any of those rungs are built, since the properties this chapter defines are cheap to design in and expensive to retrofit.

Three questions this chapter answers:

1. Is the evidence a task needs actually obtainable through the tools the system has, from what it knows when it needs to know it?
2. What must a tool's contract guarantee before its results are trustworthy inputs to a model *and* to an evaluation?
3. When is a cheap tier good enough, when does a task need an expensive one, and what is allowed to decide?

Workflow structure — how a task is decomposed into steps and tool calls — is this chapter's concern only insofar as it determines what evidence becomes reachable and when. Specifying *what a step should do* (prompts, instructions, decomposition text) is rung 4 (RC-6, task-specification gap), not this chapter.

## 2. Inputs required

- A diagnosis from chapter 07 naming RC-3, RC-4, or RC-9 — or a design-time decision to build retrieval/tools/routing before any diagnosis exists.
- The [task ontology](GLOSSARY.md#task-ontology) and per-stratum evidence requirements from [chapter 03](03_EVALUATION_FOUNDATION.md).
- The tool surface the deployed system will actually call — schemas, backing store, and any proxy/gateway hop between model and tool — not a description of it.
- Per-tier unit costs (weak/strong/frontier) and a verifier or scorer capable of judging correctness, if routing is in scope.
- The project's [stakes tier](GLOSSARY.md#stakes-tier) (from [templates/PROJECT_PROFILE.md](templates/PROJECT_PROFILE.md)) — it sets the graduation and rollback bar for any automated routing decision.

## 3. Decisions this chapter supports

- Whether a low score on a stratum is a model weakness (RC-10/RC-11) or an evidence-reachability defect (RC-3) that is unfair to charge to the model.
- What a tool's contract must specify before it is trustworthy, and how that contract is versioned.
- Deterministic gate vs. learned router for a cascade, and what a learned router must clear before it competes at all.
- Whether routing pays for itself, and at what offload share.
- Whether a routing or decision component may move from observe-only to automated action, and what rehearsing that move costs.

## 4. Normative principles

**[PRINCIPLE] Evidence reachability is measured, not argued.** (strong-evidence)
[Evidence reachability](GLOSSARY.md#evidence-reachability) — every fact a task requires is actually obtainable through the deployed tool set, from what the system can know at call time — is an analytic property of the tool set and the task, not of the model. Scoring a stratum whose evidence is unreachable measures the harness, and reads in an uninspected report as model weakness. Two enforcement points are required for any new task class before a model ever sees it: a static test that the required evidence *can* be returned by some tool call in the deployed set, and a dynamic replay of the real evidence-gathering plan through the real tool broker that reports the recall ceiling per stratum. A stratum whose measured ceiling sits below its passing threshold is unwinnable by construction; this is the same [reachability ceiling](GLOSSARY.md#reachability-ceiling) discipline chapter 03 applies to the instrument as a whole, applied here to the tool layer specifically. [CASE: CASE-004](examples/CASE-004_harness-defects.md).

**[PRINCIPLE] Tool contracts are part of the execution system and are versioned like code.** (strong-evidence)
A [tool contract](GLOSSARY.md#tool-contract) — schema, addressing, result ordering, pagination, cohort/tenant keying, permissions, error semantics, byte-level transport fidelity — is not an implementation detail behind an API signature; it is part of the [execution system](GLOSSARY.md#execution-system) chapter 02 defines, and a silent change to it invalidates comparability exactly as a silent model or runtime change does. A tool's sort order and returned-column set are frequently *the* thing that makes a property diagnosable at all: a class that depends on distinguishing event time from posting order, or on clustering across entities, can be undiagnosable in principle — not merely hard — under a contract that omits the distinguishing field or scopes to the wrong entity. [CASE: CASE-004](examples/CASE-004_harness-defects.md), [CASE: CASE-008](examples/CASE-008_transport-serialization-defect.md).

**[PRINCIPLE] A deterministic gate is the default cascade mechanism when a task-level verifier exists.** (strong-evidence)
A [cascade](GLOSSARY.md#cascade) needs an [escalation](GLOSSARY.md#escalation) rule; where the task has an objectively checkable output, the default is a [deterministic gate](GLOSSARY.md#deterministic-gate) — an explicit rule over verifiable output signals (schema conformance, verifier result, citation validity), not a learned classifier. First-principles case: a deterministic gate needs no training data, is fully auditable, cannot leak evidence identity because it reads nothing but the current attempt's own verifiable properties, and does not inherit the generalization failure mode documented for learned gates (below). This is a stronger default than the published literature's, which is uniformly learned-gate-based [EXT-ROUTE-001]; the internal record shows a verifier-gated deterministic cascade recovering a substantial share of the quality gap between tiers at a modest fraction of strong-tier calls, with zero unnecessary escalations. [CASE: CASE-007](examples/CASE-007_deterministic-cascade-gate.md).

**[PRINCIPLE] A learned routing or decision component is not believed until it beats its own class-identity ceiling under leave-one-group-out validation.** (strong-evidence)
Compute the [class-identity ceiling](GLOSSARY.md#class-identity-ceiling) — the performance a comparator achieves by predicting purely from which stratum/template an item belongs to — before crediting any learned component's score. A candidate indistinguishable from that ceiling has learned the grouping, not the intended signal, and same-group cross-validation cannot detect this: the audit MUST use leave-one-group-out validation, and the per-fold read SHOULD be restricted to folds whose held-out group contains both outcome classes (pooled out-of-fold metrics are null-biased under class-clustered labels and are not evidence about transfer), tests generalization beyond memorized identity. Individually legitimate, production-observable features can *jointly* and indirectly identify the forbidden group variable even when no single feature names it; do not assume removal is possible — quantify the indirect-identification rate (e.g., a leave-one-out nearest-neighbor test on the feature vectors alone) and read every downstream result net of that channel. External corroboration: published cascade routers show near-random performance out of distribution [EXT-ROUTE-001]. This is the [leakage audit](GLOSSARY.md#leakage-audit). [CASE: CASE-003](examples/CASE-003_learned-router-leakage.md).

**[PRINCIPLE] Automated action from a learned or mutating routing component is earned in stages, never granted at deployment.** (case-study + inference)
[Observe-only graduation](GLOSSARY.md#observe-only-graduation): leakage audit passed → observe-only shadow period with measured agreement/regret → pre-registered promotion gate on the qualification split → automated action with a defined rollback and monitoring plan. The leakage-audit and observe-only stages are exercised practice (a candidate router was fitted, audited, and run to a pre-registered confirmatory read entirely offline, never automating a live decision). The promotion-gate-to-automated-action and rollback stages are prescribed here as doctrine: *status: doctrine — not yet exercised (see §7 for what validation would look like)*. Never let a component whose leakage audit is unresolved sit in a live decision path, observe-only or not, if its output is visible to any downstream system that could act on it.

**[DEFAULT] Fail-open vs. fail-closed is chosen per consequence class, not defaulted globally.** (heuristic)
A gate or judge that times out or errors can [fail-open](GLOSSARY.md#fail-open) (serve the weak tier's answer — availability-preserving) or [fail-closed](GLOSSARY.md#fail-closed) (refuse — consequence-preserving). Fail-open is defensible on low-stakes, high-availability paths; it is a defect when it silently swallows a consequence the [rigor dial](GLOSSARY.md#rigor-dial) requires to bind. State the choice explicitly per edge in a multi-tier topology (§6) and record it as part of the routing policy, not as an incidental default of the gate library.

## 5. Default procedure

### 5.1 Evidence reachability

1. For each stratum in the [task ontology](GLOSSARY.md#task-ontology), enumerate the facts a correct answer requires.
2. For each fact, name the tool call (or call sequence) that returns it, in the form the task actually requires (not merely "the value exists in storage").
3. Watch for **two-phase addressing**: a fact addressed by an identifier the system cannot learn without first making another call. If the evidence plan has this shape, split it into phases explicitly and test phase two's addressability from phase one's actual output, not from a generator's internal state.
4. Run a static per-stratum test that the tool set *can* return the required evidence, and a dynamic replay of the real evidence-gathering plan through the real tool broker against the corpus, reporting recall as a measured ceiling per stratum.
5. Treat any stratum below its passing threshold as a harness defect until proven otherwise (P2, chapter 00) — never as a model result.
6. Verify tool results cannot cross task/tenant boundaries: a cohort- or time-scoped tool call must carry an explicit non-overlap guarantee on the windows or cohorts each evaluation item occupies, or one call can silently answer from another item's data.
7. Re-run the static and dynamic checks after any change to the corpus, the tool contracts, or the evidence plan — reachability is a property of the pairing, not of either side alone.

### 5.2 Tool contract design

Every tool exposed to a model, and every tool used to build or score an evaluation, needs an explicit contract — not an inferred one. Checklist:

| Property | Requirement |
|---|---|
| Schema | Explicit input/output types; no implicit coercion the caller must guess |
| Result ordering | A stated, deterministic sort key — never "database default order" |
| Column/field set | Every field the task's evidence plan depends on is named in the contract, not merely present in some response |
| Cohort/tenant keying | Scoping parameters (customer, tenant, time window) stated; cross-entity queries carry a non-overlap or isolation guarantee |
| Pagination/limits | Stated limit semantics; a caller must be able to tell "no more results" from "results truncated" |
| Addressability | Every selector the contract requires is one the caller can actually construct from prior results — no phantom identifiers |
| Byte-level transport fidelity | Any proxy, gateway, or serialization hop between model and tool is verified byte-equivalent for anything a downstream grammar- or format-constrained consumer depends on (key order, whitespace, numeric formatting) — verified, not assumed [CASE: CASE-008](examples/CASE-008_transport-serialization-defect.md) |
| Permissioning | Least-privilege; a tool MUST hold no grant on data it has no task reason to reach — this is the mechanical half of [ground-truth isolation](GLOSSARY.md#ground-truth-isolation) (chapter 13) |
| Error semantics | Distinguishable failure modes (not found / not permitted / transient error) a caller can act on differently |
| Versioning | The contract is versioned as part of [execution-system](GLOSSARY.md#execution-system) identity; a version bump is a frozen-identity-breaking change like a model or runtime bump |

Prefer narrow, typed, read-only tools over direct data-store access: narrow tools force a stable interface, produce better execution traces, and make the reachability check in §5.1 tractable. Where a tool must integrate with an external or provider-native system, expose both the normalized and the provider-native identifiers — cross-system ID mapping is a realistic error source and useful evaluation material in its own right, not incidental plumbing to hide.

### 5.3 Context policy

The [context policy](GLOSSARY.md#context-policy) is the part of the execution system governing what enters the model's context:

- **Budget allocation.** Fix, per task type, how the available context window is split between instructions, retrieved/tool evidence, and generation headroom; treat this as a versioned parameter, not an emergent property of whatever fits.
- **Retrieval integration.** State how retrieved or tool-sourced evidence enters the prompt (structured fields vs. free text) and whether the model can distinguish evidence from instructions from its own prior output.
- **Context-rot hygiene.** Long-running or multi-turn contexts accumulate stale, contradicted, or superseded evidence; define a pruning or re-grounding rule rather than letting context grow monotonically.
- **Structured evidence presentation.** Prefer explicit, labeled evidence blocks (source, timestamp, identifier) over undifferentiated concatenation — this is what makes citation verification (§5.2, the verifier in chapter 03/07) possible at all.

### 5.4 Routing and cascade design

1. **Oracle analysis first.** Before building anything, compute the [oracle](GLOSSARY.md#oracle-analysis) upper bound: for a sample of paired weak/strong outcomes, the share where the weak tier alone succeeds, the share the strong tier alone rescues, the share where escalation would still fail, and the rare inversion cases (weak succeeds, strong fails — review these by hand; they are usually corpus or scorer defects, not evidence of the weak tier's superiority). If the oracle gain over weak-only is small, no router is worth its cost — stop here (§7).
2. **Check the economics.** Apply the break-even formula (§8) with your own tier costs before committing engineering time.
3. **Build the deterministic gate.** If the task has a verifier, wire escalation to its verifiable failure signals (no valid output, failed citation/schema check, any other deterministic verifier failure) — the gate MUST NOT read anything gold-derived (chapter 04's gold-label boundary, restated for routing in §6).
4. **Only if headroom remains below the oracle**, consider a learned router as an *addition*, composed as `escalate = deterministic_rule OR learned_risk ≥ threshold`; it MUST NOT replace a working deterministic gate. Gate the candidate behind a TRAIN-only eligibility check (minimum out-of-fold discrimination and minimum lift over the class-identity ceiling) before it is allowed into selection at all.
5. **Leakage-audit any admitted candidate** (§4) before it is allowed to select anything.
6. **Observe-only shadow**, then a pre-registered promotion gate on the qualification split (§7), before any automated action.
7. **Instrument before deploying**: production monitoring plan (chapter 12) and a rollback path (chapter 10) exist before graduation, not after.

## 6. Project adaptation parameters

**[PARAMETER] Routing-input taxonomy — which signals may inform a routing/escalation decision, and where.**

| Feature class | Examples | Admissible where |
|---|---|---|
| **Task-intrinsic** | content, task class/complexity signals *derivable from the input itself*, evidence-bundle shape, tool-call count/pattern | Design-time features and production-observable, non-gold signals; caution — bundle shape and call-count features can indirectly encode class identity (§4) even when class itself is withheld |
| **System-state** | queue depth, budget burn, current-tier health/latency, degraded-mode flags | Any decision point; these are operational, not evidence about the task |
| **Policy** | consequence/stakes tier, SLA, permission scope, fail-open/closed mode | Any decision point; these constrain *what the gate is allowed to decide*, not what it observes |
| **Verifier/output** | schema validity, citation resolution, verifier pass/fail, confidence calibration against work actually done | Deterministic gates and learned routers alike — these are production-observable at serve time |
| **Gold/ground-truth** | correct label, expected action, evidence recall against a gold answer, scenario/class/seed identifiers, scorer internals | **MUST NOT** be admissible to any live routing/gate decision. Admissible only offline, to define training labels or to score outcomes after the fact (chapter 04's gold-label boundary: gold labels score but never choose) |

Enforce the last row structurally, not by convention: an explicit feature-name allowlist with forbidden-name schema errors, gold-removal invariance tests, extraction-with-no-gold-fields tests, and an import ban preventing feature-extraction code from importing evaluation or scoring modules. This is the leakage-audit machinery's build-time half; chapter 13 covers the runtime/permission half.

Other parameters to set per project, never shipped as universal numbers: confirmation-streak length before an escalation commits; whether a judge failure resets or holds a confirmation streak; fail-open vs. fail-closed per edge (§4); the promotion-gate thresholds in §7; the break-even threshold that triggers building a router at all (§8).

## 7. Decision gates and stopping conditions

**[DECISION GATE] Deterministic gate vs. learned router.** Inputs: does a task-level verifier exist for the output; what does oracle analysis say the remaining headroom is above the deterministic gate. Rule: deterministic gate is default whenever a verifier exists; a learned router is considered only as an addition, only after eligibility and leakage-audit gating (§4, §5.4). Outcome: build deterministic only, or deterministic + candidate learned router queued for the graduation gate below.

**[DECISION GATE] Observe-only → automated-action graduation (G13).**

| Stage | Requirement | Evidence type |
|---|---|---|
| 1. Leakage audit | Beats class-identity ceiling under leave-one-group-out; feature-provenance review passed; OOD caution addressed | Measured, pre-registered |
| 2. Observe-only shadow | Runs alongside the incumbent, decisions logged, never acted on; agreement/regret vs. incumbent measured over a pre-registered window | Measured |
| 3. Promotion gate | Pre-registered rule evaluated once on the qualification split (one-look discipline, chapter 04); passes a stated, non-degenerate improvement bar — **[PARAMETER]** set per project, e.g. a materially large improvement above a noise floor *and* a bound against collapse toward the expensive tier, not a bare utility optimum (a threshold chosen by maximizing catches-minus-cost with no cap degenerates to "always escalate" or "never escalate" at extreme base rates) | Measured, one-look |
| 4. Rollback path defined | Chapter 10's rollback path exists and is rehearsed before automated action, not designed after an incident | *doctrine — not yet exercised* |
| 5. Monitoring plan | Chapter 12's drift/monitoring plan for the component is live before graduation | *doctrine — not yet exercised* |

A candidate that fails stage 1 MUST NOT proceed to stage 2, regardless of how good its offline numbers look. De-automation (reverting a graduated component to observe-only or to the deterministic gate) is pre-registered on the same terms as promotion — a component does not get to keep its automated status by default once a regression is observed.

**[STOP CONDITION] Global tripwires for this chapter.**

1. A stratum's measured evidence-reachability ceiling is below its passing threshold — stop and fix the tool contract or the evidence plan before evaluating anything on it (§5.1).
2. A learned router's out-of-fold score is indistinguishable from its class-identity ceiling — it has not cleared the leakage audit; it may not select, route, or score anything (§4).
3. Oracle analysis shows small headroom over the cheaper tier — do not build a router; the deterministic gate (or no gate) is the answer (§5.4 step 1).
4. A promotion-gate rule's wording admits two readings — compute and disclose the outcome under both; never silently resolve the ambiguity in the result's favor.
5. A candidate's confirmatory test would also be met by a same-size random policy at non-trivial probability — report this power figure alongside any "confirmed" verdict; a low-power confirmation is not a confirmation.
6. Any tool contract change (ordering, columns, scope) ships without a version bump — treat it as an unpinned execution-system change (chapter 02) and re-run comparability-dependent evaluations.

## 8. Metrics and formulas

**Routing break-even.** The minimum share of traffic that must be served by the cheaper tier for a routing layer to pay for its own gate/judge overhead.

```
f_min = C_gate / (C_strong − C_weak)
```

- `C_gate` — per-item cost of running the escalation gate/judge (currency or compute-time units).
- `C_strong`, `C_weak` — per-item cost of the strong and weak tiers, same units.
- `f_min` — minimum fraction of total items that must resolve on the weak tier for the routed system to cost no more than always using the strong tier.

*Derivation:* without routing, cost per item is `C_strong`. With routing, cost per item is `C_gate + f·C_weak + (1−f)·C_strong`. Setting the two equal and solving for `f` gives `f_min` above.

*Worked example (illustrative, invented round numbers).* Weak tier `C_weak = $0.002`/item, strong tier `C_strong = $0.020`/item, gate `C_gate = $0.001`/item. `f_min = 0.001 / (0.020 − 0.002) = 0.001 / 0.018 ≈ 5.6%`. If the deployed gate keeps at least 5.6% of traffic on the weak tier, routing is cheaper than strong-only; below that share, the gate's own overhead outweighs the savings — do not deploy it. **[ADAPT: EXT-SWITCHYARD-001]**: on one published benchmark (a 145-task agent suite, one weak/strong pairing, as-of 2026-08-11), this rule's minimum offload was a small single-digit percentage against an achieved offload above 90%, yielding a reported cost reduction near three-quarters with accuracy retention in the low-to-mid 90s percent — figures conditioned on that specific pairing and suite; re-measure your own tier costs before trusting the shape of the result.

**Rescue rate / unnecessary-escalation rate.** For a cascade's [escalations](GLOSSARY.md#escalation):

```
rescue_rate = successes_after_escalation / total_escalations
unnecessary_rate = (escalations where the weak tier would have succeeded) / total_escalations
```

A gate with high rescue rate and low unnecessary rate is doing its job cheaply; a gate with low rescue rate is escalating things the strong tier cannot fix either (residual capability gap, not a routing problem — back to rung 7+).

**False-negative cost.** The expensive failures in a cascade are the ones that are *not* escalated and fail anyway (routing false negatives), not the escalations that turn out unnecessary. Report false negatives as a first-class number alongside all-pass rate; a headline all-pass improvement that leaves false negatives unchanged has not closed the gap that matters.

**Oracle ceiling.**

```
oracle_all_pass = 1 − both_fail_share
```

where `both_fail_share` is the fraction of paired items neither tier resolves — the quality ceiling achievable by *any* router over the two tiers, independent of how good the router is.

**Class-identity ceiling comparator.** Fit a comparator that predicts the routing target from group/stratum identity alone (e.g., the majority outcome within each group). A candidate router's performance is credited only for the margin above this comparator, evaluated under leave-one-group-out.

**Multi-tier composition.** For N ≥ 3 tiers, compose edges: each edge between adjacent tiers carries its own gate (deterministic or learned), its own escalation semantics (fail-open/closed, confirmation streak), and its own break-even computed from that edge's local pair of tier costs. There is no single global break-even for a chain — compute and report one per edge.

```
tier_1 --(edge A gate)--> tier_2 --(edge B gate)--> tier_3
       f_min(A) = C_gateA / (C_2 − C_1)     f_min(B) = C_gateB / (C_3 − C_2)
```

## 9. Failure modes and anti-patterns

**[REJECTED]** (condition: always — these are generically wrong)

- **Assuming proxy/infrastructure transparency.** Believing a request-path change (proxy, adapter, gateway) does not affect model behavior because it is schema- or semantically equivalent, without paired same-session, byte-level output verification. [CASE: CASE-008](examples/CASE-008_transport-serialization-defect.md).
- **Treating tool ordering/columns as an implementation detail.** A tool's sort order and returned-field set are part of its contract; changing either without a version bump silently changes which properties are diagnosable.
- **Ungated learned-component adoption.** Deploying a learned router or classifier into any decision path — even observe-only, if its output reaches a downstream actor — without a passed leakage audit, whenever its training data is drawn from a small number of templates or clusters.
- **Pooled cross-validation under clustered labels.** Reporting a single pooled out-of-fold metric from grouped/leave-one-group-out CV when the label is strongly correlated with the group; the pooled number can read as generalization when it is fold base-rate shift.
- **Threshold-only utility optimization.** Choosing an operating threshold by maximizing a bare utility function (catches minus cost) with no cap, letting it silently degenerate to "always escalate" or "never escalate" at extreme base rates.
- **Silent post-hoc rule relaxation.** Loosening a pre-registered promotion/confirmation criterion after seeing shadow or qualify-split results, or resolving an ambiguous rule wording in favor of whichever reading passes, without disclosing both readings (chapter 04's amendment-legitimacy rule applies to routing gates exactly as it applies to experiments).
- **Ignoring gate power.** Reporting a pre-registered promotion rule as confirmed without computing what a same-size random policy would score under the identical rule; a low-power confirmation is not information.
- **Trusting aggregate rates over paired disagreement review.** Comparing routing configurations only by aggregate all-pass rate without manually reviewing individual disagreement cells; corpus/scorer defects routinely masquerade as routing-quality differences and only paired review catches them. Report both as-measured and review-corrected numbers side by side when a review does correct something — never overwrite the raw figure.
- **Building a router before an oracle analysis.** Investing in a learned routing component before measuring the paired-oracle opportunity map is a way to buy engineering effort for a gain that was never there.
- **Fail-open as an unexamined library default.** Shipping a gate's fail-open/closed behavior as whatever the library ships, rather than a stated choice per edge tied to the consequence class of that edge.

## 10. Vendor recipes

| Source | Verdict | Gives | Missing / your job | As-of |
|---|---|---|---|---|
| [NV-SWITCHYARD-001] NVIDIA NeMo Switchyard | **[ADAPT]** | An escalation-router product with four documented decision mechanisms and explicit parameters: weak-first, judge-on-actual-output, confirmation streaks, per-session latching, fail-open default, judge-failure-holds-the-streak semantics | The decision layer — when fail-open is *wrong* for your consequence class; three-tier composition (the shipped config schema admits exactly two tiers per route — chain routes or write a custom policy selector for more); production maturity (pre-alpha, vendor's own "not for production use" as of this verification) | 2026-08-21 (product v0.2.0, 2026-08-10) |
| [EXT-SWITCHYARD-001] LangChain Switchyard benchmark | **[ADAPT]** | The break-even formula (§8) and one published operating point demonstrating it | Scope-conditioned to one weak/strong pairing on one fixed task suite — substitute your own tier costs, gate cost, and task mix before trusting the shape of the result, not just the formula | 2026-08-11 |
| [EXT-ROUTE-001] Cascade/learned-router literature (FrugalGPT, RouteLLM, AutoMix, HybridLLM) | **[REFERENCE]** | The published design space for cascades — uniformly learned gates; RouteLLM's out-of-distribution near-random result is the standing caution behind §4's leakage-audit requirement | A deterministic-gate alternative is outside this literature's design space; do not expect it to validate that choice — it corroborates the caution about the alternative instead | 2026-08-21 |
| [NV-SLMRESEARCH-001] NVIDIA Research, small-language-models-for-agentic-AI position paper | **[REFERENCE]** | The rationale for a small/local-default, large/frontier-fallback cascade topology | Rationale only, not a procedure — pair with §5.4's procedure, not a substitute for it | 2026-08-20 |
| [NV-NEMOCLAW-001] NemoClaw / OpenShell agent sandbox | **[REFERENCE]** | A demo-grade credential-custody wrapper with host-side cost/quality routing around community agent harnesses | Pre-alpha, wraps community harnesses rather than being a validated security boundary; the tool-calling security threat model (least privilege, injection red-teaming, credential custody) is chapter 13's G8, doctrine-not-yet-exercised there | 2026-08-20 |

## 11. Worked examples

- [CASE-004](examples/CASE-004_harness-defects.md) — evidence unreachable by the deployed tool set, and a tool's sort order making a class undiagnosable, both initially indistinguishable from model weakness until reachability replay and disagreement review isolated them.
- [CASE-008](examples/CASE-008_transport-serialization-defect.md) — a routing/proxy hop silently reordered a request's serialized field order, breaking a grammar-constrained consumer that depended on it; found only by byte-equivalence verification, not by behavioral spot-checks.
- [CASE-007](examples/CASE-007_deterministic-cascade-gate.md) — a verifier-gated deterministic cascade achieving near-total rescue with zero unnecessary escalations, outside the published learned-gate design space.
- [CASE-003](examples/CASE-003_learned-router-leakage.md) — a learned router that scored well until a leave-one-group-out audit showed its features encoded which template a case belonged to; nothing beat the class-identity ceiling, and the deterministic gate was retained.

**Illustrative oracle + routing-tier decision (invented round numbers).** A team pairs weak- and strong-tier outputs on 200 held-out items:

| Cell | Share | Reading |
|---|---|---|
| weak-pass / strong-pass | 30% | weak sufficient — cheap coverage |
| weak-fail / strong-pass | 55% | rescueable — a gate should escalate these |
| weak-pass / strong-fail | 3% | inversion — review by hand before trusting either score |
| both-fail | 12% | neither tier resolves it — a routing problem cannot fix this |

Oracle ceiling = 1 − 12% = 88%. With `C_weak = $0.001`, `C_strong = $0.015`, `C_gate = $0.0005`: `f_min = 0.0005 / 0.014 ≈ 3.6%`. The measured rescueable share (55%) is far above `f_min`'s complement, so routing is worth building; a deterministic gate is the first thing to build (§5.4), and only the residual 12% both-fail share is a candidate for a rung-7+ intervention (chapter 09), never for a smarter gate.

## 12. Outputs and artifacts

- A written tool-contract specification per tool (§5.2 checklist), versioned with the rest of the execution system.
- The static and dynamic evidence-reachability test results per stratum, re-run after any corpus or contract change.
- A routing policy document: gate type per edge, escalation semantics, fail-open/closed choice, and (for multi-tier) the per-edge break-even.
- For any learned routing candidate: a leakage-audit report (class-identity ceiling comparison, leave-one-group-out results, feature-provenance review), an oracle-analysis report, an observe-only shadow log, and — on graduation — a [method decision record](GLOSSARY.md#method-decision-record) recording the promotion-gate result and both readings of any ambiguous rule clause.

## 13. Sources

| ID | Role here |
|---|---|
| [NV-SWITCHYARD-001] | Escalation-router mechanics and parameter vocabulary, ADAPT |
| [EXT-SWITCHYARD-001] | Routing break-even formula and one published operating point, ADAPT |
| [EXT-ROUTE-001] | Learned-gate literature and the OOD-generalization caution behind the leakage-audit requirement |
| [NV-SLMRESEARCH-001] | Rationale for the small/local-default, large/frontier-fallback cascade topology |
| [NV-NEMOCLAW-001] | Credential-custody wrapper reference; cross-ref chapter 13 G8 |
| [INT-CASE-003], [INT-CASE-004], [INT-CASE-007], [INT-CASE-008] | Internal case evidence backing this chapter's principles |

Gap dispositions in this chapter:

- **G11 (routing-input taxonomy): COVERED** — §6, the task-intrinsic × system-state × policy × verifier/output × gold-label admissibility table.
- **G13 (observe-only → automated-action graduation criteria): COVERED**, with the promotion-gate and rollback/monitoring stages marked **COVERED-AS-DOCTRINE-NOT-YET-EXERCISED** — §7, the five-stage graduation gate; the leakage-audit and observe-only stages carry case-study evidence, the promotion-gate-to-automated-action and rollback stages do not yet.
- **G19 (tool-contract design): COVERED** — §5.2, the tool-contract checklist, and §4's principle binding contracts to execution-system identity.

---

> [← Previous](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md) · [Index](README.md) · [Next →](09_TRAINING_AND_DATA.md)
