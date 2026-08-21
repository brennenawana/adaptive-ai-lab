# Project Profile

> Structured intake for a new AI-system project or workstream: the ~20-field
> questionnaire that [QUICKSTART](../QUICKSTART.md) routes on and the
> [rigor dial](../GLOSSARY.md#rigor-dial) calibrates from.
>
> Index: [../README.md](../README.md) · Governing chapter:
> [01. Project Intake and Decision Context](../01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md)

## When to use / when not to

- Use at the start of any new AI-system project or workstream — before a model,
  runtime, or architecture is chosen. Filling it in is the first action this
  playbook asks for.
- Use whenever a live project's outcome, constraints, or stakes change materially
  (new regulatory scope, a budget change, a latency requirement that tightens,
  data residency changing) — revise the profile and re-run the
  [archetype](../GLOSSARY.md#archetype)/tier routing; do not let the original
  intake silently go stale.
- Do NOT treat this as a one-time form filed away and forgotten — it is a living
  input, not a deliverable.
- Do NOT use it as a substitute for an [experiment contract](../GLOSSARY.md#experiment-contract).
  This profile sets project-level context and consequence; it does not freeze a
  single experiment's statistical plan (that is
  [templates/EXPERIMENT_CONTRACT.md](EXPERIMENT_CONTRACT.md)).
- Do NOT let a partially-filled profile block starting work at Tier 1 — fields you
  cannot yet answer are written `[unknown — <what would resolve it>]`, not left
  blank; a profile with honest unknowns is more useful than one padded with
  invented certainty.

## Rigor-tier applicability

Required at every [stakes tier](../GLOSSARY.md#stakes-tier) — it is the instrument
that *determines* the tier (field 21), so it cannot itself be tier-gated away.

- **Tier 1 (Exploratory):** fill it in a single sitting from what is already known;
  gaps are acceptable if labeled `[unknown]`.
- **Tier 2 (Consequential) and Tier 3 (High-stakes/regulated):** fill it in full
  before the first frozen [experiment contract](EXPERIMENT_CONTRACT.md); expect
  gaps in fields 10–13 (compute and budget) to become early
  [STOP CONDITION]s in their own right, and expect fields 3, 6, and 19
  (criticality, privacy/residency, regulatory) to be read together as inputs to
  the chapter 13 threat-model review before anything ships.

## Chapter key

Referenced by number in each field's "Consumes in" line below.

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

*Asks:* What business or mission outcome does this system serve, stated as a
decision or result it drives — not a feature description.
*Why it matters:* Every quality bar, budget, and rigor decision downstream is
meaningless without a decision to serve; "what decision will this evidence
drive?" is this playbook's first question of any work item.
*Consumes in:* 00, 01, 14.

**Value:** `[...]`
*State it as a decision or measurable result ("cut resolution time for X by Y",
"replace incumbent system Z"), not a technology description ("build a chatbot").*

## 2. Task population & volume

*Asks:* What is the space of tasks/items the system handles, and how many per
day/week/month (with peak vs average)?
*Why it matters:* Bounds eval-corpus sampling design, capacity/concurrency
planning, and per-request unit economics.
*Consumes in:* 03, 04, 06, 11.

**Value:** `[...]`
*Describe the task space (languages, domains, item types) and give a volume range,
not a single guessed number — the range itself is information.*

## 3. Criticality / failure cost

*Asks:* What happens when the system is wrong, per failure class — who is
affected and at what cost (financial, safety, reputational, purely internal)?
*Why it matters:* The primary input to the [stakes tier](../GLOSSARY.md#stakes-tier)
(field 21) and to every [consequence-bearing tolerance](../GLOSSARY.md#consequence-bearing-tolerance)
set later.
*Consumes in:* 00, 03, 04, 13.

**Value:** `[...]`
*Enumerate failure classes separately — "wrong but harmless" and "wrong and
actionable" carry different costs even inside one system.*

## 4. Quality/reliability target

*Asks:* What is the quality bar, and does reliability *under repetition* matter
(a single good answer vs. the same answer holding up across retries)?
**Sub-prompt — behavioral compatibility:** if the system replaces or sits inside
an existing human process, state explicitly whether *behavioral compatibility /
human-process interchangeability is itself a requirement* (required / not
required, and why). Deviations that are adjudicated-correct but operationally or
safety-costly — reviewers must recognize the reasoning, downstream steps assume
the incumbent's shape — make it required. This declaration is what decides
whether a human-agreement floor is a promotion **gate** or only a diagnostic
(chapter 10 §5).
*Why it matters:* Sets qualification-gate thresholds and whether
[pass^k](../GLOSSARY.md#pass-at-k-vs-pass-to-the-k) reliability claims apply, as
opposed to single-shot pass rate; the compatibility declaration routes the
human-baseline shadow gate (10 §5–§6).
*Consumes in:* 03, 04.

**Value:** `[...]`
*State the bar as a measurable rate against a named instrument ("≥X% on the
qualification suite"), and say explicitly whether repeated-attempt reliability is
part of the claim.*

## 5. Latency/throughput/SLA

*Asks:* Per-request latency ceiling (and at what percentile), required sustained
throughput, and any contractual SLA.
*Why it matters:* Selects the [operating point](../GLOSSARY.md#operating-point)
and materially shapes runtime and hardware choice.
*Consumes in:* 05, 06, 11.

**Value:** `[...]`
*Give a percentile, not just a mean ("p95 < Xs"), and separate interactive
latency needs from batch/offline throughput needs if both exist.*

## 6. Privacy/security/data residency

*Asks:* Where may data live, where must it never leave, and what PII/sensitive-data
handling rules apply?
*Why it matters:* Filters which [execution surfaces](../GLOSSARY.md#execution-surface)
(managed API vs. self-hosted vs. local) are even admissible, before any
capability comparison starts.
*Consumes in:* 05, 10, 13.

**Value:** `[...]`
*Name the specific constraint (e.g., "must not leave the deployed region",
"no raw customer PII in any third-party API call"), not just "privacy matters".*

## 7. Data & knowledge availability

*Asks:* What reference material, knowledge sources, and existing ground truth
exist, and how current/complete are they?
*Why it matters:* Bounds [evidence reachability](../GLOSSARY.md#evidence-reachability)
for retrieval design and, later, whether training data plausibly contains a
target skill.
*Consumes in:* 03, 08, 09.

**Value:** `[...]`
*Note freshness and coverage gaps explicitly — "current, centrally maintained" is
a different input than "scattered, six months stale".*

## 8. Tool/action permissions

*Asks:* What external tools or actions may the system invoke, and at what
privilege (read-only vs. write/mutate)?
*Why it matters:* Defines the [tool contract](../GLOSSARY.md#tool-contract) surface
and the scope of the prompt-injection threat model.
*Consumes in:* 08, 13.

**Value:** `[...]`
*List each tool/action class and its privilege level separately; "read-only
document search" and "can issue refunds" are different profiles entirely.*

## 9. Model candidates

*Asks:* Which model families/sizes/execution surfaces are under consideration,
and why those?
*Why it matters:* Seeds the [execution system](../GLOSSARY.md#execution-system)
definition and the bounded candidate set that runtime/harness selection screens.
*Consumes in:* 02, 05, 09.

**Value:** `[...]`
*A short list with the reason each candidate is in scope is more useful here than
a single pre-committed choice — selection happens in chapter 05, not at intake.*

## 10. Owned compute

*Asks:* What hardware is already owned or otherwise available at zero marginal
cost?
*Why it matters:* The floor input to the rent-vs-buy decision and to capacity
planning.
*Consumes in:* 06, 11.

**Value:** `[...]`
*State device class/count and how exclusively it is available to this project
(dedicated vs. shared/contended).*

## 11. Rentable compute

*Asks:* What rented/cloud compute is accessible on demand, and under what terms?
*Why it matters:* The alternative capacity source the
[demand ledger](../GLOSSARY.md#demand-ledger) weighs against ownership.
*Consumes in:* 11.

**Value:** `[...]`
*Note tier (secure vs. community/preemptible) if known — that distinction
matters for both cost and data-exposure policy.*

## 12. Managed APIs

*Asks:* Which vendor APIs are under consideration or already contracted, and
under what quotas/rate limits?
*Why it matters:* An [execution surface](../GLOSSARY.md#execution-surface) with
different provenance, reproducibility, and cost properties from self-hosted
options.
*Consumes in:* 05, 11.

**Value:** `[...]`
*Name the vendor relationship (existing contract vs. new) and any known rate
limits — both affect the candidate set chapter 05 can actually screen.*

## 13. Capex budget

*Asks:* What one-time capital is pre-approved for hardware purchase, if any?
*Why it matters:* An input to the [purchase trigger](../GLOSSARY.md#purchase-trigger)
— capital committed before a trigger fires is the anti-pattern chapter 11 exists
to prevent.
*Consumes in:* 11.

**Value:** `[...]`
*State "none pre-approved" explicitly if that is the truth — an unstated budget
tends to get silently assumed as "whatever it takes".*

## 14. Recurring budget

*Asks:* What is the ongoing monthly ceiling for inference/API/cloud spend?
*Why it matters:* Bounds the operating point and any routing
[break-even](../GLOSSARY.md#break-even) calculation.
*Consumes in:* 08, 11.

**Value:** `[...]`
*A number with a period ("$X/month"), not a vague "keep it cheap".*

## 15. Utilization/growth expectations

*Asks:* What sustained utilization is expected, and over what growth trajectory?
*Why it matters:* The forward-looking input the demand ledger needs to
distinguish transient busyness from sustained fleet demand.
*Consumes in:* 11.

**Value:** `[...]`
*Distinguish "flat for N months" from "expected to grow Nx by <date>" — the
purchase-trigger math depends on which.*

## 16. Staffing/time

*Asks:* Who is available to do this work, at what fraction of their time, over
what horizon?
*Why it matters:* Scales what rigor tier is realistically executable; a
Tier-2 artifact set assumed onto zero staffing produces theater, not rigor.
*Consumes in:* 00, 01.

**Value:** `[...]`
*State headcount, allocation, and horizon together ("1 engineer, ~30%, 8
weeks"), not just headcount.*

## 17. Deployment environment

*Asks:* Where does the system run in production — cloud/on-prem/edge/embedded,
and under what orchestration?
*Why it matters:* Shapes [execution-system](../GLOSSARY.md#execution-system)
pinning and the operational-handoff document a future operator needs.
*Consumes in:* 02, 10.

**Value:** `[...]`
*Name the actual target environment, not the dev/test environment, if they
differ.*

## 18. Observability constraints

*Asks:* What telemetry/logging is permitted, and for how long may it be
retained?
*Why it matters:* Bounds what the [telemetry floor](../GLOSSARY.md#telemetry-floor)
and [trajectory record](../GLOSSARY.md#trajectory-record) can capture.
*Consumes in:* 12.

**Value:** `[...]`
*State any hard prohibitions (e.g., "no raw user identity beyond an internal
ID") separately from soft preferences.*

## 19. Regulatory/compliance

*Asks:* What regulatory regimes or audit requirements apply (or plausibly will)?
*Why it matters:* Can force Tier 3 by itself, regardless of what the other
fields say.
*Consumes in:* 00, 13.

**Value:** `[...]`
*Write "none identified" explicitly rather than leaving this blank — silence
here is easy to mistake for "checked, none apply".*

## 20. Existing evidence

*Asks:* What prior evals, incumbent-system metrics, or production logs already
exist — including **any incumbent or automated system currently in use and its
observed failures** (if none, say so explicitly; do not leave this half of the
field unanswered because field 9's "model candidates" looks like the closer fit)?
*Why it matters:* Seeds the baseline and licenses the
[cold-start parameterization](../01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md)
procedure (borrowed priors, calibration pilot) when nothing exists yet. This is
also the single field [QUICKSTART](../QUICKSTART.md)'s routing reads to decide
whether an incumbent exists and is failing (→ Archetype C) — there is no separate
"existing system" field; incumbent identity and its observed failures live here.
*Consumes in:* 01, 03, 07.

**Value:** `[...]`
*If nothing exists, say so — "none, only ad hoc anecdote" is itself a load-bearing
fact for chapter 01's cold-start procedure. If an incumbent or automated system
does exist, name it and its observed failure modes explicitly, even if no formal
eval has scored it yet — "an incumbent exists but has never been measured" is a
different profile than "no incumbent exists."*

## 21. Stakes / consequence tolerance

*Asks:* Which [stakes tier](../GLOSSARY.md#stakes-tier) does this project's
riskiest decision sit at, and why?
*Why it matters:* Drives the [rigor dial](../GLOSSARY.md#rigor-dial) — the
mandatory-artifact set QUICKSTART assigns.
*Consumes in:* 00, 01, 04, 14.

Tier definitions (summarized from chapter 00 §6 — that chapter is normative if
this summary and it ever disagree):

| Tier | Signature | Adds on top of the never-skippable floor |
|---|---|---|
| **1 — Exploratory** | Internal, reversible, low blast radius | Lightweight profile; notes-grade pinned provenance; smoke-scale evals for direction only |
| **2 — Consequential** (default) | Business decisions, customer-visible behavior | Frozen experiment contracts; versioned suites + integrity gates; MDE/effective-N + INCONCLUSIVE; look ledger; prediction ledger; demand ledger before purchases |
| **3 — High-stakes / regulated** | Safety, money movement, compliance, audit | Tamper-evident record of record; security/threat-model review; pass^k reliability claims; judge calibration; shadow→canary with human approval; rehearsed rollback; periodic methodology audit |

**Value:** `[...]`
*Name the tier and the specific field(s) above that put it there (usually 3, 6,
or 19). Remember: rigor attaches to the riskiest DECISION this project makes, not
to the project's overall prestige — a Tier-1 project that starts shipping to
production escalates that one decision to Tier-2/3 artifacts.*

## Derived outputs

*Filled in after intake, using [QUICKSTART](../QUICKSTART.md) — this section is
the profile's output, not another question to answer from scratch.*

- **Archetype:** `[...]` *(the QUICKSTART route this profile matches, and which
  fields above triggered it — e.g., "greenfield, managed-API-only", "local/private
  deployment mandate", "cost reduction of an existing API-heavy system")*
- **Stakes tier:** `[...]` *(1 / 2 / 3, from field 21)*
- **Mandatory artifact set:** `[...]` *(the templates and gates this tier
  requires, per chapter 00 §6 and QUICKSTART's per-archetype table)*
- **First three actions:** `1. [...]` `2. [...]` `3. [...]`

## Completing this template

Delete no section. Every numbered field above must appear in the filled
document, in order. If a field genuinely does not apply to this project, write
`N/A — <reason>` in its Value line rather than removing the field — absence is a
decision, and downstream chapters and reviewers need to see that it was
considered, not omitted.

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
   review; single-shot, no pass^k requirement.
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
20. Existing evidence: none; only ad hoc answers from HR staff in chat.
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
- Next step after filling this in: [QUICKSTART](../QUICKSTART.md) routes it to
  an archetype, a stakes tier, and a first-three-actions list.

---

[Index](../README.md) · [Quickstart](../QUICKSTART.md) · [Glossary](../GLOSSARY.md)
