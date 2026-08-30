# Quickstart — The Project Navigator

> Part of the **Adaptive AI Systems Playbook** v0.1.1 ·
> [Index](README.md) · [Glossary](GLOSSARY.md) · [Principles](00_PRINCIPLES_AND_SCOPE.md)
> **Time:** about twenty minutes to a routed plan and your first three actions.

You have a project in front of you. Maybe an assistant that keeps getting things
wrong and nobody can say how often. Maybe an extraction pipeline that works and
costs too much. Maybe an empty repository and three weeks to show something.

Fifteen chapters is too many to read before you start. So this page does the
narrowing for you. Answer a set of questions about the project, and you get back a
short reading list, a small set of documents you have to produce, and three things
to do next.

The questions are about facts — what the project does, who it can hurt, what
already exists — not about which chapters look interesting. Answer them honestly
and the routing takes care of itself. Answer them the way you wish the project were
and you will get a plan for a different project.

Wherever you enter, **your first sprint ends in the same place**: one short
document, written before you run anything, that fixes what you are testing and what
you will do about each possible result. For most projects that document is a frozen
[experiment contract](GLOSSARY.md#experiment-contract) (Tier 2+). For the
lowest-stakes ones it is a written lightweight plan covering six obligations
(Tier 1). Step 2 tells you which. Everything below routes toward one of the two.

---

## Step 1 — Fill in the project profile (~10 minutes)

Copy [templates/PROJECT_PROFILE.md](templates/PROJECT_PROFILE.md) into your own
repository and answer its questions.

You will not be able to answer all of them yet. Write "unknown" and keep going. An
unknown routes too — usually toward chapter 01, which is the chapter about turning
a vague request into a stated decision.

The profile has many fields. Seven of them carry almost all of the routing weight,
and every question later on this page reads off one of them by number:

| Profile field (number and name) | Routing question it answers | Used at |
|---|---|---|
| **20** — Existing evidence (including any incumbent/automated system and its observed failures) | Do you already have a **trusted eval** for this task? Does an **incumbent** exist, and is it failing its own quality bar? | Step 3, nodes 1 and 2 |
| **1** — Business outcome | Is the goal **cost reduction** of an already-working system? Is the deliverable the lab capability itself? | Step 3, nodes 3 and 6 |
| **19** — Regulatory/compliance · **3** — Criticality / failure cost | Do **audit / reliability obligations dominate** the requirements? | Step 3, node 4 |
| **6** — Privacy/security/data residency · **17** — Deployment environment | Is a deployment **no managed API can satisfy** actually mandated? | Step 3, node 5 |
| **21** — Stakes / consequence tolerance | Which [rigor tier](GLOSSARY.md#stakes-tier) governs? | Step 2 |
| **4** — Quality/reliability target · **7** — Data & knowledge availability | Is output **objectively verifiable** or judge-graded? | Step 3, modifiers |
| **9** — Model candidates · **12** — Managed APIs | Will any comparison **cross execution surfaces** (machines, sessions, providers)? | Step 3, modifiers |

**You are done with this step when** every field has something written in it — even
if several of them say "unknown".

## Step 2 — Set the rigor tier

How much proof you owe is set by what happens when the system is wrong. That is the
only input. A demo nobody acts on and a tool that moves money need different amounts
of evidence, and the difference has nothing to do with how interesting the project
is. This proportionality is what the playbook calls the
[rigor dial](GLOSSARY.md#rigor-dial).

Read your tier off the profile's stakes field (field 21). The definitions are
normative and live in [00 §6](00_PRINCIPLES_AND_SCOPE.md).

| Tier | You are here if… | Mandatory artifacts (beyond the floor) |
|---|---|---|
| **1 — Exploratory** | internal, reversible, low blast radius — and no decision outside your own team rides on the results | lightweight profile; notes-grade pinned provenance; smoke-scale evals for direction only |
| **2 — Consequential** *(default)* | business decisions or customer-visible behavior ride on results | frozen contracts · versioned suites + integrity gates · MDE/effective-N + INCONCLUSIVE · look ledger · prediction ledger · demand ledger before purchases |
| **3 — High-stakes / regulated** | safety, money movement, compliance, audit | Tier 2 + tamper-evident record of record · threat-model review · pass^k reliability claims · judge calibration where judges used · shadow→canary with human approval · rehearsed rollback · periodic audit |

Two rules settle most of the arguments about which row applies.

- **A human reviewer does not buy you Tier 1.** Picture an internal drafting tool
  where a person reads and edits every output before it reaches anyone. That is
  still **Tier 2** if the output feeds a **tracked business metric** — throughput,
  resolution time, cost per case, a staffing or workflow decision. Review shrinks
  the blast radius of a single bad output. It does not remove the business decision
  riding on the aggregate result. Tier 1 is for work whose results drive no
  decision outside the team that produced them.
- **When two fields disagree, take the higher tier.** Field 3 says "purely
  internal" and field 19 names a regulator. Field 1 says "prototype" and the output
  is customer-visible. Both are common. Tier is set by the riskiest decision the
  project makes, so disagreement between fields resolves upward, not to the average.

Six obligations hold at every tier, Tier 1 included — the
[never-skippable floor](GLOSSARY.md#never-skippable-floor). State the decision and
the claim. Keep provenance sufficient to identify what produced a result. Define the
eval/ground-truth boundary before any quality claim. Predeclare consequences for
decision thresholds. Record how much held-out exposure has been spent. Retain
outcome evidence. They are
spelled out with their headings under
[Where your first sprint ends](#where-your-first-sprint-ends), at the bottom of this
page.

**Rule of proportion:** rigor attaches to the *decision*, not to the project. A
Tier-1 prototype making a ship-to-production decision escalates that decision to
Tier-2/3 artifacts.

**You are done with this step when** you have written down a tier number, and can
name in one sentence the decision that made it that number.

## Step 3 — Route to your archetype

Projects come in six shapes here, lettered A through F. The playbook calls one of
those shapes an [archetype](GLOSSARY.md#archetype). You get exactly one letter, and
it decides which three or four chapters you read first.

Read the tree from the top. Take the **first** branch whose condition is true, then
stop. Every condition is a fact from a numbered profile field — Step 1's table says
which. Node 1 is the exception to "stop at the first true branch": it adds a
prerequisite and then sends you onward. It never ends the walk.

```
1. PRE-CHECK — never terminal: it adds a prerequisite, it does not assign a letter.
   Trusted eval for this task exists?  (field 20)
   │  yes ──►  nothing to add
   │  no  ──►  note "eval first": chapter 03 comes before optimization and
   │           selection, whatever letter you land on
   ▼ either answer continues to 2
2. Incumbent AI/automated system exists AND is failing its own
   quality bar — or the gap has no trusted measurement?      ──yes──►  C  (fix-what-exists)
   ▼ no
3. Goal = cost reduction of a working system with an
   established, MEASURED quality bar?                        ──yes──►  D  (cost/routing)
   ▼ no
4. Regulatory / audit / reliability obligations dominate
   the requirements?                                         ──yes──►  E  (high-stakes)
   ▼ no
5. Privacy / residency / IP constraints mandate a deployment
   that NO managed API can satisfy — not even an in-tenant /
   VPC-scoped, no-retention configuration?                   ──yes──►  B  (local mandate)
   ▼ no
6. The deliverable is the evaluation/experimentation
   capability itself (a lab, not a product)?                 ──yes──►  F  (lab bootstrap)
   ▼ no
7.                                                                     A  (greenfield)
```

### Reading the contested nodes

Three of those conditions carry qualifiers. The qualifiers are part of the
condition, not commentary on it.

**Node 2 — what "failing its own quality bar" means.** Every system short of 100%
produces some observed failures. That alone is not archetype C. C fires when the
incumbent is missing an established bar, **or** when nobody can say whether it is,
because no trusted measurement of the gap exists.

Two exclusions follow, and both are common. An incumbent that demonstrably meets a
measured bar and is merely expensive is archetype **D**, not C. And a predecessor
tool you intend to **replace** with a differently-shaped system — rather than
diagnose and repair — is not the incumbent this node means, because there is nothing
to diagnose, only something to supersede. C is for the system you plan to keep and
fix.

**Node 4 sits before node 5 deliberately.** A regulated project frequently answers
yes to both. E's governance set is a strict superset of B's rigor, so a project that
is both routes to **E** — and carries its residency constraint with it, into the
admissible-execution-surface question in
[05 §5.2](05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md). B is for the case where the
deployment surface is the binding constraint and audit obligations are not.

**Node 5 — what "no managed API can satisfy" means.** Providers will run a model
inside your own cloud tenancy or VPC, with retention switched off. A residency or
confidentiality rule that such an endpoint *can* satisfy does **not** fire this node.
That rule is still real, and it still constrains which
[execution surfaces](GLOSSARY.md#execution-surface) are admissible — 05 §5.2's regime
criterion asks exactly this question. It does not decide that the model must run
self-hosted.

The node fires only when a **stated rule** — a contract, a law, a written policy —
would otherwise be violated. Discomfort, preference, and "it feels safer local" are
not mandates. If the applicable rule turns out to be genuinely unwritten, that
ambiguity is itself your first action: get it written, before it silently re-routes
your project.

### Then check two modifiers

These apply on top of whatever letter you landed on. Node 1's eval-first note is a
third, and it applies whatever the letter.

**Modifier 1 — your outputs are judge-graded.** Fields 4 and 7 say the bar is
open-ended rather than objectively verifiable: the outputs are summaries, or
explanations, or drafts, and no script can mark them right or wrong. So you are
planning to have a model grade them.

Split the bar first. Parts of an open-ended output are usually still checkable by
code — the citation resolves, the length limit holds, the JSON parses. Deterministic
verification stays the default wherever any part of the output is checkable, and
every checkable dimension stays deterministic. A judge only handles what is left over.
For that remainder:

- **Tier 2+:** add the judge-calibration protocol
  ([03 §5.7](03_EVALUATION_FOUNDATION.md), `doctrine — not yet exercised`) to your
  mandatory set *before* any quality claim. Record the calibrated judge as the
  contract's scorer/verifier identity **before** the contract freezes. An
  uncalibrated judge cannot be a frozen scorer.
- **Tier 1:** do **not** put a judge on an adoption decision —
  [03 §6](03_EVALUATION_FOUNDATION.md) is explicit about this. Use human
  spot-grading instead: a small dual-labelled sample, with disagreements
  adjudicated. Keep any judged score for direction only.
- Wherever a paired outcome feeds an [oracle analysis](GLOSSARY.md#oracle-analysis)
  or a cascade study, gate its judged dimensions through this modifier *before* you
  trust the oracle ceiling. An uncalibrated judge produces a silently wrong ceiling
  that looks like evidence.

**Modifier 2 — you plan a comparison that crosses machines, sessions, or
providers.** Fields 9 and 12 are where this shows up. Read chapter 02 **now**,
before trusting any number from such a comparison: comparability claims may not
cross an unmeasured
[reproducibility boundary](GLOSSARY.md#reproducibility-boundary). This pulls 02
forward into any archetype's entry path, not only B's.

**You are done with this step when** you have one letter and a list of the modifiers
that fired.

## Step 4 — Your route

Find your letter below and read only that block. Each one gives you the chapters to
open, the chapters you may leave closed for now, the documents you owe, and three
actions you can start today.

The three actions are written at Tier 2. Tier 1 substitutions are in the rules that
follow the six blocks.

### A — Greenfield, API-models-only

*Nothing in the tree fired. You are building something new, and managed models are
allowed.*

- **Read first:** [01](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) →
  [03](03_EVALUATION_FOUNDATION.md) →
  [04](04_EXPERIMENT_DESIGN_AND_STATISTICS.md)
- **Typically skippable at start:** 06, 09, 11-hardware (keep 11-API-economics)
- **Mandatory templates:** PROJECT_PROFILE · EXPERIMENT_CONTRACT · TEST_LOOK_LEDGER ·
  PREDICTION_LEDGER
- **First three actions:**
  1. Fill the profile. State the decision each evidence item will drive.
  2. Derive the task ontology from real traces or tickets (03 §5.1). Draft the first
     eval set with measured ceilings (03 §5.5).
  3. Freeze the first contract: 2–4 candidate models, one factor,
     [MDE](GLOSSARY.md#mde) stated — the smallest true difference the design can
     detect — and the scorer/verifier identity named. A judge may only be named once
     calibrated; see modifier 1.

### B — Local / private deployment mandate

*A written rule says the model cannot run on someone else's infrastructure, in any
configuration.*

- **Read first:** [01](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) →
  [02](02_EXECUTION_SYSTEM_MODEL.md) → [03](03_EVALUATION_FOUNDATION.md), then 06
  early
- **Typically skippable at start:** 09 until the ladder reaches it; 10 until a
  candidate exists
- **Mandatory templates:** A's set + COMPUTE_DEMAND_LEDGER · OPERATIONAL_HANDOFF
- **First three actions:**
  1. Fill the profile, residency constraints included. Pick the runtime **regime**
     (05 §5.2) — not a runtime.
  2. Pin the first execution-system identity and run the reproducibility-boundary
     probes (02). Run the **capacity fit probe** — context length plus generation cap
     against accelerator memory — per
     [06 §5.2.D](06_INFERENCE_PERFORMANCE_AND_CAPACITY.md) and 06 §8.
  3. Build the eval substrate (03) against the pinned identity, then freeze the first
     contract.

### C — Existing system underperforming

*Something is already running, and it is missing its bar — or nobody can prove
either way.*

- **Read first:** [01](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) →
  [03](03_EVALUATION_FOUNDATION.md) (eval first!) →
  [07](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md)
- **Typically skippable at start:** 05 — selection is premature until diagnosis
- **Mandatory templates:** A's set + PERFORMANCE_AUTOPSY
- **First three actions:**
  1. Do **not** change the system yet. Build and validate the eval from harvested
     failures (03; error-analysis-first).
  2. Diagnose. Classify the observed failures into the
     [taxonomy](GLOSSARY.md#canonical-failure-taxonomy) (03 §5.2) — instrument
     defects first.
  3. Pick the highest applicable ladder rung with a cheap
     [diagnostic gate](GLOSSARY.md#diagnostic-gate) (07). Freeze the contract for
     that intervention.

### D — Cost reduction of an API-heavy system

*It works, at a quality bar somebody actually measured. It costs too much.*

- **Read first:** [01](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) →
  [08](08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md) →
  [11](11_ECONOMICS_HARDWARE_AND_CLOUD.md) — **plus
  [02](02_EXECUTION_SYSTEM_MODEL.md) first whenever the candidate tiers span
  execution surfaces or providers**, which a cascade normally does. (08's own
  prerequisites are 00, 02, 03, 07.)
- **Typically skippable at start:** 09; and 03 only to *verify* eval trust — if the
  bar is not actually measured, you are archetype C
- **Mandatory templates:** A's set + COMPUTE_DEMAND_LEDGER
- **First three actions:**
  1. Verify the quality bar is real: a trusted eval plus a measured baseline. If it
     is not, re-route to C.
  2. Run [oracle analysis](GLOSSARY.md#oracle-analysis) and
     [break-even](GLOSSARY.md#break-even) (08/11) before building any router. If any
     paired outcome depends on judged rather than deterministic scoring, gate it
     through modifier 1 first.
  3. Design the cascade with a
     [deterministic gate](GLOSSARY.md#deterministic-gate) if a verifier exists.
     Freeze the routing experiment contract with a per-arm execution-system identity.

### E — High-stakes / compliance-bound

*Safety, money movement, or an auditor is in the picture, and those obligations
dominate the requirements.*

- **Read first:** [01](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) →
  [13](13_GOVERNANCE_PROVENANCE_AND_SECURITY.md) →
  [03](03_EVALUATION_FOUNDATION.md) →
  [04](04_EXPERIMENT_DESIGN_AND_STATISTICS.md)
- **Typically skippable at start:** nothing. Tier 3 curtails no chapter; 09 waits for
  the ladder like everyone else.
- **Mandatory templates:** the full Tier-3 set (all nine templates), **plus the
  governance artifacts of 13 §12** — record of record, clean-room boundary document,
  license register, trajectory privacy-classification table, tool-calling threat
  model + permission-tier table, canary-string registry, eval-corpus regulated-data
  disposition record. Several of these have no dedicated template yet; instantiate
  them from 13 §11's tables (13 §12 says which).
- **First three actions:**
  1. Instantiate governance at intake: record of record, ground-truth isolation,
     threat model (13). Note that 13's redaction-pipeline and tool-threat-model
     procedures are labelled `doctrine — not yet exercised`, so budget time to
     validate them rather than assuming a proven recipe.
  2. Build the eval with per-stratum ceilings and forbidden-claim scoring (03). Plan
     pass^k for reliability claims.
  3. Freeze the first contract with consequence-bearing tolerances and
     human-approval gates named.

### F — Lab / methodology bootstrap

*The thing you are building is the ability to evaluate and experiment — a lab, not a
product.*

- **Read first:** [00](00_PRINCIPLES_AND_SCOPE.md) →
  [03](03_EVALUATION_FOUNDATION.md) →
  [04](04_EXPERIMENT_DESIGN_AND_STATISTICS.md) →
  [12](12_OBSERVABILITY_LEARNING_AND_PROMOTION.md)
- **Typically skippable at start:** 10 until a client system exists
- **Mandatory templates:** EXPERIMENT_CONTRACT · EVAL_SUITE_RELEASE_CONTRACT ·
  TEST_LOOK_LEDGER · METHOD_DECISION_RECORD
- **First three actions:**
  1. Choose the first *realistic* target task. Realism beats miniature: the
     discoveries that matter need breadth.
  2. Build the versioned suite, the integrity gates, and the telemetry floor (03, 12).
  3. Freeze the lab's first frozen-comparison contract, to exercise the whole
     machinery end to end.

### Three rules apply whatever your letter

1. **Everyone owes an EVAL_SUITE_RELEASE_CONTRACT.** Chapter 03 is in every entry
   path above — that is, everywhere — and this document follows chapter 03. At Tier
   2+, any suite version an
   [EXPERIMENT_CONTRACT](templates/EXPERIMENT_CONTRACT.md) cites as its frozen
   scientific baseline **MUST** have a completed
   [EVAL_SUITE_RELEASE_CONTRACT](templates/EVAL_SUITE_RELEASE_CONTRACT.md), written
   at the moment of freeze. It is named above only where building the suite *is* the
   archetype's headline deliverable. It is mandatory in the others too.
2. **Tier-3 uplift, any archetype.** Tier attaches to the decision, not to the
   letter. So a Tier-3 project routed to A, B, C, D, or F adds — on top of that
   block's set — **chapter 13 at intake and the full nine-template set**, plus E's
   governance artifacts from 13 §12. If you are Tier 3, read E's block as well as
   your own.
3. **Reading the three actions at Tier 1.** Every block's actions are written at
   Tier 2. At Tier 1, substitute the written lightweight plan for the frozen
   contract, notes-grade provenance for pinned identities, and smoke-scale evals for
   direction only. Reachability ceilings are *argued* at intake and *measured* before
   any adoption claim (03 §6) — never assumed away. Nothing on the never-skippable
   floor downgrades at any tier.

**Want to watch a full pass before you run yours?**
[examples/WALKTHROUGH_rag-document-qa.md](examples/WALKTHROUGH_rag-document-qa.md)
takes one invented project through the whole navigator end to end. The
`examples/SYNTH-*` files ([index](examples/README.md)) are compact passes, one per
project shape.

## The default lifecycle

Whichever letter you got, the work proceeds through the same loop. The chapter in
parentheses supplies that step's procedure;
[00 §5](00_PRINCIPLES_AND_SCOPE.md) states the structural rules about the ordering.

```
define decision/problem (01) → trustworthy eval substrate (03) → integrity/ceilings (03)
→ simplest credible baseline (05) → frozen execution-system identity (02)
→ candidate characterization (05/06) → failure diagnosis (03/07)
→ intervention choice (07 → 08|09) → capability/quality eval (04)
→ performance characterization (06) → economics (11) → shadow/canary (10)
→ promote / rollback (10) → production evidence back into learning (12 → 03)
```

## Global tripwires

Eight situations mean the plan is wrong and needs redrawing, not pushing through.
They hold at any tier and in any archetype. The chapter in parentheses has the
recovery procedure.

**[STOP CONDITION]** Stop and re-plan the moment any of these is true:

1. A quality claim is about to be made with **no trusted eval** behind it (03).
2. A stratum's **measured ceiling is below its passing threshold**. The instrument is
   broken; scores on it are meaningless (03).
3. A comparison is about to **cross an unmeasured reproducibility boundary** —
   session, host, provider redeploy (02).
4. A pre-registered tolerance was breached, and the named consequence is being
   **argued with instead of executed** (04).
5. **Training or hardware purchase** is being decided below the ladder's evidence
   bar (07/09), or without the demand ledger and a pre-committed trigger (11).
6. A result **below the design's [MDE](GLOSSARY.md#mde)** is being read as a
   difference — or as equivalence (04).
7. Held-out exposure has **hit the refresh threshold** in the look ledger (03/04).
8. A learned or automated component is about to act on live traffic **without a
   passed leakage audit and an observe-only period** (08).

## Where your first sprint ends

There are two possible finish lines, and your tier decides which one is yours.

**Tier 2+ — a frozen, committed
[EXPERIMENT_CONTRACT](templates/EXPERIMENT_CONTRACT.md)** for the first real
experiment. Question, decision, prediction, MDE, consequence-bearing tolerances: all
sections present, or marked N/A with a reason. Its sections discharge the floor for
you.

**Tier 1 — a written lightweight plan.** One short document, six headings, one per
never-skippable-floor item ([00 §6](00_PRINCIPLES_AND_SCOPE.md)), in this order:

1. **Decision and claim** — the decision this work drives, and the claim that needs
   evidence.
2. **Provenance notes** — what produced any result you might act on: model and
   version, prompt/config, date, where it ran. Notes-grade is fine; absent is not.
3. **Eval boundary** — what counts as ground truth, where it lives, and how it is
   kept out of the system's reach. Written *before* the first quality claim.
4. **Consequences** — for each threshold or tolerance that would drive a decision:
   what happens when it is missed, decided in advance.
5. **Held-out accounting** — which items are held out, and one line per look at
   them. Exposure is spent, not free.
6. **Where results are recorded** — where raw outputs and scores are retained, so a
   claim can be re-checked later.

The completed profile, the chosen archetype, and the first three actions (01 §5.6)
are the *inputs* to this plan. The six headings above are its required contents. A
Tier-1 plan is short — a page is normal — but no heading is optional, because these
are exactly the obligations that cannot be repaired after the fact.

If you sit down to write that document and cannot, the navigator has just told you
something useful. The section you could not fill in is your next action.

---

> [Index](README.md) · [Glossary](GLOSSARY.md) · [00 — Principles](00_PRINCIPLES_AND_SCOPE.md)
