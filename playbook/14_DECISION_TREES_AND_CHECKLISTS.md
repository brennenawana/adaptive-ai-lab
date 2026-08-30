# 14. Decision Trees and Checklists

> Part of the **Adaptive AI Systems Playbook** v0.1.1 ·
> [← Previous](13_GOVERNANCE_PROVENANCE_AND_SECURITY.md) · [Index](README.md)
> **Reading time:** reference — printed-page usable during execution.

Chapters 00–13 make the arguments. This page carries the conclusions: the trees
that pick your branch, the gates that stop the work, the lists you tick before
you spend money. It is the page to keep open in a tab.

**It has no authority of its own.** Every entry is a compressed restatement, it
names the chapter it came from, and on any difference that chapter governs —
this page is the one that has gone stale. **Release consistency check:** at every
playbook release, each entry's citation is re-verified against its source
chapter's current text, and an entry that no longer matches its source is a
release blocker (§8).

Two numbers appear everywhere below. A bare number is a chapter, and `§` picks a
section inside one: `(03 §5.6)` means chapter 03, section 5.6. The
[index](README.md) lists every chapter by name.

---

## 1. The lifecycle at a glance

```
define decision/problem (01) → trustworthy eval substrate (03) → integrity/ceilings (03)
→ simplest credible baseline (05) → frozen execution-system identity (02)
→ candidate characterization (05/06) → failure diagnosis (03/07)
→ intervention choice (07 → 08|09) → capability/quality eval (04)
→ performance characterization (06) → economics (11) → shadow/canary (10)
→ promote / rollback (10) → production evidence back into learning (12 → 03)
```

Structural rules for that loop (00 §5):

- Eval trust precedes optimization. Nothing is optimized against a number
  chapter 03 has not made trustworthy.
- Chapter 02 — the pinned execution-system identity — precedes any comparison
  that crosses runs.
- Chapter 04 gates every selection and every intervention experiment.
- Chapter 11 (economics) is consulted three times: at intake, at capacity
  planning, and at deployment.
- Chapter 13 (governance) is instantiated at intake for Tier-3 work.
- The loop closes: production evidence goes back into evaluation, 12 → 03.

## 2. The intervention ladder card (00 §4 P3; 03 §5.2; 07)

Ten rungs, cheapest and most reversible first. You descend only when every rung
above is exhausted or recorded as inapplicable.

| Rung | Intervention | Fixes | Descend only with |
|---|---|---|---|
| 0 | Instrument integrity | RC-1 — the measuring instrument is wrong | — always first; nothing else is interpretable |
| 1 | Infrastructure/runtime | RC-2 — serving stack, transport, config, or environment corrupts execution | evidence the instrument is sound |
| 2 | Evidence/retrieval/context | RC-3 — facts the task needs are absent and unreachable | rungs 0–1 cleared |
| 3 | Tool contracts & output enforcement | RC-4 — tool/API contract defect; RC-5 — correct content lost to parsing or format failures | rungs 0–2 cleared |
| 4 | Specification & verification | RC-6 — the system was never told what to do; RC-7 — its own verifier passes failures silently | rungs 0–3 cleared |
| 5 | Generation/reasoning budget | RC-8 — context window, reasoning budget, or truncation bounds the outcome | diagnosis showing budget binds outcomes (07 §5.2–5.3) |
| 6 | Routing/escalation | RC-9 — work sent to the wrong tier | verifier/oracle analysis (08) |
| 7 | Fine-tuning | RC-10 — a skill gap the model could learn from obtainable data | the full train-at-all gate (09 §4, §7) |
| 8 | Larger/different model | RC-11 — the model class cannot do it at any budget | pre-registered transfer/ceiling test: fine-tuning demonstrably insufficient, not merely untried (07 §5.1) |
| 9 | Architectural redesign | RC-12 — the system topology is wrong for the task shape | staged one-variable-at-a-time ladder run showing the residual gap tracks the topology, not any single component, plus a method decision record at commit (07 §5.1) |

Never train, buy a bigger model, or redesign (rungs 7–9) around a defect sitting
at rungs 0–4 (00 P3). Rungs 1–6 may be locally re-sequenced only on clear
diagnosis; rung 0's priority is normative.

This card's "Descend only with" column compresses two separate cells of 07 §5.1
— its Entry-evidence and Exit-evidence columns — into one, for brevity. Where
this card's text differs from 07 §5.1, or from the rung-descent gate in 07 §7
(which binds on the Exit-evidence column specifically), 07 governs. This chapter
carries no independent authority; see the opening note above.

