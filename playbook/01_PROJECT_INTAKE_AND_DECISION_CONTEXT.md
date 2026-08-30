# 01. Project Intake and Decision Context

> Part of the **Adaptive AI Systems Playbook** v0.1.1 ·
> [← Previous](00_PRINCIPLES_AND_SCOPE.md) · [Index](README.md) · [Next →](02_EXECUTION_SYSTEM_MODEL.md)
> **Reading time:** ~15 min. **Prerequisites:** [00](00_PRINCIPLES_AND_SCOPE.md).

## 1. Purpose and when to read this

*"We want AI to help with X."*

Some version of that sentence starts most projects, and there is nothing wrong with
it. It is honest about the goal and honest about the vagueness. The problem is that
nothing follows from it. It does not say what would count as help, who is harmed when
the help is wrong, or what result would mean the idea was a dead end. Months later it
also gives you no way to settle whether the thing you built worked.

This chapter is the conversion. Read it first on every new engagement, immediately
after chapter 00 — before a model is shortlisted, before an evaluation is designed,
before compute is rented or bought. What you have at the end that the opening sentence
did not contain:

- a **named decision** — a question with a yes and a no, each implying something
  different to do next;
- a completed [project profile](GLOSSARY.md#project-profile), the intake record every
  later chapter reads its facts from;
- an assigned [stakes tier](GLOSSARY.md#stakes-tier), which fixes how much proof this
  project owes;
- an **inventory of constraints**, sorted into the ones that eliminate options and the
  ones you can trade against;
- a first-pass [archetype](GLOSSARY.md#archetype) — the project shape that sets your
  reading order;
- a **committed first sprint**, with a stated place where it stops.

**Honesty note.** Much of this chapter is playbook synthesis. The intake method here
was assembled from general evaluation-practice literature and first-principles
argument — it was not read off a large internal record of varied project intakes.
Individual claims are marked `(inference)` where that is the case; where an external
source corroborates a step, it is cited. So treat this chapter as a well-argued
starting procedure, not as a validated instrument, and revise it in your own
[method decision record](GLOSSARY.md#method-decision-record) as it meets real
projects.

## 2. Inputs required

Three things. The first is the one that gets skipped.

- **Whoever owns the business decision**, reachable for the intake conversation
  (§5.1). Several of the fields below have no answer anywhere except in that person's
  head.
- **Access to whatever already exists**: an incumbent system, prior evaluations,
  production logs, support tickets, cost data.
- **Chapter 00's principles and [rigor dial](GLOSSARY.md#rigor-dial).** This chapter
  applies them at the intake boundary; it does not redefine them.

No completed template is required to start this chapter. It produces the first one.

## 3. Decisions this chapter supports

Five decisions run through this chapter. Each is cheaper to make here than anywhere
downstream of here.

- Whether a request is a decision-driving work item at all, or must be re-scoped
  before anything else happens.
- The project's [stakes tier](GLOSSARY.md#stakes-tier) and therefore its mandatory
  artifact set (00 §6).
- Which candidate execution systems are admissible at all, before any are evaluated.
- A first-pass archetype and reading path — [QUICKSTART](QUICKSTART.md) is the
  normative router; this chapter previews it and hands off.
- What the first sprint commits to, and exactly where it must stop.

## 4. Normative principles

**[PRINCIPLE] Name the decision before naming the work.** (consensus)
"Build an eval." "Try a few models." "See if fine-tuning helps." Each of those is an
activity, and none of them is a decision. They start making sense only once someone
states the decision they serve — *should we replace provider X's API with a
self-hosted model for this population, at this quality bar, by this date?* That
question has a yes and a no, and the two answers lead somewhere different. This
instantiates 00 P1 (evaluate first) at the intake boundary: an evaluation built before
its decision is named tends to measure whatever was easy to measure. External guidance
on evaluation design opens with the objective and works backward to the dataset and
metrics, never forward from a convenient dataset [EXT-EVAL-002], [EXT-EVAL-001];
vendor practitioner guidance independently converges on evaluation infrastructure as
the first engineering act, not a late addition [NV-AGENTICBLOGS-001].

**[PRINCIPLE] Constraints are inventoried, and hard ones enforced, before any
candidate is shortlisted.** (inference — first-principles)
Picture three weeks spent evaluating four models, a winner chosen — and then someone
notices that the data may not leave the jurisdiction, and the winner has no endpoint
inside it. Nothing about the evaluation was wrong. It was simply run on a candidate
that was never admissible — and the check that would have caught it is the cheap one.
Selecting a model, provider, or deployment surface before checking hard constraints
(data residency, licensing, tool permissions, an unreachable latency floor) risks
discovering inadmissibility after evaluation cost is already sunk. Constraints define
the *admissible set*; candidate selection (05) ranks *within* it. Reversing the order
wastes the more expensive step on candidates the cheaper step would have eliminated
for free.

**[PRINCIPLE] Stakes tier is set at intake, not discovered at deployment.**
(inference — first-principles)
The rigor dial (00 §6) scales the mandatory-artifact set from the very first
experiment contract onward. Assigning the tier only after a first result is
inconvenient means retrofitting provenance and statistics — and the
[never-skippable floor](GLOSSARY.md#never-skippable-floor) has already named those as
unrepairable after the fact (00 §6: you cannot reconstruct what produced a number
after the fact). That is why the tier is a profile field (§5.1), not an afterthought.

**[PRINCIPLE] Kill criteria are pre-registered at intake, not discovered after a
disappointing pilot.** (inference — first-principles, extends 00 P7)
00 P7 pre-registers *experiment*-level tolerances with consequences; this principle
applies the same discipline one level up, to the *project*. The conditions under which
the project itself is re-scoped or stopped are named before evaluation-suite
construction begins, not read off a result the team did not want. A kill criterion
discovered only in hindsight was never a criterion — it was a rationalization.

## 5. Default procedure

### 5.1 The intake question set

**[DEFAULT] The intake field set.** (inference) Mirrors
[templates/PROJECT_PROFILE.md](templates/PROJECT_PROFILE.md); every field SHOULD be
answered before archetype selection (§5.4), and every field marked "always mandatory"
MUST be answered before any spend on evaluation or compute.

Field names below are identical strings to
[templates/PROJECT_PROFILE.md](templates/PROJECT_PROFILE.md)'s field headers, so
the two tables stay grep-able as one questionnaire.

Twenty-one questions is a lot to ask in one sitting, so the third column says why each
one earns its place here rather than later, and the fourth says which chapter is
waiting on the answer. Other files in this playbook cite these fields **by number** —
so the numbering is part of the interface, not presentation.

| # | Field | Captures | Why it matters at intake | Primarily feeds |
|---|---|---|---|---|
| 1 | Business outcome | The business result the system must produce — not the technology | Anchors the decision (§5.2); everything else is subordinate to it | §5.2, 03 |
| 2 | Task population & volume | The set of requests/tasks in scope, its boundaries, and how many per period | Defines what an evaluation corpus must represent | 03 (corpus design) |
| 3 | Criticality / failure cost | What happens when the system is wrong, and to whom | Primary input to the stakes tier | 00 §6 |
| 4 | Quality/reliability target | The bar the system must clear, and how firm it is | Becomes the evaluation claim's threshold (§5.2) | 03, 04 |
| 5 | Latency/throughput/SLA | Response-time and volume requirements | A hard filter on runtime/serving choices | 05, 06 |
| 6 | Privacy/security/data residency | What data may leave which boundary, to which surfaces | Frequently the first hard constraint (§5.3) | 05, 13 |
| 7 | Data & knowledge availability | What evidence, documents, or tools already exist to ground answers | Determines whether retrieval is possible at all | 08 |
| 8 | Tool/action permissions | What the system may read, call, or change, and under whose authority | Bounds cascade/tool-contract design and the security review | 08, 13 |
| 9 | Model candidates | Any models already under consideration or contractually available | Seeds the shortlist; never a substitute for the shortlist procedure | 05 |
| 10 | Owned compute | Hardware already available to the project | A supply-side constraint on execution surfaces | 06, 11 |
| 11 | Rentable compute | Cloud/rental access and procurement constraints | Alternate supply for the same constraint | 11 |
| 12 | Managed APIs | Frontier/managed providers already contracted or permitted | Alternate supply; interacts with field 6 | 05, 11 |
| 13 | Capex budget | Capital available for a hardware purchase, if any | Gates the [purchase trigger](GLOSSARY.md#purchase-trigger) | 11 |
| 14 | Recurring budget | Ongoing spend ceiling (API + rental + ops) | Becomes a consequence-bearing tolerance once the system ships | 04, 11 |
| 15 | Utilization/growth expectations | Expected volume now and its trajectory | Distinguishes within-run busyness from sustained demand | 11 ([demand ledger](GLOSSARY.md#demand-ledger)) |
| 16 | Staffing/time | Who executes and reviews this work, and the calendar | Sets what rigor is executable, not merely desirable | 00 §6 |
| 17 | Deployment environment | Where the system will actually run in production | Feeds execution-surface and promotion design | 02, 10 |
| 18 | Observability constraints | What telemetry/monitoring already exists or is required | Determines whether the telemetry floor is a build item | 12 |
| 19 | Regulatory/compliance | Audit, safety, or legal regimes that apply | A primary input to the stakes tier and to governance | 00 §6, 13 |
| 20 | Existing evidence | Prior evals, incumbent-system metrics, production logs, tickets — **including any incumbent or automated system currently in use and its observed failures**; there is no separate "existing system" field | Reused as priors (§5.5) and as error-analysis input; the single field [QUICKSTART](QUICKSTART.md) reads to detect an incumbent that is failing its own quality bar | 03, QUICKSTART routing |
| 21 | Stakes / consequence tolerance | The decision owner's direct statement of how wrong is acceptable, and to whom | Sets the stakes tier directly | 00 §6 |

Fields 3, 4, 6, 19, and 21 are **always mandatory**, even for a one-person Tier-1
exploration: they are the inputs the never-skippable floor and the stakes tier depend
on. The remaining fields SHOULD be answered as completely as the project's maturity
allows. An honest "unknown — to be measured" is an acceptable value and is itself a
profile entry, not a blank — usually it is also your next action.

Those five are also the tier conversation in miniature, which is why they cannot wait.
Field 3 asks what a wrong answer costs and who pays it. Field 19 asks whether an
auditor, a regulator, or a legal regime has a claim on the answer. Field 21 asks the
decision owner to state out loud how wrong is acceptable. Read together against the tier signatures in 00 §6, they usually
name the tier without an argument; when two of them point at different tiers, the
higher one wins (§6). Do this at intake and the tier is what keeps a small project
small — it is the mechanism that lets an exploratory piece of work skip artifacts a
regulated deployment could never skip, deliberately rather than by drift.

### 5.2 Requirement → evaluation claim formulation

Every requirement MUST be restated as an evaluation claim, with the decision it
drives stated explicitly, before an evaluation is built for it or a candidate is
chosen against it (00 P1):

```
Vague request        "We want AI to help our support team with X."
      │  name the decision
      ▼
Decision              "Should we deploy an AI system to do Y for population Z,
                       replacing/augmenting the current process, by date D?"
      │  name the claim the evidence must support
      ▼
Evaluation claim      "System S achieves quality bar Q on population Z (field 4),
                       verified by evaluation E, within the latency/cost bounds
                       of fields 5/14."
      │  hand off
      ▼
Chapter 03            E becomes a task ontology, a stratified corpus, and a
                       grading method — derived from real failure modes, not
                       assumed (03 §5, requirement → task-ontology derivation).
```

Each step down that ladder is narrower than the one above it. A decision carries a
date and an alternative; a claim carries a threshold, a population, and the instrument
that will measure it. If you cannot yet fill in Q or Z, intake is not finished — and
the blank is telling you which conversation to have next.

The requirement → task ontology derivation itself (error-analysis-first, root-cause
stratification, [task ontology](GLOSSARY.md#task-ontology) versioning) is chapter
03's subject; this chapter's job ends at handing off a decision and a claim that 03
can operationalize.

### 5.3 Constraints inventory: hard vs. soft, and kill criteria

**[DEFAULT] Classify every constraint as hard or soft before shortlisting.**
(inference)

The split is about what a constraint does to your candidate set. A hard constraint
removes candidates outright, however well they score. A soft one is something you buy
and sell against — worse latency for lower cost, more spend for more quality. Sorting
them at intake is cheap. Skipping the sort costs you the whole selection you then run
without it.

| Constraint class | Example | Usually hard or soft | Effect on the candidate set |
|---|---|---|---|
| Data residency / privacy | Data must not leave a jurisdiction; a managed API is contractually forbidden | Hard | Eliminates any execution surface that violates it, before selection (05) |
| Licensing | Base-weight license forbids commercial use, or output ownership is disputed | Hard | Eliminates the artifact regardless of measured quality (13) |
| Latency floor | An interactive path needs a response time no candidate tier can reach | Hard, once measured | Eliminates tiers whose measured operating point cannot reach it (06) |
| Tool/action permission | Write actions require human approval at this stakes tier | Hard at Tier 3, soft below | Shapes cascade/permission design (08, 13); rarely eliminates a candidate outright |
| Budget ceiling | A recurring spend cap | Usually soft | Trades off against quality/latency; degrades gracefully rather than eliminating |
| Staffing/time | Rigor achievable given reviewer bandwidth | Soft, but consequential | May force a stakes-tier de-scope *conversation* — never a silent skip of the floor (00 §6) |

**[DECISION GATE] Kill criteria at intake.** A hard-constraint check MUST run before
an evaluation suite is built or compute is spent: if no candidate execution system
can satisfy every hard constraint at any plausible operating point, the project is
re-scoped or killed at intake, not discovered to be unworkable after a suite exists
for it. Record the check's outcome and its date in the project profile — a "no hard
constraint eliminates every candidate" finding is itself evidence, not an absence of
one.

Writing the kill condition down while you still have no results is the entire
mechanism, and it is the part teams resist. Afterwards every number is negotiable: the
pilot was unlucky, the prompt was never tuned, one more week would do it. Some of
those objections will be true. What you cannot do afterwards is tell your own judgment
apart from your own investment in the answer, because by then they feel identical from
the inside. A threshold fixed while you are still indifferent to which side of it you
land on is the only kind that survives landing on the wrong side.

This is the project-level analog of a
[consequence-bearing tolerance](GLOSSARY.md#consequence-bearing-tolerance) (04): it
predates any experiment, but it obeys the same rule — the condition and its
consequence are stated *before* the fact that would trigger it is known.

### 5.4 Archetype selection — preview

Projects rhyme. Six shapes cover most of them, and the shape you are in decides which
three or four chapters you open first — so this is the step that turns fifteen
chapters into a short reading list.

**[DEFAULT] Archetype table.** (inference) A first-pass classification, using only
facts already captured in §5.1. [QUICKSTART.md](QUICKSTART.md) is the *normative*
router: it keys on the profile's actual field values, carries the full decision
tree, the mandatory-template list per tier, and the global tripwires. The table below
previews the shape of that routing; do not treat "closest-looking row" as a
substitute for running the navigator.

| Archetype | Signature profile facts | Typical entry chapters | Often skippable at start |
|---|---|---|---|
| A — Greenfield, managed-API-only | No owned hardware; API budget; quality bar not yet firm | 01 → 03 → 04 | 06, 09, the hardware half of 11 |
| B — Local/private deployment mandate | Privacy/residency constraint dominates; owned or planned hardware | 01 → 02 → 03 (06 early) | 09, until the ladder reaches it |
| C — Existing system underperforming | A system already runs; failures are observed; no trusted eval yet | 01 → 03 (eval before anything) → 07 | 05 — selection is premature before diagnosis |
| D — Cost reduction of an API-heavy system | Traffic and spend are known; quality bar is established | 01 → 08 (routing) → 11 | 09; 03 only far enough to confirm eval trust |
| E — High-stakes / compliance-bound | Audit or regulatory requirement; reliability claims needed | 01 → 13 → 03 → 04 | Nothing — no chapter is optional at this tier |
| F — Methodology/capability bootstrap | Building the evaluation capability itself; no client system yet | 00 → 03 → 04 → 12 | 10, until a real deployment target exists |

Worked, non-authoritative profiles at three of these rows:
[SYNTH-01](examples/SYNTH-01_api-only-assistant.md) (A),
[SYNTH-02](examples/SYNTH-02_private-local-deployment.md) (B),
[SYNTH-08](examples/SYNTH-08_high-stakes-audited-deployment.md) (E). A full
navigator pass, profile through first sprint, is worked end-to-end in
[WALKTHROUGH](examples/WALKTHROUGH_rag-document-qa.md).

### 5.5 Cold-start parameterization

**[DEFAULT] Cold-start parameterization procedure.** (inference — first-principles)
You have to set a number and nothing tells you what it should be. A confidence
threshold for escalating to a human, an eligibility gate, a utilization cap — and
there is no incumbent system to copy it from and no prior evidence base to calibrate
it against. This is a recurring intake problem, and the tempting response is to pick a
round number and move on. Five steps make the number defensible instead.

1. **Anchor on task consequence.** Start from the stakes tier (00 §6), not from a
   convenient round number — a Tier-3 decision earns a tighter provisional band than
   a Tier-1 one, before any data exists.
2. **Borrow external reference points as priors, explicitly labeled non-binding.** A
   vendor default, a published comparable benchmark, or an adjacent project's
   calibrated value. State the source and name, in writing, the reason it might not
   transfer.
3. **Run a calibration pilot sized for direction, not inference.** Enough cases to
   see which side of a threshold you are on, not enough to claim a margin — this is
   [screening, not inference](GLOSSARY.md#screening-vs-inference) (04); an
   [MDE](GLOSSARY.md#mde) is not yet a meaningful statement at this sample size.
4. **Pre-register how the first real data will revise the parameter.** The revision
   rule — the formula, the split it reads, the sample size that triggers it — is
   fixed *before* the pilot runs, so the eventual change is legitimate under 04's
   [amendment legitimacy](GLOSSARY.md#amendment-legitimacy) rule rather than
   post-hoc threshold shopping.
5. **Never let a placeholder threshold silently become policy.** A value set under
   step 3 stays visibly provisional — recorded in the profile as, e.g., "cold-start;
   revision due at n = 300" — until step 4's procedure actually fires. Treating it
   as calibrated the moment it stops feeling arbitrary is the anti-pattern this
   procedure exists to prevent (§9).

**Worked illustrative example** (invented, round numbers; no project value travels
here):
> A team has no incumbent for a new document-classification task and must set a
> provisional "escalate to human review" confidence threshold before any labeled
> data exists. *Step 1*: the decision is Tier 2 (customer-visible, reversible), so
> the team allows a wider provisional band than a Tier-3 payment decision would get.
> *Step 2*: a comparable published system's threshold, 0.70, is recorded as a
> non-binding prior. *Step 3*: a 40-case pilot on the iterate split shows the region
> separating confident-correct from confident-wrong sits somewhere between 0.55 and
> 0.75 — enough to pick a provisional value of 0.65, not enough to defend a specific
> point. *Step 4*: the first real experiment contract pre-registers that the
> threshold will be re-derived from a stated formula once 300 iterate-split cases
> are labeled, before any qualify-split execution. *Step 5*: the profile records the
> value as "cold-start — revision due at n = 300," so no one downstream mistakes it
> for a calibrated production threshold.

### 5.6 The first-sprint contract

Intake ends in a commitment, and the commitment is deliberately small: one sprint,
with the place it stops written down in advance. Everything after that first sprint
depends on what the first sprint finds, so committing to it now would be committing on
information you do not have yet.

**[DEFAULT] Every first sprint ends at the same place.** (inference) Whatever the
archetype, the first sprint's committed scope stops at:

- **Tier 2 and Tier 3**: a frozen
  [templates/EXPERIMENT_CONTRACT.md](templates/EXPERIMENT_CONTRACT.md) for the first
  real experiment (chapter 04) — question, decision, prediction, splits, MDE, and
  consequence-bearing tolerances all stated before data.
- **Tier 1**: a written lightweight plan — the completed profile, the chosen
  archetype, and the first three actions — is sufficient; a frozen contract is not
  yet required.

"Lightweight" scales the *weight* of each floor item, not which floor items exist:
nothing in the never-skippable floor (00 §6) is waived. So the Tier-1 deliverable is
not a separate content list to author from scratch. It is defined as satisfying all
six floor items, mapped one-to-one onto what the completed profile, the locked
archetype, and the first three actions already produce:

| # | Never-skippable floor item (00 §6) | Satisfied at Tier 1 by |
|---|---|---|
| 1 | State the decision and the claim to be evidenced | Profile field 1 (business outcome), restated as an evaluation claim via §5.2 |
| 2 | Preserve enough execution-system/artifact provenance to identify what produced any result | Profile fields 9/12/17 (model candidates, managed APIs, deployment environment) plus notes-grade pinned provenance on whatever the first three actions actually run |
| 3 | Define the evaluation/ground-truth boundary before making a quality claim | Profile field 4 (quality target) plus the locked archetype's entry chapter (typically 03), named explicitly in the first three actions |
| 4 | Predeclare consequences for decision-driving thresholds and tolerances | The archetype lock (§7) and any [cold-start parameters](#55-cold-start-parameterization) (§5.5), each carrying a stated consequence even at smoke scale — no threshold is set and left unconsequenced |
| 5 | Treat held-out evidence as consumable; record exposure | The first three actions name which split or sample is spent, and that it was looked at is logged, even without a full [look ledger](GLOSSARY.md#look-ledger) |
| 6 | Retain outcome evidence | Raw outputs from the first three actions are kept, not summarized away into a single judgment |

This mapping is what "written lightweight plan" means in this chapter and in
[QUICKSTART](QUICKSTART.md#where-your-first-sprint-ends) — QUICKSTART restates the
identical six-item floor mapping at its own first-sprint endpoint; a Tier-1 plan
satisfying this table satisfies both.

**[DEFAULT] Commit only the first sprint; describe the rest as gated, not
scheduled.** (inference — first-principles) State later work as a sequence of
milestones, each carrying its own prerequisites, cost class, and a pre-declared
go/no-go rule — not as a fixed multi-month plan committed in full at intake. A
milestone's gate is accepted by the decision owner named in the profile (§5.1, field
21), never self-assessed by whoever executed it (13 carries the general role
separation). This keeps a plan's later stages honest about what is still
conditional, and prevents a first-sprint commitment from silently becoming a
program-wide one.

## 6. Project adaptation parameters

Four things in this chapter are yours to set rather than to copy. The third column
says what to check the setting against.

| Parameter | How to choose/measure it | Calibrate against |
|---|---|---|
| Stakes-tier assignment | Read fields 3, 4, 6, 19, 21 against the tier signatures in 00 §6; when signals conflict, take the higher tier | 00 §6's tier table |
| Cold-start prior source (§5.5 step 2) | Prefer a source solving a materially similar task, with its own stated evidence strength; downgrade priors from adjacent-but-different domains explicitly | The task population (field 2) |
| Kill-criteria thresholds (§5.3) | Derive from the hard constraints actually in force for this project — do not borrow another project's thresholds | The constraints inventory itself |
| "Mandatory" field set beyond the always-mandatory five (§5.1) | Widen as stakes tier rises; a Tier-3 project SHOULD treat all 21 fields as mandatory before archetype selection | 00 §6 tier table |

## 7. Decision gates and stopping conditions

**[DECISION GATE] Profile-complete gate.** The five always-mandatory fields (§5.1:
criticality, quality target, privacy/residency, regulatory, stakes tolerance) MUST be
answered before archetype selection (§5.4) proceeds; remaining fields SHOULD be
complete before the first-sprint contract is frozen, and MUST be complete at Tier 3.

**[DECISION GATE] Archetype lock.** The chosen archetype, its entry chapters, and its
skippable-at-start list are recorded in the profile before the first sprint's
actions begin. A later archetype change is a profile amendment, not a silent drift.

The three conditions below mean stop, not slow down. Each one says what to do instead.

**[STOP CONDITION] No decision named.** Work is about to start ("build an eval,"
"try some models") with no decision stated behind it — restates 00's global tripwire
1 at the intake boundary. Stop and complete §5.2 first.

**[STOP CONDITION] Universal hard-constraint failure.** No candidate execution system
satisfies every hard constraint at any tested or plausible operating point (§5.3).
Stop; re-scope or kill the project before an evaluation suite or compute spend
commits to it.

**[STOP CONDITION] Placeholder threshold about to become policy.** A cold-start value
set under §5.5 step 3 is about to be relied on for a real decision without §5.5 step
4's pre-registered revision having fired. Stop; either run the revision procedure or
explicitly re-flag the value as provisional in the decision record.

## 8. Metrics and formulas

N/A — intake produces no statistics of its own; there is nothing here to compute. The
statistics canon begins at chapter 04; formula derivations live in
[references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md).

## 9. Failure modes and anti-patterns

Three of the five below are one move wearing different clothes: something that should
have been fixed in advance gets decided by a result instead.

**[REJECTED]** (condition: always)

- **Solution-first intake.** Choosing a model, vendor, or architecture before naming
  the decision it is supposed to inform. The candidate becomes the frame instead of
  the output of one.
- **Deferred stakes tier.** Assigning the stakes tier only after a first result is
  inconvenient, so that the "right" tier is whichever one the result already
  survives. The tier is set from consequence (§5.1 fields 3/19/21), not from outcome.
- **Placeholder-to-policy drift.** A cold-start value (§5.5) treated as calibrated
  the moment it stops feeling arbitrary, without ever executing the pre-registered
  revision procedure that would have made that legitimate. The value did not become
  more true; it became less examined.
- **Kill criteria written after the fact.** A "we would have stopped if X" told after
  a disappointing pilot is not a kill criterion — it is a story. Kill criteria that
  were not written down before the pilot do not count (§5.3).
- **Treating the intake questionnaire as a one-time form.** Constraints and budgets
  change; a profile that is never revisited quietly drifts out of sync with the
  project it describes, and downstream chapters keep citing a stale field.

## 10. Vendor recipes

**[ADAPT: EXT-EVAL-002]** OpenAI's eval-design ordering (objective → dataset →
metrics → run → iterate) is adapted here one level up the stack: apply "objective
before dataset" to the *project*, not only to a single evaluation suite — name the
decision (§5.2) before any evaluation work begins. As of verification, the
methodology content is current; the vendor's specific hosted tooling around it is
being retired and is not what is being adopted here.

**[ADAPT: EXT-EVAL-001]** Anthropic's eval-design documentation independently opens
with explicit, multidimensional criteria before construction — the same ordering
this chapter's §5.2 formalizes as requirement → decision → claim.

**[REFERENCE: NV-AGENTICBLOGS-001]** Vendor practitioner guidance corroborates
evaluate-first as the operating order for the most successful teams observed, not
merely a recommended one — cited in full in chapter 00 P1; referenced again here
because it is the ordering this chapter's whole procedure exists to protect at the
intake boundary.

**[ADAPT: EXT-OPS-002]** The ML Test Score rubric's category structure (28 tests
across four sections; score = minimum across categories, not an average) is
previewed at intake as a shape of the obligations a project will eventually need to
demonstrate, scaled by the stakes tier assigned here — not run as a self-audit yet.
The rubric's operational use as a periodic self-audit is chapter 12's subject.

## 11. Worked examples

All of these are invented illustrations rather than case evidence. What travels from
them is the reasoning, never the numbers.

- [SCENARIO-11](examples/SCENARIO-11_diagnostic-gate.md) — a cheap, pre-registered
  diagnostic determined whether a large experiment should run at all, before any of
  its cost was spent; illustrates naming the decision and its evidence bar ahead of
  spend (§5.2, §5.6).
- [SCENARIO-05](examples/SCENARIO-05_hardware-purchase-discipline.md) — a demand ledger
  and a pre-committed purchase trigger, set before the hardware was wanted,
  prevented a purchase that a later measurement showed would not have paid for
  itself; illustrates kill-criteria discipline applied to a capex decision (§5.3).
- [WALKTHROUGH](examples/WALKTHROUGH_rag-document-qa.md) — a full navigator pass,
  profile through archetype through first-sprint contract, on a synthetic
  non-trivial project.
- [SYNTH-01](examples/SYNTH-01_api-only-assistant.md),
  [SYNTH-02](examples/SYNTH-02_private-local-deployment.md),
  [SYNTH-08](examples/SYNTH-08_high-stakes-audited-deployment.md) — profile-to-
  archetype routing worked across three stakes tiers.

## 12. Outputs and artifacts

- A completed [templates/PROJECT_PROFILE.md](templates/PROJECT_PROFILE.md) —
  the ~20-field intake, all always-mandatory fields answered.
- An assigned stakes tier and a recorded archetype (§5.4).
- A constraints inventory (hard vs. soft) and the intake-level kill-criteria check
  (§5.3), dated.
- Any cold-start parameters set under §5.5, each carrying its pre-registered
  revision rule.
- The first-sprint commitment: a frozen
  [templates/EXPERIMENT_CONTRACT.md](templates/EXPERIMENT_CONTRACT.md) (Tier 2+) or
  a written lightweight plan (Tier 1) — with any later milestones stated as gated,
  not scheduled (§5.6).

## 13. Sources

| ID | Role here |
|---|---|
| [NV-AGENTICBLOGS-001] | Evaluate-first ordering, corroborating 00 P1 at the intake boundary |
| [EXT-EVAL-001] | Explicit-criteria-first eval design ordering |
| [EXT-EVAL-002] | Objective→dataset→metrics ordering, adapted one level up to project intake |
| [EXT-OPS-002] | ML Test Score rubric — previewed here as the shape of eventual obligations |

Gap dispositions in this chapter: **G2 (rigor sizing, shared with 00): COVERED** —
the profile capture point is §5.1 field 21 and the always-mandatory field set of §7;
the tier definitions and artifact mapping themselves are normative in 00 §6.
**G4 (cold-start parameterization): COVERED** — the five-step procedure and worked
example are §5.5.

---

> [← Previous](00_PRINCIPLES_AND_SCOPE.md) · [Index](README.md) · [Next →](02_EXECUTION_SYSTEM_MODEL.md)
