# Quickstart — The Project Navigator

> Part of the **Adaptive AI Systems Playbook** v0.1.0 ·
> [Index](README.md) · [Glossary](GLOSSARY.md) · [Principles](00_PRINCIPLES_AND_SCOPE.md)
> **Time:** ~15 minutes to a routed plan and your first three actions.

This page turns a concrete project into a reading path, a mandatory-artifact set,
and the first three actions — routed on **profile facts, not vibes**. You do not
need to read the whole book first; you need to answer the questions below honestly.

The navigator's promise: whatever your project shape, your **first sprint ends at
the same place** — a frozen [experiment contract](GLOSSARY.md#experiment-contract)
for your first real experiment (Tier 2+), or a written lightweight plan covering
the six floor items (Tier 1). Everything routes toward that.

---

## Step 1 — Fill the project profile (~10 minutes)

Copy [templates/PROJECT_PROFILE.md](templates/PROJECT_PROFILE.md) and fill it. If
you can't answer a field, write "unknown" — unknowns route too (mostly toward
chapter 01). Every routing condition on this page reads off a **numbered profile
field**; these are the fields the navigator routes on hardest:

| Profile field (number and name) | Routing question it answers | Used at |
|---|---|---|
| **20** — Existing evidence (including any incumbent/automated system and its observed failures) | Do you already have a **trusted eval** for this task? Does an **incumbent** exist, and is it failing its own quality bar? | Step 3, nodes 1 and 2 |
| **1** — Business outcome | Is the goal **cost reduction** of an already-working system? Is the deliverable the lab capability itself? | Step 3, nodes 3 and 6 |
| **19** — Regulatory/compliance · **3** — Criticality / failure cost | Do **audit / reliability obligations dominate** the requirements? | Step 3, node 4 |
| **6** — Privacy/security/data residency · **17** — Deployment environment | Is a deployment **no managed API can satisfy** actually mandated? | Step 3, node 5 |
| **21** — Stakes / consequence tolerance | Which [rigor tier](GLOSSARY.md#stakes-tier) governs? | Step 2 |
| **4** — Quality/reliability target · **2** — Task population & volume | Is output **objectively verifiable** or judge-graded? | Step 3, modifiers |
| **9** — Model candidates · **12** — Managed APIs | Will any comparison **cross execution surfaces** (machines, sessions, providers)? | Step 3, modifiers |

## Step 2 — Set the rigor tier

From the profile's stakes field (field 21; definitions in
[00 §6](00_PRINCIPLES_AND_SCOPE.md)):

| Tier | You are here if… | Mandatory artifacts (beyond the floor) |
|---|---|---|
| **1 — Exploratory** | internal, reversible, low blast radius — and no decision outside your own team rides on the results | lightweight profile; notes-grade pinned provenance; smoke-scale evals for direction only |
| **2 — Consequential** *(default)* | business decisions or customer-visible behavior ride on results | frozen contracts · versioned suites + integrity gates · MDE/effective-N + INCONCLUSIVE · look ledger · prediction ledger · demand ledger before purchases |
| **3 — High-stakes / regulated** | safety, money movement, compliance, audit | Tier 2 + tamper-evident record of record · threat-model review · pass^k reliability claims · judge calibration where judges used · shadow→canary with human approval · rehearsed rollback · periodic audit |

Two boundary rules that decide most contested cases:

- **Mandatory human review does not buy you Tier 1.** An internal tool whose output
  feeds a **tracked business metric** — throughput, resolution time, cost per case,
  a staffing or workflow decision — is **Tier 2** even when a human reviews and
  edits every output before it reaches anyone. Review shrinks the blast radius of a
  single bad output; it does not remove the business decision riding on the
  aggregate result. Tier 1 is for work whose results drive no decision outside the
  team that produced them.
- **When signals conflict, take the higher tier.** Field 3 says "purely internal"
  but field 19 names a regulator; field 1 says "prototype" but the output is
  customer-visible. Tier is set by the riskiest decision the project makes, so
  disagreement between fields resolves upward, not to the average.