## 3. Decision trees

### 3.1 Project routing (QUICKSTART, normative router; 01)

Every condition is a fact from the project profile. Walk top down and stop at
the first one that is true. QUICKSTART carries the same seven nodes with their
qualifiers spelled out, and QUICKSTART is the normative version.

1. **Pre-check — does a trusted eval for this task already exist?** If no, note
   "03 before optimization and selection". Either answer continues to node 2;
   this node never assigns a letter.
2. **An incumbent AI or automated system exists AND is failing its own quality
   bar — or the gap has no trusted measurement?** → **C** (fix what exists)
3. **The goal is cost reduction of a working system with an established,
   MEASURED quality bar?** → **D** (cost/routing)
4. **Regulatory, audit, or reliability obligations dominate?** → **E**
   (high-stakes)
5. **Privacy, residency, or IP constraints mandate a deployment NO managed API
   can satisfy — not even in-tenant/VPC-scoped and no-retention — because a
   stated rule would otherwise be violated?** → **B** (local mandate)
6. **The deliverable is the lab capability itself?** → **F** (lab bootstrap)
7. Nothing above fired → **A** (greenfield)

Two modifiers apply on top of whichever letter you land on. Judge-graded
outputs make the 03 §5.7 protocol mandatory. Any comparison crossing machines,
sessions, or providers means reading 02 now.

### 3.2 Grader choice (03 §5.6)

```
Is the output objectively verifiable — can code decide right or wrong?
    YES → deterministic grader (MUST)
    NO  ↓
Is it open-ended or preference-shaped?
    YES   → calibrated LLM judge — 03 §5.7's protocol first
    MIXED → split it: deterministic grader on the checkable part,
            calibrated judge on the rest, scored and reported separately
```

### 3.3 Deterministic gate vs. learned router (08 §7)

```
Does a task-level verifier exist — something that can check an answer
without a human?
    NO  → design a verifier first (08 §4). A learned gate with no verifier
          anywhere has no rescue measurement to be judged against.
    YES ↓
The deterministic gate is the DEFAULT. Now run oracle analysis: is there
material headroom above what that gate already catches?
    NO  → stop; no router
    YES ↓
A learned router is considered ONLY as an addition to the gate, and only
through: leakage audit (class-identity ceiling + leave-one-group-out
validation) → observe-only period → graduation gate (08 §7).
```

### 3.4 Compute supply (11 §5)

```
A written privacy/residency requirement that NO compliant managed surface
satisfies — not even in-tenant/VPC-scoped with retention off
(11 Q0a = QUICKSTART node 5)?
    YES → private capacity. Owned-only if, and only if, the same requirement
          also bars renting someone else's hardware (11 Q0b).
    NO  ↓
Does the demand ledger show sustained hours ≥ H*, the rent-vs-buy break-even?
    NO  → rent per milestone, or managed APIs; keep the ledger running
    YES ↓
Has the pre-committed purchase trigger fired?
    NO  → keep renting; do not buy on impulse
    YES ↓
Benchmark the candidate device on YOUR pinned workload → buy the minimal
benchmark-chosen configuration → acceptance test before it becomes an
execution system (02).
```

### 3.5 Train or not (07 §7; 09 §7)

```
Does the diagnosis land on RC-10, a learnable capability gap?
    NO  → wrong rung; go back to 07
    YES ↓
Are rungs 0–6 exhausted or inapplicable, each with evidence?
    NO  → work the cheaper rung first
    YES ↓
Does the training data demonstrably contain the skill, and is it legally
usable? (Provider ToS + base-model license checked AT TRAINING TIME; every
model-generated component provenance-qualified — record ownership is not
admissibility, 09 §5.)
    NO  → stop
    YES ↓
Do the economics close — cost per successful task vs. the alternatives (11)?
    NO  → stop
    YES ↓
Rig-first: pipeline de-risked end-to-end with provenance → ablation-sized runs
→ full-suite forgetting gate → post-tune promotion gate (09).
```

### 3.6 Promotion pipeline (10 §5)

```
offline confirm (04)
  → shadow              mirrored traffic, no user impact
  → canary              a small real fraction, ONE at a time, causal metric set
  → progressive rollout
  → steady state
```

Each stage carries named entry and exit gates, and pins the execution-system
identity per stage. The rollback path is REHEARSED before the first canary
(10 §5).

## 4. Decision gates, by stage

Every gate in chapters 00–13, one line each, with the chapter that defines it.

