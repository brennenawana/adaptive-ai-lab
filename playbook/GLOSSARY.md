# Glossary

> Part of the **Adaptive AI Systems Playbook** v0.1.1 ·
> [Index](README.md) · [Quickstart](QUICKSTART.md)

Every term the playbook relies on is defined **once, here**. Chapters link to these
definitions and never redefine them, so you can read a chapter straight through and
come back here for whatever did not land.

**Precedence:** chapter 00 (principles) > chapters 01–14 > this glossary
(definitions) > references/ (derivations). That ordering answers two different
questions differently. On what a term *means*, this file wins: if a chapter's usage of
a defined term conflicts with the definition here, the chapter has a bug. On what a
term *permits*, this file never wins — a definition here does not create, widen, or
override a permission, exception, or threshold stated normatively in chapter 00 or a
chapter. Where this file and a normative statement appear to conflict, the normative
text governs.

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
Not every statement in this playbook asks the same thing of you. Some are rules. Some
are starting points you are expected to retune. Some are only pointers to someone
else's work. So every methodological statement carries one of eight letters saying
which kind it is: **A** generic normative principle · **B** generic default/heuristic ·
**C** project parameter · **D** vendor recipe, follow · **E** vendor recipe, adapt ·
**F** reference · **G** case study/empirical lesson · **H** rejected/deprecated.
Chapters render the letter as a callout badge — `[PRINCIPLE]`, `[DEFAULT]`,
`[PARAMETER]`, `[FOLLOW]`, `[ADAPT]`, `[REFERENCE]`, `[CASE]`, `[REJECTED]` — so you
can tell a requirement from a suggestion without reading the surrounding argument.

### absence case
A test item whose right answer is *nothing*. Nothing is wrong, nothing is missing,
no action is needed. Absence cases are how you put a price on a system's willingness to
invent findings. If every item in the corpus has something to find, a model that always
finds something scores perfectly, and you will not discover that habit until it is
running against real inputs.

### amendment legitimacy
Halfway through an experiment you realize a threshold in the frozen contract was set
wrong. Changing it might be honest engineering, or it might be moving the goalposts to
somewhere the results can clear. Amendment legitimacy is the set of conditions that
tells the two apart, and all of them must hold: the amendment procedure itself was
pre-registered; the amendment derives only from iterate-split evidence via formulas
fixed at freeze; it is committed before any qualification/confirmation execution; its
direction of benefit is analyzed and disclosed; and any amendment that moves in the
direction of permitting a pass carries a mandatory skeptical-reader note. See
chapter 04.

