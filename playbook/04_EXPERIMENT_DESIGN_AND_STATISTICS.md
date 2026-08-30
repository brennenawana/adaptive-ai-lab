# 04. Experiment Design and Statistics

> Part of the **Adaptive AI Systems Playbook** v0.1.1 ·
> [← Previous](03_EVALUATION_FOUNDATION.md) · [Index](README.md) · [Next →](05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md)
> **Reading time:** ~30 min. **Prerequisites:** [00](00_PRINCIPLES_AND_SCOPE.md),
> [02](02_EXECUTION_SYSTEM_MODEL.md), [03](03_EVALUATION_FOUNDATION.md).

## 1. Purpose and when to read this

Same suite, two configurations, and the new one comes out ahead by four points.
Somebody now has to say whether that is a reason to switch.

The honest answer turns on things nobody was watching while the run was going. How
many genuinely independent observations those items carried. What size of gap the
suite could ever have told apart from noise. Whether the bar the result is being
compared against was written down before the numbers came back, or after. Get those
wrong and you do not get an obviously wrong answer. You get a confident one, which
is worse, because nothing about it looks broken from the outside.

Read this chapter before designing, freezing, or running any experiment a decision
will be made from — a model or configuration comparison, a calibration pilot, a
routing or fine-tuning acceptance test. It is what turns "we ran an eval and got a
number" into a claim that survives scrutiny. Four questions, in order:

- What can this design detect, and what is it blind to?
- When may an arm stop early without breaking the claim?
- What is a mid-run change allowed to do?
- What verdict is the finished comparison actually entitled to?

