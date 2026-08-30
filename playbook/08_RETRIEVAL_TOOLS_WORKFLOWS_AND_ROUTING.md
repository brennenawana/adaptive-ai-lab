# 08. Retrieval, Tools, Workflows, and Routing

> Part of the **Adaptive AI Systems Playbook** v0.1.1 ·
> [← Previous](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md) · [Index](README.md) · [Next →](09_TRAINING_AND_DATA.md)
> **Reading time:** ~24 min. **Prerequisites:** [00](00_PRINCIPLES_AND_SCOPE.md), [02](02_EXECUTION_SYSTEM_MODEL.md), [03](03_EVALUATION_FOUNDATION.md), [07](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md).

## 1. Purpose and when to read this

An assistant is asked when a customer's refund was approved. It does the sensible
thing: calls the ledger tool, reads what comes back, and writes an answer. The tool
returns the twenty most recent rows, newest first, with nothing in the response saying
whether more rows exist, and no field separating when an entry was *made* from when the
event it records actually happened. The refund is in row twenty-three. The assistant
answers that there is no record of a refund.

Nobody was careless here, and no model would have got that answer right. The fact it
needed never reached the model. Nothing in what did reach the model said so.

Now the same assistant meets a genuinely hard ticket — one a larger, costlier model
would have handled correctly. It answers confidently and wrongly, for a fraction of the
price. Somebody has to decide *before the answer exists* which tickets are worth the
expensive model, using only what can be seen at that moment.