**Intake — 01 §7**
- **Kill criteria at intake.** The hard-constraint check runs before any spend.
- **Profile-complete gate.** Every always-mandatory profile field is answered.
- **Archetype lock.** The route and the first sprint are committed in writing.

**Measurement validity — 02 §7**
- **Identity-change gate.** Any change to a pinned execution-system component
  creates a new identity. Re-baseline, or isolate the factor explicitly.

**Instrument — 03 §7**
- **Suite release gate.** All release gates pass on the full corpus before the
  version is tagged.
- **Grader-choice gate.** Decided by task shape (§3.2 above).
- **Judge-trust gate.** No judge score drives a decision before all eight steps
  of the 03 §5.7 protocol complete.

**Experiment — 04 §7**
- **Freeze gate.** Every item in §6.1 is true — contract committed and
  content-hash bound, tolerances consequence-bearing with the PROCEED cost
  pre-registered at freeze, statistical plan written (clustering unit → ICC →
  DEFF → N_eff → MDE) with its verdict-reading table, prediction and look
  ledgers updated — before any qualification or confirmation execution, and
  before any iterate-split evidence is used for inference. *Cold start:* a
  declared-prior ICC plus a pre-registered re-estimation procedure that
  completes before the qualification look (§6.1).
- **Amendment legitimacy.** All five conditions hold, or a method decision
  record is written.
- **Diagnostic run kind.** Probes live inside the fail-closed record and are
  non-promotable.

**Selection — 05 §7**
- **Shortlist freeze.** Hard filters and diversity are documented before
  screening starts.
- **Runtime regime.** The regime — determinism/provenance vs. throughput vs.
  managed vs. hybrid — is chosen before any engine is argued about.

**Performance — 06 §7**
- **Operating-point selection.** Read off swept curves against stated latency
  constraints, then pinned.
- **Finding-vs-waste classification.** A dominant cost bucket is a finding if
  and only if it is task-intrinsic and decision-moving; otherwise it is waste,
  routed to engineering.

**Optimization — 07 §7**
- **Rung descent.** Evidence that the cheaper rungs are exhausted or
  inapplicable.
- **Diagnostic-gate verdict.** Pre-registered GO / RE-SCOPE / DROP bands, with
  data-sufficiency taking precedence; completion alone never produces GO.

**Routing — 08 §7**
- **Deterministic vs. learned** (§3.3 above).
- **Observe-only → automated-action graduation.** Leakage audit passed +
  observe-only agreement/regret measured + pre-registered promotion gate +
  rollback defined + monitoring plan live.

**Training — 09 §7**
- **Train-at-all** (§3.5 above).
- **Rig graduation.** The train → merge → quantize → serve → eval loop runs
  end-to-end with full provenance before any real training run.
- **Legal/license clearance.** Current provider terms and the base-model license
  reviewed and recorded at training time.
- **Post-tune promotion.** Forgetting gate passed + paired comparison against
  the base + deployment gate.

**Deployment — 10 §4, §7**
- **Stage advance.** The current stage's exit gates are met, with ONE declared
  treatment per stage — a frozen candidate system may differ in several
  components, but no undeclared second change rides along (10 §4) — and human
  approval per stakes tier.

**Economics — 11 §7**
- **Purchase trigger.** A pre-committed condition fired, fed by the demand
  ledger.
- **Rent-vs-buy break-even.** H* computed from measured inputs and honest
  utilization.

**Observability — 12 §7**
- **Telemetry-floor gate.** The floor is landed before any long or expensive
  run; otherwise the run is a non-promotable diagnostic.
- **Automation graduation reversal.** A fired drift trigger reverts the
  component to observe-only, automatically.
- **Periodic audit below threshold.** Blocks the next Tier-3 promotion until
  remediated.

**Governance — 13 §7**
- **Acquisition gate.** License and provenance recorded before weights or data
  enter the system.
- **Tool-permission gate.** Least privilege, with write actions gated by stakes
  tier, before exposure.
- **Publication gate.** Canary strings present and no held-out content, before
  anything derived from protected material ships.

## 5. Stop conditions (master list)

The eight global tripwires (00 §7, QUICKSTART) — stop and re-plan when:

1. A quality claim is about to be made with no trusted eval behind it (03).
2. A stratum's measured ceiling is below its passing threshold (03).
3. A comparison is about to cross an unmeasured reproducibility boundary (02).
4. A breached tolerance's named consequence is being argued with, not executed (04).
5. Training or hardware purchase is being decided below the ladder's evidence
   bar or without the demand ledger + trigger (07/09/11).
