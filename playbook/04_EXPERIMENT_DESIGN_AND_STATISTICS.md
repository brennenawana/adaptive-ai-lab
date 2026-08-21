# 04. Experiment Design and Statistics

> Part of the **Adaptive AI Systems Playbook** v0.1.0 ·
> [← Previous](03_EVALUATION_FOUNDATION.md) · [Index](README.md) · [Next →](05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md)
> **Reading time:** ~30 min. **Prerequisites:** [00](00_PRINCIPLES_AND_SCOPE.md),
> [02](02_EXECUTION_SYSTEM_MODEL.md), [03](03_EVALUATION_FOUNDATION.md).

## 1. Purpose and when to read this

Read this chapter before designing, freezing, or running any experiment a decision
will be made from — a model or configuration comparison, a calibration pilot, a
routing or fine-tuning acceptance test. It turns "we ran an eval and got a number"
into a claim that survives scrutiny: what the design can and cannot detect, when
an arm may stop early without breaking the claim, what a mid-run change is allowed
to do, and what verdict the finished comparison is actually entitled to.

This chapter does not build the instrument (chapter 03) or pin what is being
measured (chapter 02); it assumes both exist and answers one question: given a
trustworthy [evaluation instrument](03_EVALUATION_FOUNDATION.md) and a
[frozen execution-system identity](GLOSSARY.md#frozen-identity), how do you design
an experiment whose answer you can act on? The statistics stated here are the
canon this playbook uses everywhere else; full derivations, assumption boxes, and
worked calculations live in
[references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md) — this
chapter states what to use and why; that file proves it.

## 2. Inputs required

- A trusted evaluation instrument from chapter 03: validated categories, measured
  ceilings, isolated gold labels.
- A [frozen execution-system identity](GLOSSARY.md#frozen-identity) per arm and
  any relevant [reproducibility-boundary](GLOSSARY.md#reproducibility-boundary)
  probe results (chapter 02 §5) — a comparison is not "about the model" if the
  runtime, harness, or hardware moved underneath it.
- A stated decision the experiment drives, and the project's
  [stakes tier](GLOSSARY.md#stakes-tier) ([rigor dial](GLOSSARY.md#rigor-dial),
  chapter 00 §6) — which fixes how much of this chapter's machinery is mandatory.
- For clustered domains: a candidate [clustering unit](GLOSSARY.md#clustering-unit)
  and an [ICC](GLOSSARY.md#icc) estimate — measured on a related suite, or, for a
  cold-start project with no prior suite, a **declared prior** ICC labelled as such
  and frozen together with the pre-registered re-estimation procedure that will
  replace it before the qualification look (§5 Step 9, §7).

## 3. Decisions this chapter supports

- Is this experiment worth running, and at roughly what size? (prediction ledger,
  [MDE](GLOSSARY.md#mde))
- Can this arm stop now, and what may the report say if it does? (curtailment,
  [spend semantics](GLOSSARY.md#spend-semantics))
- Is a mid-run change a legitimate amendment or post-hoc threshold shopping?
  (amendment legitimacy)
- Where does a cheap diagnostic or exploratory run live in the record? (diagnostic
  run kind)
- What did the finished comparison actually establish — CONFIRMED, REFUTED,
  INCONCLUSIVE, or a bare ranking? (verdict vocabulary)

## 4. Normative principles

**[PRINCIPLE] The contract executes; nobody improvises mid-run.** (consensus)
An [experiment contract](GLOSSARY.md#experiment-contract) fixes the question,
prediction, splits, calibration rules, statistical plan, and gates before any data
is collected — [pre-registration](GLOSSARY.md#pre-registration). Once
[frozen](GLOSSARY.md#freeze), the rule runs the experiment, not the investigator's
judgment mid-run. This is clinical-trial consensus: a data/safety monitoring board
executes a pre-specified adaptation rule rather than exercising discretion in the
moment [EXT-STOPPING-002]. The adaptation rule itself MAY be pre-registered — what
is forbidden is inventing a rule after seeing outcomes.

**[PRINCIPLE] A held-out split is spent at the first executed item.** (strong-evidence)
[Spend semantics](GLOSSARY.md#spend-semantics): a partial run already reveals the
sufficient statistic for the item it ran, so there is no "peek and re-run." Every
[look](GLOSSARY.md#look) — including an offline replay of stored outputs — is
recorded in the [look ledger](GLOSSARY.md#look-ledger)
([templates/TEST_LOOK_LEDGER.md](templates/TEST_LOOK_LEDGER.md)), and a
pre-registered exposure threshold triggers the suite-refresh review (chapter 03).
This is also why [certainty curtailment](GLOSSARY.md#certainty-curtailment) is admissible: its
only possible consequence is irreversibly rejecting an already-spent look, not an
early peek at a fresh one.

**[PRINCIPLE] Every tolerance names its breach consequence before data.** (strong-evidence)
A [consequence-bearing tolerance](GLOSSARY.md#consequence-bearing-tolerance) states,
in the contract, what happens on breach: **ABORT**, **RECALIBRATE**, or
**PROCEED-WITH-DECLARED-CEILING** — evaluated by
[curtailed exact counting](GLOSSARY.md#curtailed-exact-counting)
and enforced [fail-closed](GLOSSARY.md#fail-closed) by the runner. The PROCEED
branch carries a hard condition: **the declared ceiling and the projected cost of
proceeding are pre-registered in the contract at freeze, per tolerance** — not
written after the breach is observed, by the party that wants to proceed. A price
authored post-data is the unpriced escape hatch under another name and returns the
decision to mid-run investigator judgment, which the first principle above forbids;
a PROCEED clause with no pre-registered cost MUST fail contract review (§7), and no
cost may be invented later to rescue it. First-principles
argument: a tolerance whose breach clause is silent — "record and proceed" with no
priced consequence — is not a control, because detecting a violation changes
nothing about what happens next. Corroborated by the DSMB pre-specification pattern
[EXT-STOPPING-002] and by [CASE-001](examples/CASE-001_consequence-bearing-tolerances.md),
where exactly this gap let a measured, large tolerance breach proceed unpriced.

**[PRINCIPLE] Screening ranks; only a frozen comparison infers.** (strong-evidence)
[Screening vs inference](GLOSSARY.md#screening-vs-inference): racing and
successive-halving (ASHA-style rungs) on the iterate split rank candidates cheaply
to decide who advances [EXT-STOPPING-003]. Screening results MUST NOT carry
significance claims and MUST NOT replace the frozen qualify/confirm comparison —
it feeds that comparison; it never substitutes for it.

**Defer is not eliminate — the precedence rule.** The two families inside
[EXT-STOPPING-003] behave differently and MUST NOT be conflated. A *rank-based*
rung (successive halving / ASHA drops the bottom 1 − 1/η by rank at every rung)
separates candidates on margins that are arbitrarily small and routinely far below
the rung's own MDE; such a rung MAY only **DEFER** or **SUSPEND** a candidate —
stop spending on it now, keep it revivable at the frozen comparison, and record the
deferral with its margin. **Permanent** elimination requires one of exactly two
warrants: a *racing* confidence bound (Hoeffding/Bernstein, computed at the
[clustering unit](GLOSSARY.md#clustering-unit), which eliminates only once the
bound separates candidates) or a margin at or above the elimination rule's
threshold below. Absent one of those, a candidate that lost a rung is deferred, not
gone. Accepting rank-based permanent elimination anyway is a deliberate, priced
trade-off: record it as a [method decision record](GLOSSARY.md#method-decision-record)
naming the noise-elimination risk you are buying.

**[PRINCIPLE] No candidate is eliminated on a margin the design cannot resolve.** (strong-evidence)
The [elimination rule](GLOSSARY.md#elimination-rule): no candidate is withdrawn from
selection on a margin smaller than the pilot's own [MDE](GLOSSARY.md#mde). Below
that margin the licensed moves are: both candidates proceed under a pre-registered
budget, the decision defers to the qualification split, or the selection metric
changes to one the pilot can actually resolve. First-principles argument: a
decision made on noise the design admits it cannot distinguish from zero is a coin
flip dressed as one. This rule binds *screening as well as selection* — a rung's
rank order is not a margin, so rungs defer and racing bounds eliminate (see the
precedence rule above). It governs *comparative* margins only; an absolute
pass-rate gate is a decision rule rather than an inference and is deliberately
exempt, under the sizing obligation stated in §8.

**[PRINCIPLE] Same-item comparisons pair; clustered outcomes cluster-correct.** (strong-evidence)
[Paired design](GLOSSARY.md#paired-design): same-item cross-arm comparisons use
paired standard errors, not two-sample SEs — free statistical power any same-item
design should claim [EXT-STATS-001]. Separately, whenever outcomes correlate within
a [clustering unit](GLOSSARY.md#clustering-unit) (task class, template, document,
session), cluster-robust paired inference (a t-test on per-cluster means, df =
clusters − 1) is the primary statistic; McNemar exact on discordant pairs is
secondary, MUST be labeled anti-conservative under clustering [EXT-STATS-001]. A
comparison reported without checking for clustering is wrong not because
clustering is exotic, but because independence was never verified.

**[PRINCIPLE] Gold labels score; they never choose.** (consensus)
The [gold-label](GLOSSARY.md#gold-labels) boundary: ground truth MAY score outcomes
and fit pre-registered calibration procedures on the iterate split. It MUST NOT be
readable by the system under test at inference time, and MUST NOT select, route, or
tune anything on qualify or confirm splits — enforced structurally, not by
convention (see [ground-truth isolation](GLOSSARY.md#ground-truth-isolation) and
chapter 13's permission/role-isolation mechanics).

**[PRINCIPLE] A causal claim across an instability boundary needs a paired control.** (strong-evidence)
Chapter 02's principle, restated because it binds experiment design directly: once
a [reproducibility-boundary](GLOSSARY.md#reproducibility-boundary) probe finds an
axis unstable, no comparison crossing it may claim causal attribution to one
intervention without a
[contemporaneous paired control](GLOSSARY.md#contemporaneous-paired-control) —
both arms in the same session/window, everything but the intervention fixed,
order pre-registered and counterbalanced — or the claim MUST be declared
unavailable and the comparison relabeled descriptive
[CASE-012](examples/CASE-012_restart-instability-paired-controls.md). Session
instability is itself outcome correlation — model it as §8 models any clustering
unit, not as a separate problem.

**[PRINCIPLE] A diagnostic run lives inside the fail-closed record, non-promotable.** (strong-evidence)
A cheap probe run to inform a GO/RE-SCOPE/DROP decision (chapter 07's
[diagnostic gate](GLOSSARY.md#diagnostic-gate)) is recorded under the
[diagnostic run kind](GLOSSARY.md#diagnostic-run-kind): ledgered, cryptographically
non-promotable — it can inform, it cannot qualify. A relaxed, unrecorded path
recreates exactly the defect [provenance](GLOSSARY.md#provenance) exists to forbid
(chapter 00's P10) [CASE-011](examples/CASE-011_diagnostic-gate.md).

## 5. Default procedure

**Step 1 — State the question, the decision, and a prediction.** One sentence: the
question this experiment answers and the decision its answer drives. Record a
pre-run point estimate and interval for the primary metric in the
[prediction ledger](templates/PREDICTION_LEDGER.md) — scored against the actual
result on completion. A handful of entries turns "is this experiment worth
running?" from taste into an empirical question about your own calibration.

**Step 2 — Define splits and roles.** Three roles, whatever their sizes: an
**iterate split** (freely re-run for screening, calibration, pilots, diagnostics —
consequence-bearing tolerances apply, re-runs ledgered), a **qualification split**
(one look per candidate, against pre-frozen gates), and a **confirmation split**
(one look, confirmation only) — [one-look discipline](GLOSSARY.md#one-look-discipline):
select on the qualification look, confirm on the confirmation look, never iterate
against either. **Do not size these splits by tradition or by copying another
project's numbers** — derive them from a power analysis targeted at the MDE the
decision needs (§8); a round default with no derivation is a placeholder that
silently becomes policy if nobody revisits it.

**Step 3 — Freeze the execution-system identity per arm.** Pin every arm per
chapter 02 §5 Step 1 before any iterate-split inference; if arms cross a measured
reproducibility boundary, design the contemporaneous paired control now (§4), not
after seeing results.

**Step 4 — Pre-register calibration rules as consequence-bearing tolerances.** For
every parameter calibrated on the iterate split (a generation cap, a decoding
budget, a server setting), state the calibration procedure, the tolerance, and the
named consequence on breach (ABORT / RECALIBRATE / PROCEED-WITH-DECLARED-CEILING —
the declared ceiling and its projected cost written *here, at freeze*, never after
the breach); evaluate by curtailed exact counting (§8) — halt the phase
and execute the named consequence at violation *k*+1 of a ≤*k*-in-*n* tolerance, no
hypothesis test, no error-rate claim. Check whether the tolerance is actually
likely to bind for this candidate class before trusting it: a rule whose fallback
fires for every candidate has not calibrated anything; it has silently become the
policy.

**Step 5 — If screening more than two candidates, pre-register racing/ASHA
rungs.** Rungs run on the iterate split only and MUST be stratum-balanced at every
rung (a rung built from one stratum's cases inverts real rankings under
clustering — §9); screening produces a ranking, feeding but never replacing the
frozen qualify/confirm comparison (§4). Pre-register which rung outcome is a
**deferral** (rank-based: revivable at the frozen comparison) and which, if any, is
a **permanent elimination** (racing confidence bound at the clustering unit, or a
margin ≥ the elimination-rule threshold) — §4's precedence rule. Filter
near-duplicate configurations with a cheap bake-off before paying full evaluation
cost for each.

**Step 6 — Pre-register the statistical plan.** State the clustering unit and its
ICC (measured, or a declared prior with the re-estimation procedure that replaces
it — §7), the design effect and effective N it implies, the MDE at the project's
α/power targets, and — before any data — what each possible outcome will be read as
(CONFIRMED / REFUTED / INCONCLUSIVE / RANKED; §8). Where the outcome is judge- or
annotator-graded, state the grader reliability assumed in the power calculation
(κ or agreement rate) and its source — a noisy grader inflates the N you need (§8).
If a [descriptive vocabulary](GLOSSARY.md#descriptive-vocabulary) is licensed,
define its categories now, together with any equivalence margin ±d and the
equivalence test that a "competitive"/"no material difference" category requires
(§8) — no margin, no such category. Set the elimination-rule threshold from the
same MDE (§4) and commit to the three licensed moves below it. If the decision also
turns on an absolute pass-rate bar, record the bar's own resolvability here
(is `bar ± MDE` straddled? — §8).

**Step 7 — Pre-register curtailment.** State whether certainty curtailment applies
to qualify/confirm arms, its bar, and the three mandatory guards (§8): spend
semantics, interval-only partial reporting, and the paired-comparison firewall.
Disabling curtailment requires a written justification in the contract.

**Step 8 — Pre-register the amendment procedure, if any**, against §7's amendment
legitimacy gate: what may be amended, from what evidence, under what disclosure.
Silence here means no amendment is legitimate later without a
[method decision record](GLOSSARY.md#method-decision-record).

**Step 9 — Freeze.** Commit the contract (content-hash bound) **before any
qualification- or confirmation-split item executes, and before any iterate-split
evidence is used for inference** — screening, calibration, and an ICC-estimation
pilot on the iterate split MAY precede the freeze, each still running under its own
rules registered before it executes (Steps 4–5), but the moment iterate-split
output feeds an inferential claim or fixes a gate value, freeze first. Cold start
with no prior ICC: freeze carrying a *declared prior* ICC plus the pre-registered
re-estimation procedure that MUST complete before the qualification look (§7).
Nothing above the amendment log changes after this point.

**Step 10 — Execute in round-robin order.** For any run whose prefix might inform
an interim decision — a screening rung, a curtailment check, a calibration pilot —
interleave execution across strata (one item per stratum, repeat) so every prefix
is approximately stratum-balanced. Stratum-*blocked* order (all of one class, then
the next) makes every prefix unrepresentative — the worst case for any interim
rule, since the strata seen first and last are not a random sample of the whole
(§9).

**Step 11 — Score against pre-frozen gates; apply curtailment where it fires.**
Report a curtailed arm's certain interval and unrun strata (§8) — never a partial
point estimate — and exclude it from every paired comparison, ranking, and
screening rung.

**Step 12 — Compute the verdict.** Primary: cluster-robust paired inference.
Secondary: McNemar exact, labeled anti-conservative under clustering. Read the
verdict off the pre-registered test, not off the point estimate: the primary
statistic either crosses its pre-registered threshold (CONFIRMED in the predicted
direction, REFUTED against it) or it does not, and every non-crossing result is
**INCONCLUSIVE** — reported with its confidence interval *and* the design's MDE, so
the reader sees what this design could have resolved. Never "no difference" or
"equivalent"; a "competitive"/"no material difference" reading is licensed only by
a pre-registered equivalence margin and a passed equivalence check (§8).

**Step 13 — Close the loop.** Score the prediction ledger entry against the
actual result, append the look(s) to the look ledger and any executed amendment to
the amendment log, and route exploratory or diagnostic side-runs to the
non-promotable diagnostic run kind (§4) — never off the record.

## 6. Project adaptation parameters

**[PARAMETER] Split sizes.** Derived from a power analysis targeted at the MDE the
decision needs (§8), not copied from another project — a Tier-1 direction-finding
pilot needs far less power than a Tier-3 adoption gate on the same metric. State
the derivation in the contract, not just the resulting number.

**[PARAMETER] α and power targets.** Default α=.05, power=.80 for a Tier-2 project
(the canonical MDE formula, §8). A Tier-3 decision SHOULD tighten one or both and
state the tightened values; a Tier-1 pilot MAY relax power in exchange for an
explicit "screening only, not inference" label.

**[PARAMETER] Curtailment bar and tolerance *k*.** The pass-rate `bar` in the
certainty curtailment rule (§8) is the decision's actual adoption/rejection
threshold, taken from the contract's qualification/confirmation gate, not
convention — and N is sized so `bar ± MDE` is not straddled, because curtailment's
rejection is irreversible (§8). The tolerance *k* for a consequence-bearing
calibration rule comes from a source that exists *before* the pilot it governs: a
prior suite's measured violation rate, a stated operational tolerance for the
failure mode, or an explicit pre-registered pilot run under a separate contract. It
is never derived from the pilot this tolerance governs — that is circular against
the freeze point (§5 Step 9) and is post-hoc threshold selection — and never picked
to make a preferred setting pass.

**[PARAMETER] Racing/ASHA rung sizes and reduction factor η.** Calibrate to
candidate count and iterate-split size; every rung MUST be stratum-balanced
regardless (§5 Step 5, §9).

**[PARAMETER] Look-ledger refresh threshold.** The count of qualify/confirm looks
against one suite version that triggers the chapter 03 suite-refresh review — state
it in writing; a threshold decided informally after the fact is not a threshold.

**[PARAMETER] pass^k subset and *k*.** Sized to be affordable against a stochastic
arm's per-call cost, not fixed at one value across every project.

## 7. Decision gates and stopping conditions

**[DECISION GATE] Freeze gate.** The freeze point is one point, stated once:
**before any qualification- or confirmation-split item executes, and before any
iterate-split evidence is used for inference.** All of the following MUST be true
at that point — this table is the canonical checklist the contract template and
chapter 14 restate:

| # | Requirement | Where it lives |
|---|---|---|
| 1 | Contract committed, content-hash bound, before any qualification/confirmation execution and before any iterate-split evidence is used for inference | [templates/EXPERIMENT_CONTRACT.md](templates/EXPERIMENT_CONTRACT.md) |
| 2 | Every calibrated parameter's tolerance names ABORT / RECALIBRATE / PROCEED-WITH-DECLARED-CEILING, with the projected PROCEED cost **pre-registered at freeze** | §4, §5 Step 4 |
| 3 | Statistical plan written: clustering unit, ICC (measured, or a declared prior with its pre-registered re-estimation procedure), DEFF, N_eff, MDE, verdict-reading table | §5 Step 6, §8 |
| 4 | Prediction ledger entry filled | §5 Step 1 |
| 5 | Look ledger updated with this experiment's planned looks | §5 Step 2 |
| 6 | Execution-system identity + authoritative clock declared per arm, node placement pre-registered | chapter 02 §5–6 |
| 7 | Elimination-rule threshold stated (= pilot's own MDE) | §4, §5 Step 6 |
| 8 | Curtailment clause + the three guards stated, or disabled with written justification | §5 Step 7, §8 |

The contract template MAY append template-implementation items — a recorded
smoke/integrity pass, declared round-robin ordering — tied to its own sections;
those are implementation detail, not additional gate requirements.

*Tier applicability.* Rows 2, 5, and 6 restate never-skippable floor items
(chapter 00 §6: predeclared consequences, recorded held-out exposure, identifiable
provenance) and bind at **every** tier, Tier 1 included — at Tier 1 in their floor
form (exposure recorded durably somewhere; the full look ledger is the Tier-2
instrument). Rows 1, 3, 4, 7, and 8 are mandatory at **Tier 2+**; a Tier-1
exploratory pilot MAY carry them in notes-grade form provided its output is
labelled "screening only, not inference" (§6) and never used for an adoption claim.
A Tier-1 project making a Tier-3 decision inherits the higher tier's rows
(chapter 00 §6's rule of proportion).

*Cold start — no prior ICC.* A greenfield project has no related suite to measure
an ICC on, and this playbook forbids both assuming zero (§8) and copying another
project's number (§6). The licensed path: freeze carrying a **declared prior ICC**,
labelled as such in the contract, plus a pre-registered re-estimation procedure —
an ICC-estimation pilot on the iterate split, or under the non-promotable
[diagnostic run kind](GLOSSARY.md#diagnostic-run-kind) (§4) — which MUST complete,
with its DEFF / N_eff / MDE revision committed, **before the qualification look**.
Because that procedure was pre-registered, draws only on iterate-split evidence,
and lands before any qualify/confirm execution, the revision satisfies the
amendment-legitimacy gate below by construction; it is still logged as an
amendment, with condition 4's direction-of-benefit disclosure (a downward ICC
revision raises N_eff and lowers the stated MDE — exactly the direction a
skeptical reader must be shown).

**[DECISION GATE] Amendment legitimacy.** A change to a frozen contract is a
legitimate amendment, not post-hoc threshold shopping, only if **all five** hold:

1. The amendment procedure itself was pre-registered at freeze.
2. It is derived only from iterate-split evidence, via formulas fixed at freeze.
3. It is committed before any qualify/confirm execution.
4. Its direction of benefit is analyzed and disclosed — does it happen to favor a
   pass, stated plainly?
5. When it moves toward permitting a pass, a **mandatory** skeptical-reader note
   states how a reader inclined to distrust the result would characterize it.

An amendment failing any condition MUST NOT be applied without a written
[method decision record](templates/METHOD_DECISION_RECORD.md) documenting the
deviation and its scope.

**[DECISION GATE] Diagnostic run kind.** Where should a cheap pre-run probe live?

| | Diagnostic run kind (inside the fail-closed record, non-promotable) | Unrecorded ad-hoc run |
|---|---|---|
| Provenance | Ledgered, hash-chained, auditable | None — unreproducible by construction |
| Can inform a GO / RE-SCOPE / DROP decision | Yes, against pre-registered decision bands | Informally at best; never binds a decision at Tier 2+ |
| Can qualify a candidate or promote a result | No — cryptographically non-promotable | N/A — invisible to the record |
| Overhead | Same discipline as any registered run (small) | Looks cheaper; recreates the unrecorded-execution-path defect (chapter 00 P10) |
| Correct choice | Always, for a pre-registered diagnostic (chapter 07) | Never, at Tier 2+ |

**[STOP CONDITION] Global tripwires.**

| Trigger | Required response |
|---|---|
| A consequence-bearing tolerance breaches | Execute the named consequence — arguing with it instead is chapter 00's global tripwire #4 |
| Certainty curtailment fires (§8) | Halt that arm, report the certain interval only, exclude it from every paired comparison, ranking, and screening rung |
| The look-ledger's pre-registered exposure threshold is hit | Trigger the chapter 03 suite-refresh review before the next qualify/confirm look |
| The primary statistic did not cross its pre-registered threshold, and the result is about to be reported as a difference or as an equivalence | Report INCONCLUSIVE with its confidence interval and the design's MDE. A "competitive"/"no material difference" reading requires a pre-registered equivalence margin ±d and a passed equivalence check (§8) — pre-registration alone does not license it |
| A rank-based screening rung is about to remove a candidate permanently | Downgrade to DEFER (revivable at the frozen comparison) unless a racing confidence bound or a margin ≥ the elimination-rule threshold warrants elimination (§4) |

## 8. Metrics and formulas

Statements only — assumptions, proofs, and additional worked calculations live in
[references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md), linked
section by section below. All worked numbers in this section are **illustrative,
invented, and round** — a generic support-ticket-triage classifier comparison, not
any project's measured data.

### Clustering unit, ICC, design effect, effective N

A [clustering unit](GLOSSARY.md#clustering-unit) is any grouping within which
outcomes correlate — task category, template, document, or (per chapter 02) a
session/host axis a reproducibility probe found unstable. [ICC](GLOSSARY.md#icc)
is the share of outcome variance attributable to cluster membership, estimated
from data (one-way ANOVA on per-cluster indicators; never assumed zero, never
copied from another project). A cold-start project with nothing to estimate from
freezes a *declared prior* and re-estimates it before the qualification look, under
§7's cold-start path — a labelled prior with a committed replacement procedure, not
a borrowed number. Full estimation forms (ANOVA and paired-difference):
[references/STATISTICS_FORMULAS.md#icc](references/STATISTICS_FORMULAS.md#icc).

```
DEFF   = 1 + (m − 1) × ICC        # m = average cluster size
N_eff  = N / DEFF
```

*Worked example (illustrative, invented round numbers).* A suite of 200 items is
grouped into 20 task categories, 10 items each (m=10). A pilot measures ICC = 0.30
**on the per-item paired differences `d_i`** — not on either arm's marginal
outcomes, which is a different number and the wrong input for a paired analysis
(see [references/STATISTICS_FORMULAS.md §2](references/STATISTICS_FORMULAS.md#icc)).
`DEFF = 1 + (10−1)×0.30 = 3.70`. `N_eff = 200 / 3.70 ≈ 54` — the suite carries the
statistical weight of about 54 independent pairs, not 200. Full derivation:
[references/STATISTICS_FORMULAS.md#design-effect](references/STATISTICS_FORMULAS.md#design-effect).

### Minimum detectable effect (MDE)

[MDE](GLOSSARY.md#mde) is computed before the experiment, at stated α and power,
after clustering correction. For a paired binary comparison, an approximate
closed form (McNemar-based; full derivation, exact and asymptotic forms:
[references/STATISTICS_FORMULAS.md#mde](references/STATISTICS_FORMULAS.md#mde)):

```
MDE ≈ (z_α/2 + z_power) × √(pd / N_eff)
```

where `pd` is the expected **discordance rate** (share of item-pairs where the two
arms disagree at all). **The MDE ≤ pd constraint**: a paired difference in success
rate can never exceed the discordance rate by construction (|Δ| ≤ pd — only
discordant pairs can contribute to a paired difference), so a design whose stated
MDE exceeds its plausible discordance cannot detect *any* effect this comparison
could produce. That is an underpowering signal, not necessarily an arithmetic slip:
it falls out of a correctly evaluated formula whenever `N_eff < 7.84 / pd` at
α=.05 / power=.80 (7.84 = (1.96+0.84)²). Recheck the arithmetic first, then add
clusters or relax the power target — and either way, do not read MDE > pd as
evidence about the world.

*Worked example (illustrative, continuing above).* At α=.05, power=.80
(`z_α/2≈1.96`, `z_power≈0.84`), N_eff≈54, expected discordance `pd=0.20`:
`MDE ≈ (1.96+0.84) × √(0.20/54) ≈ 0.17` — this design resolves a ~17-point paired
difference and no smaller one. Since 0.17 ≤ 0.20 the design is just barely coherent
at this discordance rate (equivalently, N_eff ≈ 54 clears the 7.84/0.20 ≈ 39
threshold); a design on the wrong side of it needs more N_eff (more clusters, not
more items per cluster) or a relaxed power target before it is worth running.

**Assumption — the per-item outcome is observed without error.** Every MDE and
power form here, and in the formulary's §1–§5, treats the recorded score as the
truth. A noisy grader — an LLM judge, or annotators at imperfect agreement —
attenuates the observed effect toward zero and inflates the N needed to detect a
real one, so a judge-graded design sized straight from these formulas is
systematically underpowered on exactly the dimension chapter 03 §5.7 flags as
highest-risk (and, where the noise is asymmetric between arms, it can bias the
direction as well). See the measurement-error note in
[references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md), and state
the grader reliability used in the power calculation (κ or agreement rate) and its
source in the contract (§5 Step 6).

### Paired-difference standard error

[Paired design](GLOSSARY.md#paired-design): paired SE is strictly smaller than the
naive two-sample SE whenever per-item outcomes correlate positively across arms —
true almost always for same-item designs, since items easy for one arm tend to be
easy for the other. *Worked example (illustrative).* Two-sample: p₁=0.70, p₂=0.60,
n=100 each → `SE ≈ √(0.70×0.30/100 + 0.60×0.40/100) ≈ 0.067`. Paired, same 100
items, discordance pd=0.25 → `SE ≈ √(0.25/100) = 0.050`.

An SE is not a resolvable effect: **"resolves" is reserved for the MDE**, which at
α=.05 / power=.80 is ≈ 2.80 × SE. So this pair of designs resolves ~14 points
paired (2.80 × 0.050 = 0.140) versus ~18.8 points two-sample (2.80 × 0.067 =
0.188) — a ~25% tighter design for free, and neither resolves the 10-point observed
gap in this example, which is **INCONCLUSIVE** at this design. Reading the 10-point
gap as a difference because it exceeds one SE is precisely the sub-MDE promotion
§9 rejects and chapter 00's tripwire #6 fires on. Full derivation:
[references/STATISTICS_FORMULAS.md#paired-difference-se](references/STATISTICS_FORMULAS.md#paired-difference-se).

### Curtailment arithmetic

**Consequence-bearing tolerances** ([curtailed exact counting](GLOSSARY.md#curtailed-exact-counting)):
with a tolerance of at most *k* violations in *n*, halt the phase at violation
*k*+1 and execute the named consequence. Exact arithmetic; no distributional
assumption, no error-rate claim. *Worked example*: tolerance ≤3 violations of 40
iterate-split items → the phase halts and escalates at the 4th violation, wherever
in the sequence it falls.

**[Certainty curtailment](GLOSSARY.md#certainty-curtailment)** (qualify/confirm
arms): halt an arm when `passes + items_remaining < ⌈bar × N⌉`. *Worked example*:
bar=0.60, N=50 (`⌈0.60×50⌉=30`); after 35 items, 8 passes, 15 remaining →
`8+15=23 < 30` → curtail — this arm cannot reach the bar even if every remaining
item passes. Three mandatory guards, all in force whenever curtailment is enabled:

1. **Spend semantics** — curtailment's only admissible consequence is irreversible
   rejection of an already-spent arm, never an early peek. To keep it that way, the
   curtailment statistic is computed by the runner and exposed only as
   **HALT / CONTINUE**: interim pass counts on a qualify/confirm arm are not
   disclosed to the operator before that arm completes or halts, so a legitimate
   stopping rule cannot quietly become an interim read of held-out outcomes that
   informs other in-flight choices.
2. **Interval-only reporting** — report the certain interval `[k, k+remaining]/N`
   plus the unrun strata, never a partial point estimate (which systematically
   over- or understates the true rate depending on which strata went unrun).
3. **Paired-comparison firewall** — a curtailed arm never enters a paired
   comparison, a ranking, or a screening rung; only its certain interval and its
   unrun strata are reportable. Curtailment deletes items non-randomly, by whatever
   strata were left unrun, which can flip a paired test's outcome — or an
   ordering — by composition alone.

**Absolute gates vs. the MDE floor.** Certainty curtailment establishes that an
arm's *observed* count cannot reach ⌈bar × N⌉. That is arithmetic about the run,
not an inference about the arm's true rate — so a pass-rate bar is a **decision
rule**, and absolute gates are deliberately exempt from the MDE floor that governs
comparative margins (§4). The exemption is a design choice, not an oversight, and
it carries an obligation: **size N so that `bar ± MDE` is not straddled.** A design
whose certain interval can only ever land within one MDE of the bar cannot
distinguish "misses the bar" from "sits at the bar," and curtailment's rejection is
irreversible. Compute the bar's own resolvability in the statistical plan (§5
Step 6) and record it; where N cannot be raised, state in the contract that
near-bar rejections are accepted as a known, priced cost of the gate.

Curtailment's savings are asymmetric: it fires only on arms already headed for
rejection, and the arms that consume the most wall clock in practice are the ones
near the decision boundary, which rarely trigger it. Report savings honestly, never
oversold; adopt curtailment for tail-risk and decision-quality protection — a speed
rationale for a stopping rule is chapter 00's anti-pattern
[CASE-001](examples/CASE-001_consequence-bearing-tolerances.md). Full arithmetic:
[references/STATISTICS_FORMULAS.md#curtailment](references/STATISTICS_FORMULAS.md#curtailment).

### Sequential-rule admissibility

[Sequential-rule admissibility](GLOSSARY.md#sequential-rule-admissibility): a
calibrated sequential test's (SPRT and relatives) nominal error-rate guarantee
assumes an exchangeable/independent outcome stream in execution order. When
outcomes cluster by stratum and execution proceeds in **blocked** order, the
effective number of independent looks is smaller than the nominal count and the
realized false-positive rate can inflate materially above α — the multiplier
depends on ICC and block structure and MUST be checked, not assumed away
[EXT-STOPPING-001] (contested; admissible only after a **passed** independence
check — the check's steps and its pass criterion are stated once, in
[references/STATISTICS_FORMULAS.md §7](references/STATISTICS_FORMULAS.md#sequential-admissibility),
and are not restated here; §9 carries this chapter's REJECTED-conditional).
Curtailed exact counting and certainty curtailment make no distributional
claim and are immune to this failure mode — this playbook's default. Mechanism in
full:
[references/STATISTICS_FORMULAS.md#sequential-admissibility](references/STATISTICS_FORMULAS.md#sequential-admissibility).

### pass@k vs pass^k

[pass-at-k-vs-pass-to-the-k](GLOSSARY.md#pass-at-k-vs-pass-to-the-k): pass@k (Chen
et al.; `pass@k = 1 − C(n−c, k) / C(n, k)` for *n* samples with *c* correct)
measures capability under retry. pass^k measures reliability under repetition —
under an i.i.d. per-attempt assumption at success probability *p*, `pass^k = p^k`.
*Worked example (illustrative)*: p=0.90 → pass^5 ≈ 0.59; pass^10 ≈ 0.35. A system
reliable at pass@1 can collapse at pass^k on identical tasks [EXT-AGENT-001];
report pass^k — not pass@1 alone — for any reliability claim about a stochastic
arm, on a declared subset sized to its per-call cost. The i.i.d. assumption is
exactly what a pass^k measurement should test, not presume — correlated failures
(a shared root cause) collapse pass^k faster than the formula predicts. Full
derivation: [references/STATISTICS_FORMULAS.md#pass-at-k-vs-pass-to-the-k](references/STATISTICS_FORMULAS.md#pass-at-k-vs-pass-to-the-k).

### Verdict vocabulary

The verdict is read off the **pre-registered test**, never off a post-hoc
comparison of the observed effect against the MDE (the MDE is a pre-data property
of the design; comparing it to an observed effect after the fact is post-hoc power
reasoning). The glossary definition is canonical: INCONCLUSIVE means *the design
could not resolve the question at its MDE*.

| Verdict | Means | Reported alongside |
|---|---|---|
| **CONFIRMED** | The pre-registered primary statistic crosses its threshold in the predicted direction | Secondary statistic, clustering caveat, the interval, the design's MDE |
| **REFUTED** | The primary statistic crosses its threshold against prediction, or a pre-registered absolute gate fails outright | Secondary statistic, clustering caveat, the interval, the design's MDE |
| **INCONCLUSIVE** | The primary statistic does not cross its threshold — in either direction. The default verdict, and the one every non-crossing result takes, whatever the size of the observed effect | The interval, and the design's MDE as the statement of what it could have resolved |
| **RANKED** | Output of a screening comparison (§5 Step 5) | No significance claim of any kind; whether each outcome was a deferral or a warranted elimination (§4) |

[Descriptive vocabulary](GLOSSARY.md#descriptive-vocabulary): a set of outcome
categories MAY be pre-registered *before data* to describe a result the design
could not resolve. Pre-registration fixes *who chose the words and when*; it cannot
supply resolving power the data lack, so two constraints bind:

- Pre-registered descriptive categories **MUST NOT assert equivalence or
  direction.** "Materially better/worse" is a comparative inferential claim and
  "competitive" is an equivalence claim; neither is licensed by pre-registration
  alone.
- A "competitive" / "no material difference" category is licensed **only** by a
  pre-registered equivalence margin ±d together with a TOST-style equivalence check
  (equivalently: a confidence interval falling entirely inside ±d). Absent that
  margin and that check, the verdict is **INCONCLUSIVE**, reported with its
  interval.

A CI that leaves the ±d band fails the equivalence check even when the point
estimate sits comfortably inside it — that case is INCONCLUSIVE with the interval
printed, not "competitive." Never treat a null result as evidence of equivalence.

## 9. Failure modes and anti-patterns

**[REJECTED]** (condition: always — these are generically wrong)

- **Unpriced escape hatches.** A tolerance breach clause of "record and proceed"
  with no stated consequence — including a PROCEED-WITH-DECLARED-CEILING whose
  ceiling or projected cost is written after the breach rather than pre-registered
  at freeze [CASE: CASE-001].
- **Speed rationales for stopping rules.** Curtailment's value is decision quality
  and tail-risk protection; the speed framing invites cutting exactly the guards
  that matter.
- **Promoting sub-MDE margins to decisions.** Adopting or eliminating a candidate
  on a margin the design cannot resolve — including reading a gap larger than one
  SE, but smaller than the MDE, as a difference [CASE: CASE-002], [CASE: CASE-010].
- **Silent rank-based permanent elimination at a screening rung.** Dropping the
  bottom 1 − 1/η by rank is a deferral mechanism; treating it as elimination
  without a racing confidence bound, an at-threshold margin, or a method decision
  record pricing the accepted risk relocates the elimination-rule failure upstream
  of the guards that look for it (§4) [EXT-STOPPING-003].
- **An equivalence-shaped sentence with no equivalence test.** Reporting
  "competitive" / "no material difference" from a pre-registered category alone,
  without a margin ±d and a passed TOST-style check (§8).
- **Calibrated sequential tests without an independence check.** (condition:
  outcomes cluster within execution-ordered groups, unchecked) — SPRT-family rules
  inflate their real error rate here [CASE: CASE-002], [EXT-STOPPING-001];
  assumption-free curtailed counting is the default absent a passed check.
- **Post-hoc threshold shopping disguised as an amendment.** A mid-run change
  failing any of §7's five amendment-legitimacy conditions, applied without a
  method decision record.
- **Diagnostics running outside the fail-closed record.** The exact unrecorded
  path provenance exists to forbid [CASE: CASE-011].
- **Gold labels reachable at inference time, or used to select/route/tune on a
  qualify/confirm split.** Always wrong, structurally enforced in chapter 13.
- **Curtailed arms entering paired comparisons, rankings, or screening rungs.**
  Deletes items non-randomly by stratum, which can flip a paired-test outcome — or
  a leaderboard ordering — by composition alone.
- **Stratum-blocked execution order for a run whose prefix might inform an interim
  decision.** Makes every prefix unrepresentative — the worst case for a screening
  rung, a curtailment check, or any other interim read (§5 Step 10).
- **A single small-sample pilot headline treated as a validated result.** A
  candidate or claim from a pilot alone, without qualify/confirm-split validation,
  is a hypothesis, not a finding [CASE: CASE-010].

**A materiality/noise threshold needs its own measured floor per configuration
family**, not a one-time or borrowed estimate — re-derive, don't inherit, when a
configuration changes.

## 10. Vendor recipes

| Vendor / project | Verdict | What it gives you | As-of / caveat |
|---|---|---|---|
| Paired/clustered statistics package [FOLLOW: EXT-STATS-001] | FOLLOW | SE formulas for binary scores, clustered/paired-difference SEs, the power/MDE formula this chapter's canon is built on | Stable; the largest single external contribution to this chapter |
| Productized paired McNemar method [FOLLOW: EXT-AMAZON-LLMSTATS-001] | FOLLOW | Independently published, reviewed McNemar method, usable standalone on stored eval output as a sanity check | Reference code unmaintained but usable — see [references/SOURCES.md](references/SOURCES.md) |
| Vendor eval-SDK compare/gate tooling [FOLLOW: NV-EVALSDK-001] | FOLLOW (tooling) | Productized McNemar testing, power/MDE tables, INCONCLUSIVE-on-underpowered as shipped commands | Cite for the operational implementation, not as the source of this chapter's principles |
| Racing/successive-halving screening [ADAPT: EXT-STOPPING-003] | ADAPT | Hoeffding/Bernstein racing, Hyperband, ASHA for candidate screening | Two corrections here: mandatory stratum-balanced rungs (§5, §9), and rank-based rungs defer while only a racing confidence bound (or an at-threshold margin) eliminates (§4) |
| Progressive-subset margin-of-error tables [ADAPT: NV-MODELOPTRESEARCH-001] | ADAPT | Binomial margin-of-error-by-sample-size table; explicit first-N ordering-bias warning | Directly supports §5 Step 10's round-robin requirement |
| Sequential/always-valid testing literature [REFERENCE: EXT-STOPPING-001] | REFERENCE (contested) | SPRT and confidence-sequence machinery — what §9's REJECTED-conditional is stated against | Usable only once a passed independence check licenses it |
| Clinical-trial adaptive-design consensus [ADAPT: EXT-STOPPING-002] | ADAPT | The pre-register-the-adaptation-rule pattern behind §4's first principle and §7's amendment gate | Mature, consensus; specific spending-function conventions not adopted here |
| pass@k / pass^k literature [ADAPT: EXT-AGENT-001] | ADAPT | Estimator and reliability-collapse finding behind this chapter's pass^k guidance | Not yet run against this playbook's own suites |

## 11. Worked examples

- [CASE-001](examples/CASE-001_consequence-bearing-tolerances.md) — a tolerance's
  breach clause carried no priced consequence; a measured, large calibration
  breach proceeded anyway. Lesson: name the consequence, or the tolerance is
  decoration.
- [CASE-002](examples/CASE-002_clustered-eval-effective-n.md) — clustered outcomes
  silently collapsed a suite's effective N; a headline comparison that looked
  significant was not, once computed cluster-robustly. Lesson: power grows with
  the number of clusters, not replications within them.
- [CASE-010](examples/CASE-010_pilot-optimism-collapse.md) — a small pilot's
  headline result ran optimistic and collapsed at confirmation scale; a
  pre-registered adoption rule with fluke guards caught it. Lesson: small-n pilots
  direct; they do not confirm.
- [CASE-011](examples/CASE-011_diagnostic-gate.md) — a cheap, pre-registered
  paired-probe diagnostic decided an expensive experiment's fate under a
  data-sufficiency precedence rule. Lesson: completion alone never produces GO.
- A full worked INCONCLUSIVE verdict — reported with its confidence interval and
  the design's MDE, with a pre-registered descriptive vocabulary held to the
  equivalence-margin constraint of §8 — appears in
  [examples/SYNTH-09_inconclusive-result.md](examples/SYNTH-09_inconclusive-result.md).

## 12. Outputs and artifacts

- A frozen [experiment contract](templates/EXPERIMENT_CONTRACT.md): question,
  prediction, execution-system identity per arm, splits, consequence-bearing
  calibration rules, selection/elimination rules, statistical plan, curtailment
  clause, gates, telemetry requirements, roles, and an append-only amendment log.
- A [prediction ledger](templates/PREDICTION_LEDGER.md) entry, scored
  predicted-vs-actual on completion, and updated rows in the
  [look ledger](templates/TEST_LOOK_LEDGER.md) for every look this experiment spent.
- A verdict report: primary statistic with its confidence interval, secondary
  statistic, clustering caveat, the design's MDE, and one of
  CONFIRMED / REFUTED / INCONCLUSIVE / RANKED.
- Any diagnostic/exploratory side-runs, recorded under the non-promotable
  diagnostic run kind — never off the record — and any principle or contract
  deviation as a [method decision record](templates/METHOD_DECISION_RECORD.md).

## 13. Sources

| ID | Role here |
|---|---|
| [EXT-STATS-001] | Clustered/paired SE, DEFF/N_eff, MDE machinery — the statistical canon this chapter states |
| [EXT-STOPPING-001] | Sequential/always-valid testing; the reference the REJECTED-conditional stance (§9) is stated against |
| [EXT-STOPPING-002] | DSMB/clinical-trial pre-specification — the contract-executes-not-the-investigator pattern and amendment-legitimacy gate |
| [EXT-STOPPING-003] | Racing/successive-halving screening; adopted with a mandatory stratum-balance correction |
| [EXT-AGENT-001] | pass@k estimator and pass^k reliability-collapse finding |
| [NV-EVALSDK-001] | Productized McNemar/power/INCONCLUSIVE tooling — cited for the operational implementation |
| [EXT-AMAZON-LLMSTATS-001] | Independently published, standalone-usable paired McNemar method |
| [NV-MODELOPTRESEARCH-001] | Progressive-subset margin-of-error table pattern; first-N ordering-bias warning |
| [INT-CASE-001], [INT-CASE-002], [INT-CASE-010], [INT-CASE-011], [INT-CASE-012] | Empirical case evidence backing §4, §8, §9, §11 |

**Gap dispositions in this chapter:**

- **G15 (amendment legitimacy): COVERED** — the five-condition gate, §7.
- **G16 (gold-label usage boundary): COVERED** — the operational rule, §4, with
  its structural enforcement cross-referenced to chapter 13.
- **G17 (diagnostics inside vs outside the fail-closed machinery): COVERED** — the
  non-promotable diagnostic run kind and its trade-off table, §4 and §7.
- **G18 (split-sizing honesty): COVERED** — §5 Step 2 and §6 state explicitly that
  split sizes are a power-analysis output, not a convention, and this chapter
  deliberately does not prescribe generic sizes; all statistical generality here
  is carried by [EXT-STATS-001] and the other external sources above, stated
  rather than invented.

---

> [← Previous](03_EVALUATION_FOUNDATION.md) · [Index](README.md) · [Next →](05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md)