Those two situations are this chapter. It covers rungs 2, 3, and 6 of the
[intervention ladder](GLOSSARY.md#intervention-ladder): what the system can *know*
(retrieval, tools, context) and what it does with an escalation decision (routing,
cascades).

Read it when a diagnosis from [chapter 07](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md)
lands on RC-3 (missing/unreachable evidence), RC-4 (tool/API contract defect), or RC-9
(routing/escalation mismatch) in the
[canonical failure taxonomy](GLOSSARY.md#canonical-failure-taxonomy). Read it also
*before* any of those rungs are built — the properties defined here are cheap to design
in and expensive to retrofit.

Three questions this chapter answers:

1. Is the evidence a task needs actually obtainable through the tools the system has,
   from what it knows when it needs to know it?
2. What must a tool's contract guarantee before its results are trustworthy inputs to a
   model *and* to an evaluation?
3. When is a cheap tier good enough, when does a task need an expensive one, and what is
   allowed to decide?

One boundary is worth fixing now. Workflow structure — how a task is broken into steps
and tool calls — belongs to this chapter only insofar as it determines what evidence
becomes reachable and when. Specifying *what a step should do* — the prompts, the
instructions, the decomposition text — is rung 4 (RC-6, task-specification gap), and it
is not this chapter.

## 2. Inputs required

- A diagnosis from chapter 07 naming RC-3, RC-4, or RC-9 — or a design-time decision to
  build retrieval, tools, or routing before any diagnosis exists.
- The [task ontology](GLOSSARY.md#task-ontology) and per-stratum evidence requirements
  from [chapter 03](03_EVALUATION_FOUNDATION.md). You need to know what a correct answer
  requires before you can ask whether the tools can supply it.
- The tool surface the deployed system will actually call — schemas, backing store, and
  any proxy or gateway hop sitting between model and tool. The deployed surface, not a
  description of it.
- Per-tier unit costs (weak / strong / frontier) and a verifier or scorer capable of
  judging correctness, if routing is in scope.
- The project's [stakes tier](GLOSSARY.md#stakes-tier) (from
  [templates/PROJECT_PROFILE.md](templates/PROJECT_PROFILE.md)). The tier is what sets
  the graduation and rollback bar for any automated routing decision.

## 3. Decisions this chapter supports

- Whether a low score on a stratum is a model weakness (RC-10/RC-11) or an
  evidence-reachability defect (RC-3) that is unfair to charge to the model.
- What a tool's contract must specify before it is trustworthy, and how that contract is
  versioned.
- Deterministic gate vs. learned router for a cascade, and what a learned router must
  clear before it competes at all.
- Whether routing pays for itself, and at what offload share.
- Whether a routing or decision component may move from observe-only to automated
  action, and what rehearsing that move costs.

## 4. Normative principles

**[PRINCIPLE] Evidence reachability is measured, not argued.** (strong-evidence)

Take one task the system is supposed to handle. List every fact a correct answer needs.
Now ask, for each fact, whether some call in the deployed tool set returns it — starting
from what the system knows at the moment it has to ask. That property is
[evidence reachability](GLOSSARY.md#evidence-reachability), and it is a property of the
tool set paired with the task. The model is not involved in it.

This matters because of what an unreachable fact looks like from the outside. It looks
like a bad score. Score a stratum whose evidence cannot be retrieved and you have
measured your harness; the report says the model is weak, and nothing in the number
disagrees.

So two enforcement points are required for any new task class, before a model ever sees
it. A **static** test that the required evidence *can* be returned by some tool call in
the deployed set. And a **dynamic** replay of the real evidence-gathering plan through
the real tool broker, reporting the recall ceiling per stratum. A stratum whose measured
ceiling sits below its passing threshold is unwinnable by construction. This is the same
[reachability ceiling](GLOSSARY.md#reachability-ceiling) discipline chapter 03 applies
to the instrument as a whole, pointed here at the tool layer specifically.
[SCENARIO: SCENARIO-04](examples/SCENARIO-04_harness-defects.md).

**[PRINCIPLE] Tool contracts are part of the execution system and are versioned like code.** (strong-evidence)

A [tool contract](GLOSSARY.md#tool-contract) is the written promise a tool makes about
what comes back: schema, addressing, result ordering, pagination, cohort/tenant keying,
permissions, error semantics, byte-level transport fidelity. Where that promise is
unwritten, everyone downstream infers it from whatever they happened to see — the model,
the person building the evaluation, and the person later trying to explain a bad result.

Writing it down is the cheapest defense you have against a specific and nasty class of
bug. When a tool errors, you find out. When a tool quietly returns the right rows in the
wrong order, or drops a field, or truncates without saying so, you get a fluent,
confident, wrong answer that no amount of output inspection distinguishes from a correct
one. That is not an implementation detail hiding behind an API signature; it is part of
the [execution system](GLOSSARY.md#execution-system) chapter 02 defines, and a silent
change to it invalidates comparability exactly as a silent model or runtime change does.

How far this reaches is easy to underestimate. A tool's sort order and returned-column
set are frequently *the* thing that makes a property diagnosable at all. A task class
that turns on distinguishing event time from posting order, or on clustering across
entities, can be undiagnosable in principle — not merely hard — under a contract that
omits the distinguishing field or scopes to the wrong entity. No model, at any budget,
recovers a field it was never shown.
[SCENARIO: SCENARIO-04](examples/SCENARIO-04_harness-defects.md),
[SCENARIO: SCENARIO-08](examples/SCENARIO-08_transport-serialization-defect.md).

**[PRINCIPLE] A deterministic gate is the default cascade mechanism when a task-level verifier exists.** (strong-evidence)

Try the cheap model first and hand the hard ones up to the expensive one — that shape is
a [cascade](GLOSSARY.md#cascade), and handing a task up is
[escalation](GLOSSARY.md#escalation). Every cascade needs a rule for when to escalate.
Where the task has an objectively checkable output, the default rule is a
[deterministic gate](GLOSSARY.md#deterministic-gate): explicit conditions over verifiable
signals — schema conformance, verifier result, citation validity — with no trained
classifier in it.

The case is first-principles, and it is four-part. A deterministic gate needs no training
data. It is fully auditable, because you can read it. It cannot leak evidence identity,
because it reads nothing except verifiable properties of the current attempt. And it does
not inherit the generalization failure documented for learned gates in the next
principle.

This is a stronger default than the published literature's, which is uniformly
learned-gate-based [EXT-ROUTE-001]. An illustrative worked scenario shows the shape the
argument takes when it goes well: a verifier-gated deterministic cascade recovering a
substantial share of the quality gap between tiers, at a modest fraction of strong-tier
calls, with zero unnecessary escalations.
[SCENARIO: SCENARIO-07](examples/SCENARIO-07_deterministic-cascade-gate.md).

**[PRINCIPLE] A learned routing or decision component is not believed until it beats its own class-identity ceiling under leave-one-group-out validation.** (strong-evidence)

Here is the question this principle exists to force, and it is worth being blunt about
it: *did your router learn whether an answer is correct, or did it learn which kind of
item it is looking at?*

Those two are easy to confuse, because the second one scores well. Evaluation items come
from somewhere — templates, source documents, customers, sessions. If some of those
groups are systematically harder than others, a classifier can do respectably by
recognizing the group and reciting that group's base rate, without extracting one bit of
information from the answer in front of it.

So compute the [class-identity ceiling](GLOSSARY.md#class-identity-ceiling) before
crediting any learned component's score: the performance a comparator achieves by
predicting purely from which stratum or template an item belongs to. A candidate
indistinguishable from that ceiling has learned the grouping, not the intended signal.

Same-group cross-validation cannot detect this — if the same group appears in training
and in test, memorizing the group is rewarded rather than exposed. The audit MUST
therefore use leave-one-group-out validation, which holds out an entire group and asks
whether the component transfers to one it has never seen. That is the test for
generalization beyond memorized identity. The per-fold read SHOULD be restricted to
folds whose held-out group contains both outcome classes; pooled out-of-fold metrics are
null-biased under class-clustered labels and are not evidence about transfer.

One more trap, and it is the one that survives careful hygiene. Individually legitimate,
production-observable features can *jointly and indirectly* identify the forbidden group
variable even when no single feature names it — how many tool calls were made, how large
the evidence bundle was, how long the prompt ran. Do not assume removal is possible.
Quantify the indirect-identification rate instead (for example, a leave-one-out
nearest-neighbor test on the feature vectors alone), and read every downstream result net
of that channel. External corroboration: published cascade routers show near-random
performance out of distribution [EXT-ROUTE-001]. All of this together is the
[leakage audit](GLOSSARY.md#leakage-audit).
[SCENARIO: SCENARIO-03](examples/SCENARIO-03_learned-router-leakage.md).

**[PRINCIPLE] Automated action from a learned or mutating routing component is earned in stages, never granted at deployment.** (case-study + inference)

Passing an offline evaluation is not permission to make decisions. The right to act is
earned through [observe-only graduation](GLOSSARY.md#observe-only-graduation): leakage
audit passed → observe-only shadow period with measured agreement/regret →
pre-registered promotion gate on the qualification split → automated action with a
defined rollback and monitoring plan.

Be precise about how well supported each stage is. The first two are worked through in
an illustrative scenario — a candidate router fitted, audited, and taken to a
pre-registered confirmatory read entirely offline, never automating a live decision
([SCENARIO: SCENARIO-03](examples/SCENARIO-03_learned-router-leakage.md)). The
promotion-gate-to-automated-action and rollback stages are prescribed here as doctrine:
*status: doctrine — not yet exercised (see §7 for what validation would look like)*.

One rule admits no staging. Never let a component whose leakage audit is unresolved sit
in a live decision path, observe-only or not, if its output is visible to any downstream
system that could act on it. "Observe-only" is a claim about what the component does,
not about what its readers do.

**[DEFAULT] Fail-open vs. fail-closed is chosen per consequence class, not defaulted globally.** (heuristic)

A gate or judge that times out or errors has to do something. It can
[fail-open](GLOSSARY.md#fail-open) — serve the weak tier's answer, preserving
availability — or [fail-closed](GLOSSARY.md#fail-closed) — refuse, preserving the
consequence.

Neither is right in general. Fail-open is defensible on low-stakes, high-availability
paths. It is a defect when it silently swallows a consequence the
[rigor dial](GLOSSARY.md#rigor-dial) requires to bind: the gate that was supposed to stop
something stops nothing, and the only trace is a timeout in a log. State the choice
explicitly per edge in a multi-tier topology (§6), and record it as part of the routing
policy — not as an incidental default of whatever gate library you installed.

## 5. Default procedure

### 5.1 Prove the evidence is reachable

1. For each stratum in the [task ontology](GLOSSARY.md#task-ontology), enumerate the
   facts a correct answer requires.
2. For each fact, name the tool call — or the call sequence — that returns it, in the
   form the task actually requires. "The value exists in storage" is not the same claim
   and does not count.
3. Watch for **two-phase addressing**: a fact addressed by an identifier the system
   cannot learn without first making another call. Where the evidence plan has this
   shape, split it into phases explicitly, and test phase two's addressability from
   phase one's *actual output* — not from what a generator knew internally when it
   wrote the item.
4. Run the static per-stratum test that the tool set *can* return the required evidence,
   and the dynamic replay of the real evidence-gathering plan through the real tool
   broker against the corpus, reporting recall as a measured ceiling per stratum.
5. Treat any stratum below its passing threshold as a harness defect until proven
   otherwise (P2, chapter 00). Never as a model result.
6. Verify that tool results cannot cross task or tenant boundaries. A cohort- or
   time-scoped call must carry an explicit non-overlap guarantee on the windows or
   cohorts each evaluation item occupies; without one, a single call can silently answer
   from another item's data and every score built on it is contaminated.
7. Re-run the static and dynamic checks after any change to the corpus, the tool
   contracts, or the evidence plan. Reachability is a property of the pairing, not of
   either side alone, so either side moving can break it.

### 5.2 Write the tool contract down

Every tool exposed to a model — and every tool used to build or score an evaluation —
needs an explicit contract rather than an inferred one. Writing it down is cheap, and the
class of failure it removes is the kind you cannot see by looking at the output.
Checklist:

| Property | Requirement |
|---|---|
| Schema | Explicit input/output types; no implicit coercion the caller has to guess at |
| Result ordering | A stated, deterministic sort key — never "database default order" |
| Column/field set | Every field the task's evidence plan depends on is named in the contract, not merely present in some response |
| Cohort/tenant keying | Scoping parameters (customer, tenant, time window) stated; cross-entity queries carry a non-overlap or isolation guarantee |
| Pagination/limits | Stated limit semantics; a caller must be able to tell "no more results" from "results truncated" |
| Addressability | Every selector the contract requires is one the caller can actually construct from prior results — no phantom identifiers |
| Byte-level transport fidelity | Any proxy, gateway, or serialization hop between model and tool is verified byte-equivalent for anything a downstream grammar- or format-constrained consumer depends on (key order, whitespace, numeric formatting) — verified, not assumed [SCENARIO: SCENARIO-08](examples/SCENARIO-08_transport-serialization-defect.md) |
| Permissioning | Least-privilege; a tool MUST hold no grant on data it has no task reason to reach — this is the mechanical half of [ground-truth isolation](GLOSSARY.md#ground-truth-isolation) (chapter 13) |
| Error semantics | Distinguishable failure modes (not found / not permitted / transient error) that a caller can act on differently |
| Versioning | The contract is versioned as part of [execution-system](GLOSSARY.md#execution-system) identity; a version bump is a frozen-identity-breaking change, like a model or runtime bump |

Prefer narrow, typed, read-only tools over handing the model direct data-store access.
Narrow tools force a stable interface, produce execution traces you can actually read,
and make the reachability check in §5.1 tractable at all.

Where a tool must integrate with an external or provider-native system, expose both the
normalized and the provider-native identifiers. Cross-system ID mapping is a realistic
error source and useful evaluation material in its own right — not incidental plumbing
to hide.

### 5.3 Decide what gets into the context

The [context policy](GLOSSARY.md#context-policy) is the part of the execution system
governing what enters the model's context. Left undecided, it still exists; it is just
decided by whatever fits.

- **Budget allocation.** Fix, per task type, how the available context window splits
  between instructions, retrieved or tool-sourced evidence, and generation headroom.
  Treat that split as a versioned parameter.
- **Retrieval integration.** State how retrieved evidence enters the prompt — structured
  fields or free text — and whether the model can tell evidence from instructions from
  its own earlier output.
- **Context-rot hygiene.** Long-running or multi-turn contexts accumulate stale,
  contradicted, and superseded evidence. Define a pruning or re-grounding rule instead of
  letting context grow monotonically.
- **Structured evidence presentation.** Prefer explicit, labeled evidence blocks —
  source, timestamp, identifier — over undifferentiated concatenation. This is what makes
  citation verification (§5.2, and the verifier in chapters 03 and 07) possible at all.

### 5.4 Design the routing and the cascade

1. **Oracle analysis first — before you build anything.** Imagine a gate that already
   knows which tier will succeed on each item and always picks that one. It cannot
   exist. But you can compute exactly what it would have scored, because you can run
   both tiers on a fixed sample and look. That is an
   [oracle analysis](GLOSSARY.md#oracle-analysis): two runs and some arithmetic, and it
   prices the *entire* opportunity a router is competing for. On a sample of paired
   weak/strong outcomes, count four things — the share where the weak tier alone
   succeeds, the share the strong tier alone rescues, the share where escalation would
   still fail, and the rare inversions where the weak tier succeeds and the strong tier
   fails. Review those inversions by hand; they are usually corpus or scorer defects
   rather than evidence of the weak tier's superiority. If the oracle gain over
   weak-only is small, no router is worth its cost — stop here (§7). This is the
   cheapest step in the chapter and the one most often skipped.
2. **Check the economics.** Apply the break-even formula (§8) with your own tier costs,
   before committing engineering time.
3. **Build the deterministic gate.** If the task has a verifier, wire escalation to its
   verifiable failure signals: no valid output, a failed citation or schema check, any
   other deterministic verifier failure. The gate MUST NOT read anything gold-derived
   (chapter 04's gold-label boundary, restated for routing in §6).
4. **Only if headroom remains below the oracle**, consider a learned router as an
   *addition*, composed as `escalate = deterministic_rule OR learned_risk ≥ threshold`.
   It MUST NOT replace a working deterministic gate. Gate the candidate behind a
   TRAIN-only eligibility check — minimum out-of-fold discrimination and minimum lift
   over the class-identity ceiling — before it is allowed into selection at all.
5. **Leakage-audit any admitted candidate** (§4) before it is allowed to select
   anything.
6. **Run it observe-only**, then through a pre-registered promotion gate on the
   qualification split (§7), before any automated action.
7. **Instrument before deploying.** The production monitoring plan (chapter 12) and the
   rollback path (chapter 10) exist before graduation, not after.

## 6. Project adaptation parameters

**[PARAMETER] Routing-input taxonomy — which signals may inform a routing/escalation decision, and where.**

Not every signal that predicts well is allowed to decide. This table separates the two
questions.

| Feature class | Examples | Admissible where |
|---|---|---|
| **Task-intrinsic** | content, task class/complexity signals *derivable from the input itself*, evidence-bundle shape, tool-call count/pattern | Design-time features and production-observable, non-gold signals; caution — bundle shape and call-count features can indirectly encode class identity (§4) even when class itself is withheld |
| **System-state** | queue depth, budget burn, current-tier health/latency, degraded-mode flags | Any decision point; these are operational, not evidence about the task |
| **Policy** | consequence/stakes tier, SLA, permission scope, fail-open/closed mode | Any decision point; these constrain *what the gate is allowed to decide*, not what it observes |
| **Verifier/output** | schema validity, citation resolution, verifier pass/fail, confidence calibration against work actually done | Deterministic gates and learned routers alike — these are production-observable at serve time |
| **Gold/ground-truth** | correct label, expected action, evidence recall against a gold answer, scenario/class/seed identifiers, scorer internals | **MUST NOT** be admissible to any live routing/gate decision. Admissible only offline, to define training labels or to score outcomes after the fact (chapter 04's gold-label boundary: gold labels score but never choose) |

That last row is the one that gets violated by accident, so enforce it structurally
rather than by convention. Four mechanisms, all cheap: an explicit feature-name allowlist
that raises a schema error on a forbidden name; gold-removal invariance tests, which
confirm the features come out identical with the gold fields deleted; extraction tests
that run with no gold fields present at all; and an import ban preventing
feature-extraction code from importing evaluation or scoring modules. This is the
leakage-audit machinery's build-time half — chapter 13 covers the runtime and permission
half.

Other parameters to set per project, never shipped as universal numbers: the confirmation-
streak length before an escalation commits; whether a judge failure resets or holds a
confirmation streak; fail-open vs. fail-closed per edge (§4); the promotion-gate
thresholds in §7; and the break-even threshold that triggers building a router at all
(§8).

## 7. Decision gates and stopping conditions

**[DECISION GATE] Deterministic gate vs. learned router.** Inputs: does a task-level
verifier exist for the output; what does oracle analysis say the remaining headroom is
above the deterministic gate. Rule: the deterministic gate is the default whenever a
verifier exists, and a learned router is considered only as an addition, only after
eligibility and leakage-audit gating (§4, §5.4). Outcome: either build deterministic
only, or build deterministic plus a candidate learned router queued for the graduation
gate below.

**[DECISION GATE] Observe-only → automated-action graduation (G13).**

| Stage | Requirement | Evidence type |
|---|---|---|
| 1. Leakage audit | Beats class-identity ceiling under leave-one-group-out; feature-provenance review passed; OOD caution addressed | Measured, pre-registered |
| 2. Observe-only shadow | Runs alongside the incumbent, decisions logged, never acted on; agreement/regret vs. incumbent measured over a pre-registered window | Measured |
| 3. Promotion gate | Pre-registered rule evaluated once on the qualification split (one-look discipline, chapter 04); passes a stated, non-degenerate improvement bar — **[PARAMETER]** set per project, e.g. a materially large improvement above a noise floor *and* a bound against collapse toward the expensive tier, not a bare utility optimum (a threshold chosen by maximizing catches-minus-cost with no cap degenerates to "always escalate" or "never escalate" at extreme base rates) | Measured, one-look |
| 4. Rollback path defined | Chapter 10's rollback path exists and is rehearsed before automated action, not designed after an incident | *doctrine — not yet exercised* |
| 5. Monitoring plan | Chapter 12's drift/monitoring plan for the component is live before graduation | *doctrine — not yet exercised* |

A candidate that fails stage 1 MUST NOT proceed to stage 2, regardless of how good its
offline numbers look. And de-automation — reverting a graduated component to observe-only
or back to the deterministic gate — is pre-registered on the same terms as promotion. A
component does not get to keep its automated status by default once a regression is
observed; someone should not have to win an argument under pressure to turn it off.

**[STOP CONDITION] Global tripwires for this chapter.** Each of these means stop, not
proceed carefully.

1. A stratum's measured evidence-reachability ceiling is below its passing threshold —
   fix the tool contract or the evidence plan before evaluating anything on it (§5.1).
2. A learned router's out-of-fold score is indistinguishable from its class-identity
   ceiling — it has not cleared the leakage audit, and it may not select, route, or
   score anything (§4).
3. Oracle analysis shows small headroom over the cheaper tier — do not build a router.
   The deterministic gate, or no gate, is the answer (§5.4 step 1).
4. A promotion-gate rule's wording admits two readings — compute and disclose the
   outcome under both. Never silently resolve the ambiguity in the result's favor.
5. A candidate's confirmatory test would also be met by a same-size random policy at
   non-trivial probability — report that power figure alongside any "confirmed" verdict.
   A low-power confirmation is not a confirmation.
6. Any tool contract change (ordering, columns, scope) ships without a version bump —
   treat it as an unpinned execution-system change (chapter 02) and re-run the
   comparability-dependent evaluations.

## 8. Metrics and formulas

**Routing break-even.** The minimum share of traffic that must be served by the cheaper
tier for a routing layer to pay for its own gate/judge overhead. A gate is not free: it
runs on every item, including the ones it decides to leave alone.

```
f_min = C_gate / (C_strong − C_weak)
```

- `C_gate` — per-item cost of running the escalation gate/judge (currency or
  compute-time units).
- `C_strong`, `C_weak` — per-item cost of the strong and weak tiers, same units.
- `f_min` — minimum fraction of total items that must resolve on the weak tier for the
  routed system to cost no more than always using the strong tier.

*Derivation:* without routing, cost per item is `C_strong`. With routing, cost per item
is `C_gate + f·C_weak + (1−f)·C_strong`. Setting the two equal and solving for `f` gives
`f_min` above.

*Worked example (illustrative, invented round numbers).* Weak tier `C_weak = $0.002`/item,
strong tier `C_strong = $0.020`/item, gate `C_gate = $0.001`/item.
`f_min = 0.001 / (0.020 − 0.002) = 0.001 / 0.018 ≈ 5.6%`. If the deployed gate keeps at
least 5.6% of traffic on the weak tier, routing is cheaper than strong-only. Below that
share, the gate's own overhead outweighs the savings — do not deploy it.
**[ADAPT: EXT-SWITCHYARD-001]**: on one published benchmark (a 145-task agent suite, one
weak/strong pairing, as-of 2026-08-11), this rule's minimum offload was a small
single-digit percentage against an achieved offload above 90%, yielding a reported cost
reduction near three-quarters with accuracy retention in the low-to-mid 90s percent —
figures conditioned on that specific pairing and suite; re-measure your own tier costs
before trusting the shape of the result.

**Rescue rate / unnecessary-escalation rate.** These are the two numbers that say whether
a gate is any good. For a cascade's [escalations](GLOSSARY.md#escalation):

```
rescue_rate = successes_after_escalation / total_escalations
unnecessary_rate = (escalations where the weak tier would have succeeded) / total_escalations
```

A gate with a high rescue rate and a low unnecessary rate is doing its job cheaply. A
gate with a low rescue rate is escalating things the strong tier cannot fix either —
which is a residual capability gap, not a routing problem, and sends you back to rung 7+.

**False-negative cost.** The expensive failures in a cascade are the ones that are *not*
escalated and fail anyway — the routing false negatives — not the escalations that turn
out to have been unnecessary. An unnecessary escalation costs you one strong-tier call. A
false negative costs you a wrong answer that nothing caught. Report false negatives as a
first-class number alongside all-pass rate: a headline all-pass improvement that leaves
false negatives unchanged has not closed the gap that matters.

**Oracle ceiling.**

```
oracle_all_pass = 1 − both_fail_share
```

where `both_fail_share` is the fraction of paired items neither tier resolves. This is
the quality ceiling achievable by *any* router over those two tiers, independent of how
good the router is. Compute it early, because it caps the argument: no gate design,
however clever, scores above it. The gap between that ceiling and what the strong tier
already reaches on its own is all the quality a router can add — the other half of what
routing buys is cost, which is the break-even computation above.

**Class-identity ceiling comparator.** Fit a comparator that predicts the routing target
from group or stratum identity alone — for instance, the majority outcome within each
group. A candidate router's performance is credited only for the margin above this
comparator, evaluated under leave-one-group-out.

**Multi-tier composition.** For N ≥ 3 tiers, compose edges. Each edge between adjacent
tiers carries its own gate (deterministic or learned), its own escalation semantics
(fail-open/closed, confirmation streak), and its own break-even computed from that edge's
local pair of tier costs. There is no single global break-even for a chain — compute and
report one per edge.

```
tier_1 --(edge A gate)--> tier_2 --(edge B gate)--> tier_3
       f_min(A) = C_gateA / (C_2 − C_1)     f_min(B) = C_gateB / (C_3 − C_2)
```

## 9. Failure modes and anti-patterns

**[REJECTED]** (condition: always — these are generically wrong)

- **Assuming proxy/infrastructure transparency.** Believing that a request-path change —
  a proxy, an adapter, a gateway — does not affect model behavior because it is schema-
  or semantically equivalent, without paired same-session, byte-level output
  verification. [SCENARIO: SCENARIO-08](examples/SCENARIO-08_transport-serialization-defect.md).
- **Treating tool ordering/columns as an implementation detail.** A tool's sort order and
  returned-field set are part of its contract. Change either without a version bump and
  you have silently changed which properties are diagnosable at all.
- **Ungated learned-component adoption.** Deploying a learned router or classifier into
  any decision path — including observe-only, if its output reaches a downstream actor —
  without a passed leakage audit, whenever its training data is drawn from a small number
  of templates or clusters.
- **Pooled cross-validation under clustered labels.** Reporting a single pooled
  out-of-fold metric from grouped or leave-one-group-out CV when the label is strongly
  correlated with the group. The pooled number can read as generalization when it is fold
  base-rate shift.
- **Threshold-only utility optimization.** Choosing an operating threshold by maximizing a
  bare utility function (catches minus cost) with no cap, letting it silently degenerate
  to "always escalate" or "never escalate" at extreme base rates.
- **Silent post-hoc rule relaxation.** Loosening a pre-registered promotion or
  confirmation criterion after seeing shadow or qualify-split results — or resolving an
  ambiguous rule wording in favor of whichever reading passes — without disclosing both
  readings. Chapter 04's amendment-legitimacy rule applies to routing gates exactly as it
  applies to experiments.
- **Ignoring gate power.** Reporting a pre-registered promotion rule as confirmed without
  computing what a same-size random policy would score under the identical rule. A
  low-power confirmation is not information.
- **Trusting aggregate rates over paired disagreement review.** Comparing routing
  configurations only by aggregate all-pass rate, without manually reviewing the
  individual disagreement cells. Corpus and scorer defects routinely masquerade as
  routing-quality differences, and only paired review catches them. Where a review does
  correct something, report the as-measured and review-corrected numbers side by side —
  never overwrite the raw figure.
- **Building a router before an oracle analysis.** Investing in a learned routing
  component before measuring the paired-oracle opportunity map is a way to buy engineering
  effort for a gain that was never there.
- **Fail-open as an unexamined library default.** Shipping a gate's fail-open/closed
  behavior as whatever the library happens to do, rather than as a stated choice per edge,
  tied to the consequence class of that edge.

## 10. Vendor recipes

| Source | Verdict | Gives | Missing / your job | As-of |
|---|---|---|---|---|
| [NV-SWITCHYARD-001] NVIDIA NeMo Switchyard | **[ADAPT]** | An escalation-router product with four documented decision mechanisms and explicit parameters: weak-first, judge-on-actual-output, confirmation streaks, per-session latching, fail-open default, judge-failure-holds-the-streak semantics | The decision layer — when fail-open is *wrong* for your consequence class; three-tier composition (the shipped config schema admits exactly two tiers per route, so chain routes or write a custom policy selector for more); production maturity (pre-alpha, and the vendor's own "not for production use" as of this verification) | 2026-08-21 (product v0.2.0, 2026-08-10) |
| [EXT-SWITCHYARD-001] LangChain Switchyard benchmark | **[ADAPT]** | The break-even formula (§8) and one published operating point demonstrating it | Scope-conditioned to one weak/strong pairing on one fixed task suite — substitute your own tier costs, gate cost, and task mix before trusting the shape of the result, not just the formula | 2026-08-11 |
| [EXT-ROUTE-001] Cascade/learned-router literature (FrugalGPT, RouteLLM, AutoMix, HybridLLM) | **[REFERENCE]** | The published design space for cascades — uniformly learned gates; RouteLLM's out-of-distribution near-random result is the standing caution behind §4's leakage-audit requirement | A deterministic-gate alternative sits outside this literature's design space, so do not expect it to validate that choice; what it does instead is corroborate the caution about the alternative | 2026-08-21 |
| [NV-SLMRESEARCH-001] NVIDIA Research, small-language-models-for-agentic-AI position paper | **[REFERENCE]** | The rationale for a small/local-default, large/frontier-fallback cascade topology | Rationale only, not a procedure — pair it with §5.4's procedure rather than substituting it | 2026-08-20 |
| [NV-NEMOCLAW-001] NemoClaw / OpenShell agent sandbox | **[REFERENCE]** | A demo-grade credential-custody wrapper with host-side cost/quality routing around community agent harnesses | Pre-alpha; it wraps community harnesses rather than being a validated security boundary. The tool-calling security threat model (least privilege, injection red-teaming, credential custody) is chapter 13's G8, doctrine-not-yet-exercised there | 2026-08-20 |

## 11. Worked examples

The scenarios below are invented. Each one illustrates a rule in this chapter; none of
them is the evidence for one.

- [SCENARIO-04](examples/SCENARIO-04_harness-defects.md) — evidence unreachable by the
  deployed tool set, and a tool's sort order making a whole class undiagnosable. Both
  were initially indistinguishable from model weakness, until reachability replay and
  disagreement review isolated them.
- [SCENARIO-08](examples/SCENARIO-08_transport-serialization-defect.md) — a routing/proxy
  hop silently reordered a request's serialized field order, breaking a
  grammar-constrained consumer that depended on it. Found only by byte-equivalence
  verification, never by behavioral spot-checks.
- [SCENARIO-07](examples/SCENARIO-07_deterministic-cascade-gate.md) — a verifier-gated
  deterministic cascade achieving near-total rescue with zero unnecessary escalations,
  outside the published learned-gate design space, with an oracle analysis capping the
  prize before any gate logic was written.
- [SCENARIO-03](examples/SCENARIO-03_learned-router-leakage.md) — a learned router that
  scored well until a leave-one-group-out audit showed its features encoded which template
  a case belonged to. Nothing beat the class-identity ceiling, and the deterministic gate
  was retained.

**Illustrative oracle + routing-tier decision (invented round numbers).** A team pairs
weak- and strong-tier outputs on 200 held-out items and sorts the results into four
cells:

| Cell | Share | Reading |
|---|---|---|
| weak-pass / strong-pass | 30% | weak sufficient — cheap coverage |
| weak-fail / strong-pass | 55% | rescueable — a gate should escalate these |
| weak-pass / strong-fail | 3% | inversion — review by hand before trusting either score |
| both-fail | 12% | neither tier resolves it — a routing problem cannot fix this |

Oracle ceiling = 1 − 12% = 88%. With `C_weak = $0.001`, `C_strong = $0.015`,
`C_gate = $0.0005`: `f_min = 0.0005 / 0.014 ≈ 3.6%`. The gate repays its own overhead
once more than 3.6% of traffic stays on the weak tier, and the weak tier already answers
30% of this sample correctly — so routing is worth building here. The 55%
rescueable share is the population a gate exists to serve; a deterministic gate is the
first thing to build against it (§5.4). Only the residual 12% both-fail share is a
candidate for a rung-7+ intervention (chapter 09), and never for a smarter gate.

## 12. Outputs and artifacts

- A written tool-contract specification per tool (the §5.2 checklist), versioned with the
  rest of the execution system.
- The static and dynamic evidence-reachability test results per stratum, re-run after any
  corpus or contract change.
- A routing policy document: gate type per edge, escalation semantics, fail-open/closed
  choice, and — for multi-tier — the per-edge break-even.
- For any learned routing candidate: a leakage-audit report (class-identity ceiling
  comparison, leave-one-group-out results, feature-provenance review), an oracle-analysis
  report, an observe-only shadow log, and — on graduation — a
  [method decision record](GLOSSARY.md#method-decision-record) recording the
  promotion-gate result and both readings of any ambiguous rule clause.

## 13. Sources

| ID | Role here |
|---|---|
| [NV-SWITCHYARD-001] | Escalation-router mechanics and parameter vocabulary, ADAPT |
| [EXT-SWITCHYARD-001] | Routing break-even formula and one published operating point, ADAPT |
| [EXT-ROUTE-001] | Learned-gate literature and the OOD-generalization caution behind the leakage-audit requirement |
| [NV-SLMRESEARCH-001] | Rationale for the small/local-default, large/frontier-fallback cascade topology |
| [NV-NEMOCLAW-001] | Credential-custody wrapper reference; cross-ref chapter 13 G8 |

Gap dispositions in this chapter:

- **G11 (routing-input taxonomy): COVERED** — §6, the task-intrinsic × system-state ×
  policy × verifier/output × gold-label admissibility table.
- **G13 (observe-only → automated-action graduation criteria): COVERED**, with the
  promotion-gate and rollback/monitoring stages marked
  **COVERED-AS-DOCTRINE-NOT-YET-EXERCISED** — §7, the five-stage graduation gate. To be
  precise about the support: the leakage-audit and observe-only stages are worked through
  in an illustrative scenario, and the promotion-gate-to-automated-action and rollback
  stages are not worked through anywhere. None of these stages has an internal execution
  record behind it in this build.
- **G19 (tool-contract design): COVERED** — §5.2, the tool-contract checklist, and §4's
  principle binding contracts to execution-system identity.

---

> [← Previous](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md) · [Index](README.md) · [Next →](09_TRAINING_AND_DATA.md)