6. A sub-MDE result is being read as a difference — or as equivalence (04).
7. Held-out exposure has hit the refresh threshold in the look ledger (03/04).
8. A learned or automated component is about to act on live traffic without a
   passed leakage audit and an observe-only period (08).

Then the per-chapter additions, one line each:

| Stop when… | Source |
|---|---|
| No decision is named for work about to start | 01 §7 |
| No candidate execution system passes the hard constraints | 01 §7 |
| A cold-start placeholder threshold is about to become policy, unrevisited | 01 §7 |
| A runtime, engine, or config changed mid-comparison without a new identity | 02 §7, 05 §7 |
| An optimization is being committed to a format the deployment target can't run | 02 §7 |
| Two arms of one comparison disagree on an item and nobody has reviewed it | 03 §7 |
| A rubric change is proposed with no independently identified instrument defect | 03 §7 |
| Certainty curtailment fires — halt the arm, interval-only report, firewall | 04 §7 |
| Selection is proceeding without a trusted eval, or stalling past the first-sprint contract | 05 §7 |
| A margin-based elimination is about to happen below the pilot's MDE | 04/05 §7 |
| The capacity fit probe fails for the planned configuration | 06 §7 |
| The telemetry floor is not landed before a long or expensive run | 06/12 §7 |
| Two performance numbers from different tools or metric definitions are about to be compared | 06 §7 |
| A multi-tenant SLA claim is being made from single-tenant data | 06 §7 |
| A completion-only or proxy metric is about to license a GO | 07 §7 |
| A diagnostic's reconfirmed sample is below its pre-registered sufficiency floor | 07 §7 |
| The opportunity-cost test says this rung is exhausted | 07 §7 |
| A quantized artifact is below its pre-registered recovery bar and about to ship | 07 §7 |
| A routing tripwire fires (unnecessary-escalation spike, rescue-rate drop, gate latency breach) | 08 §7 |
| The full-suite forgetting gate breaches after a tune | 09 §7 |
| The sample-size ablation shows no signal at the largest affordable rung | 09 §7 |
| A deployment tripwire fires (canary metric breach, in-flight incompatibility) | 10 §7 |
| A hardware purchase is being justified from a within-run busy-percentage | 11 §7 |
| A cited price or benchmark carries no as-of date or provenance | 11 §7 |
| A protected corpus is about to land on an insufficient cloud tier | 11 §7, 13 §7 |
| A telemetry defect is found in already-published numbers — halt reliance, no silent patches | 12 §7 |
| The harvested-failure backlog is past its triage SLA | 12 §7 |
| Tier-2+ work is about to run without a frozen contract, or outside the record | 13 §7 |
| A protected data class turns out to be enforced at only one layer | 13 §7 |
| Provider terms haven't been re-checked since the last training decision | 13 §7 |
| A tool grant enables writes without its stakes-tier approval gate | 13 §7 |
| Held-out or protected content is about to be published without canaries | 13 §7 |

## 6. Checklists

### 6.1 Contract freeze (04 §7; [templates/EXPERIMENT_CONTRACT.md](templates/EXPERIMENT_CONTRACT.md))

