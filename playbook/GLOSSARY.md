# Glossary

> Part of the **Adaptive AI Systems Playbook** v0.1.0 ·
> [Index](README.md) · [Quickstart](QUICKSTART.md)

The canonical vocabulary of this playbook. Terms are defined **once, here**; chapters
link to these definitions and never redefine them.

**Precedence:** chapter 00 (principles) > chapters 01–14 > this glossary
(definitions) > references/ (derivations). This file is authoritative for what a
term *means* — if a chapter's usage of a defined term conflicts with the definition
here, the chapter has a bug. It is never authoritative for what a term *permits*: a
definition here does not create, widen, or override a permission, exception, or
threshold stated normatively in chapter 00 or a chapter. Where this file and a
normative statement appear to conflict, the normative text governs.

Thematic index:
**Measurement validity** — [execution system](#execution-system) · [frozen identity](#frozen-identity) · [reproducibility boundary](#reproducibility-boundary) · [comparability claim](#comparability-claim) · [contemporaneous paired control](#contemporaneous-paired-control) · [dual-clock telemetry](#dual-clock-telemetry) · [authoritative clock](#authoritative-clock) · [execution surface](#execution-surface)
**Evaluation instruments** — [task ontology](#task-ontology) · [canonical failure taxonomy](#canonical-failure-taxonomy) · [symptom vs root cause](#symptom-vs-root-cause) · [cause-to-action table](#cause-to-action-table) · [reachability ceiling](#reachability-ceiling) · [static integrity gates](#static-integrity-gates) · [gold labels](#gold-labels) · [ground-truth isolation](#ground-truth-isolation) · [criteria drift](#criteria-drift) · [suite release](#suite-release) · [cross-suite refusal](#cross-suite-refusal) · [canary string](#canary-string) · [leakage](#leakage) · [distractor](#distractor) · [absence case](#absence-case) · [forbidden claim](#forbidden-claim) · [frontier-saturation check](#frontier-saturation-check) · [inversion check](#inversion-check) · [regression suite vs capability suite](#regression-suite-vs-capability-suite)
**Experiment discipline** — [experiment contract](#experiment-contract) · [pre-registration](#pre-registration) · [freeze](#freeze) · [amendment legitimacy](#amendment-legitimacy) · [look](#look) · [spend semantics](#spend-semantics) · [look ledger](#look-ledger) · [one-look discipline](#one-look-discipline) · [consequence-bearing tolerance](#consequence-bearing-tolerance) · [curtailed exact counting](#curtailed-exact-counting) · [certainty curtailment](#certainty-curtailment) · [paired-comparison firewall](#paired-comparison-firewall) · [elimination rule](#elimination-rule) · [screening vs inference](#screening-vs-inference) · [prediction ledger](#prediction-ledger) · [verdict vocabulary](#verdict-vocabulary) · [descriptive vocabulary](#descriptive-vocabulary) · [smoke tier](#smoke-tier) · [diagnostic gate](#diagnostic-gate) · [diagnostic run kind](#diagnostic-run-kind) · [round-robin ordering](#round-robin-ordering)
**Statistics** — [clustering unit](#clustering-unit) · [ICC](#icc) · [design effect](#design-effect) · [effective N](#effective-n) · [MDE](#mde) · [INCONCLUSIVE](#inconclusive) · [paired design](#paired-design) · [pass-at-k vs pass-to-the-k](#pass-at-k-vs-pass-to-the-k) · [sequential-rule admissibility](#sequential-rule-admissibility)
**System design** — [intervention ladder](#intervention-ladder) · [incumbent system](#incumbent-system) · [cascade](#cascade) · [escalation](#escalation) · [rescue](#rescue) · [deterministic gate](#deterministic-gate) · [learned router](#learned-router) · [leakage audit](#leakage-audit) · [class-identity ceiling](#class-identity-ceiling) · [oracle analysis](#oracle-analysis) · [observe-only graduation](#observe-only-graduation) · [silent failure](#silent-failure) · [evidence reachability](#evidence-reachability) · [tool contract](#tool-contract) · [context policy](#context-policy)
**Operations & economics** — [operating point](#operating-point) · [performance autopsy](#performance-autopsy) · [finding vs waste](#finding-vs-waste) · [effective bandwidth](#effective-bandwidth) · [goodput](#goodput) · [demand ledger](#demand-ledger) · [purchase trigger](#purchase-trigger) · [break-even](#break-even) · [shadow deployment](#shadow-deployment) · [canary deployment](#canary-deployment) · [rollback path](#rollback-path) · [failure harvesting](#failure-harvesting) · [telemetry floor](#telemetry-floor) · [trajectory record](#trajectory-record)
**Governance & meta** — [record of record](#record-of-record) · [fail-closed](#fail-closed) · [fail-open](#fail-open) · [provenance](#provenance) · [clean-room boundary](#clean-room-boundary) · [rigor dial](#rigor-dial) · [stakes tier](#stakes-tier) · [never-skippable floor](#never-skippable-floor) · [project profile](#project-profile) · [archetype](#archetype) · [A-to-H classification](#a-to-h-classification) · [evidence-strength labels](#evidence-strength-labels) · [vendor verdicts](#vendor-verdicts) · [doctrine-not-yet-exercised](#doctrine-not-yet-exercised) · [method decision record](#method-decision-record)

---

### A-to-H classification
The taxonomy every methodological statement in this playbook carries: **A** generic
normative principle · **B** generic default/heuristic · **C** project parameter ·
**D** vendor recipe, follow · **E** vendor recipe, adapt · **F** reference ·
**G** case study/empirical lesson · **H** rejected/deprecated. Rendered in chapters
as the callout badges `[PRINCIPLE]`, `[DEFAULT]`, `[PARAMETER]`, `[FOLLOW]`,
`[ADAPT]`, `[REFERENCE]`, `[CASE]`, `[REJECTED]`.

### absence case
An evaluation item whose correct answer is that nothing is wrong or nothing is
missing. Absence cases price a system's willingness to confabulate; a corpus without
them rewards models that always find something.

### amendment legitimacy
The conditions under which changing a frozen experiment contract mid-experiment is
legitimate rather than post-hoc threshold shopping: the amendment procedure itself was
pre-registered; the amendment derives only from iterate-split evidence via formulas
fixed at freeze; it is committed before any qualification/confirmation execution; its
direction of benefit is analyzed and disclosed; and any amendment that moves in the
direction of permitting a pass carries a mandatory skeptical-reader note. See
chapter 04.

### archetype
A named project shape (e.g., API-only greenfield, local/private deployment mandate,
cost reduction of an API-heavy system) used by [QUICKSTART](QUICKSTART.md) to route a
[project profile](#project-profile) to a reading path, mandatory templates, and first
actions.

### authoritative clock
The clock declared, per metric, as the one a published number is computed from.
Required because realtime and monotonic clocks can disagree materially in virtualized
environments; every experiment contract declares the authoritative clock per metric.
See [dual-clock telemetry](#dual-clock-telemetry).

### break-even
Any pre-committed formula that converts a resource decision into measurable terms.
Two recur throughout this playbook: **routing break-even** — the minimum share of
traffic that must be served by the cheaper tier for a routing layer to pay for its
gate/judging cost — and **rent-vs-buy break-even** — the sustained utilization above
which owning hardware beats renting it. Formulas in
[references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md) and chapter 11.

### canary deployment
Serving a small, real fraction of production traffic from a new system while
comparing a small set of causally attributable metrics against the incumbent. Distinct
from [shadow deployment](#shadow-deployment) (which serves no user-visible traffic).
Chapter 10.

### canary string
A unique marker (typically a GUID plus a stated do-not-train sentence) embedded in
held-out evaluation content and any published excerpt of it, so that verbatim
reproduction of the marker by a model, or its appearance in a training corpus, is
detectable evidence of [leakage](#leakage).

### cascade
A system topology in which work is attempted by a cheaper/weaker tier first and
[escalated](#escalation) to a stronger/costlier tier when a gate decides the first
attempt is insufficient. See [deterministic gate](#deterministic-gate),
[rescue](#rescue), chapter 08.

### canonical failure taxonomy
This playbook's single generic root-cause taxonomy for AI-system underperformance:
twelve root-cause classes (RC-1 measurement/instrument defect; RC-2 infrastructure/
runtime defect; RC-3 missing/unreachable evidence; RC-4 tool/API contract defect;
RC-5 output/format enforcement gap; RC-6 task-specification gap; RC-7 verification
gap; RC-8 capacity/budget exhaustion; RC-9 routing/escalation mismatch; RC-10
learnable capability gap; RC-11 fundamental capability gap; RC-12 architecture
mismatch), each mapped to the [intervention-ladder](#intervention-ladder) rung that
addresses it. Defined normatively in chapter 03; operationalized in chapters 07
and 14.

### cause-to-action table
A closed mapping from each root cause in a [task ontology](#task-ontology) to the
sanctioned next actions for it. Making this table explicit — and, where the system is
told it, keeping the model-facing copy and the scorer's copy provably in sync — turns
"the remedy was not derived from the diagnosis" from an invisible failure mode into a
testable property. Chapter 03.

### certainty curtailment
Stopping an evaluation arm when the remaining items can no longer change the
decision: with `passes + items_remaining < ⌈bar × N⌉` the arm cannot reach the bar,
so continuing spends resources without information. Exact arithmetic, no
distributional assumptions. Carries three mandatory guards:
[spend semantics](#spend-semantics), interval-only partial reporting, and the
[paired-comparison firewall](#paired-comparison-firewall). Adopted for decision
quality and tail-risk protection — never as a speed story. Chapter 04.

### class-identity ceiling
The performance a [learned router](#learned-router) (or any learned component)
achieves by recognizing *which stratum/template an item belongs to* rather than the
signal it is supposed to learn. Computed by predicting the target from group identity
alone; a learned component that does not beat this ceiling under leave-one-group-out
validation has learned the grouping, not the task. Chapter 08; the audit is the
[leakage audit](#leakage-audit).

### clean-room boundary
The declared list of material that must never enter a system or corpus: proprietary
third-party assets, unlicensed data, secrets, and anything whose presence would
contaminate evaluation or create legal exposure. Chapter 13.

### clustering unit
The grouping within which evaluation outcomes are correlated (scenario class,
document, template, session, user). Statistics that assume independence across items
are miscalibrated when outcomes cluster; the clustering unit must be identified
before power or significance is claimed. Chapter 04.

### comparability claim
Any statement that two measured numbers can be meaningfully compared. Valid only
when both numbers come from the same [frozen identity](#frozen-identity), or the
comparison explicitly isolates one factor, and the comparison does not cross an
unmeasured [reproducibility boundary](#reproducibility-boundary). Chapter 02.

### consequence-bearing tolerance
A pre-registered tolerance that names, in advance, what happens when it is breached:
**ABORT** (halt, return to design), **RECALIBRATE** (re-derive the parameter by a
pre-registered procedure before proceeding), or **PROCEED-WITH-DECLARED-CEILING**
(continue, at a declared measurement ceiling whose projected cost is computed and
committed *in the contract, at freeze* — never authored after the breach is
observed). Evaluated by [curtailed exact counting](#curtailed-exact-counting) and
enforced [fail-closed](#fail-closed) by the runner. A tolerance without a named
consequence is an unpriced escape hatch — the anti-pattern this concept exists to
kill. Chapter 04; [CASE-001](examples/CASE-001_consequence-bearing-tolerances.md).

### context policy
The part of an [execution system](#execution-system) that governs what enters the
model's context: budget allocation, retrieval integration, evidence formatting,
truncation behavior. Chapter 08.

### contemporaneous paired control
The control design required for causal claims that would otherwise cross a measured
instability boundary: both arms run in the same session/window with everything except
the intervention held fixed, order pre-registered and counterbalanced. When a
contemporaneous control is unavailable, the causal claim is declared unavailable and
the comparison is labeled descriptive. Chapters 02 and 04.

### criteria drift
The empirically supported phenomenon that evaluation criteria cannot be fully
specified before seeing outputs — criteria and ground truth co-evolve as graders see
real behavior. Managed by versioned [suite releases](#suite-release), never by silent
in-place edits. Chapter 03.

### cross-suite refusal
Tooling-level refusal to compare results across different suite versions. Numbers
from different suite versions are different instruments; the comparison is refused by
machinery rather than discouraged by convention. Chapter 03.

### curtailed exact counting
The evaluation rule for [consequence-bearing tolerances](#consequence-bearing-tolerance):
with a tolerance of at most k violations in n, the run halts the phase at violation
k+1 and escalates to the named consequence. A count, not a hypothesis test — it makes
no error-rate claim and is therefore immune to the clustering pathologies that break
i.i.d.-calibrated sequential tests. Chapter 04.

### demand ledger
An append-only record of compute demand (e.g., GPU-hours and spend per month,
including honest NOT-RUN rows) maintained *before* any capital decision. The
instrument that distinguishes within-run busyness from sustained fleet demand.
Template: [templates/COMPUTE_DEMAND_LEDGER.md](templates/COMPUTE_DEMAND_LEDGER.md);
chapter 11.

### descriptive vocabulary
A set of outcome descriptions pre-registered in the contract *before data*, for
results the experiment's design cannot statistically resolve. Pre-registered
descriptive categories MAY NOT themselves assert equivalence or direction: a
"competitive" / "no material difference" category is licensed only by a
pre-registered equivalence margin ±d plus a TOST-style equivalence check (or a
confidence interval falling fully inside ±d) — never by a null or sub-[MDE](#mde)
result read as equivalence on pre-registration alone. Absent that margin and check,
the verdict is [INCONCLUSIVE](#inconclusive), reported with its confidence
interval. Chapter 04.

### design effect
DEFF = 1 + (m − 1) × [ICC](#icc), where m is the average cluster size: the factor by
which clustering inflates the variance of an estimate relative to independent
sampling. [Effective N](#effective-n) = N / DEFF. Chapter 04;
[references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md).

### deterministic gate
A cascade escalation gate implemented as an explicit rule over verifiable output
signals (verifier results, schema conformance, evidence citations) rather than a
learned classifier. When a task-level verifier exists, the deterministic gate is this
playbook's default: auditable, leakage-immune, and empirically capable of
near-perfect [rescue](#rescue) routing.
[CASE-007](examples/CASE-007_deterministic-cascade-gate.md); chapter 08.

### diagnostic gate
A cheap, pre-registered probe run *before* an expensive experiment, designed to
decide that experiment's fate (GO / re-scope / DROP) with decision bands fixed in
advance. Carries data-sufficiency precedence: an underpowered diagnostic returns
[INCONCLUSIVE](#inconclusive), and completion alone never produces GO. Chapter 07;
[CASE-011](examples/CASE-011_diagnostic-gate.md).

### diagnostic run kind
A run type inside the provenance machinery that is recorded in the ledger but
cryptographically non-promotable: it can inform, it cannot qualify. The mechanism
that lets diagnostics stay inside the [fail-closed](#fail-closed) record instead of
running off the books. Chapters 04 and 13.

### distractor
An answer option, action, or label that is deliberately valid for no item in the
corpus. Reaching for it is a measurable signal of name-anchoring rather than
reasoning. Chapter 03.

### doctrine-not-yet-exercised
The honesty marker this playbook attaches to any procedure it prescribes but has no
internal execution record for (and no directly transferable external validation):
`status: doctrine — not yet exercised`. Readers get the full procedure and an honest
statement of its validation status.

### dual-clock telemetry
Recording both realtime and monotonic clock stamps on every measured span, so clock
pathologies (virtualization skew, NTP steps) are detectable after the fact and every
metric can name its [authoritative clock](#authoritative-clock). Chapters 06 and 12.

### effective bandwidth
The memory bandwidth a workload actually achieves (measured tokens/s × bytes touched
per token), as opposed to the hardware's spec-sheet bandwidth. Decode-bound serving
scales with effective, not nominal, bandwidth; the ratio between them is a measured
property of the stack. Chapter 06.

### effective N
The number of statistically independent observations a clustered sample is worth:
N_eff = N / [DEFF](#design-effect). Comparisons on clustered suites can have an
effective N several times smaller than the item count — small enough to turn headline
differences into noise. Chapter 04;
[CASE-002](examples/CASE-002_clustered-eval-effective-n.md).

### elimination rule
No candidate is withdrawn from selection on a margin smaller than the pilot's own
[MDE](#mde). Below that margin the licensed moves are: both candidates proceed under
a pre-registered budget, the decision defers to the qualification split, or the
selection metric changes to one the pilot can resolve. Chapter 04.

### escalation
Passing a task from a cheaper tier to a stronger tier in a [cascade](#cascade),
under an explicit policy (gate rule, confirmation streaks, latching, timeout
behavior, [fail-open](#fail-open)/[fail-closed](#fail-closed) semantics). Chapter 08.

### evidence reachability
The designed property that every fact an evaluation item requires is actually
obtainable through the deployed tool set, starting from what the system can know at
call time. Violations create permanently unwinnable items that masquerade as model
weakness. Measured, not argued — see [reachability ceiling](#reachability-ceiling).
Chapters 03 and 08.

### evidence-strength labels
The strength annotation carried by every principle and default: `consensus`,
`strong-evidence`, `heuristic`, `contested`, `case-study`, `inference`. A recent
paper is never rendered as law; a single project's result is never rendered as
consensus.

### execution surface
The kind of place a model runs: local open-weights inference, self-hosted/rented
inference, managed API, subscription coding-agent harness, cloud agent environment.
Different surfaces have different provenance, reproducibility, and cost properties;
a methodology must say which surfaces a claim covers.

### execution system
The full identity of the thing being measured: model + artifact/quantization/adapter
+ runtime/provider + hardware/host + harness + context policy + retrieval/knowledge +
tools + workflow + generation/reasoning budget + verifier/grader + environment.
A comparison claim is about the frozen execution system unless the experiment
explicitly isolates one factor. Never collapse model/runtime/provider/harness/
hardware into one ambiguous label. Chapter 02.

### experiment contract
The frozen, pre-registered document that defines an experiment before any data:
question and the decision it drives, prediction, baseline, execution-system identity,
splits, calibration rules with [consequence-bearing tolerances](#consequence-bearing-tolerance),
selection/elimination rules, statistical plan with [MDE](#mde) and
[effective N](#effective-n), gates, telemetry, analysis plan, roles, amendment log.
Template: [templates/EXPERIMENT_CONTRACT.md](templates/EXPERIMENT_CONTRACT.md);
chapter 04.

### fail-closed
The design stance in which work that lacks its prerequisites (registration, frozen
contract, integrity gates) is *refused by machinery* rather than discouraged by
convention. The complement of [fail-open](#fail-open). Chapters 04 and 13.

### fail-open
Behavior that defaults to proceeding when a component fails (e.g., an escalation
judge that times out serves the weak tier's answer). A legitimate, explicit choice
for availability-critical paths — and a defect when it silently swallows a
consequence that was supposed to bind. Chapter 08.

### failure harvesting
Feeding observed production failures back into the lab in ladder order: first as
evaluation candidates, then as retrieval/context fixes, and only later as training
data. Chapter 12.

### finding vs waste
The decision test for a dominant cost bucket in a measured run: it is a **finding**
(an object of study) if it is task-intrinsic and moves the decision the experiment
serves; it is **waste** (overhead to eliminate) if it is harness/infrastructure
friction orthogonal to the question. Chapter 06.

### forbidden claim
An assertion class that is scored as failure regardless of other correctness because
believing it would trigger a costly or harmful real-world action (e.g., asserting
fraud from evidence that cannot show it). A harm-weighted scoring construct.
Chapter 03.

### freeze
The moment an [experiment contract](#experiment-contract), suite, or configuration
becomes immutable-by-machinery (content-hash bound, append-only amendments after).
Nothing above the amendment log changes after freeze. Chapters 04 and 13.

### frontier-saturation check
An instrument-validation probe: run the strongest available system on the suite; a
suite the strongest arm cannot approach its measured ceiling on is suspect (the
instrument, not the model, is presumptively broken). Chapter 03.

### frozen identity
An [execution system](#execution-system) pinned as one identity (hashes, versions,
config, host) for the duration of a comparison. Any change — including a provider-side
redeploy — creates a new identity and breaks [comparability](#comparability-claim)
until re-measured. Chapter 02.

### gold labels
Ground-truth answers used by scoring. The boundary rule: gold labels **score but
never choose** — they may score outcomes and fit pre-registered calibration
procedures on the iterate split, but they may never be readable by the system under
test at inference time, and never select, route, or tune anything on held-out splits.
Chapters 04 and 13.

### goodput
Throughput that meets a stated latency/quality constraint (as opposed to raw
throughput). The serving-side analog of "cost per successful task". Chapter 06.

### ground-truth isolation
The structural guarantee that evaluation answer keys are unreachable from any
model-facing surface — enforced by permission separation *and* verified by
reachability tests, not by convention. Chapter 13.

### ICC
Intraclass correlation coefficient: the share of outcome variance attributable to
cluster membership. The input to [DEFF](#design-effect) and
[effective N](#effective-n). Estimated from data (e.g., ANOVA on per-cluster
indicators), never assumed zero. Chapter 04.

### INCONCLUSIVE
A first-class experimental verdict: the design could not resolve the question at its
[MDE](#mde). Reported as-is; never rounded to "no difference" or "equivalent". An
experiment that cannot say INCONCLUSIVE will eventually say something false.
Chapter 04.

### incumbent system
An existing, already-deployed automated or AI system whose outputs are observable —
not a manual, human-performed process. [Canary](#canary-deployment) and
[shadow](#shadow-deployment) deployments compare a candidate against it, and the
[QUICKSTART](QUICKSTART.md) archetype tree asks whether one exists and is failing
its own quality bar before routing toward optimization work. A workflow that is
today performed by a human, with no automated system standing behind it, has no
incumbent system in this sense. Chapters 08 and 10.

### intervention ladder
The normative order of interventions on a measured gap: rung 0 instrument integrity,
1 infrastructure/runtime, 2 evidence/retrieval/context, 3 tool contracts & output
enforcement, 4 specification & verification (prompt/workflow/verifier), 5
generation/reasoning-budget calibration, 6 routing/escalation, 7 fine-tuning, 8
larger/different model, 9 architectural redesign. Descending a rung requires evidence
the cheaper rungs are exhausted or inapplicable; never train around defects at rungs
0–4. Short normative form in chapter 00; operational form in chapter 07.

### inversion check
An instrument-validation signal: a systematically weaker system beating a stronger
one on a stratum indicates the stratum rewards guessing or the instrument is broken —
investigate the instrument before believing the score. Chapter 03.

### leakage
Any path by which held-out evaluation content, its answers, or its distribution
reaches the system under test or its training data. Includes classical contamination,
[gold-label](#gold-labels) exposure, and structural leakage (features encoding item
identity — see [class-identity ceiling](#class-identity-ceiling)). Chapters 03, 08, 13.

### leakage audit
The validation battery any learned component must pass before its measured
performance is believed: group-identity ceiling comparison, leave-one-group-out
evaluation, feature-provenance review (what could this feature encode?), and
out-of-distribution checks. Chapter 08;
[CASE-003](examples/CASE-003_learned-router-leakage.md).

### learned router
A routing/escalation gate implemented as a trained model over task or trajectory
features. Admissible only after a passed [leakage audit](#leakage-audit) and an
[observe-only graduation](#observe-only-graduation); contrast
[deterministic gate](#deterministic-gate). Chapter 08.

### look
One read of a held-out split's outcomes for a decision or report — including offline
replays of stored outputs. Counted in the [look ledger](#look-ledger); analyses
computed within an already-counted look do not count again. Chapter 04.

### look ledger
The append-only record of every [look](#look) at a held-out split. Held-out data is a
consumable resource; the ledger is its fuel gauge, and a pre-registered exposure
threshold triggers the suite-refresh review. Template:
[templates/TEST_LOOK_LEDGER.md](templates/TEST_LOOK_LEDGER.md); chapters 03 and 04.

### MDE
Minimum detectable effect: the smallest true difference a design can detect at
stated α and power, computed *before* the experiment (and after clustering
correction). Every contract states its MDE; margins below MDE cannot support
adoption or [elimination](#elimination-rule) decisions. Chapter 04.

### method decision record
A short ADR-style document recording the adoption, rejection, or revision of a
methodology element: context, decision, evidence, consequences. Feeds the CHANGELOG.
Template: [templates/METHOD_DECISION_RECORD.md](templates/METHOD_DECISION_RECORD.md).

### never-skippable floor
The six obligations that apply at every [stakes tier](#stakes-tier): state the
decision and claim; preserve provenance sufficient to identify what produced a
result; define the evaluation/ground-truth boundary before quality claims;
predeclare consequences for decision-driving thresholds; treat held-out evidence as
consumable and record exposure; retain outcome evidence. Chapter 00.

### observe-only graduation
The staged path by which a learned or automated component earns the right to act:
leakage audit passed → observe-only shadow period with measured agreement/regret →
pre-registered promotion gate → automated action with a defined rollback and
monitoring plan. De-automation conditions are pre-registered too. Chapters 08 and 12.

### oracle analysis
Computing the upper bound a routing/selection policy could achieve with perfect
knowledge (e.g., always choosing the tier that would succeed), before building any
router. If the oracle gain is small, no router is worth its cost. Chapter 08.

### one-look discipline
The rule that qualification and confirmation splits are read once per candidate for
their decision: select on the qualification look, confirm on the confirmation look,
and never iterate against either. Chapter 04.

### operating point
The chosen position on a measured latency-throughput curve (concurrency, batch
size, budget) at which a system is declared to run. Selected from sweep data against
stated latency constraints, then pinned. Chapter 06.

### paired design
Comparing systems on the *same items* and analyzing the per-item differences. Paired
standard errors are strictly tighter whenever per-item outcomes correlate across
arms — same-item comparisons get this power for free and must claim it. Chapter 04.

### paired-comparison firewall
Guard on [certainty curtailment](#certainty-curtailment): curtailed arms never enter
paired comparisons. Curtailing deletes items non-randomly (by stratum composition),
which can flip paired test outcomes purely compositionally. Chapter 04.

### pass-at-k vs pass-to-the-k
pass@k (some of k attempts succeeds) measures capability under retry; pass^k (all of
k attempts succeed) measures reliability under repetition. Stochastic systems can
score high pass@1 and collapse at pass^k on identical tasks; reliability claims about
non-deterministic systems report pass^k on a declared subset. Chapter 04.

### performance autopsy
A standing post-run forensic procedure: reconstruct the timeline from multiple
telemetry sources, identify the critical path, attribute cost buckets, run
counterfactuals (what would N nodes / a faster device / a smaller budget have
saved), and cross-check clock validity. Template:
[templates/PERFORMANCE_AUTOPSY.md](templates/PERFORMANCE_AUTOPSY.md); chapter 06.

### pre-registration
Fixing hypotheses, procedures, thresholds, consequences, and analysis plans before
data collection, in a form that cannot be silently revised
([freeze](#freeze)). The adaptation rule may be pre-registered too — what is
forbidden is inventing rules after seeing outcomes. Chapter 04.

### prediction ledger
A running record of pre-run effect estimates (point + interval, per primary metric)
scored against actuals on completion. A handful of entries turns "is this experiment
worth running?" from taste into an empirical question about your own calibration.
Template: [templates/PREDICTION_LEDGER.md](templates/PREDICTION_LEDGER.md);
chapter 04.

### project profile
The structured intake questionnaire capturing a project's outcome, constraints,
resources, and [stakes tier](#stakes-tier) — the input the
[QUICKSTART](QUICKSTART.md) navigator routes on. Template:
[templates/PROJECT_PROFILE.md](templates/PROJECT_PROFILE.md); chapter 01.

### provenance
The evidence chain answering "what exactly produced this result?": artifact hashes,
execution-system digests, contract bindings, dataset digests, run records. Stored in
the [record of record](#record-of-record). Chapter 13.

### purchase trigger
A pre-committed condition (e.g., K consecutive months of rented spend above X, or a
committed always-on serving requirement) that must fire before capital is spent —
defined *before* wanting the hardware, fed by the [demand ledger](#demand-ledger).
Chapter 11; [CASE-005](examples/CASE-005_hardware-purchase-discipline.md).

### reachability ceiling
The measured maximum score a stratum permits given the corpus, tools, and thresholds
— demonstrated by replaying the evidence plan through the real tool broker, not
argued from the generator. A stratum whose ceiling is below the passing threshold is
unwinnable, and scores on it measure the defect, not the model. Chapter 03.

### record of record
The single authoritative, tamper-evident store of experimental truth (hash-chained,
append-only). Dashboards may mirror it; they never replace it. Chapter 13.

### regression suite vs capability suite
A regression suite asks "did anything that used to work break?" (broad, stable,
run often); a capability suite asks "can the system do X?" (targeted, versioned,
run at decisions). Conflating them produces suites too expensive to run often and
too noisy to decide with. Chapter 03.

### reproducibility boundary
The empirically measured envelope within which repeated runs agree (same session?
across restarts? across hosts? across provider redeploys? under concurrency?).
Measured by probes, then comparisons are scoped to it. Never assumed. Chapter 02;
[CASE-012](examples/CASE-012_restart-instability-paired-controls.md).

### rescue
In a [cascade](#cascade), the event where escalation succeeds on an item the lower
tier failed: the gate's value is measured by rescue rate (escalations that succeed)
against unnecessary-escalation rate (escalations that were not needed). Chapter 08.

### rigor dial
This playbook's proportionality mechanism: project stakes (captured in the
[project profile](#project-profile)) scale the mandatory artifact set through three
[stakes tiers](#stakes-tier), above an invariant
[never-skippable floor](#never-skippable-floor). Chapter 00 defines it; QUICKSTART
applies it.

### rollback path
The pre-designed, rehearsed route back from a promotion: triggers (pre-registered
thresholds with consequences), mechanics (state/version compatibility), ownership,
and verification. A rollback that has never been exercised is a hypothesis, not a
path. Chapter 10.

### round-robin ordering
Interleaving execution across strata (one item per stratum, repeat) so that any
prefix of a run is approximately stratum-balanced. Makes interim evidence
representative; stratum-blocked order makes every prefix unrepresentative and is the
worst case for any interim decision rule. Chapter 04.

### screening vs inference
Screening ranks candidates cheaply to decide who advances (racing, successive
halving, stratum-balanced rungs on the iterate split); inference makes calibrated
claims (frozen comparisons on held-out splits). Screening results never carry
significance claims, and screening never replaces the frozen comparison. Chapter 04.

### sequential-rule admissibility
The conditions under which a sequential statistical stopping rule's error guarantees
hold — chiefly independence of the outcome stream in execution order. Clustered,
stratum-ordered execution inflates the real error rate of i.i.d.-calibrated rules;
check independence first or use assumption-free counting
([curtailed exact counting](#curtailed-exact-counting),
[certainty curtailment](#certainty-curtailment)) instead. Chapter 04.

### shadow deployment
Mirroring real production traffic to a candidate system whose outputs are logged but
never served to users, for offline comparison against the incumbent. Chapter 10.

### silent failure
A failure the system presents as success: confidently wrong output, unverified
claims, passed-but-wrong verification. The most expensive failure class in
cascades, and the reason [the in-system verification gap](#canonical-failure-taxonomy)
(RC-7, rung 4) is checked explicitly rather than assumed absent — a verifier that
passes failures silently produces no signal of its own. Chapters 00 and 05.

### smoke tier
A fixed, minutes-scale, stratified mini-evaluation that runs *inside* the
[fail-closed](#fail-closed) machinery — results ledgered, cryptographically
non-promotable — for detecting harness/schema/tool-contract breakage before real
spend. It never justifies adoption or elimination decisions (its MDE is enormous by
design). Chapter 03 (smoke tier) and chapter 04
([diagnostic run kind](#diagnostic-run-kind), the ledger mechanism that makes it
non-promotable).

### spend semantics
A held-out split is spent at the *first executed item*, not the last: partial runs
reveal the sufficient statistic, so there is no "peek and re-run". The reason
[certainty curtailment](#certainty-curtailment) is admissible at all (its only
consequence is irreversible rejection of an already-spent look). Chapter 04.

### stakes tier
The three-level consequence classification of the [rigor dial](#rigor-dial):
Tier 1 exploratory · Tier 2 consequential (default) · Tier 3 high-stakes/regulated.
Rigor attaches to the *decision's* consequence, not the project's prestige: a Tier-1
project making a Tier-3 decision escalates that decision to Tier-3 artifacts.
Chapter 00.

### static integrity gates
Instrument-validation checks that run on the full corpus as executable commands
(reachability replay, gold-answer scoring, corpus determinism) — protected from
subsetting, because they are the instruments that catch instrument defects.
Chapter 03.

### suite release
A versioned, contract-governed release of an evaluation suite: ceilings measured,
gold answers gated, determinism verified, changes documented, cross-suite comparison
refused. Template:
[templates/EVAL_SUITE_RELEASE_CONTRACT.md](templates/EVAL_SUITE_RELEASE_CONTRACT.md);
chapter 03.

### symptom vs root cause
The discipline of keeping user-visible failure categories (symptoms) distinct from
diagnosed causes: the category is what the operator sees; the
[canonical failure taxonomy](#canonical-failure-taxonomy) class is what is wrong.
Systems that learn symptom→remedy lookups fail exactly on the deliberately ambiguous
symptoms. Chapter 03.

### task ontology
The closed, versioned vocabulary of a project's evaluation domain: what an item can
be about, what can have caused it, what may be recommended, and which claims are
forbidden. Changing it is a breaking change to the suite. Chapter 03.

### telemetry floor
The minimum instrumentation required *before* any long or expensive run: run
lifecycle events, per-invocation statistics (tokens, latency, finish reason),
[dual-clock](#dual-clock-telemetry) stamps, preserved server/engine logs, resource
sampling, config snapshot. Post-run forensics is impossible to retrofit. Chapter 12.

### tool contract
The full behavioral specification of a tool exposed to a model: schema, addressing,
result ordering, pagination, cohort/tenant keying, permissions, error semantics, and
byte-level transport fidelity. Tool contracts are part of the
[execution system](#execution-system) and are versioned like code. Chapter 08;
[CASE-008](examples/CASE-008_transport-serialization-defect.md).

### trajectory record
The minimum durable record of one task execution: identifiers, execution-system
identity, inputs/context, retrieval and tool calls with results, output,
verification, outcome, latency, tokens, cost, clocks, versions, mutations, human
feedback, deployment stage. Chapter 12 defines the field set.

### vendor verdicts
The four stances this playbook takes on vendor material: **FOLLOW** (mature,
follow by the book), **ADAPT** (mechanics sound, decision layer missing — substitute
stated pieces), **REFERENCE** (consult, don't depend), **DEPRECATED** (do not adopt;
recorded to prevent re-adoption). Every verdict carries an as-of date and freshness
sensitivity; see [references/SOURCES.md](references/SOURCES.md).

### verdict vocabulary
The closed set of experimental outcomes: **CONFIRMED** / **REFUTED** /
**[INCONCLUSIVE](#inconclusive)** (+ **RANKED** for screening). Reports print the
primary statistic, the secondary statistic, and the clustering caveat. Chapter 04.

---

[Index](README.md) · [Quickstart](QUICKSTART.md)