This chapter does not build the instrument, and it does not pin down what is being
measured. Chapter 03 builds the instrument; chapter 02 pins the thing under test.
Both are assumed to exist by the time you are here, which leaves one question:
given a trustworthy [evaluation instrument](03_EVALUATION_FOUNDATION.md) and a
[frozen execution-system identity](GLOSSARY.md#frozen-identity), how do you design
an experiment whose answer you can act on?

The statistics stated here are the canon this playbook uses everywhere else. They
are *stated*, not derived. Full derivations, assumption boxes, and worked
calculations live in
[references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md) — this
chapter says what to use and why; that file proves it.

## 2. Inputs required

- **A trusted evaluation instrument** from chapter 03: validated categories,
  measured ceilings, isolated gold labels. Everything below assumes the instrument
  itself has already been checked.
- **A [frozen execution-system identity](GLOSSARY.md#frozen-identity) per arm**,
  plus any relevant [reproducibility-boundary](GLOSSARY.md#reproducibility-boundary)
  probe results (chapter 02 §5). A comparison is not "about the model" if the
  runtime, harness, or hardware moved underneath it while you were measuring.
- **The decision this experiment drives, stated**, together with the project's
  [stakes tier](GLOSSARY.md#stakes-tier) ([rigor dial](GLOSSARY.md#rigor-dial),
  chapter 00 §6). The tier is what fixes how much of this chapter's machinery is
  mandatory rather than merely advisable.
- **For clustered domains**: a candidate [clustering unit](GLOSSARY.md#clustering-unit)
  and an [ICC](GLOSSARY.md#icc) estimate — measured on a related suite. A cold-start
  project with no prior suite to measure on freezes a **declared prior** ICC,
  labelled as such, together with the pre-registered re-estimation procedure that
  will replace it before the qualification look (§5 Step 9, §7).

## 3. Decisions this chapter supports

- Is this experiment worth running at all, and at roughly what size? (prediction
  ledger, [MDE](GLOSSARY.md#mde))
- Can this arm stop now, and what is the report allowed to say if it does?
  (curtailment, [spend semantics](GLOSSARY.md#spend-semantics))
- Is this mid-run change a legitimate amendment, or is it post-hoc threshold
  shopping? (amendment legitimacy)
- Where does a cheap diagnostic or exploratory run live in the record? (diagnostic
  run kind)
- What did the finished comparison actually establish — CONFIRMED, REFUTED,
  INCONCLUSIVE, or a bare ranking? (verdict vocabulary)

## 4. Normative principles

**[PRINCIPLE] The contract executes; nobody improvises mid-run.** (consensus)
Write down the question, the prediction, the splits, the calibration rules, the
statistical plan, and the gates — all of it, before any data is collected. That
document is an [experiment contract](GLOSSARY.md#experiment-contract), and writing
it in advance is [pre-registration](GLOSSARY.md#pre-registration). Once it is
[frozen](GLOSSARY.md#freeze), the rule runs the experiment; the investigator's
judgment mid-run does not. Medicine settled this a long time ago: a data and safety
monitoring board executes an adaptation rule specified in advance, rather than
exercising discretion in the moment [EXT-STOPPING-002]. Note what this does *not*
forbid. The adaptation rule itself MAY be pre-registered — adapting is fine. What
is forbidden is inventing a rule after seeing outcomes.

**[PRINCIPLE] A held-out split is spent at the first executed item.** (strong-evidence)
Start a held-out run, stop it after three items, and it can feel as though you
still hold an unused split. You do not. Those three items have already shown you
their outcomes, and there is no un-seeing them — so there is no "peek and re-run."
That is [spend semantics](GLOSSARY.md#spend-semantics): a partial run already
reveals the sufficient statistic for the item it ran. Every
[look](GLOSSARY.md#look) is recorded in the [look ledger](GLOSSARY.md#look-ledger)
([templates/TEST_LOOK_LEDGER.md](templates/TEST_LOOK_LEDGER.md)) — including an
offline replay of stored outputs, which is still a look — and a pre-registered
exposure threshold triggers the suite-refresh review (chapter 03). This is also why
[certainty curtailment](GLOSSARY.md#certainty-curtailment) is admissible: its only
possible consequence is irreversibly rejecting an already-spent look, not an early
peek at a fresh one.

**[PRINCIPLE] Every tolerance names its breach consequence before data.** (strong-evidence)
A threshold detects. A control detects *and* does something. The gap between them
is one sentence, and that sentence is this principle. A
[consequence-bearing tolerance](GLOSSARY.md#consequence-bearing-tolerance) states,
in the contract, what happens on breach: **ABORT**, **RECALIBRATE**, or
**PROCEED-WITH-DECLARED-CEILING**. Breaches are evaluated by
[curtailed exact counting](GLOSSARY.md#curtailed-exact-counting) and enforced
[fail-closed](GLOSSARY.md#fail-closed) by the runner, so the check is machinery
rather than a reviewer's memory.

The PROCEED branch is the one that gets abused, so it carries a hard condition:
**the declared ceiling and the projected cost of proceeding are pre-registered in
the contract at freeze, per tolerance** — not written after the breach is observed,
by the party that wants to proceed. A price authored post-data is the unpriced
escape hatch under another name, and it returns the decision to mid-run
investigator judgment, which the first principle above forbids. So a PROCEED clause
with no pre-registered cost MUST fail contract review (§7), and no cost may be
invented later to rescue it.

Why this and not something lighter, from first principles: a tolerance whose breach
clause is silent — "record and proceed" with no priced consequence — is not a
control, because detecting a violation changes nothing about what happens next.
Corroborated by the DSMB pre-specification pattern [EXT-STOPPING-002] and by
[SCENARIO-01](examples/SCENARIO-01_consequence-bearing-tolerances.md), where exactly
this gap let a measured, large tolerance breach proceed unpriced.

**[PRINCIPLE] Screening ranks; only a frozen comparison infers.** (strong-evidence)
There are cheap ways to narrow eight candidates to two: run everyone briefly, drop
the laggards, run the survivors longer. Racing and successive halving (ASHA-style
rungs) on the iterate split do exactly that, and they are worth using
[EXT-STOPPING-003]. What they produce is an ordering, not a result. That is
[screening vs inference](GLOSSARY.md#screening-vs-inference), and the boundary is
strict: screening results MUST NOT carry significance claims and MUST NOT replace
the frozen qualify/confirm comparison. Screening feeds that comparison; it never
substitutes for it.

**Defer is not eliminate — the precedence rule.** [EXT-STOPPING-003] holds two
families of method that look alike from outside and behave differently, and they
MUST NOT be conflated.

The first cuts by *rank*. Successive halving and ASHA drop the bottom 1 − 1/η by
rank at every rung, and rank does not care how close the race was: the candidate a
hundredth of a point behind is cut exactly like the one ten points behind. Those
margins are arbitrarily small and routinely far below the rung's own MDE. So a
rank-based rung MAY only **DEFER** or **SUSPEND** a candidate — stop spending on it
now, keep it revivable at the frozen comparison, and record the deferral with its
margin.

The second cuts on a *bound*. **Permanent** elimination requires one of exactly two
warrants: a *racing* confidence bound (Hoeffding/Bernstein, computed at the
[clustering unit](GLOSSARY.md#clustering-unit), which eliminates only once the
bound separates candidates), or a margin at or above the elimination rule's
threshold, stated below. Absent one of those, a candidate that lost a rung is
deferred, not gone.

You may accept rank-based permanent elimination anyway. It is a deliberate, priced
trade-off, and pricing it means recording a
[method decision record](GLOSSARY.md#method-decision-record) that names the
noise-elimination risk you are buying.

**[PRINCIPLE] No candidate is eliminated on a margin the design cannot resolve.** (strong-evidence)
Dropping a candidate is a decision, and it needs the same standard of evidence as
choosing one. The [elimination rule](GLOSSARY.md#elimination-rule) says it plainly:
no candidate is withdrawn from selection on a margin smaller than the pilot's own
[MDE](GLOSSARY.md#mde). Below that margin exactly three moves are licensed — both
candidates proceed under a pre-registered budget, the decision defers to the
qualification split, or the selection metric changes to one the pilot can actually
resolve.

The argument is first-principles: a decision made on noise the design admits it
cannot distinguish from zero is a coin flip dressed as one. Two scope notes do real
work here. This rule binds *screening as well as selection* — a rung's rank order
is not a margin, which is why rungs defer and racing bounds eliminate (see the
precedence rule above). And it governs *comparative* margins only; an absolute
pass-rate gate is a decision rule rather than an inference and is deliberately
exempt, under the sizing obligation stated in §8.

**[PRINCIPLE] Same-item comparisons pair; clustered outcomes cluster-correct.** (strong-evidence)
Two obligations here, and they are separate.

First: if both arms ran the *same items*, analyze the per-item differences instead
of comparing two overall averages. Item difficulty then cancels rather than
contributing noise. That is a [paired design](GLOSSARY.md#paired-design), and its
standard errors are tighter than two-sample SEs — free statistical power that any
same-item design should claim, because you already paid for it by running the same
items [EXT-STATS-001].

Second, and separately: whenever outcomes correlate within a
[clustering unit](GLOSSARY.md#clustering-unit) — task class, template, document,
session — cluster-robust paired inference is the primary statistic. That means a
t-test on the per-cluster means, df = clusters − 1. McNemar exact on discordant
pairs is secondary and MUST be labeled anti-conservative under clustering
[EXT-STATS-001]: it reads as more decisive than the clustered data support.

A comparison reported without checking for clustering is wrong — not because
clustering is exotic, but because independence was never verified.

**[PRINCIPLE] Gold labels score; they never choose.** (consensus)
The answer key grades the work. It gets no vote in what runs. That is the
[gold-label](GLOSSARY.md#gold-labels) boundary, and it permits exactly two uses:
ground truth MAY score outcomes, and MAY fit pre-registered calibration procedures
on the iterate split. Everything else is closed. It MUST NOT be readable by the
system under test at inference time, and MUST NOT select, route, or tune anything
on qualify or confirm splits. Every version of "we used the labels to pick
something" converts a measurement into a fit. Enforced structurally, not by
convention — see [ground-truth isolation](GLOSSARY.md#ground-truth-isolation) and
chapter 13's permission/role-isolation mechanics.

**[PRINCIPLE] A causal claim across an instability boundary needs a paired control.** (strong-evidence)
This is chapter 02's principle, restated because it binds experiment design
directly. Run the baseline Monday and the change Wednesday, and everything that
moved in between is sitting inside your result. So: once a
[reproducibility-boundary](GLOSSARY.md#reproducibility-boundary) probe finds an
axis unstable, no comparison crossing it may claim causal attribution to one
intervention without a
[contemporaneous paired control](GLOSSARY.md#contemporaneous-paired-control) — both
arms in the same session/window, everything but the intervention fixed, order
pre-registered and counterbalanced. Without that control, the claim MUST be
declared unavailable and the comparison relabeled descriptive
[SCENARIO-12](examples/SCENARIO-12_restart-instability-paired-controls.md).

One connection saves you inventing machinery: session instability *is* outcome
correlation. Model it as §8 models any clustering unit, not as a separate problem.

**[PRINCIPLE] A diagnostic run lives inside the fail-closed record, non-promotable.** (strong-evidence)
Before committing to an expensive experiment you want a cheap probe run, to inform
a GO / RE-SCOPE / DROP decision (chapter 07's
[diagnostic gate](GLOSSARY.md#diagnostic-gate)). The temptation is to run it off to
one side, unregistered, because it is only a probe. It goes in the record instead,
under the [diagnostic run kind](GLOSSARY.md#diagnostic-run-kind): ledgered,
cryptographically non-promotable — it can inform, it cannot qualify. A relaxed,
unrecorded path is not a shortcut; it recreates exactly the defect
[provenance](GLOSSARY.md#provenance) exists to forbid (chapter 00's P10)
[SCENARIO-11](examples/SCENARIO-11_diagnostic-gate.md).

## 5. Default procedure

**Step 1 — State the question, the decision, and a prediction.** One sentence for
the question this experiment answers, and one for the decision its answer drives.
Then, before the run, write down what you expect: a point estimate and an interval
for the primary metric, in the [prediction ledger](templates/PREDICTION_LEDGER.md).
On completion, score that prediction against the actual result. A handful of
entries turns "is this experiment worth running?" from taste into an empirical
question about your own calibration.

**Step 2 — Define splits and roles.** Three roles, whatever their sizes.

- An **iterate split** you may re-run freely — screening, calibration, pilots,
  diagnostics. Consequence-bearing tolerances still apply, and re-runs are still
  ledgered.
- A **qualification split**, read once per candidate, against pre-frozen gates.
- A **confirmation split**, read once, for confirmation only.

That is [one-look discipline](GLOSSARY.md#one-look-discipline): select on the
qualification look, confirm on the confirmation look, never iterate against either.

**Do not size these splits by tradition or by copying another project's numbers.**
Derive them from a power analysis targeted at the MDE the decision needs (§8). A
round default with no derivation behind it is a placeholder, and a placeholder
nobody revisits silently becomes policy.

**Step 3 — Freeze the execution-system identity per arm.** Pin every arm per
chapter 02 §5 Step 1, before any iterate-split inference. If arms cross a measured
reproducibility boundary, design the contemporaneous paired control now (§4) — not
after seeing which way the results went.

**Step 4 — Pre-register calibration rules as consequence-bearing tolerances.**
Some parameters get calibrated on the iterate split: a generation cap, a decoding
budget, a server setting. For each one, state three things — the calibration
procedure, the tolerance, and the named consequence on breach (ABORT /
RECALIBRATE / PROCEED-WITH-DECLARED-CEILING, with the declared ceiling and its
projected cost written *here, at freeze*, never after the breach).

Evaluate by curtailed exact counting (§8): halt the phase and execute the named
consequence at violation *k*+1 of a ≤*k*-in-*n* tolerance. No hypothesis test, no
error-rate claim — a count.

Then check something the arithmetic will not tell you. Is this tolerance actually
likely to bind for this candidate class? A rule whose fallback fires for every
candidate has not calibrated anything; it has silently become the policy.

**Step 5 — If screening more than two candidates, pre-register racing/ASHA
rungs.** Rungs run on the iterate split only, and every rung MUST be
stratum-balanced — a rung built from one stratum's cases inverts real rankings
under clustering (§9). What comes out is a ranking, feeding but never replacing the
frozen qualify/confirm comparison (§4).

Pre-register which rung outcome is a **deferral** (rank-based: revivable at the
frozen comparison) and which, if any, is a **permanent elimination** (racing
confidence bound at the clustering unit, or a margin ≥ the elimination-rule
threshold) — §4's precedence rule. And filter near-duplicate configurations with a
cheap bake-off before paying full evaluation cost for each of them.

**Step 6 — Pre-register the statistical plan.** This is the step that gets skipped,
and skipping it is what produces confidently wrong results. Before any data, write
down:

- The clustering unit and its ICC — measured, or a declared prior carrying the
  re-estimation procedure that will replace it (§7).
- The design effect and effective N that ICC implies.
- The MDE at the project's α/power targets.
- What each possible outcome will be read as: CONFIRMED / REFUTED / INCONCLUSIVE /
  RANKED (§8). Fixing this before the data is what stops the result choosing its
  own interpretation.
- Where the outcome is judge- or annotator-graded, the grader reliability assumed
  in the power calculation (κ or agreement rate) and its source. A noisy grader
  inflates the N you need (§8).
- If a [descriptive vocabulary](GLOSSARY.md#descriptive-vocabulary) is licensed,
  its categories — together with any equivalence margin ±d and the equivalence test
  that a "competitive"/"no material difference" category requires (§8). No margin,
  no such category.
- The elimination-rule threshold, set from the same MDE (§4), plus a commitment to
  the three licensed moves below it.
- If the decision also turns on an absolute pass-rate bar, that bar's own
  resolvability: is `bar ± MDE` straddled? (§8)

**Step 7 — Pre-register curtailment.** State whether certainty curtailment applies
to qualify/confirm arms, what its bar is, and the three mandatory guards (§8):
spend semantics, interval-only partial reporting, and the paired-comparison
firewall. Disabling curtailment is allowed; it requires a written justification in
the contract.

**Step 8 — Pre-register the amendment procedure, if any**, against §7's amendment
legitimacy gate: what may be amended, from what evidence, under what disclosure.
Silence here is not neutral. It means no amendment is legitimate later without a
[method decision record](GLOSSARY.md#method-decision-record).

**Step 9 — Freeze.** Commit the contract, content-hash bound, **before any
qualification- or confirmation-split item executes, and before any iterate-split
evidence is used for inference.**

Both halves of that bind. Screening, calibration, and an ICC-estimation pilot on
the iterate split MAY precede the freeze, each still running under its own rules
registered before it executes (Steps 4–5). But the moment iterate-split output
feeds an inferential claim or fixes a gate value, freeze first.

Cold start with no prior ICC: freeze carrying a *declared prior* ICC plus the
pre-registered re-estimation procedure that MUST complete before the qualification
look (§7). Nothing above the amendment log changes after this point.

**Step 10 — Execute in round-robin order.** One item per stratum, then round again.
This matters for any run whose prefix might inform an interim decision — a
screening rung, a curtailment check, a calibration pilot — because interleaving
makes every prefix approximately stratum-balanced.

The alternative is stratum-*blocked* order: all of one class, then the next. That
makes every prefix unrepresentative, which is the worst case for any interim rule,
since the strata seen first and last are not a random sample of the whole (§9).

**Step 11 — Score against pre-frozen gates; apply curtailment where it fires.**
Report a curtailed arm's certain interval and unrun strata (§8) — never a partial
point estimate — and exclude it from every paired comparison, ranking, and
screening rung.

**Step 12 — Compute the verdict.** Primary: cluster-robust paired inference.
Secondary: McNemar exact, labeled anti-conservative under clustering.

Read the verdict off the pre-registered test, not off the point estimate. The
primary statistic either crosses its pre-registered threshold or it does not.
Crossing in the predicted direction is CONFIRMED; crossing against it is REFUTED.
Every non-crossing result is **INCONCLUSIVE** — however large the observed gap
looks — reported with its confidence interval *and* the design's MDE, so the reader
sees what this design could have resolved.

Never "no difference." Never "equivalent." A "competitive"/"no material difference"
reading is licensed only by a pre-registered equivalence margin and a passed
equivalence check (§8).

**Step 13 — Close the loop.** Score the prediction ledger entry against the actual
result. Append the look or looks to the look ledger, and any executed amendment to
the amendment log. Route exploratory or diagnostic side-runs to the non-promotable
diagnostic run kind (§4) — never off the record.

## 6. Project adaptation parameters

**[PARAMETER] Split sizes.** Derived from a power analysis targeted at the MDE the
decision needs (§8), not copied from another project — a Tier-1 direction-finding
pilot needs far less power than a Tier-3 adoption gate on the same metric. State
the derivation in the contract, not just the resulting number.

**[PARAMETER] α and power targets.** Default α=.05, power=.80 for a Tier-2 project;
these are the values the canonical MDE formula in §8 assumes. A Tier-3 decision
SHOULD tighten one or both and state the tightened values. A Tier-1 pilot MAY relax
power, in exchange for an explicit "screening only, not inference" label.

**[PARAMETER] Curtailment bar and tolerance *k*.** Two numbers, two different
rules.

The pass-rate `bar` in the certainty curtailment rule (§8) is the decision's actual
adoption/rejection threshold, taken from the contract's qualification/confirmation
gate — not a conventional round number. And N is sized so `bar ± MDE` is not
straddled, because curtailment's rejection is irreversible (§8).

The tolerance *k* for a consequence-bearing calibration rule comes from a source
that exists *before* the pilot it governs: a prior suite's measured violation rate,
a stated operational tolerance for the failure mode, or an explicit pre-registered
pilot run under a separate contract. It is never derived from the pilot this
tolerance governs — that is circular against the freeze point (§5 Step 9) and is
post-hoc threshold selection — and never picked to make a preferred setting pass.

**[PARAMETER] Racing/ASHA rung sizes and reduction factor η.** Calibrate to
candidate count and iterate-split size; every rung MUST be stratum-balanced
regardless (§5 Step 5, §9).

**[PARAMETER] Look-ledger refresh threshold.** The count of qualify/confirm looks
against one suite version that triggers the chapter 03 suite-refresh review. State
it in writing — a threshold decided informally after the fact is not a threshold.

**[PARAMETER] pass^k subset and *k*.** Sized to be affordable against a stochastic
arm's per-call cost, not fixed at one value across every project.

## 7. Decision gates and stopping conditions

**[DECISION GATE] Freeze gate.** The freeze point is one point, stated once:
**before any qualification- or confirmation-split item executes, and before any
iterate-split evidence is used for inference.** All of the following MUST be true
at that point. This table is the canonical checklist — the contract template and
chapter 14 restate it rather than adding to it.

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
smoke/integrity pass, declared round-robin ordering — tied to its own sections.
Those are implementation detail, not additional gate requirements.

*Tier applicability.* Rows 2, 5, and 6 restate never-skippable floor items
(chapter 00 §6: predeclared consequences, recorded held-out exposure, identifiable
provenance), so they bind at **every** tier, Tier 1 included — at Tier 1 in their
floor form, meaning exposure recorded durably somewhere, with the full look ledger
being the Tier-2 instrument. Rows 1, 3, 4, 7, and 8 are mandatory at **Tier 2+**; a
Tier-1 exploratory pilot MAY carry them in notes-grade form provided its output is
labelled "screening only, not inference" (§6) and never used for an adoption claim.
A Tier-1 project making a Tier-3 decision inherits the higher tier's rows
(chapter 00 §6's rule of proportion).

*Cold start — no prior ICC.* A greenfield project has no related suite to measure
an ICC on, and this playbook forbids both of the easy answers: assuming zero (§8)
and copying another project's number (§6). The licensed path is to freeze carrying
a **declared prior ICC**, labelled as such in the contract, plus a pre-registered
re-estimation procedure — an ICC-estimation pilot on the iterate split, or under
the non-promotable [diagnostic run kind](GLOSSARY.md#diagnostic-run-kind) (§4).
That procedure MUST complete, with its DEFF / N_eff / MDE revision committed,
**before the qualification look**.

Notice that the revision satisfies the amendment-legitimacy gate below by
construction: the procedure was pre-registered, it draws only on iterate-split
evidence, and it lands before any qualify/confirm execution. It is still logged as
an amendment, and it still carries condition 4's direction-of-benefit disclosure —
a downward ICC revision raises N_eff and lowers the stated MDE, which is exactly
the direction a skeptical reader must be shown.

**[DECISION GATE] Amendment legitimacy.** Halfway through, you notice a threshold
in the frozen contract was set wrong. Fixing it might be honest engineering, or it
might be moving the goalposts to somewhere the results can clear — and from the
inside those two feel identical. A change to a frozen contract is a legitimate
amendment, not post-hoc threshold shopping, only if **all five** hold:

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

### Clustering unit, ICC, design effect, effective N — count your groups, not your rows

Start with the mistake, because it is almost invisible from a results table.

You built a suite by listing 20 kinds of task and writing 10 questions of each
kind. That is 200 items, and 200 feels like a sample size. But whether the system
handles a given kind of task is mostly decided by what that kind of task demands —
so it tends to get all 10 of a category right, or all 10 wrong. Those 10 items are
not 10 independent tests. They are closer to one.

The grouping inside which outcomes travel together is the
[clustering unit](GLOSSARY.md#clustering-unit): task category, template, document,
or (per chapter 02) a session/host axis a reproducibility probe found unstable. How
strongly outcomes travel together inside it is the [ICC](GLOSSARY.md#icc) — the
share of outcome variance attributable to cluster membership. It is estimated from
data (one-way ANOVA on per-cluster indicators; never assumed zero, never copied
from another project). A cold-start project with nothing to estimate from freezes a
*declared prior* and re-estimates it before the qualification look, under §7's
cold-start path — a labelled prior with a committed replacement procedure, not a
borrowed number. Full estimation forms (ANOVA and paired-difference):
[references/STATISTICS_FORMULAS.md#icc](references/STATISTICS_FORMULAS.md#icc).

Those two facts convert rows into evidence. The
[design effect](GLOSSARY.md#design-effect) is the factor by which clustering
inflates your noise; divide by it and you have the
[effective N](GLOSSARY.md#effective-n) — the number to use anywhere you were about
to use the item count:

```
DEFF   = 1 + (m − 1) × ICC        # m = average cluster size
N_eff  = N / DEFF
```

*Worked example (illustrative, invented round numbers).* A suite of 200 items is
grouped into 20 task categories, 10 items each (m=10). A pilot measures ICC = 0.30
**on the per-item paired differences `d_i`** — not on either arm's marginal
outcomes, which is a different number and the wrong input for a paired analysis
(see [references/STATISTICS_FORMULAS.md §2](references/STATISTICS_FORMULAS.md#icc)).
So `DEFF = 1 + (10−1)×0.30 = 3.70` and `N_eff = 200 / 3.70 ≈ 54`. The suite carries
the statistical weight of about 54 independent pairs, not 200.

Nothing about the measured scores changed. What changed is what those scores are
allowed to support.

**To grow N_eff**, the two obvious moves are not equivalent, and the gap is larger
than it looks. The cluster count `k` enters linearly and without bound.
Items-per-cluster `m` enters with diminishing returns and saturates at `k/ICC` —
here 20/0.30 ≈ 67, however many items those 20 categories are made to hold.

Compare the two as increments from where this suite already stands, at N_eff ≈ 54:

- **More items in the same 20 categories:** at most **+13**, no matter how many you
  buy. You are already 80% of the way to that ceiling.
- **50 new categories of 10 items:** N_eff ≈ 500/3.70 ≈ 135, so about **+135**.

Ten times the return, for the same 500 items. Compute both before buying anything. Full derivation:
[references/STATISTICS_FORMULAS.md#design-effect](references/STATISTICS_FORMULAS.md#design-effect).

### Minimum detectable effect (MDE) — the smallest gap this design can see

Every design has a floor: a true difference so small the design cannot reliably
tell it from zero. Knowing that floor *before* you run is what tells you whether
the experiment is worth running at all. If it works out to 30 points, an argument
about a 5-point gap is not one this design can settle, and you have saved yourself
the run.

That floor is the [MDE](GLOSSARY.md#mde). It is computed before the experiment, at
stated α and power, and after clustering correction — in that order, because the
clustering correction is what makes the number honest. For a paired binary
comparison, an approximate closed form (McNemar-based; full derivation, exact and
asymptotic forms:
[references/STATISTICS_FORMULAS.md#mde](references/STATISTICS_FORMULAS.md#mde)):

```
MDE ≈ (z_α/2 + z_power) × √(pd / N_eff)
```

where `pd` is the expected **discordance rate** (share of item-pairs where the two
arms disagree at all). Items both arms pass, or both fail, say nothing about which
arm is better, so they do not enter.

**The MDE ≤ pd constraint**: a paired difference in success rate can never exceed
the discordance rate by construction (|Δ| ≤ pd — only discordant pairs can
contribute to a paired difference), so a design whose stated MDE exceeds its
plausible discordance cannot detect *any* effect this comparison could produce.
That is an underpowering signal, not necessarily an arithmetic slip: it falls out
of a correctly evaluated formula whenever `N_eff < 7.84 / pd` at α=.05 / power=.80
(7.84 = (1.96+0.84)²). Recheck the arithmetic first, then add clusters or relax the
power target — and either way, do not read MDE > pd as evidence about the world.

*Worked example (illustrative, continuing above).* At α=.05, power=.80
(`z_α/2≈1.96`, `z_power≈0.84`), N_eff≈54, expected discordance `pd=0.20`:
`MDE ≈ (1.96+0.84) × √(0.20/54) ≈ 0.17` — this design resolves a ~17-point paired
difference and no smaller one. Since 0.17 ≤ 0.20 the design is just barely coherent
at this discordance rate (equivalently, N_eff ≈ 54 clears the 7.84/0.20 ≈ 39
threshold). A design on the wrong side of that needs more N_eff — prefer adding
independent clusters, which grow N_eff without bound; adding items inside existing
clusters still helps while ICC < 1, with returns that flatten once m approaches
1/ICC and a ceiling at N_eff = k/ICC however many items each cluster holds — or a
relaxed power target, before it is worth running.

**Assumption — the per-item outcome is observed without error.** Every MDE and
power form here, and in the formulary's §1–§5, treats the recorded score as the
truth. Often it is not. A noisy grader — an LLM judge, or annotators at imperfect
agreement — attenuates the observed effect toward zero and inflates the N needed to
detect a real one. So a judge-graded design sized straight from these formulas is
systematically underpowered on exactly the dimension chapter 03 §5.7 flags as
highest-risk; and where the noise is asymmetric between arms, it can bias the
direction as well. See the measurement-error note in
[references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md), and state
the grader reliability used in the power calculation (κ or agreement rate) and its
source in the contract (§5 Step 6).

### Paired-difference standard error — resolution you already paid for

Run both arms on the same items and you have bought something you may not be
claiming. [Paired design](GLOSSARY.md#paired-design): paired SE is strictly smaller
than the naive two-sample SE whenever per-item outcomes correlate positively across
arms — true almost always for same-item designs, since items easy for one arm tend
to be easy for the other. *Worked example (illustrative).* Two-sample: p₁=0.70,
p₂=0.60, n=100 each → `SE ≈ √(0.70×0.30/100 + 0.60×0.40/100) ≈ 0.067`. Paired, same
100 items, discordance pd=0.25 → `SE ≈ √(0.25/100) = 0.050`.

Now the part that gets misused. An SE is not a resolvable effect: **"resolves" is
reserved for the MDE**, which at α=.05 / power=.80 is ≈ 2.80 × SE. So this pair of
designs resolves ~14 points paired (2.80 × 0.050 = 0.140) versus ~18.8 points
two-sample (2.80 × 0.067 = 0.188) — a ~25% tighter design for free, and neither
resolves the 10-point observed gap in this example, which is **INCONCLUSIVE** at
this design. Reading the 10-point gap as a difference because it exceeds one SE is
precisely the sub-MDE promotion §9 rejects and chapter 00's tripwire #6 fires on.
Full derivation:
[references/STATISTICS_FORMULAS.md#paired-difference-se](references/STATISTICS_FORMULAS.md#paired-difference-se).

### Curtailment arithmetic — stopping when the outcome is already decided

**Consequence-bearing tolerances** ([curtailed exact counting](GLOSSARY.md#curtailed-exact-counting)):
with a tolerance of at most *k* violations in *n*, halt the phase at violation
*k*+1 and execute the named consequence. That is the whole procedure. Exact
arithmetic; no distributional assumption, no error-rate claim. *Worked example*:
tolerance ≤3 violations of 40 iterate-split items → the phase halts and escalates
at the 4th violation, wherever in the sequence it falls.

**[Certainty curtailment](GLOSSARY.md#certainty-curtailment)** (qualify/confirm
arms) answers a different question — can this arm still reach its bar? Halt it when
`passes + items_remaining < ⌈bar × N⌉`. *Worked example*: bar=0.60, N=50
(`⌈0.60×50⌉=30`); after 35 items, 8 passes, 15 remaining → `8+15=23 < 30` →
curtail — this arm cannot reach the bar even if every remaining item passes, so
every further item spends money to learn nothing. Three mandatory guards, all in
force whenever curtailment is enabled:

1. **Spend semantics** — curtailment's only admissible consequence is irreversible
   rejection of an already-spent arm, never an early peek. Keeping it that way is
   mechanical: the curtailment statistic is computed by the runner and exposed only
   as **HALT / CONTINUE**. Interim pass counts on a qualify/confirm arm are not
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
comparative margins (§4).

The exemption is a design choice, not an oversight, and it carries an obligation:
**size N so that `bar ± MDE` is not straddled.** A design whose certain interval
can only ever land within one MDE of the bar cannot distinguish "misses the bar"
from "sits at the bar," and curtailment's rejection is irreversible. Compute the
bar's own resolvability in the statistical plan (§5 Step 6) and record it; where N
cannot be raised, state in the contract that near-bar rejections are accepted as a
known, priced cost of the gate.

One thing to be honest about. Curtailment's savings are asymmetric: it fires only
on arms already headed for rejection, and the arms that consume the most wall clock
in practice are the ones near the decision boundary, which rarely trigger it.
Report savings honestly, never oversold; adopt curtailment for tail-risk and
decision-quality protection — a speed rationale for a stopping rule is chapter 00's
anti-pattern
[SCENARIO-01](examples/SCENARIO-01_consequence-bearing-tolerances.md). Full
arithmetic:
[references/STATISTICS_FORMULAS.md#curtailment](references/STATISTICS_FORMULAS.md#curtailment).

### Sequential-rule admissibility — when the early-stopping guarantee is not yours

Rules that let you stop an experiment early come with an error-rate guarantee, and
that guarantee has fine print. [Sequential-rule
admissibility](GLOSSARY.md#sequential-rule-admissibility): a calibrated sequential
test's (SPRT and relatives) nominal error-rate guarantee assumes an
exchangeable/independent outcome stream in execution order. Evaluation runs
frequently are not. When outcomes cluster by stratum and execution proceeds in
**blocked** order, the effective number of independent looks is smaller than the
nominal count and the realized false-positive rate can inflate materially above α —
the multiplier depends on ICC and block structure and MUST be checked, not assumed
away [EXT-STOPPING-001].

That source is contested here: the sequential rules it describes are admissible
only after a **passed** independence check. The check's steps and its pass
criterion are stated once, in
[references/STATISTICS_FORMULAS.md §7](references/STATISTICS_FORMULAS.md#sequential-admissibility),
and are not restated here; §9 carries this chapter's REJECTED-conditional.

Curtailed exact counting and certainty curtailment make no distributional claim at
all, so they are immune to this failure mode — which is why they are this
playbook's default. Mechanism in full:
[references/STATISTICS_FORMULAS.md#sequential-admissibility](references/STATISTICS_FORMULAS.md#sequential-admissibility).

### pass@k vs pass^k — capability under retry, reliability under repetition

Two questions that sound alike and are not.
[pass-at-k-vs-pass-to-the-k](GLOSSARY.md#pass-at-k-vs-pass-to-the-k): "can it do
this if I let it try k times?" is pass@k (Chen et al.;
`pass@k = 1 − C(n−c, k) / C(n, k)` for *n* samples with *c* correct), and it
measures capability under retry. "Will it do this k times running?" is pass^k, and
it measures reliability under repetition — under an i.i.d. per-attempt assumption
at success probability *p*, `pass^k = p^k`.

The second falls off faster than intuition expects. *Worked example
(illustrative)*: p=0.90 → pass^5 ≈ 0.59; pass^10 ≈ 0.35. A system reliable at
pass@1 can collapse at pass^k on identical tasks [EXT-AGENT-001]; report pass^k —
not pass@1 alone — for any reliability claim about a stochastic arm, on a declared
subset sized to its per-call cost. And treat the i.i.d. assumption as the thing a
pass^k measurement should test, not presume: correlated failures (a shared root
cause) collapse pass^k faster than the formula predicts. Full derivation:
[references/STATISTICS_FORMULAS.md#pass-at-k-vs-pass-to-the-k](references/STATISTICS_FORMULAS.md#pass-at-k-vs-pass-to-the-k).

### Verdict vocabulary — and why INCONCLUSIVE is a result

A finished comparison ends in one of four ways, and "it looked promising" is not
among them.

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

INCONCLUSIVE is the row worth dwelling on, because teams read it as a failed
experiment and it is not one. It is a finding about the design: this test could not
tell the difference, and here is the size of difference it could have told. You can
act on that — buy more clusters, change the metric, leave the question open and
decide on something the suite *can* measure. What you may not do is round it toward
comfort. INCONCLUSIVE is not evidence that the arms are alike, and an experiment
with no way to say "we could not tell" will eventually say something false instead.

[Descriptive vocabulary](GLOSSARY.md#descriptive-vocabulary): a set of outcome
categories MAY be pre-registered *before data* to describe a result the design
could not resolve. Be exact about what pre-registration buys. It fixes *who chose
the words and when*; it cannot supply resolving power the data lack. So two
constraints bind:

- Pre-registered descriptive categories **MUST NOT assert equivalence or
  direction.** "Materially better/worse" is a comparative inferential claim and
  "competitive" is an equivalence claim; neither is licensed by pre-registration
  alone.
- A "competitive" / "no material difference" category is licensed **only** by a
  pre-registered equivalence margin ±d together with a TOST-style equivalence check
  (equivalently: a confidence interval falling entirely inside ±d). Absent that
  margin and that check, the verdict is **INCONCLUSIVE**, reported with its
  interval.

One case catches people out. A CI that leaves the ±d band fails the equivalence
check even when the point estimate sits comfortably inside it — that case is
INCONCLUSIVE with the interval printed, not "competitive." Never treat a null
result as evidence of equivalence.

## 9. Failure modes and anti-patterns

**[REJECTED]** (condition: always — these are generically wrong)

- **Unpriced escape hatches.** A tolerance breach clause of "record and proceed"
  with no stated consequence — including a PROCEED-WITH-DECLARED-CEILING whose
  ceiling or projected cost is written after the breach rather than pre-registered
  at freeze [SCENARIO: SCENARIO-01].
- **Speed rationales for stopping rules.** Curtailment's value is decision quality
  and tail-risk protection; the speed framing invites cutting exactly the guards
  that matter.
- **Promoting sub-MDE margins to decisions.** Adopting or eliminating a candidate
  on a margin the design cannot resolve — including reading a gap larger than one
  SE, but smaller than the MDE, as a difference [SCENARIO: SCENARIO-02], [SCENARIO: SCENARIO-10].
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
  inflate their real error rate here [SCENARIO: SCENARIO-02], [EXT-STOPPING-001];
  assumption-free curtailed counting is the default absent a passed check.
- **Post-hoc threshold shopping disguised as an amendment.** A mid-run change
  failing any of §7's five amendment-legitimacy conditions, applied without a
  method decision record.
- **Diagnostics running outside the fail-closed record.** The exact unrecorded
  path provenance exists to forbid [SCENARIO: SCENARIO-11].
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
  is a hypothesis, not a finding [SCENARIO: SCENARIO-10].

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

Invented scenarios, each built to make one of this chapter's failures visible.

- [SCENARIO-01](examples/SCENARIO-01_consequence-bearing-tolerances.md) — a tolerance's
  breach clause carried no priced consequence; a measured, large calibration
  breach proceeded anyway. Lesson: name the consequence, or the tolerance is
  decoration.
- [SCENARIO-02](examples/SCENARIO-02_clustered-eval-effective-n.md) — clustered outcomes
  silently collapsed a suite's effective N; a headline comparison that looked
  significant was not, once computed cluster-robustly. Lesson: under material
  clustering, adding independent clusters buys power without bound, while
  replications inside existing clusters saturate at N_eff = k/ICC.
- [SCENARIO-10](examples/SCENARIO-10_pilot-optimism-collapse.md) — a small pilot's
  headline result ran optimistic and collapsed at confirmation scale; a
  pre-registered adoption rule with fluke guards caught it. Lesson: small-n pilots
  direct; they do not confirm.
- [SCENARIO-11](examples/SCENARIO-11_diagnostic-gate.md) — a cheap, pre-registered
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