### archetype
Most projects rhyme with one of a handful of familiar shapes, and a named shape is an
archetype — API-only greenfield, local/private deployment mandate, cost reduction of an
API-heavy system, and so on. [QUICKSTART](QUICKSTART.md) matches your
[project profile](#project-profile) to one, then routes you to a reading path,
mandatory templates, and first actions. The point is that you do not have to choose
where to start from a table of contents.

### authoritative clock
A machine has more than one clock, and they do not always agree. So when you publish a
timing number, you name the clock it was computed from: that named clock is the
authoritative clock for that metric. This is not pedantry — realtime and monotonic
clocks can disagree materially in virtualized environments, and the same span can yield
two different durations depending on which one you asked. Every experiment contract
declares the authoritative clock per metric. See
[dual-clock telemetry](#dual-clock-telemetry).

### break-even
The point at which a spend starts paying for itself — any pre-committed formula that
converts a resource decision into measurable terms. Committing to the formula first is
the whole mechanism; it is what stops the threshold being reverse-engineered from the
answer you already wanted. Two recur throughout this playbook: **routing break-even** —
the minimum share of traffic that must be served by the cheaper tier for a routing
layer to pay for its gate/judging cost — and **rent-vs-buy break-even** — the sustained
utilization above which owning hardware beats renting it. Formulas in
[references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md) and chapter 11.

### canary deployment
Send a small, real slice of production traffic to the new system, leave the rest on the
old one, and compare a small set of causally attributable metrics between them. Real
users are affected, which is both the point — some failures only surface when someone
is depending on the answer — and the reason the fraction is kept small. Distinct from
[shadow deployment](#shadow-deployment) (which serves no user-visible traffic).
Chapter 10.

### canary string
A tripwire for finding out whether your test data escaped. You embed a unique marker —
typically a GUID plus a stated do-not-train sentence — in held-out evaluation content
and in any published excerpt of it. The marker means nothing on its own, so there is
only one way a model could reproduce it verbatim, and only one way it could turn up in
a training corpus. Either sighting is detectable evidence of [leakage](#leakage).

### cascade
Try the cheap model first, and hand the hard ones up to the expensive one. That is a
cascade: work is attempted by a cheaper/weaker tier first and
[escalated](#escalation) to a stronger/costlier tier when a gate decides the first
attempt is insufficient. Everything that determines whether a cascade is worth having
lives in that gate — how it decides, and what it costs to run. See
[deterministic gate](#deterministic-gate), [rescue](#rescue), chapter 08.

### canonical failure taxonomy
"The system is bad at this" is not a diagnosis anyone can act on. This playbook's
single generic root-cause taxonomy for AI-system underperformance forces every measured
gap to land on something specific, through twelve root-cause classes (RC-1
measurement/instrument defect; RC-2 infrastructure/runtime defect; RC-3
missing/unreachable evidence; RC-4 tool/API contract defect; RC-5 output/format
enforcement gap; RC-6 task-specification gap; RC-7 verification gap; RC-8
capacity/budget exhaustion; RC-9 routing/escalation mismatch; RC-10 learnable
capability gap; RC-11 fundamental capability gap; RC-12 architecture mismatch). Each is
mapped to the [intervention-ladder](#intervention-ladder) rung that addresses it, so
naming the cause also names the fix. Defined normatively in chapter 03;
operationalized in chapters 07 and 14.

### cause-to-action table
A table with one row per root cause in your [task ontology](#task-ontology), listing
the next actions sanctioned for it — a closed mapping, so anything not listed is not
licensed. Writing it down makes a common failure visible: a system that diagnoses one
thing and then recommends something unrelated to it. Without the table nobody can
demonstrate that the remedy was not derived from the diagnosis; with it, that becomes a
testable property. Where the system is told the table, the model-facing copy and the
scorer's copy are kept provably in sync. Chapter 03.

### certainty curtailment
An arm needs 80 passes out of 120 items to clear its bar. It has already failed 45,
with 30 left to run. It cannot get there, and every remaining item costs money to learn
nothing. Certainty curtailment is stopping the arm at that point. The trigger is
arithmetic rather than statistical: with `passes + items_remaining < ⌈bar × N⌉` the arm
cannot reach the bar, so continuing spends resources without information. Exact
arithmetic, no distributional assumptions. It carries three mandatory guards:
[spend semantics](#spend-semantics), interval-only partial reporting, and the
[paired-comparison firewall](#paired-comparison-firewall). Adopted for decision
quality and tail-risk protection — never as a speed story. Chapter 04.

### class-identity ceiling
Your router looks accurate, but it may have learned nothing more useful than "items
from template 7 are hard". The class-identity ceiling measures how much accuracy that
shortcut alone buys: the performance a [learned router](#learned-router) (or any
learned component) achieves by recognizing *which stratum/template an item belongs to*
rather than the signal it is supposed to learn. You compute it by predicting the target
from group identity alone. A learned component that does not beat this ceiling under
leave-one-group-out validation has learned the grouping, not the task. Chapter 08; the
audit is the [leakage audit](#leakage-audit).

### clean-room boundary
A written list of what may never enter a system or corpus, decided in advance rather
than adjudicated case by case once something is already in: proprietary third-party
assets, unlicensed data, secrets, and anything whose presence would contaminate
evaluation or create legal exposure. Most of its value comes from existing before
anyone is under deadline pressure to make an exception. Chapter 13.

### clustering unit
Write eight questions from the same source document and the system tends to get all
eight right or all eight wrong. They are not eight independent tests; they are closer
to one. The grouping inside which outcomes travel together is the clustering unit —
scenario class, document, template, session, user. Statistics that assume independence
across items are miscalibrated when outcomes cluster, so the clustering unit must be
identified before power or significance is claimed. Chapter 04.

### comparability claim
Setting two numbers side by side is itself a claim: that they were produced under
conditions similar enough for the difference between them to mean something. Naming the
claim is what makes it checkable. It is valid only when both numbers come from the same
[frozen identity](#frozen-identity), or the comparison explicitly isolates one factor,
and the comparison does not cross an unmeasured
[reproducibility boundary](#reproducibility-boundary). Chapter 02.

### consequence-bearing tolerance
A tolerance says how much deviation you will accept. A consequence-bearing tolerance
also says, in advance, what happens the moment that limit is breached — because a limit
with no stated consequence gets renegotiated the first time it bites. The consequence
is named at freeze and is one of three: **ABORT** (halt, return to design),
**RECALIBRATE** (re-derive the parameter by a pre-registered procedure before
proceeding), or **PROCEED-WITH-DECLARED-CEILING** (continue, at a declared measurement
ceiling whose projected cost is computed and committed *in the contract, at freeze* —
never authored after the breach is observed). Breaches are evaluated by
[curtailed exact counting](#curtailed-exact-counting) and enforced
[fail-closed](#fail-closed) by the runner. A tolerance without a named consequence is
an unpriced escape hatch — the anti-pattern this concept exists to kill. Chapter 04;
[SCENARIO-01](examples/SCENARIO-01_consequence-bearing-tolerances.md).

### context policy
The rules that decide what actually gets put in front of the model on a given call:
how the budget is allocated, how retrieved material is integrated, how evidence is
formatted, and what gets truncated when it does not fit. Two systems running the same
model over the same documents can behave very differently because these rules differ,
which is why the context policy counts as part of the
[execution system](#execution-system) rather than as a detail of the prompt.
Chapter 08.

### contemporaneous paired control
Run the baseline on Monday and the change on Wednesday, and everything that moved in
between — a provider redeploy, a warmer cache, a different host — is inside your
result. A contemporaneous paired control closes that gap: both arms run in the same
session/window with everything except the intervention held fixed, order pre-registered
and counterbalanced. It is the control design required for causal claims that would
otherwise cross a measured instability boundary. When a contemporaneous control is
unavailable, the causal claim is declared unavailable and the comparison is labeled
descriptive. Chapters 02 and 04.

### criteria drift
You cannot fully specify evaluation criteria before seeing outputs. Real behavior keeps
surfacing cases the rubric never anticipated, so criteria and ground truth co-evolve as
graders see real behavior. This is an empirically supported phenomenon, not a symptom
of a lazy rubric, so the fix is not to try harder up front. It is to let the criteria
change through versioned [suite releases](#suite-release), never by silent in-place
edits — so you always know which version of the instrument produced a given score.
Chapter 03.

### cross-suite refusal
Sooner or later someone puts last quarter's score next to this quarter's, taken on a
suite that has changed in between. Numbers from different suite versions are different
instruments, so the tooling declines to make that comparison at all: refused by
machinery rather than discouraged by convention, because a convention is what loses to
a deadline. Chapter 03.

### curtailed exact counting
How a [consequence-bearing tolerance](#consequence-bearing-tolerance) is actually
enforced while a run is in flight. You declared a tolerance of at most k violations in
n; the runner counts them, and when violation k+1 lands it halts the phase and
escalates to the named consequence. That is the whole procedure — a count, not a
hypothesis test. Because it makes no error-rate claim, it is immune to the clustering
pathologies that break i.i.d.-calibrated sequential tests. Chapter 04.

### demand ledger
A month-by-month record of the compute you actually used and paid for — GPU-hours and
spend per month, including honest NOT-RUN rows for the months you needed nothing.
Append-only, and maintained *before* any capital decision rather than assembled to
justify one already made. Its job is to separate two things that feel identical from
inside the week they happen in: a stretch where the machine was pinned, and sustained
fleet demand. Only the second one buys hardware. Template:
[templates/COMPUTE_DEMAND_LEDGER.md](templates/COMPUTE_DEMAND_LEDGER.md);
chapter 11.

### descriptive vocabulary
Some results your design simply cannot resolve, and you will still want words for them.
Descriptive vocabulary is that set of outcome descriptions, pre-registered in the
contract *before data*. The constraint on it is strict, because this is exactly where
unearned equivalence claims get in: pre-registered descriptive categories MAY NOT
themselves assert equivalence or direction. A "competitive" / "no material difference"
category is licensed only by a pre-registered equivalence margin ±d plus a TOST-style
equivalence check (or a confidence interval falling fully inside ±d) — never by a null
or sub-[MDE](#mde) result read as equivalence on pre-registration alone. Absent that
margin and check, the verdict is [INCONCLUSIVE](#inconclusive), reported with its
confidence interval. Chapter 04.

### design effect
The number that says what clustering is costing you. When items come in groups, an
estimate is noisier than the same count of independent draws would be, and the design
effect is the factor by which that noise is inflated: DEFF = 1 + (m − 1) × [ICC](#icc),
where m is the average cluster size. Divide by it to get what your sample is really
worth — [effective N](#effective-n) = N / DEFF. A DEFF of 1 means clustering costs you
nothing; a DEFF near 4 means 120 items carry roughly the evidence of 30. Chapter 04;
[references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md).

### deterministic gate
The rule deciding whether to escalate, written as explicit conditions over things you
can verify — verifier results, schema conformance, evidence citations — instead of as a
trained classifier. When a task-level verifier exists, this is the playbook's default,
for three reasons: you can read the rule and audit it, it is leakage-immune because
there is nothing for it to have memorized, and it is empirically capable of
near-perfect [rescue](#rescue) routing.
[SCENARIO-07](examples/SCENARIO-07_deterministic-cascade-gate.md); chapter 08.

### diagnostic gate
A cheap, pre-registered probe run *before* an expensive experiment, whose only job is
to decide that experiment's fate: GO, re-scope, or DROP. The decision bands are fixed
in advance, so the probe cannot be read charitably once its numbers are in. It also
carries data-sufficiency precedence: an underpowered diagnostic returns
[INCONCLUSIVE](#inconclusive), and completion alone never produces GO — finishing the
probe is not the same as passing it. Chapter 07;
[SCENARIO-11](examples/SCENARIO-11_diagnostic-gate.md).

### diagnostic run kind
Exploratory runs need a legitimate place to live. If the only runs on the books are the
ones that count, scratch work migrates outside the system and the record stops matching
reality. A diagnostic run kind is a run type inside the provenance machinery that is
recorded in the ledger but cryptographically non-promotable: it can inform, it cannot
qualify. That is the mechanism that lets diagnostics stay inside the
[fail-closed](#fail-closed) record instead of running off the books. Chapters 04
and 13.

### distractor
A plausible-looking option that is correct for nothing — an answer option, action, or
label deliberately valid for no item in the corpus. Anything that reaches for it is not
reasoning from the evidence; it is matching a name that sounded relevant. Planting one
turns that behavior into a measurable signal of name-anchoring rather than a suspicion.
Chapter 03.

### doctrine-not-yet-exercised
Some procedures here have been run in anger and some have not, and it would be easy to
let the two read alike. So anything this playbook prescribes without an internal
execution record behind it — and without directly transferable external validation —
carries the marker `status: doctrine — not yet exercised`. Readers get the full
procedure and an honest statement of its validation status, which is what lets you
decide how much weight to put on it.

### dual-clock telemetry
Stamp every measured span with both clocks, realtime and monotonic, instead of choosing
one. It costs almost nothing at write time and buys two things that cannot be
recovered later: clock pathologies such as virtualization skew and NTP steps become
detectable after the fact, because the two stamps disagree, and every metric can name
its [authoritative clock](#authoritative-clock). Chapters 06 and 12.

### effective bandwidth
The memory bandwidth your workload actually achieves, not the figure on the spec sheet.
You compute it from what happened: measured tokens/s × bytes touched per token. It
matters because generating tokens one at a time is limited by memory traffic, so
decode-bound serving scales with effective, not nominal, bandwidth — size a deployment
off the datasheet number and you will overpromise. The ratio between the two is a
measured property of the stack, not a constant you can look up. Chapter 06.

### effective N
How many genuinely independent observations your sample is worth once items that partly
repeat each other are discounted: N_eff = N / [DEFF](#design-effect). This is the
number to use anywhere you were about to use the item count. Comparisons on clustered
suites can have an effective N several times smaller than the item count — small enough
to turn headline differences into noise, on exactly the same data, with nothing changed
but the honesty of the arithmetic. Chapter 04;
[SCENARIO-02](examples/SCENARIO-02_clustered-eval-effective-n.md).

### elimination rule
Dropping a candidate is a decision, and it needs the same standard of evidence as
choosing one. So no candidate is withdrawn from selection on a margin smaller than the
pilot's own [MDE](#mde): if the pilot could not resolve the gap, the gap is not a
reason. Below that margin the licensed moves are: both candidates proceed under a
pre-registered budget, the decision defers to the qualification split, or the selection
metric changes to one the pilot can resolve. Chapter 04.

### escalation
The moment a [cascade](#cascade) hands a task from a cheaper tier up to a stronger one.
"Escalate when it looks hard" is not something you can build on, so the policy is
explicit: gate rule, confirmation streaks, latching, timeout behavior, and
[fail-open](#fail-open)/[fail-closed](#fail-closed) semantics. Each of those is a place
a cascade can quietly end up escalating everything, or nothing. Chapter 08.

### evidence reachability
Can the system, with the tools it actually has, starting from what it can know at call
time, get to every fact an item requires? Where the answer is yes, the item is
answerable. Where it is no, the item is permanently unwinnable, and every model will
fail it forever while looking like a model weakness. Evidence reachability is that
property, designed in deliberately — and measured, not argued: see
[reachability ceiling](#reachability-ceiling). Chapters 03 and 08.

### evidence-strength labels
Every principle and default in this playbook states how well supported it is, so you can
weigh a claim without going and reading the sources yourself. A recent paper is never
rendered as law; a single project's result is never rendered as consensus. Six labels:

- `consensus` — independent practitioners and vendors agree. Safe to adopt.
- `strong-evidence` — published results back it, and the source is in the
  [ledger](references/SOURCES.md) with a verdict and a verification date.
- `heuristic` — a useful starting value that you are expected to retune. The number is
  a place to begin, not a finding.
- `contested` — credible people disagree. The playbook states a position and says so.
- `case-study` — learned from what happened on one project, not from broad evidence.
  **Read this label carefully in this build.** The playbook was developed alongside a
  real project, and these claims come from that work — but that project's records are
  not published here, so you cannot check them. The `SCENARIO-*` files linked beside
  such claims are invented illustrations of the same lesson; they show you the shape of
  the reasoning and they are *not* the evidence for it. Treat a `case-study` claim as
  one team's experience, reported honestly and unverifiable by you.
- `inference` — reasoned from first principles and argued in place. Nobody measured it.

The last two are the ones to push back on. They are labelled precisely so you can.

### execution surface
Where a model runs, in the sense that changes what you can promise about it: local
open-weights inference, self-hosted/rented inference, managed API, subscription
coding-agent harness, cloud agent environment. These differ in provenance,
reproducibility, and cost — you can pin a local weight file indefinitely, and you
cannot stop a managed API from being redeployed underneath you. So a methodology must
say which surfaces a claim covers.

### execution system
When you say "the model scored 71%", the model is one small part of what produced that
number. The execution system is the whole of it: model + artifact/quantization/adapter
+ runtime/provider + hardware/host + harness + context policy + retrieval/knowledge +
tools + workflow + generation/reasoning budget + verifier/grader + environment.
A comparison claim is about the frozen execution system unless the experiment
explicitly isolates one factor. Never collapse model/runtime/provider/harness/
hardware into one ambiguous label — that label is where irreproducible results hide.
Chapter 02.

### experiment contract
Everything you would otherwise be tempted to decide after seeing the data, decided
while you still have none: question and the decision it drives, prediction, baseline,
execution-system identity, splits, calibration rules with
[consequence-bearing tolerances](#consequence-bearing-tolerance),
selection/elimination rules, statistical plan with [MDE](#mde) and
[effective N](#effective-n), gates, telemetry, analysis plan, roles, amendment log.
It is frozen before any data, which is the difference between a contract and a plan.
Template: [templates/EXPERIMENT_CONTRACT.md](templates/EXPERIMENT_CONTRACT.md);
chapter 04.

### fail-closed
If a run has not been registered, or its contract is not frozen, or its integrity gates
have not passed, the system does not warn you — it refuses. Work that lacks its
prerequisites is *refused by machinery* rather than discouraged by convention, on the
observation that a convention is precisely what gets skipped the night before a demo.
The complement of [fail-open](#fail-open). Chapters 04 and 13.

### fail-open
The opposite default: when a component fails, the system proceeds instead of stopping.
An escalation judge times out, so the weak tier's answer gets served. That is a
legitimate, explicit choice for availability-critical paths — a weaker answer beats no
answer. It is a defect when it silently swallows a consequence that was supposed to
bind, and the difference between the two is entirely whether someone chose it on
purpose. Chapter 08.

### failure harvesting
Production failures are the most valuable data you have, and the instinct is to train
on them. Do that last. Failure harvesting feeds them back into the lab in ladder order:
first as evaluation candidates, then as retrieval/context fixes, and only later as
training data. When you do reach training, admissibility is component-level: owning a
[trajectory record](#trajectory-record) does not confer training rights to every output
embedded in it (a managed provider's escalation responses, provider-generated labels).
Every model-generated component's provenance and terms are checked before the record
enters a training set (chapter 09 §5). Chapter 12.

### finding vs waste
Your run spent most of its wall clock in one place. Before you optimize it away, decide
which of two things it is. It is a **finding** (an object of study) if it is
task-intrinsic and moves the decision the experiment serves. It is **waste** (overhead
to eliminate) if it is harness/infrastructure friction orthogonal to the question. The
test matters because eliminating a finding destroys the very measurement you were
taking. Chapter 06.

### forbidden claim
Some wrong answers are worse than others because of what a person does next. A system
that asserts fraud from evidence that cannot show fraud gets somebody investigated. A
forbidden claim is an assertion class scored as failure regardless of other
correctness, precisely because believing it would trigger a costly or harmful
real-world action. It is a harm-weighted scoring construct: the item is not marked down
in proportion, it is failed. Chapter 03.

### freeze
The moment a document stops being editable and starts being evidence. An
[experiment contract](#experiment-contract), suite, or configuration becomes
immutable-by-machinery — content-hash bound, with amendments appended rather than
applied in place. Nothing above the amendment log changes after freeze, so a later
reader can see not only what the plan became but what it originally was. Chapters 04
and 13.

### frontier-saturation check
Point the strongest system you have access to at the suite and see how it does. If even
that arm cannot approach the suite's measured ceiling, the likely explanation is not
that every model is weak — it is that the suite is broken, and the instrument rather
than the model is presumptively at fault until you show otherwise. Chapter 03.

### frozen identity
The whole [execution system](#execution-system) pinned down as a single identity —
hashes, versions, config, host — and held still for the duration of a comparison. Any
change creates a new identity and breaks [comparability](#comparability-claim) until
re-measured. That includes changes you did not make: a provider-side redeploy counts,
which is why the identity is recorded rather than assumed. Chapter 02.

### gold labels
The known-correct answers your scorer grades against. One boundary rule governs
everything you do with them: gold labels **score but never choose**. They may score
outcomes, and they may fit pre-registered calibration procedures on the iterate split.
They may never be readable by the system under test at inference time, and they may
never select, route, or tune anything on held-out splits. Every version of "we used the
labels to pick something" quietly converts a measurement into a fit. Chapters 04
and 13.

### goodput
Throughput that counts only work meeting a stated latency/quality constraint, as
opposed to raw throughput — everything the server managed to emit, useful or not. A
system can double its raw throughput while delivering fewer usable responses, and
goodput is the number that notices. It is the serving-side analog of "cost per
successful task". Chapter 06.

### ground-truth isolation
The answer key has to sit somewhere the system under test cannot reach, not somewhere
it has merely been asked not to look. Ground-truth isolation is that structural
guarantee: evaluation answer keys are unreachable from any model-facing surface,
enforced by permission separation *and* verified by reachability tests, not by
convention. Both halves are load-bearing — the permissions state the intent, and the
tests confirm nobody wired a path around them. Chapter 13.

### ICC
Intraclass correlation coefficient: the share of outcome variance attributable to
cluster membership — how much of a result is explained by which group an item came from
rather than by the item itself. Low, and items inside a group vary as much as items
across groups, so clustering costs you little. High, and items inside a group are near
duplicates of each other. It is the input to [DEFF](#design-effect) and
[effective N](#effective-n). Estimated from data (e.g., ANOVA on per-cluster
indicators), never assumed zero. Chapter 04.

### INCONCLUSIVE
"We could not tell" is a real result, and this playbook gives it a name so it can be
reported without embarrassment. INCONCLUSIVE is a first-class experimental verdict
meaning the design could not resolve the question at its [MDE](#mde) — which is not the
same as the arms being alike. It is reported as-is; never rounded to "no difference" or
"equivalent". An experiment that cannot say INCONCLUSIVE will eventually say something
false. Chapter 04.

### incumbent system
The thing a candidate has to beat: an existing, already-deployed automated or AI system
whose outputs are observable — not a manual, human-performed process. The distinction
does real work downstream. [Canary](#canary-deployment) and
[shadow](#shadow-deployment) deployments compare a candidate against it, and the
[QUICKSTART](QUICKSTART.md) archetype tree asks whether one exists and is failing
its own quality bar before routing toward optimization work. A workflow that is
today performed by a human, with no automated system standing behind it, has no
incumbent system in this sense — and needs a different starting point, because there is
no baseline to measure against. Chapters 08 and 10.

### intervention ladder
When something underperforms there is an order to try things in, running from cheap and
reversible to expensive and permanent: rung 0 instrument integrity, 1
infrastructure/runtime, 2 evidence/retrieval/context, 3 tool contracts & output
enforcement, 4 specification & verification (prompt/workflow/verifier), 5
generation/reasoning-budget calibration, 6 routing/escalation, 7 fine-tuning, 8
larger/different model, 9 architectural redesign. Descending a rung requires evidence
the cheaper rungs are exhausted or inapplicable. The rule that saves the most money
concerns the top of the ladder: never train around defects at rungs 0–4, because a
fine-tune that compensates for a broken tool contract has bought a permanent, expensive
workaround for a bug. Short normative form in chapter 00; operational form in
chapter 07.

### inversion check
Your weakest arm beat your strongest one on some slice of the suite. That is the
inversion, and it is almost never a real capability result. A systematically weaker
system beating a stronger one on a stratum indicates the stratum rewards guessing, or
the instrument is broken — so investigate the instrument before believing the score.
Chapter 03.

### leakage
Any path by which the test reaches the thing being tested: held-out evaluation content,
its answers, or its distribution getting to the system under test or its training data.
It is broader than the obvious case. It includes classical contamination,
[gold-label](#gold-labels) exposure, and structural leakage, where a feature encodes
item identity (see [class-identity ceiling](#class-identity-ceiling)). That last kind
is the one that survives careful data hygiene, because nobody copied anything.
Chapters 03, 08, 13.

### leakage audit
Four checks a learned component must pass before its measured performance is believed:
group-identity ceiling comparison, leave-one-group-out evaluation, feature-provenance
review (what could this feature encode?), and out-of-distribution checks. Run them
before you trust the score, not after the component disappoints in production — a
leaking model looks excellent right up until the day its shortcut is unavailable.
Chapter 08; [SCENARIO-03](examples/SCENARIO-03_learned-router-leakage.md).

### learned router
A routing/escalation gate that is itself a trained model, predicting from task or
trajectory features which tier should take an item. It can capture patterns no
hand-written rule would, and it can also learn the shape of your suite instead of the
task. So it is admissible only after a passed [leakage audit](#leakage-audit) and an
[observe-only graduation](#observe-only-graduation); contrast
[deterministic gate](#deterministic-gate). Chapter 08.

### look
One read of a held-out split's outcomes for a decision or report. Re-analyzing stored
outputs offline still counts as a look — the data was already in front of you, and it
is the seeing that spends the split, not the running. Looks are counted in the
[look ledger](#look-ledger); analyses computed within an already-counted look do not
count again. Chapter 04.

### look ledger
An append-only record of every [look](#look) anyone has taken at a held-out split. It
exists because held-out data is a consumable resource: each look uses some of it up,
and with no record nobody notices the fifth one. The ledger is that resource's fuel
gauge, and a pre-registered exposure threshold triggers the suite-refresh review before
the tank is empty. Template:
[templates/TEST_LOOK_LEDGER.md](templates/TEST_LOOK_LEDGER.md); chapters 03 and 04.

### MDE
Minimum detectable effect: the smallest true difference a design can detect at stated α
and power. Knowing it up front tells you whether the experiment is worth running at
all — if your MDE works out to 30 points, an argument about a 5-point gap is not one
this design can settle. Computed *before* the experiment, and after clustering
correction. Every contract states its MDE; margins below MDE cannot support adoption or
[elimination](#elimination-rule) decisions. Chapter 04.

### method decision record
A short written record of why a piece of methodology was adopted, rejected, or revised:
context, decision, evidence, consequences, in the style of an architecture decision
record. Its practical job is to stop a settled question being relitigated every six
months by people who were not in the room. Feeds the CHANGELOG. Template:
[templates/METHOD_DECISION_RECORD.md](templates/METHOD_DECISION_RECORD.md).

### never-skippable floor
Almost everything in this playbook scales with stakes. Six obligations do not, and they
apply at every [stakes tier](#stakes-tier): state the decision and claim; preserve
provenance sufficient to identify what produced a result; define the
evaluation/ground-truth boundary before quality claims; predeclare consequences for
decision-driving thresholds; treat held-out evidence as consumable and record exposure;
retain outcome evidence. They stay mandatory because they are cheap at any scale, and
because skipping them is what makes a result unrecoverable later rather than merely
imprecise. Chapter 00.

### observe-only graduation
A component does not go from "looked good in evaluation" to "making decisions" in one
step. It earns the right to act in stages: leakage audit passed → observe-only shadow
period with measured agreement/regret → pre-registered promotion gate → automated
action with a defined rollback and monitoring plan. The shadow period is where you find
out what it does on traffic nobody curated. De-automation conditions are pre-registered
too, so switching it back off is a decision already made rather than an argument you
have to win under pressure. Chapters 08 and 12.

### oracle analysis
Before building a router, work out what a perfect one would have been worth. Assume you
always choose the tier that would succeed — that is the oracle, and its score is the
ceiling on any routing policy you could ever write. If the oracle gain is small, no
router is worth its cost, and you learned that from arithmetic on data you already have
rather than from a quarter of engineering. Chapter 08.

### one-look discipline
Each held-out split is read once per candidate, for the decision it exists to serve:
select on the qualification look, confirm on the confirmation look, and never iterate
against either. The second look is where a split quietly stops being held out — you
begin tuning toward what you saw, and the number it produces is no longer about
anything but itself. Chapter 04.

### operating point
Latency and throughput trade against each other, so "how fast is it" has no answer
until you choose a position on the curve. The operating point is that chosen
position — a specific concurrency, batch size, and budget at which the system is
declared to run. It is selected from sweep data against stated latency constraints,
then pinned, so later measurements stay comparable and nobody quotes the throughput
figure from a configuration you would never ship. Chapter 06.

### paired design
Run both systems on the *same items* and analyze the per-item differences, rather than
comparing two overall averages. Item difficulty then cancels instead of contributing
noise. Paired standard errors are strictly tighter whenever per-item outcomes *positively*
correlate across arms, which is the normal case: both arms face the same hard and easy
items. Same-item comparisons get that power for free and must claim it. Analyzing them
as though the arms were independent throws away resolution you have already paid for.
Chapter 04.

### paired-comparison firewall
A rule keeping one useful technique from contaminating another: curtailed arms never
enter paired comparisons. Stopping an arm early under
[certainty curtailment](#certainty-curtailment) deletes items non-randomly (by stratum
composition) — whichever strata were still queued are the ones that go missing — and
that alone can flip paired test outcomes purely compositionally, with nothing having
changed about the systems. Chapter 04.

### pass-at-k vs pass-to-the-k
Two questions that sound alike and are not. "Can it do this if I let it try k times?"
is pass@k (some of k attempts succeeds), and it measures capability under retry. "Will
it do this k times running?" is pass^k (all of k attempts succeed), and it measures
reliability under repetition. Stochastic systems can score high pass@1 and collapse at
pass^k on identical tasks, which is why anything meant to run unattended is judged on
the second. Reliability claims about non-deterministic systems report pass^k on a
declared subset. Chapter 04.

### performance autopsy
After an expensive run, you sit down and establish where the time and money actually
went — as a standing procedure, not only when something obviously went wrong.
Reconstruct the timeline from multiple telemetry sources, identify the critical path,
attribute cost buckets, run counterfactuals (what would N nodes / a faster device / a
smaller budget have saved), and cross-check clock validity. The counterfactuals are the
part that changes what you buy next. Template:
[templates/PERFORMANCE_AUTOPSY.md](templates/PERFORMANCE_AUTOPSY.md); chapter 06.

### pre-registration
Writing down what you will do and what each outcome will mean before collecting any
data — hypotheses, procedures, thresholds, consequences, and analysis plans, in a form
that cannot be silently revised ([freeze](#freeze)). It is not a ban on adapting: the
adaptation rule may be pre-registered too. What is forbidden is inventing rules after
seeing outcomes, at the point where you can no longer separate your judgment from your
preference. Chapter 04.

### prediction ledger
Before each run, write down what you expect — a point estimate and an interval, per
primary metric. When the run completes, score the prediction against the actuals. A
handful of entries turns "is this experiment worth running?" from taste into an
empirical question about your own calibration, and shows you whether your surprises are
genuine surprises or just optimism. Template:
[templates/PREDICTION_LEDGER.md](templates/PREDICTION_LEDGER.md); chapter 04.

### project profile
The structured intake questionnaire you fill in first: the outcome the project is for,
what constrains it, what resources it has, and its [stakes tier](#stakes-tier).
Answering it is what lets the [QUICKSTART](QUICKSTART.md) navigator route you, since
the playbook cannot tell you what to skip until it knows what you are building.
Template: [templates/PROJECT_PROFILE.md](templates/PROJECT_PROFILE.md); chapter 01.

### provenance
Six months from now somebody will point at a number and ask what produced it.
Provenance is the evidence chain that answers: artifact hashes, execution-system
digests, contract bindings, dataset digests, run records. It has to be captured while
the run is happening, because none of it can be reconstructed afterwards from the
number alone. Stored in the [record of record](#record-of-record). Chapter 13.

### purchase trigger
The condition you commit to in advance that must fire before capital is spent — K
consecutive months of rented spend above X, say, or a committed always-on serving
requirement. The timing is the entire mechanism: it is defined *before* wanting the
hardware, while you can still think about it clearly, and it is fed by the
[demand ledger](#demand-ledger) rather than by how busy last week felt. Chapter 11;
[SCENARIO-05](examples/SCENARIO-05_hardware-purchase-discipline.md).

### reachability ceiling
The best score a stratum will permit anyone to reach, given the corpus, tools, and
thresholds as they actually are. You establish it by replaying the evidence plan
through the real tool broker — demonstrated, not argued from the generator that wrote
the items. A stratum whose ceiling is below the passing threshold is unwinnable, and
every score on it measures the defect, not the model. Chapter 03.

### record of record
One store, designated in advance, holding what actually happened: the single
authoritative, tamper-evident source of experimental truth, hash-chained and
append-only, so an alteration shows up rather than passing unnoticed. Everything else
is a view onto it. Dashboards may mirror it; they never replace it. Chapter 13.

### regression suite vs capability suite
Two suites answering two questions that pull in opposite directions. A regression suite
asks "did anything that used to work break?" — broad, stable, run often. A capability
suite asks "can the system do X?" — targeted, versioned, run at decisions. Conflating
them produces suites too expensive to run often and too noisy to decide with, which is
the worst of both. Chapter 03.

### reproducibility boundary
How far you can move before the same run stops giving the same answer. Within one
session? Across restarts? Across hosts, across provider redeploys, under concurrency?
Each of those is a candidate boundary, and where yours actually sit is an empirical
fact about your stack. Measured by probes, then comparisons are scoped to stay inside
them. Never assumed. Chapter 02;
[SCENARIO-12](examples/SCENARIO-12_restart-instability-paired-controls.md).

### rescue
The event a [cascade](#cascade) exists to produce: the lower tier failed an item, the
gate escalated it, and the stronger tier got it right. Counting rescues is how you find
out whether the gate is any good — the gate's value is measured by rescue rate
(escalations that succeed) against unnecessary-escalation rate (escalations that were
not needed). A gate that escalates everything rescues everything and is worth nothing.
Chapter 08.

### rigor dial
A weekend prototype and a regulated deployment should not carry the same paperwork, and
this is the mechanism that makes the difference deliberate rather than improvised.
Project stakes, captured in the [project profile](#project-profile), scale the
mandatory artifact set through three [stakes tiers](#stakes-tier), all of it above an
invariant [never-skippable floor](#never-skippable-floor) that no tier may drop below.
Chapter 00 defines it; QUICKSTART applies it.

### rollback path
The route back from a promotion, designed and rehearsed before you need it: triggers
(pre-registered thresholds with consequences), mechanics (state/version compatibility),
ownership, and verification. Rehearsed is the load-bearing word. A rollback that has
never been exercised is a hypothesis, not a path — and the incident is where you
discover which one you had. Chapter 10.

### round-robin ordering
Run one item from each stratum, then go round again, instead of finishing one stratum
before starting the next. The reason is what happens when you stop early or look
partway through: with round-robin, any prefix of the run is approximately
stratum-balanced, which makes interim evidence representative. Stratum-blocked order
makes every prefix unrepresentative and is the worst case for any interim decision
rule. Chapter 04.

### screening vs inference
Two activities that both produce numbers and mean entirely different things. Screening
ranks candidates cheaply to decide who advances — racing, successive halving,
stratum-balanced rungs on the iterate split. Inference makes calibrated claims: frozen
comparisons on held-out splits. Screening results never carry significance claims, and
screening never replaces the frozen comparison. The failure this prevents is a cheap
ranking being written up as a finding because it happened to be the number on hand.
Chapter 04.

### sequential-rule admissibility
Rules that let you stop an experiment early come with error guarantees, and those
guarantees have fine print — chiefly that the outcome stream is independent in
execution order. Real evaluation runs frequently are not: clustered, stratum-ordered
execution inflates the real error rate of i.i.d.-calibrated rules, so the guarantee you
are leaning on is not the one you have. Check independence first, or use
assumption-free counting instead
([curtailed exact counting](#curtailed-exact-counting),
[certainty curtailment](#certainty-curtailment)). Chapter 04.

### shadow deployment
The candidate sees mirrored real production traffic and answers it, but nobody ever
receives those answers — they are logged and compared offline against the incumbent.
You get behavior on real inputs at no user risk. What you do not get is any signal that
depends on someone acting on the output. Chapter 10.

### silent failure
A failure wearing the costume of a success: confidently wrong output, claims nobody
verified, verification that passed on a wrong answer. Nothing alerts, so nothing gets
fixed, and in a cascade the item is never escalated because nothing looked wrong —
which makes this the most expensive failure class there. It is the reason
[the in-system verification gap](#canonical-failure-taxonomy) (RC-7, rung 4) is checked
explicitly rather than assumed absent: a verifier that passes failures silently
produces no signal of its own. Chapters 00 and 05.

### smoke tier
A few minutes of fixed, stratified mini-evaluation run before any real spend, to catch
the boring catastrophes — a broken harness, a changed schema, a tool contract that no
longer holds. It runs *inside* the [fail-closed](#fail-closed) machinery, with results
ledgered and cryptographically non-promotable, so it cannot quietly become the evidence
for something. It never justifies adoption or elimination decisions; its MDE is
enormous by design. Chapter 03 (smoke tier) and chapter 04
([diagnostic run kind](#diagnostic-run-kind), the ledger mechanism that makes it
non-promotable).

### spend semantics
When does a held-out split count as used up? At the *first executed item*, not the
last. A partial run already reveals the sufficient statistic, so halting and starting
over restores nothing — there is no "peek and re-run". This is also what makes
[certainty curtailment](#certainty-curtailment) admissible at all: since the look was
spent the moment it began, its only consequence is irreversible rejection of an
already-spent look. Chapter 04.

### stakes tier
Which of three consequence levels a piece of work sits at, and therefore how much of
the [rigor dial](#rigor-dial)'s artifact set is mandatory: Tier 1 exploratory · Tier 2
consequential (default) · Tier 3 high-stakes/regulated. Rigor attaches to the
*decision's* consequence, not the project's prestige: a Tier-1 project making a Tier-3
decision escalates that decision to Tier-3 artifacts. A side experiment that ends up
choosing what ships is a Tier-3 decision no matter how it was labeled when it started.
Chapter 00.

### static integrity gates
Checks that validate the instrument itself, written as executable commands over the
full corpus rather than as a review someone signs off: reachability replay, gold-answer
scoring, corpus determinism. They are deliberately protected from subsetting. Sampling
them would mean sampling the instruments that catch instrument defects, which is
exactly where a defect would then sit undetected. Chapter 03.

### suite release
Suites change; how they change is what keeps their numbers meaningful. A suite release
is a versioned, contract-governed cut of an evaluation suite with five things done:
ceilings measured, gold answers gated, determinism verified, changes documented,
cross-suite comparison refused. Every score you keep is attached to one of these
versions, so "we improved" can never quietly mean "we edited the test". Template:
[templates/EVAL_SUITE_RELEASE_CONTRACT.md](templates/EVAL_SUITE_RELEASE_CONTRACT.md);
chapter 03.

### symptom vs root cause
"The answer was late" and "the retrieval index was stale" are different kinds of
statement, and a system that treats them as one will look right until it isn't. The
discipline is to keep user-visible failure categories distinct from diagnosed causes:
the category is what the operator sees, and the
[canonical failure taxonomy](#canonical-failure-taxonomy) class is what is wrong.
Systems that learn symptom→remedy lookups fail exactly on the deliberately ambiguous
symptoms — the ones where the same appearance has several possible causes.
Chapter 03.

### task ontology
The fixed vocabulary a project's evaluation domain is allowed to use: what an item can
be about, what can have caused it, what may be recommended, and which claims are
forbidden. Closed, meaning nothing outside the list is a valid answer, and versioned,
because changing it is a breaking change to the suite rather than an edit. Writing it
down is usually the moment a team discovers it did not agree on what it was measuring.
Chapter 03.

### telemetry floor
The instrumentation that must already be running *before* any long or expensive run:
run lifecycle events, per-invocation statistics (tokens, latency, finish reason),
[dual-clock](#dual-clock-telemetry) stamps, preserved server/engine logs, resource
sampling, config snapshot. It is a floor rather than a wish list because post-run
forensics is impossible to retrofit — the question you will want to ask afterwards can
only be answered from data you were already collecting. Chapter 12.

### tool contract
Everything a model can observe about a tool exposed to it, written down: schema,
addressing, result ordering, pagination, cohort/tenant keying, permissions, error
semantics, and byte-level transport fidelity. That last item is not padding — a
serialization change that never touches the schema still changes what the model reads.
Tool contracts are part of the [execution system](#execution-system) and are versioned
like code. Chapter 08;
[SCENARIO-08](examples/SCENARIO-08_transport-serialization-defect.md).

### trajectory record
What you keep about a single task execution so it can still be understood later:
identifiers, execution-system identity, inputs/context, retrieval and tool calls with
results, output, verification, outcome, latency, tokens, cost, clocks, versions,
mutations, human feedback, deployment stage. This is the minimum, and the list is long
for a reason — a trajectory you cannot mentally replay is not evidence of anything.
Chapter 12 defines the field set.

### vendor verdicts
Vendor material is not uniformly trustworthy, so this playbook states which of four
stances it takes on each piece: **FOLLOW** (mature, follow by the book), **ADAPT**
(mechanics sound, decision layer missing — substitute stated pieces), **REFERENCE**
(consult, don't depend), **DEPRECATED** (do not adopt; recorded to prevent
re-adoption). Note that deprecated entries are kept rather than deleted, so the same
bad idea does not get rediscovered next year. Every verdict carries an as-of date and
freshness sensitivity; see [references/SOURCES.md](references/SOURCES.md).

### verdict vocabulary
An experiment may end in one of a closed set of ways, and "it looked promising" is not
among them: **CONFIRMED** / **REFUTED** / **[INCONCLUSIVE](#inconclusive)**, plus
**RANKED** for screening. Alongside the verdict, reports print the primary statistic,
the secondary statistic, and the clustering caveat — so the verdict always travels with
the evidence that produced it. Chapter 04.

---

[Index](README.md) · [Quickstart](QUICKSTART.md)