The canonical eight-item freeze gate. 04 §7's table and the template's Freeze
Checklist are the same eight items; this condensation adds none of its own. (The
template's own smoke/integrity-pass and round-robin-ordering checks are
template-implementation detail tied to its own sections, not additional gate
requirements — see the template's Freeze Checklist.)

- [ ] **Contract committed, content-hash bound** — before any qualification/confirmation execution and before any iterate-split evidence is used for inference (cold start: declared prior ICC + pre-registered re-estimation procedure, completing before the qualification look)
- [ ] **Tolerances named**: every calibrated parameter's tolerance names ABORT / RECALIBRATE / PROCEED-WITH-DECLARED-CEILING, with the projected PROCEED cost pre-registered at freeze
- [ ] **Statistical plan written**: clustering unit, ICC (measured, or a declared prior with its re-estimation procedure), DEFF, N_eff, MDE, verdict-reading table
- [ ] **Prediction-ledger entry** filled
- [ ] **Look ledger** updated with this experiment's planned looks
- [ ] **Execution-system identity + authoritative clock** declared per arm, node placement pre-registered
- [ ] **Elimination-rule threshold** stated (= pilot's own MDE)
- [ ] **Curtailment clause + three guards** stated, or disabled with written justification

### 6.2 Suite release (03 §5.9; [templates/EVAL_SUITE_RELEASE_CONTRACT.md](templates/EVAL_SUITE_RELEASE_CONTRACT.md))

- [ ] Release contract written and frozen before implementation
- [ ] Exact changelist: defect → change → enforcing invariant, per item
- [ ] Reachability ceiling per stratum ≥ threshold + margin, measured on the built corpus
- [ ] Gold-answer gate at ceiling; corpus determinism digest match
- [ ] Cross-arm disagreement review closed; frontier-saturation check passed
- [ ] Cross-suite refusal active; baselines re-established in the fixed order
- [ ] Canary strings present in anything published

### 6.3 Before any long or expensive run (12 §5.1; 06 §7)

- [ ] Run lifecycle events (signal-safe start/end) live
- [ ] Per-invocation stats persisted (tokens, latency, finish reason)
- [ ] Dual-clock stamps + authoritative clock declared per metric
- [ ] Server/engine logs preserved; resource sampler on
- [ ] Config snapshot recorded; capacity fit probe passed

### 6.4 Promotion (10 §5; [templates/OPERATIONAL_HANDOFF.md](templates/OPERATIONAL_HANDOFF.md))

- [ ] Offline confirmation passed (04) on the exact execution system being shipped
- [ ] Shadow period completed; comparison design pre-registered
- [ ] Rollback path rehearsed, ownership named, triggers pre-registered with consequences
- [ ] ONE canary at a time; small causal metric set; aggregation window ≪ canary duration
- [ ] Human approval recorded per stakes tier; identity pinned per stage

### 6.5 Training entry (09 §7)

- [ ] RC-10 diagnosis with ladder-exhaustion evidence (07)
- [ ] Data legality: provider ToS + base-model license checked at training time, recorded
- [ ] Training data component-provenance-qualified (09 §5): every model-generated component's terms permit training use — record ownership alone is not admissibility; no unauthorized managed-provider outputs embedded; no held-out contamination (canaries verified)
- [ ] Rig graduated: full pipeline + provenance record end-to-end
- [ ] Sample-size ablation planned; full-suite forgetting gate pre-registered

### 6.6 Hardware purchase (11 §7; [templates/COMPUTE_DEMAND_LEDGER.md](templates/COMPUTE_DEMAND_LEDGER.md))

- [ ] Demand ledger shows sustained demand (honest NOT-RUN rows included)
- [ ] Pre-committed trigger fired (defined before wanting the hardware)
- [ ] Candidate device benchmarked on the pinned workload
- [ ] Prices re-verified at order time (every recorded price is a dated snapshot)
- [ ] Acceptance test planned before the device becomes an execution system (02)

### 6.7 Annual/major-release methodology audit (12 §5.8)

- [ ] Rubric-based self-audit run (score = minimum across categories)
- [ ] Instrument checks: ceilings re-verified, telemetry pipeline cross-checks green
- [ ] Look-ledger and suite-refresh status reviewed
- [ ] Doctrine-not-yet-exercised items reviewed: any now exercised? any to retire?
- [ ] This chapter's consistency check (§8) passed

## 7. The rigor dial card (00 §6)

Six obligations hold at every tier, Tier 1 included — the floor, never skippable:
the decision and the claim are stated · provenance is sufficient to identify what
produced a result · the eval/ground-truth boundary is drawn before any quality
claim · consequences are predeclared on decision thresholds · held-out exposure
is ledgered · outcome evidence is retained.

Each tier below adds to the floor, and to the tiers above it.

| Tier | Adds |
|---|---|
| **1 — exploratory** | lightweight profile, notes-grade pinning, smoke-scale evals (direction only) |
| **2 — consequential** *(default)* | frozen contracts; versioned suites + integrity gates; MDE/N_eff/INCONCLUSIVE; look + prediction + demand ledgers |
| **3 — high-stakes** | tamper-evident record, threat model, pass^k, judge calibration, human-gated shadow→canary, rehearsed rollback, periodic audit |

Rigor attaches to the decision's consequence, not the project's prestige.

## 8. Release consistency check (owner procedure)

At each release:

1. Regenerate the gate and stop inventory from chapters 00–13 — mechanically,
   by searching for the `[DECISION GATE]` and `[STOP CONDITION]` badges.
2. Diff it against §4 and §5.
3. Re-verify each checklist item against its cited section.
4. Treat any mismatch as a release blocker. Fix the chapter or fix this
   condensation; never let the two drift apart.

Record the check in the release's [CHANGELOG](CHANGELOG.md) entry.

---

> [← Previous](13_GOVERNANCE_PROVENANCE_AND_SECURITY.md) · [Index](README.md)