**The [never-skippable floor](GLOSSARY.md#never-skippable-floor) applies at every
tier** — state the decision and claim; keep provenance sufficient to identify what
produced a result; define the eval/ground-truth boundary before quality claims;
predeclare consequences for decision thresholds; ledger held-out exposure; retain
outcome evidence.

**Rule of proportion:** rigor attaches to the *decision*, not the project. A Tier-1
prototype making a ship-to-production decision escalates that decision to Tier-2/3
artifacts.

## Step 3 — Route to your archetype

Walk the tree top-down; take the **first** branch whose condition is true. Every
condition is a fact from a numbered profile field (Step 1's table names which).
Node 1 is a pre-check, not a destination: it never ends the walk.

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

**Reading the contested nodes.** Three conditions carry qualifiers that decide the
route, and they are part of the condition, not commentary:

- **Node 2 — "failing its own quality bar."** Every system below 100% has *some*
  observed failures; that alone is not archetype C. C fires when the incumbent is
  missing an established bar, **or** when nobody can say whether it is because no
  trusted measurement of the gap exists. Two exclusions follow: an incumbent that
  demonstrably meets a measured bar and is merely expensive is archetype **D**, not
  C; and a predecessor tool you intend to **replace** with a differently-shaped
  system — rather than diagnose and repair — is not the incumbent this node means,
  because there is nothing to diagnose, only something to supersede. C is for the
  system you plan to keep and fix.
- **Node 4 before node 5, deliberately.** A regulated project frequently answers
  yes to both. E's governance set is a strict superset of B's rigor, so a project
  that is both routes to **E** and carries its residency constraint into the
  admissible-execution-surface question in [05 §5.2](05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md).
  B is for the case where the deployment surface is the binding constraint and
  audit obligations are not.
- **Node 5 — "no managed API can satisfy."** A residency or confidentiality rule
  that an in-tenant / VPC-scoped, no-retention managed endpoint *can* satisfy does
  **not** fire this node: it constrains which
  [execution surfaces](GLOSSARY.md#execution-surface) are admissible (05 §5.2's
  regime criterion asks exactly this), not whether the model must run self-hosted.
  The node fires only when a **stated rule** — contract, law, written policy —
  would otherwise be violated; discomfort, preference, or "it feels safer local" is
  not a mandate. If the applicable rule is genuinely unwritten, that ambiguity is
  itself the first action: get it written before it silently re-routes your project.

Two cross-cutting modifiers, applied after the letter (node 1's eval-first note is
a third, and applies whatever the letter):

- **Judge-graded outputs** (fields 4/7 say the bar is open-ended, not objectively
  verifiable). Deterministic verification stays the default wherever any part of
  the output is checkable — split the bar first and keep every checkable dimension
  deterministic. For what is left:
  - **Tier 2+:** add the judge-calibration protocol
    ([03 §5.7](03_EVALUATION_FOUNDATION.md), `doctrine — not yet exercised`) to
    your mandatory set *before* any quality claim, and record the calibrated judge
    as the contract's scorer/verifier identity **before** the contract freezes — an
    uncalibrated judge cannot be a frozen scorer.
  - **Tier 1:** do **not** put a judge on an adoption decision
    ([03 §6](03_EVALUATION_FOUNDATION.md) is explicit about this). Use human
    spot-grading instead — a small dual-labelled sample with disagreements
    adjudicated — and keep any judged score for direction only.
  - Wherever a paired outcome feeds an [oracle analysis](GLOSSARY.md#oracle-analysis)
    or a cascade study, gate its judged dimensions through this modifier *before*
    trusting the oracle ceiling: an uncalibrated judge produces a silently wrong
    ceiling that looks like evidence.
- **Any cross-machine / cross-session / cross-provider comparison planned**
  (fields 9/12): read chapter 02 **now**, before trusting any number — comparability
  claims may not cross an unmeasured
  [reproducibility boundary](GLOSSARY.md#reproducibility-boundary). This pulls 02
  forward into any archetype's entry path, not only B's.

## Step 4 — Your route

| | Entry path (first 3 chapters) | Typically skippable at start | Mandatory templates (Tier 2; Tier 1 may downgrade to notes) | First three actions |
|---|---|---|---|---|
| **A — Greenfield, API-models-only** | [01](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) → [03](03_EVALUATION_FOUNDATION.md) → [04](04_EXPERIMENT_DESIGN_AND_STATISTICS.md) | 06, 09, 11-hardware (keep 11-API-economics) | PROJECT_PROFILE · EXPERIMENT_CONTRACT · TEST_LOOK_LEDGER · PREDICTION_LEDGER | 1. Fill the profile; state the decision each evidence item will drive. 2. Derive the task ontology from real traces/tickets (03 §5.1) and draft the first eval set with measured ceilings (03 §5.5). 3. Freeze the first contract: 2–4 candidate models, one factor, MDE stated, scorer/verifier identity named (a judge may only be named once calibrated — see the modifier) — *(Tier 1: write the lightweight plan instead)*. |
| **B — Local / private deployment mandate** | [01](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) → [02](02_EXECUTION_SYSTEM_MODEL.md) → [03](03_EVALUATION_FOUNDATION.md) (then 06 early) | 09 until the ladder reaches it; 10 until a candidate exists | A's set + COMPUTE_DEMAND_LEDGER · OPERATIONAL_HANDOFF | 1. Fill the profile incl. residency constraints; pick the runtime **regime** (05 §5.2), not a runtime. 2. Pin the first execution-system identity and run the reproducibility-boundary probes (02); run the **capacity fit probe** — context length + generation cap against accelerator memory — per [06 §5.2.D](06_INFERENCE_PERFORMANCE_AND_CAPACITY.md) and 06 §8. 3. Build the eval substrate (03) against the pinned identity; freeze the first contract — *(Tier 1: lightweight plan instead)*. |
| **C — Existing system underperforming** | [01](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) → [03](03_EVALUATION_FOUNDATION.md) (eval first!) → [07](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md) | 05 (selection is premature until diagnosis) | A's set + PERFORMANCE_AUTOPSY | 1. Do NOT change the system yet: build/validate the eval from harvested failures (03; error-analysis-first). 2. Diagnose: classify observed failures into the [taxonomy](GLOSSARY.md#canonical-failure-taxonomy) (03 §5.2) — instrument defects first. 3. Pick the highest applicable ladder rung with a cheap [diagnostic gate](GLOSSARY.md#diagnostic-gate) (07); freeze the contract for that intervention — *(Tier 1: lightweight plan instead)*. |
| **D — Cost reduction of an API-heavy system** | [01](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) → [08](08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md) → [11](11_ECONOMICS_HARDWARE_AND_CLOUD.md) — **plus [02](02_EXECUTION_SYSTEM_MODEL.md) first whenever the candidate tiers span execution surfaces or providers**, which a cascade normally does (08's own prerequisites are 00, 02, 03, 07) | 09; 03 only to *verify* eval trust (if the bar isn't actually measured, you are archetype C) | A's set + COMPUTE_DEMAND_LEDGER | 1. Verify the quality bar is real: a trusted eval + measured baseline (else re-route to C). 2. Run [oracle analysis](GLOSSARY.md#oracle-analysis) + [break-even](GLOSSARY.md#break-even) (08/11) before building any router — if any paired outcome depends on judged rather than deterministic scoring, gate it through the judge-graded modifier first. 3. Design the cascade with a [deterministic gate](GLOSSARY.md#deterministic-gate) if a verifier exists; freeze the routing experiment contract with a per-arm execution-system identity — *(Tier 1: lightweight plan instead)*. |
| **E — High-stakes / compliance-bound** | [01](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) → [13](13_GOVERNANCE_PROVENANCE_AND_SECURITY.md) → [03](03_EVALUATION_FOUNDATION.md) → [04](04_EXPERIMENT_DESIGN_AND_STATISTICS.md) | nothing — Tier 3 curtails no chapter; 09 waits for the ladder like everyone else | full Tier-3 set (all nine templates) **+ the governance artifacts of 13 §12**: record of record, clean-room boundary document, license register, trajectory privacy-classification table, tool-calling threat model + permission-tier table, canary-string registry, eval-corpus regulated-data disposition record — several of these have no dedicated template yet; instantiate them from 13 §11's tables (13 §12 says which) | 1. Instantiate governance at intake: record of record, ground-truth isolation, threat model (13) — note that 13's redaction-pipeline and tool-threat-model procedures are labelled `doctrine — not yet exercised`, so budget time to validate them rather than assuming a proven recipe. 2. Build the eval with per-stratum ceilings and forbidden-claim scoring (03); plan pass^k for reliability claims. 3. Freeze the first contract with consequence-bearing tolerances and human-approval gates named. |
| **F — Lab / methodology bootstrap** | [00](00_PRINCIPLES_AND_SCOPE.md) → [03](03_EVALUATION_FOUNDATION.md) → [04](04_EXPERIMENT_DESIGN_AND_STATISTICS.md) → [12](12_OBSERVABILITY_LEARNING_AND_PROMOTION.md) | 10 until a client system exists | EXPERIMENT_CONTRACT · EVAL_SUITE_RELEASE_CONTRACT · TEST_LOOK_LEDGER · METHOD_DECISION_RECORD | 1. Choose the first *realistic* target task (realism beats miniature: the discoveries that matter need breadth). 2. Build the versioned suite + integrity gates + telemetry floor (03, 12). 3. Freeze the lab's first frozen-comparison contract to exercise the whole machinery end-to-end. |

**Three rules apply to every row, whatever your letter:**

1. **EVAL_SUITE_RELEASE_CONTRACT is implied wherever chapter 03 is in the entry
   path — that is, everywhere.** At Tier 2+, any suite version an
   [EXPERIMENT_CONTRACT](templates/EXPERIMENT_CONTRACT.md) cites as its frozen
   scientific baseline **MUST** have a completed
   [EVAL_SUITE_RELEASE_CONTRACT](templates/EVAL_SUITE_RELEASE_CONTRACT.md), written
   at the moment of freeze. It is named in the rows where building the suite *is*
   the archetype's headline deliverable; it is mandatory in the others too.
2. **Tier-3 uplift, any archetype.** Tier attaches to the decision, not the letter,
   so a Tier-3 project routed to A, B, C, D, or F adds — on top of that row's set —
   **chapter 13 at intake and the full nine-template set**, plus row E's governance
   artifacts from 13 §12. If you are Tier 3, read E's row as well as your own.
3. **Reading the action column at Tier 1.** Every row's actions are written at
   Tier 2. At Tier 1, substitute the written lightweight plan for the frozen
   contract, notes-grade provenance for pinned identities, and smoke-scale evals
   for direction only — reachability ceilings are *argued* at intake and *measured*
   before any adoption claim (03 §6), never assumed away. Nothing on the
   never-skippable floor downgrades at any tier.

**Worked passes:** the full navigator run on a synthetic project is
[examples/WALKTHROUGH_rag-document-qa.md](examples/WALKTHROUGH_rag-document-qa.md);
compact per-shape passes are the `examples/SYNTH-*` files
([index](examples/README.md)).

## The default lifecycle

Wherever you entered, work proceeds through this loop (chapters give each step's
procedure; [00 §5](00_PRINCIPLES_AND_SCOPE.md) states the structural rules):

```
define decision/problem (01) → trustworthy eval substrate (03) → integrity/ceilings (03)
→ simplest credible baseline (05) → frozen execution-system identity (02)
→ candidate characterization (05/06) → failure diagnosis (03/07)
→ intervention choice (07 → 08|09) → capability/quality eval (04)
→ performance characterization (06) → economics (11) → shadow/canary (10)
→ promote / rollback (10) → production evidence back into learning (12 → 03)
```

## Global tripwires

**[STOP CONDITION]** Stop and re-plan the moment any of these is true — at any tier,
in any archetype (the chapter in parentheses has the recovery procedure):

1. A quality claim is about to be made with **no trusted eval** behind it (03).
2. A stratum's **measured ceiling is below its passing threshold** — the instrument
   is broken; scores on it are meaningless (03).
3. A comparison is about to **cross an unmeasured reproducibility boundary** —
   session, host, provider redeploy (02).
4. A pre-registered tolerance was breached and the named consequence is being
   **argued with instead of executed** (04).
5. **Training or hardware purchase** is being decided below the ladder's evidence
   bar (07/09) or without the demand ledger + pre-committed trigger (11).
6. A result **below the design's MDE** is being read as a difference — or as
   equivalence (04).
7. Held-out exposure has **hit the refresh threshold** in the look ledger (03/04).
8. A learned or automated component is about to act on live traffic **without a
   passed leakage audit and an observe-only period** (08).

## Where your first sprint ends

- **Tier 2+**: a frozen, committed
  [EXPERIMENT_CONTRACT](templates/EXPERIMENT_CONTRACT.md) for the first real
  experiment — question, decision, prediction, MDE, consequence-bearing tolerances,
  all sections present or reasoned N/A. Its sections discharge the floor for you.
- **Tier 1**: a written **lightweight plan** — one short document with exactly six
  headings, one per never-skippable-floor item ([00 §6](00_PRINCIPLES_AND_SCOPE.md)),
  in this order:
  1. **Decision and claim** — the decision this work drives, and the claim that
     needs evidence.
  2. **Provenance notes** — what produced any result you might act on: model and
     version, prompt/config, date, where it ran. Notes-grade is fine; absent is not.
  3. **Eval boundary** — what counts as ground truth, where it lives, and how it is
     kept out of the system's reach — written *before* the first quality claim.
  4. **Consequences** — for each threshold or tolerance that would drive a
     decision: what happens when it is missed, decided in advance.
  5. **Held-out accounting** — which items are held out, and one line per look at
     them. Exposure is spent, not free.
  6. **Where results are recorded** — where raw outputs and scores are retained, so
     a claim can be re-checked later.

  The completed profile, the chosen archetype, and the first three actions
  (01 §5.6) are the *inputs* to this plan; the six headings above are its required
  contents. A Tier-1 plan is short — a page is normal — but no heading is optional,
  because these are exactly the obligations that cannot be repaired after the fact.

If you cannot produce that document, the navigator has told you something: the
missing section *is* your next action.

---

> [Index](README.md) · [Glossary](GLOSSARY.md) · [00 — Principles](00_PRINCIPLES_AND_SCOPE.md)
