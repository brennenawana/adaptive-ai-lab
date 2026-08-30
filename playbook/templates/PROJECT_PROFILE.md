# Project Profile

> The intake questionnaire you fill in first: 21 questions about what you are
> building, what constrains it, and what it costs when the system is wrong.
> [QUICKSTART](../QUICKSTART.md) routes on the answers, and the
> [rigor dial](../GLOSSARY.md#rigor-dial) reads them to decide how much proof this
> project owes.
>
> Index: [../README.md](../README.md) · Governing chapter:
> [01. Project Intake and Decision Context](../01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md)

## How to fill this in

Copy this file into your own repository and answer the questions. Half an hour is
normal. Each field tells you what it is asking, why anyone downstream cares, and
shows a specimen answer at the level of detail that is actually usable.

You will not know all 21 answers, and that is not a reason to stop. Write
`[unknown — <what would settle it>]` and keep going. An honest unknown still
routes you somewhere, usually to the conversation you need to have next. A blank
routes you nowhere, and a guess written as a fact routes you somewhere wrong.

**Five fields are mandatory at every tier**, including a one-person weekend
experiment: **3** (failure cost), **4** (quality target), **6**
(privacy/residency), **19** (regulatory), **21** (stakes). The
[never-skippable floor](../GLOSSARY.md#never-skippable-floor) and the stakes tier
both depend on them, so nothing downstream works without them (01 §5.1). Answer
the other sixteen as completely as the project's maturity allows.

## When to use / when not to

- Use at the start of any new AI-system project or workstream — before a model,
  runtime, or architecture is chosen. Filling it in is the first action this
  playbook asks for.
- Use again whenever a live project's outcome, constraints, or stakes change
  materially: a new regulatory scope, a budget cut, a latency requirement that
  tightens, data residency moving. Revise the profile and re-run the
  [archetype](../GLOSSARY.md#archetype)/tier routing. A profile nobody revisits
  drifts out of sync with the project it describes, and chapters keep citing the
  stale field.
- Do NOT treat this as a form you file away. It is a living input, not a
  deliverable.
- Do NOT use it in place of an
  [experiment contract](../GLOSSARY.md#experiment-contract). This profile sets
  project-level context and consequence. It does not freeze a single experiment's
  statistical plan — that is
  [templates/EXPERIMENT_CONTRACT.md](EXPERIMENT_CONTRACT.md).
- Do NOT let a half-filled profile block starting work at Tier 1. A profile with
  honest unknowns is worth more than one padded with invented certainty.

## Rigor-tier applicability

Required at every [stakes tier](../GLOSSARY.md#stakes-tier). It is the instrument
that *sets* the tier (field 21), so it cannot itself be tier-gated away.

- **Tier 1 (Exploratory):** one sitting, from what is already known. The five
  always-mandatory fields still get real answers; the rest may be `[unknown]`.
- **Tier 2 (Consequential) and Tier 3 (High-stakes/regulated):** fill it in full
  before the first frozen [experiment contract](EXPERIMENT_CONTRACT.md). Expect
  gaps in fields 10–13 (compute and budget) to become early [STOP CONDITION]s in
  their own right. Expect fields 3, 6, and 19 (criticality, privacy/residency,
  regulatory) to be read together as inputs to the chapter 13 threat-model review
  before anything ships.

## Chapter key

Each field's "Consumes in" line names the chapters waiting on that answer, by
number.

| # | Chapter | # | Chapter |
|---|---|---|---|
| 00 | [Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md) | 08 | [Retrieval, Tools, Workflows and Routing](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md) |
| 01 | [Project Intake and Decision Context](../01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) | 09 | [Training and Data](../09_TRAINING_AND_DATA.md) |
| 02 | [Execution System Model](../02_EXECUTION_SYSTEM_MODEL.md) | 10 | [Deployment and Operations](../10_DEPLOYMENT_AND_OPERATIONS.md) |
| 03 | [Evaluation Foundation](../03_EVALUATION_FOUNDATION.md) | 11 | [Economics, Hardware and Cloud](../11_ECONOMICS_HARDWARE_AND_CLOUD.md) |
| 04 | [Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md) | 12 | [Observability, Learning and Promotion](../12_OBSERVABILITY_LEARNING_AND_PROMOTION.md) |
| 05 | [Model, Runtime and Harness Selection](../05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md) | 13 | [Governance, Provenance and Security](../13_GOVERNANCE_PROVENANCE_AND_SECURITY.md) |
| 06 | [Inference Performance and Capacity](../06_INFERENCE_PERFORMANCE_AND_CAPACITY.md) | 14 | [Decision Trees and Checklists](../14_DECISION_TREES_AND_CHECKLISTS.md) |
| 07 | [Optimization and Intervention Ladder](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md) | | |

## 1. Business outcome

*Asks:* What business or mission outcome does this system serve? State it as a
decision it drives or a result it produces, not as a thing you are building.
*Why it matters:* Every quality bar, budget, and rigor decision downstream hangs
off this one answer. A project that cannot say what decision its evidence drives
has no way, months later, to settle whether it worked.
*Consumes in:* 00, 01, 14.

**Value:** `[...]`
*Specimen: "Cut median time-to-resolution on tier-1 support tickets by 30% by Q3."
Not: "Build a support chatbot" — that names an activity, and no result follows
from it.*

## 2. Task population & volume

*Asks:* What is the space of tasks the system handles, and how many arrive per
day, week, or month? Give peak as well as average.
*Why it matters:* An evaluation corpus has to represent this space or it measures
something else. The volume numbers drive capacity and concurrency planning, and
per-request unit economics.
*Consumes in:* 03, 04, 06, 11.

**Value:** `[...]`
*Specimen: "Inbound quote requests, English and German, roughly 40 kinds of line
item; ~2,000/week average, ~6,000 in the last week of a quarter." Give a range
rather than one guessed number — how wide the range is, is itself information.*

## 3. Criticality / failure cost

*Asks:* When the system is wrong, what happens — to whom, and at what cost,
financial or safety or reputational or purely internal? Answer once per kind of
wrong.
*Why it matters:* The primary input to the [stakes tier](../GLOSSARY.md#stakes-tier)
(field 21) and to every
[consequence-bearing tolerance](../GLOSSARY.md#consequence-bearing-tolerance) you
set later. Mandatory at every tier.
*Consumes in:* 00, 03, 04, 13.

**Value:** `[...]`
*Specimen: "Wrong-but-obvious: the reviewer spots it and re-runs, costing a
minute. Wrong-and-plausible: an incorrect part ships, and the return costs about
$400. Missed-urgent: a safety-flagged item sits in the normal queue overnight." One
line per class; "wrong but harmless" and "wrong and acted on" are priced
differently inside one system.*

## 4. Quality/reliability target

*Asks:* What bar must the system clear, and does it have to clear it
*repeatedly*? "Right once" and "right five times running" are different claims and
need different evidence.

**Sub-prompt — behavioral compatibility.** If this system replaces or sits inside
a process people run today, say explicitly whether matching how those people
behave is itself a requirement (required / not required, and why). A deviation can
be adjudicated correct and still cost you: reviewers have to recognize the
reasoning, or a downstream step assumes the incumbent's shape. Where that is true,
compatibility is required. This one declaration decides whether a human-agreement
floor is a promotion **gate** or only a diagnostic (chapter 10 §5).

*Why it matters:* Sets the qualification-gate threshold, and decides whether
[pass^k](../GLOSSARY.md#pass-at-k-vs-pass-to-the-k) reliability claims apply
rather than a single-shot pass rate. The compatibility declaration routes the
human-baseline shadow gate (10 §5–§6). Mandatory at every tier.
*Consumes in:* 03, 04.

**Value:** `[...]`
*Specimen: "≥92% of extractions exactly match the gold record on the qualification
suite. Runs unattended overnight, so reliability under repetition counts:
pass^5 on a declared 200-item core subset. Behavioral compatibility: not required
— reviewers grade the output, not the method." State the bar as a rate against a
named instrument, and say out loud whether repeated-attempt reliability is part of
the claim.*

## 5. Latency/throughput/SLA

*Asks:* How fast per request, at which percentile, at what sustained volume — and
is any of it contractual?
*Why it matters:* Selects the [operating point](../GLOSSARY.md#operating-point),
and rules runtimes and hardware in or out before any quality comparison starts.
*Consumes in:* 05, 06, 11.

**Value:** `[...]`
*Specimen: "Interactive path: p95 under 4s, p99 under 9s. Nightly batch: 50,000
documents inside a six-hour window. No external SLA." Give a percentile; a mean
hides the tail people actually complain about.*

## 6. Privacy/security/data residency

*Asks:* Where may this data live, where must it never go, and what rules cover
personal or sensitive material?
*Why it matters:* Filters which
[execution surfaces](../GLOSSARY.md#execution-surface) — managed API, self-hosted,
local — are admissible at all, before any capability comparison starts. Doing this
first is the cheap check that stops you evaluating four models and then finding the
winner has no endpoint you are allowed to use. Mandatory at every tier.
*Consumes in:* 05, 10, 13.

**Value:** `[...]`
*Specimen: "Claim documents may not leave the EU. No raw customer PII in any
third-party API call; pseudonymized IDs are acceptable. 30-day retention cap on
anything stored outside the claims system." Name the rule. "Privacy matters"
eliminates nothing.*

## 7. Data & knowledge availability

*Asks:* What reference material, knowledge sources, and known-correct answers
already exist? How current and how complete are they?
*Why it matters:* Bounds
[evidence reachability](../GLOSSARY.md#evidence-reachability) — whether the system
can actually get to the facts an answer needs — and later bears on whether a target
skill plausibly sits in training data at all.
*Consumes in:* 03, 08, 09.

**Value:** `[...]`
*Specimen: "Product manuals in a wiki, current, ~1,200 pages. Pricing rules in a
spreadsheet one person maintains, roughly a quarter stale. No labeled
question/answer pairs anywhere." "Scattered and six months stale" is a different
project from "current and centrally maintained" — say which one you have.*

## 8. Tool/action permissions

*Asks:* What may the system call or do, and at what privilege — read only, or
write and mutate?
*Why it matters:* Defines the [tool contract](../GLOSSARY.md#tool-contract) surface
and the blast radius of the prompt-injection threat model.
*Consumes in:* 08, 13.

**Value:** `[...]`
*Specimen: "Read-only: document search, order lookup. Write, behind human
approval: draft a reply into the ticket. No direct customer contact, no financial
actions." One line per class, with its privilege — "read-only document search" and
"can issue refunds" are entirely different projects.*

## 9. Model candidates

*Asks:* Which model families, sizes, or execution surfaces are under
consideration, and why each one?
*Why it matters:* Seeds the [execution system](../GLOSSARY.md#execution-system)
definition and the bounded candidate set that runtime/harness selection screens.
*Consumes in:* 02, 05, 09.

**Value:** `[...]`
*Specimen: "One mid-size open-weights model — it fits the GPU we already own. One
managed API on an existing contract — no procurement lead time. One small model as
a possible cheap tier in a cascade." A shortlist with reasons beats a single
pre-committed choice; selection happens in chapter 05, not at intake.*

## 10. Owned compute

*Asks:* What hardware is already available at zero marginal cost?
*Why it matters:* The floor input to the rent-vs-buy decision and to capacity
planning.
*Consumes in:* 06, 11.

**Value:** `[...]`
*Specimen: "Two workstation-class GPUs, 24 GB each, shared with the analytics
team — realistically we get one of them, weekday evenings." Contended capacity is
not dedicated capacity, so say which you have.*

## 11. Rentable compute

*Asks:* What rented or cloud compute can you get on demand, and on what terms?
*Why it matters:* The alternative supply that the
[demand ledger](../GLOSSARY.md#demand-ledger) weighs against ownership.
*Consumes in:* 11.

**Value:** `[...]`
*Specimen: "On-demand single-GPU instances through the existing cloud account,
secure tier only — community and preemptible providers are not approved for this
data." Note the tier if you know it; it changes both the cost and what data may
run there.*

## 12. Managed APIs

*Asks:* Which vendor APIs are under consideration or already contracted, and
under what quotas and rate limits?
*Why it matters:* A managed API is an
[execution surface](../GLOSSARY.md#execution-surface) with different provenance,
reproducibility, and cost properties from anything you host yourself — you cannot
stop a provider redeploying underneath you.
*Consumes in:* 05, 11.

**Value:** `[...]`
*Specimen: "One general-purpose vendor, existing enterprise contract, 500
requests/minute. A second vendor would need a fresh security review — treat as
unavailable this quarter." The contract status and the rate limit both decide what
chapter 05 can actually screen.*

## 13. Capex budget

*Asks:* What one-time capital is already approved for buying hardware, if any?
*Why it matters:* An input to the
[purchase trigger](../GLOSSARY.md#purchase-trigger). Capital committed before a
trigger fires is precisely the anti-pattern chapter 11 exists to prevent.
*Consumes in:* 11.

**Value:** `[...]`
*Specimen: "None pre-approved. A capex request is possible at the next quarterly
planning cycle and would need a written justification." Write "none" out loud if
that is the truth — an unstated budget gets silently assumed to be "whatever it
takes".*

## 14. Recurring budget

*Asks:* What is the ongoing monthly ceiling for inference, API, and cloud spend?
*Why it matters:* Bounds the operating point and any routing
[break-even](../GLOSSARY.md#break-even) calculation. Once the system ships, this
number usually becomes a consequence-bearing tolerance in its own right.
*Consumes in:* 08, 11.

**Value:** `[...]`
*Specimen: "$1,200/month all-in, reviewed quarterly; anything above $1,500 needs
the department head's sign-off." A number with a period attached, not "keep it
cheap".*

## 15. Utilization/growth expectations

*Asks:* What sustained usage do you expect, and on what growth curve?
*Why it matters:* The forward-looking input the demand ledger needs to tell a busy
fortnight apart from sustained fleet demand. Only the second one buys hardware.
*Consumes in:* 11.

**Value:** `[...]`
*Specimen: "Flat at current volume for two quarters, then roughly 3x if the second
business unit adopts it — that decision is expected in March." "Flat for N months"
and "3x by <date>" send the purchase-trigger arithmetic in different directions.*

## 16. Staffing/time

*Asks:* Who is doing this work, at what fraction of their time, over what horizon?
*Why it matters:* Sets what rigor is executable rather than merely desirable. A
Tier-2 artifact set assumed onto nobody's calendar produces theater, not rigor.
*Consumes in:* 00, 01.

**Value:** `[...]`
*Specimen: "One engineer at ~40% for ten weeks; one domain reviewer for two hours
a week to adjudicate labels." Headcount alone is not an answer; the allocation and
the horizon are the parts that bind.*

## 17. Deployment environment

*Asks:* Where does the system actually run in production — cloud, on-prem, edge,
embedded — and under what orchestration?
*Why it matters:* Shapes [execution-system](../GLOSSARY.md#execution-system)
pinning and the operational-handoff document a future operator will need.
*Consumes in:* 02, 10.

**Value:** `[...]`
*Specimen: "Containerized service in the company's own cloud account behind SSO,
plus a nightly batch job on the same cluster. Development happens on laptops,
which is not the target." Name the production environment, not the one you build
in, whenever they differ.*

## 18. Observability constraints

*Asks:* What telemetry and logging are you permitted to collect, and how long may
you keep it?
*Why it matters:* Bounds what the
[telemetry floor](../GLOSSARY.md#telemetry-floor) and the
[trajectory record](../GLOSSARY.md#trajectory-record) can capture. Post-run
forensics cannot be retrofitted onto data nobody was allowed to collect.
*Consumes in:* 12.

**Value:** `[...]`
*Specimen: "May log prompts, retrieved document IDs, latencies and token counts,
90-day retention. Hard prohibition: no free-text customer content in logs, and no
user identity beyond an internal hashed ID." Keep hard prohibitions separate from
soft preferences — only one of the two is negotiable later.*

## 19. Regulatory/compliance

*Asks:* Which regulatory regimes or audit requirements apply — or plausibly will,
within this system's lifetime?
*Why it matters:* Can force Tier 3 on its own, whatever the other fields say.
Mandatory at every tier.
*Consumes in:* 00, 13.

**Value:** `[...]`
*Specimen: "None identified today. Legal has flagged that transparency obligations
would apply if this ever touched hiring decisions; it does not currently." Write
"none identified" explicitly. A blank here reads as "checked, none apply" when it
usually means nobody looked.*

## 20. Existing evidence

*Asks:* What prior evaluations, incumbent-system metrics, or production logs
already exist? And — the half that gets skipped — **is there an incumbent or
automated system already doing this job, and what are its observed failures?** If
there is none, say so in words.
*Why it matters:* Seeds the baseline, and where nothing exists it licenses chapter
01's [cold-start parameterization](../01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md)
procedure — borrowed priors, calibration pilot. This is also the single field
[QUICKSTART](../QUICKSTART.md)'s routing reads to decide whether an incumbent
exists and is failing its own quality bar (→ Archetype C). There is no separate
"existing system" field: incumbent identity and its failures live here, not in
field 9's model candidates.
*Consumes in:* 01, 03, 07.

**Value:** `[...]`
*Specimen: "A rules engine has routed these tickets since 2023. Nobody has ever
scored it. Support leads say it misroutes anything mentioning two products, which
they put at roughly one in ten. No eval set exists, and no logs are kept beyond 30
days." Notice what that settles: an incumbent nobody has ever measured is a
different profile from no incumbent at all, and "none, only ad hoc anecdote" is
itself load-bearing for the cold-start procedure.*

## 21. Stakes / consequence tolerance

*Asks:* Which [stakes tier](../GLOSSARY.md#stakes-tier) does this project's
riskiest decision sit at, and why?
*Why it matters:* Drives the [rigor dial](../GLOSSARY.md#rigor-dial) — the set of
artifacts QUICKSTART will make mandatory. Mandatory at every tier.
*Consumes in:* 00, 01, 04, 14.

Tier definitions (summarized from chapter 00 §6 — that chapter is normative if
this summary and it ever disagree):

| Tier | Signature | Adds on top of the never-skippable floor |
|---|---|---|
| **1 — Exploratory** | Internal, reversible, low blast radius | Lightweight profile; notes-grade pinned provenance; smoke-scale evals for direction only |
| **2 — Consequential** (default) | Business decisions, customer-visible behavior | Frozen experiment contracts; versioned suites + integrity gates; MDE/effective-N + INCONCLUSIVE; look ledger; prediction ledger; demand ledger before purchases |
| **3 — High-stakes / regulated** | Safety, money movement, compliance, audit | Tamper-evident record of record; security/threat-model review; pass^k reliability claims; judge calibration; shadow→canary with human approval; rehearsed rollback; periodic methodology audit |

**Value:** `[...]`
*Specimen: "Tier 2. Field 3: a misrouted claim delays a customer payment, which is
customer-visible and tracked. Field 19 found no regulator. Not Tier 3 — no money
moves without a human in the loop." Name the tier and the field(s) that put it
there, usually 3, 6, or 19. Two rules settle most arguments: when two fields point
at different tiers the higher one wins, and rigor attaches to the riskiest
DECISION this project makes rather than to the project's prestige — a Tier-1
project that starts shipping to production escalates that one decision to
Tier-2/3 artifacts.*

## Derived outputs

*Filled in after intake, by running [QUICKSTART](../QUICKSTART.md). This section is
the profile's output — not another question to answer from scratch.*

- **Archetype:** `[...]` *(the QUICKSTART route this profile matches, and which
  fields triggered it — e.g. "greenfield, managed-API-only", "local/private
  deployment mandate", "cost reduction of an existing API-heavy system")*
- **Stakes tier:** `[...]` *(1 / 2 / 3, from field 21)*
- **Mandatory artifact set:** `[...]` *(the templates and gates this tier requires,
  per chapter 00 §6 and QUICKSTART's per-archetype table)*
- **First three actions:** `1. [...]` `2. [...]` `3. [...]`

## Completing this template

Delete no section. Every numbered field must appear in the filled document, in
order — chapters cite these fields by number, so the numbering is part of the
interface. If a field genuinely does not apply, write `N/A — <reason>` in its Value
line instead of removing it. Absence is a decision, and a later reader needs to see
that it was made rather than skipped.

## Miniature example

*Illustrative example — synthetic. All names and numbers invented.*

**Project: "Ask-the-Handbook"** — an internal assistant answering employee
questions from HR/IT policy documents.

1. Business outcome: cut average HR/IT question-to-answer time; ≥40% of routine
   questions answered without a human ticket.
2. Task population & volume: ~600 employee questions/week, English only, drawn
   from ~300 policy documents.
3. Criticality/failure cost: a wrong policy answer causes confusion and an
   occasional re-ticket; no safety or financial exposure identified.
4. Quality/reliability target: ≥90% judged correct-and-cited on sampled human
   review; single-shot, no pass^k requirement. Behavioral compatibility with how
   HR staff currently answer: not required.
5. Latency/throughput/SLA: p95 < 5s; ~20 concurrent users at peak.
6. Privacy/security/data residency: internal documents only, no customer PII;
   must stay inside the company's cloud tenant.
7. Data & knowledge availability: policy docs current and centrally maintained;
   no existing QA pairs.
8. Tool/action permissions: read-only document retrieval; no write actions.
9. Model candidates: one self-hosted mid-size open-weights model vs. one
   existing-contract managed API; final choice deferred to chapter 05.
10. Owned compute: one shared GPU workstation, already owned, contended with
    other teams.
11. Rentable compute: on-demand GPU rental available if a pilot needs it.
12. Managed APIs: one general-purpose vendor API under an existing contract.
13. Capex budget: none pre-approved this quarter.
14. Recurring budget: < $300/month inference spend.
15. Utilization/growth: flat for ~6 months; no growth commitment yet.
16. Staffing/time: 1 engineer, ~20%, 6 weeks.
17. Deployment environment: internal web app behind company SSO, company cloud.
18. Observability constraints: may log queries and retrieved documents; no raw
    employee identity beyond an internal user ID.
19. Regulatory/compliance: none identified — internal policy only.
20. Existing evidence: none; only ad hoc answers from HR staff in chat. No
    incumbent automated system.
21. Stakes/consequence tolerance: **Tier 1** at intake (field 3: low failure
    cost, reversible); HR has flagged it may escalate to Tier 2 if the assistant
    starts driving policy decisions rather than just answering questions.

Derived outputs — **Archetype:** RAG document-QA, greenfield, managed-API
candidate in the mix. **Stakes tier:** 1, escalate to 2 on policy-decision use.
**Mandatory artifacts:** lightweight profile + notes-grade provenance +
smoke-scale eval only. **First three actions:** (1) build a ~30-item eval set
from real HR questions, (2) run a frontier-saturation check before trusting it,
(3) pilot both model candidates against it.

## Governing chapters

- Primary: [01. Project Intake and Decision Context](../01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md)
  — where this template is introduced and the archetype/rigor-tier routing runs.
- The rigor-tier table in field 21 is normatively owned by
  [00. Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md) §6.
- Every other chapter consumes specific fields only — see each field's
  "Consumes in" line and the [chapter key](#chapter-key) above.
- Next step after filling this in: [QUICKSTART](../QUICKSTART.md) routes it to an
  archetype, a stakes tier, and a first-three-actions list.

---

[Index](../README.md) · [Quickstart](../QUICKSTART.md) · [Glossary](../GLOSSARY.md)
