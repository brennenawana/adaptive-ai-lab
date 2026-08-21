# 14. Decision Trees and Checklists

> Part of the **Adaptive AI Systems Playbook** v0.1.1 ·
> [← Previous](13_GOVERNANCE_PROVENANCE_AND_SECURITY.md) · [Index](README.md)
> **Reading time:** reference — printed-page usable during execution.

**This chapter carries no independent authority.** It is the curated operational
condensation of chapters 00–13: every gate, tree, and checklist here is a
compressed restatement, and its source chapter (cited on every entry) governs on
any difference. **Release consistency check:** at every playbook release, each
entry's citation is re-verified against its source chapter's current text; an
entry that no longer matches its source is a release blocker (§8).

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

Structural rules (00 §5): eval trust precedes optimization; 02 precedes any
cross-run comparison; 04 gates every selection/intervention experiment; 11 is
consulted at intake, capacity planning, and deployment; 13 is instantiated at
intake for Tier-3 work; the loop closes 12 → 03.

## 2. The intervention ladder card (00 §4 P3; 03 §5.2; 07)

| Rung | Intervention | Fixes | Descend only with |
|---|---|---|---|
| 0 | Instrument integrity | RC-1 | — always first; nothing else is interpretable |
| 1 | Infrastructure/runtime | RC-2 | evidence the instrument is sound |
| 2 | Evidence/retrieval/context | RC-3 | rungs 0–1 cleared |
| 3 | Tool contracts & output enforcement | RC-4, RC-5 | rungs 0–2 cleared |
| 4 | Specification & verification | RC-6, RC-7 | rungs 0–3 cleared |
| 5 | Generation/reasoning budget | RC-8 | diagnosis showing budget binds outcomes (07 §5.2–5.3) |
| 6 | Routing/escalation | RC-9 | verifier/oracle analysis (08) |
| 7 | Fine-tuning | RC-10 | the full train-at-all gate (09 §4, §7) |
| 8 | Larger/different model | RC-11 | pre-registered transfer/ceiling test: fine-tuning demonstrably insufficient, not merely untried (07 §5.1) |
| 9 | Architectural redesign | RC-12 | staged one-variable-at-a-time ladder run showing the residual gap tracks the topology, not any single component, plus a method decision record at commit (07 §5.1) |

Never train (rung 7+) around defects at rungs 0–4 (00 P3). Rungs 1–6 may be
locally re-sequenced only on clear diagnosis; rung 0's priority is normative.
This "Descend only with" column compresses both of 07 §5.1's Entry- and
Exit-evidence cells for brevity; where this card's text differs from 07 §5.1
(or from the §7 rung-descent gate, which binds on the Exit-evidence column
specifically), 07 governs — this chapter carries no independent authority (see
the opening note above).

## 3. Decision trees

### 3.1 Project routing (QUICKSTART, normative router; 01)

Profile facts → archetype (walk top-down; first true condition wins):
pre-check — trusted eval for this task exists? no → note "03 before
optimization/selection"; continue regardless · incumbent AI/automated system
exists AND is failing its own quality bar (or the gap has no trusted
measurement)? → C · cost reduction of a working system with an established,
MEASURED quality bar? → D · regulatory/audit/reliability obligations dominate?
→ E · privacy/residency/IP constraints mandate a deployment NO managed API can
satisfy — not even in-tenant/VPC-scoped, no-retention — because a stated rule
would otherwise be violated? → B · deliverable is the lab capability itself? →
F · else → A.
Modifiers: judge-graded outputs → 03 §5.7 protocol mandatory; any cross-machine/
session/provider comparison → 02 now.

### 3.2 Grader choice (03 §5.6)

```
Output objectively verifiable? ──yes──► deterministic grader (MUST)
        │ no
        ▼
Open-ended/preference-shaped? ──yes──► calibrated LLM judge (03 §5.7 protocol first)
        │ mixed
        ▼
Split: deterministic on the checkable part + calibrated judge on the rest,
scored and reported separately.
```

### 3.3 Deterministic gate vs. learned router (08 §7)

```
Task-level verifier exists? ──yes──► deterministic gate is the DEFAULT
        │                              │
        │                              ▼
        │                    Oracle analysis: is there material headroom
        │                    above the deterministic gate? ──no──► stop; no router
        │                              │ yes
        ▼                              ▼
   no verifier              learned router considered ONLY as an addition:
        │                   leakage audit (class-identity ceiling + LOGO)
        ▼                   → observe-only period → graduation gate (§4.5)
   design a verifier first (08 §4) — a learned gate without any
   verifier has no rescue measurement to be judged against.
```

### 3.4 Compute supply (11 §5)

```
Written privacy/residency requirement that NO compliant managed
surface satisfies (11 Q0a = QUICKSTART node 5)? ──yes──► private capacity
        │                                               (owned-only iff the
        │                                               requirement also bars
        │                                               rented tenancy — 11 Q0b)
        │ no
        ▼
Demand ledger shows sustained hours ≥ H* (rent-vs-buy break-even)?
        │ no ──► rent per milestone / managed APIs; keep the ledger running
        │ yes
        ▼
Pre-committed purchase trigger fired? ──no──► keep renting; do not buy on impulse
        │ yes
        ▼
Benchmark the candidate device on YOUR pinned workload → buy the minimal
benchmark-chosen configuration → acceptance test before it becomes an
execution system (02).
```

### 3.5 Train or not (07 §7; 09 §7)

```
Diagnosis lands RC-10 (learnable gap)? ──no──► wrong rung; go back to 07
        │ yes
        ▼
Rungs 0–6 exhausted or inapplicable, with evidence? ──no──► cheaper rung first
        │ yes
        ▼
Training data demonstrably contains the skill, legally usable
(provider ToS + base-model license checked AT TRAINING TIME; every
model-generated component provenance-qualified — record ownership
is not admissibility, 09 §5)? ──no──► stop
        │ yes
        ▼
Economics close (11: cost per successful task vs. alternatives)? ──no──► stop
        │ yes
        ▼
Rig-first: pipeline de-risked end-to-end with provenance ──► ablation-sized
runs ──► full-suite forgetting gate ──► post-tune promotion gate (09).
```

### 3.6 Promotion pipeline (10 §5)

```
offline confirm (04) → shadow (mirrored, no user impact) → canary (small real
fraction, ONE at a time, causal metric set) → progressive rollout → steady state
     each stage: named entry/exit gates; execution-system identity pinned per
     stage; rollback path REHEARSED before the first canary (10 §5.4).
```

## 4. Decision gates (all, by stage — one line + source)

**Intake (01 §7):** Kill criteria at intake — hard-constraint check before any
spend · Profile-complete gate — always-mandatory fields answered · Archetype
lock — route + first sprint committed in writing.

**Measurement validity (02 §7):** Identity-change gate — any change to a pinned
execution-system component creates a new identity; re-baseline or isolate the
factor explicitly.

**Instrument (03 §7):** Suite release gate — all release gates pass full-corpus
before the version tags · Grader-choice gate — by task shape (§3.2 above) ·
Judge-trust gate — no judge score drives a decision before the seven-step
protocol completes.

**Experiment (04 §7):** Freeze gate — contract committed (content-hash bound),
tolerances consequence-bearing with the PROCEED cost pre-registered at freeze,
statistical plan (clustering unit → ICC → DEFF → N_eff → MDE) + verdict-reading
table, prediction + look ledgers updated — before any qualification/confirmation
execution and before any iterate-split evidence is used for inference (cold
start: declared-prior ICC + a pre-registered re-estimation procedure completing
before the qualification look; §6.1) · Amendment legitimacy — all five
conditions or a method decision record · Diagnostic run kind — probes live
inside the fail-closed record, non-promotable.

**Selection (05 §7):** Shortlist freeze — hard filters + diversity documented
before screening · Runtime regime — regime chosen (determinism/provenance vs
throughput vs managed vs hybrid) before an engine is argued about.

**Performance (06 §7):** Operating-point selection — from swept curves against
stated latency constraints, then pinned · Finding-vs-waste classification — a
dominant cost bucket is a finding iff task-intrinsic and decision-moving; else
waste, routed to engineering.

**Optimization (07 §7):** Rung descent — evidence cheaper rungs are exhausted or
inapplicable · Diagnostic-gate verdict — pre-registered GO / RE-SCOPE / DROP
bands with data-sufficiency precedence; completion alone never produces GO.

**Routing (08 §7):** Deterministic-vs-learned (§3.3 above) · Observe-only →
automated-action graduation — leakage audit passed + observe-only
agreement/regret measured + pre-registered promotion gate + rollback defined +
monitoring plan live.

**Training (09 §7):** Train-at-all (§3.5 above) · Rig graduation — the
train→merge→quantize→serve→eval loop runs end-to-end with full provenance before
any real training run · Legal/license clearance — current provider terms +
base-model license reviewed and recorded at training time · Post-tune promotion
— forgetting gate passed + paired comparison vs. base + deployment gate.

**Deployment (10 §4, §7):** Stage advance — current stage's exit gates met, ONE
declared treatment per stage (a frozen candidate system may differ in several
components; no undeclared second change rides along — 10 §4), human approval per
stakes tier.

**Economics (11 §7):** Purchase trigger — pre-committed condition fired, fed by
the demand ledger · Rent-vs-buy break-even — H* computed with measured inputs,
honest utilization.

**Observability (12 §7):** Telemetry-floor gate — the floor is landed before any
long/expensive run, or the run is a non-promotable diagnostic · Automation
graduation reversal — a fired drift trigger reverts the component to
observe-only, automatically · Periodic audit below threshold — blocks the next
Tier-3 promotion until remediated.

**Governance (13 §7):** Acquisition gate — license + provenance recorded before
weights/data enter the system · Tool-permission gate — least privilege + write
actions gated by stakes tier before exposure · Publication gate — canary strings
+ no held-out content before anything derived from protected material ships.

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

Per-chapter additions (one line + source):

| Stop when… | Source |
|---|---|
| No decision is named for work about to start | 01 §7 |
| No candidate execution system passes the hard constraints | 01 §7 |
| A cold-start placeholder threshold is about to become policy unrevisited | 01 §7 |
| A runtime/engine/config changed mid-comparison without a new identity | 02 §7, 05 §7 |
| An optimization is being committed to a format the deployment target can't run | 02 §7 |
| Cross-arm disagreement is observed and not yet reviewed | 03 §7 |
| A rubric change is proposed with no independently identified instrument defect | 03 §7 |
| Certainty curtailment fires — halt the arm, interval-only report, firewall | 04 §7 |
| Selection is proceeding without a trusted eval, or stalling past the first-sprint contract | 05 §7 |
| A margin-based elimination is about to happen below the pilot's MDE | 04/05 §7 |
| The capacity fit probe fails for the planned configuration | 06 §7 |
| The telemetry floor is not landed before a long/expensive run | 06/12 §7 |
| Two performance numbers from different tools/metric definitions are about to be compared | 06 §7 |
| A multi-tenant SLA claim is being made from single-tenant data | 06 §7 |
| A completion-only or proxy metric is about to license a GO | 07 §7 |
| A diagnostic's reconfirmed sample is below its pre-registered sufficiency floor | 07 §7 |
| The opportunity-cost test says this rung is exhausted | 07 §7 |
| A quantized artifact is below its pre-registered recovery bar and about to ship | 07 §7 |
| A routing tripwire fires (unnecessary-escalation spike, rescue-rate drop, gate latency breach) | 08 §7 |
| The full-suite forgetting gate breaches after a tune | 09 §7 |
| The sample-size ablation shows no signal at the largest affordable rung | 09 §7 |
| A deployment tripwire fires (canary metric breach, in-flight incompatibility) | 10 §7 |
| A hardware purchase is being justified from within-run busy-percentage | 11 §7 |
| A cited price/benchmark carries no as-of date or provenance | 11 §7 |
| A protected corpus is about to land on an insufficient cloud tier | 11 §7, 13 §7 |
| A telemetry defect is found in already-published numbers — halt reliance, no silent patches | 12 §7 |
| The harvested-failure backlog is past its triage SLA | 12 §7 |
| Tier-2+ work is about to run without a frozen contract or outside the record | 13 §7 |
| A protected data class turns out to be enforced at only one layer | 13 §7 |
| Provider terms haven't been re-checked since the last training decision | 13 §7 |
| A tool grant enables writes without its stakes-tier approval gate | 13 §7 |
| Held-out or protected content is about to be published without canaries | 13 §7 |

## 6. Checklists

### 6.1 Contract freeze (04 §7; templates/EXPERIMENT_CONTRACT.md)

The canonical eight-item freeze gate — 04 §7's table and
templates/EXPERIMENT_CONTRACT.md's Freeze Checklist are the same eight items;
this condensation adds none of its own. (The template's own smoke/integrity-pass
and round-robin-ordering checks are template-implementation detail tied to its
own sections, not additional gate requirements — see the template's Freeze
Checklist.)

- [ ] Contract committed, content-hash bound — before any qualification/confirmation execution and before any iterate-split evidence is used for inference (cold start: declared prior ICC + pre-registered re-estimation procedure, completing before the qualification look)
- [ ] Every calibrated parameter's tolerance names ABORT / RECALIBRATE / PROCEED-WITH-DECLARED-CEILING, with the projected PROCEED cost pre-registered at freeze
- [ ] Statistical plan written: clustering unit, ICC (measured, or a declared prior with its re-estimation procedure), DEFF, N_eff, MDE, verdict-reading table
- [ ] Prediction-ledger entry filled
- [ ] Look ledger updated with this experiment's planned looks
- [ ] Execution-system identity + authoritative clock declared per arm, node placement pre-registered
- [ ] Elimination-rule threshold stated (= pilot's own MDE)
- [ ] Curtailment clause + three guards stated, or disabled with written justification

### 6.2 Suite release (03 §5.9; templates/EVAL_SUITE_RELEASE_CONTRACT.md)

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

### 6.4 Promotion (10 §5; templates/OPERATIONAL_HANDOFF.md)

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

### 6.6 Hardware purchase (11 §7; templates/COMPUTE_DEMAND_LEDGER.md)

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

Floor (never skippable): decision+claim stated · provenance sufficient to identify
what produced a result · eval/ground-truth boundary before quality claims ·
consequences predeclared on decision thresholds · held-out exposure ledgered ·
outcome evidence retained.

Tier 1 exploratory: + lightweight profile, notes-grade pinning, smoke-scale evals
(direction only). Tier 2 consequential (default): + frozen contracts, versioned
suites + integrity gates, MDE/N_eff/INCONCLUSIVE, look + prediction + demand
ledgers. Tier 3 high-stakes: + tamper-evident record, threat model, pass^k,
judge calibration, human-gated shadow→canary, rehearsed rollback, periodic audit.
Rigor attaches to the decision's consequence, not the project's prestige.

## 8. Release consistency check (owner procedure)

At each release: (1) regenerate the gate/stop inventory from chapters 00–13
(mechanically: search for `[DECISION GATE]` / `[STOP CONDITION]` badges);
(2) diff against §4–§5; (3) re-verify each checklist item against its cited
section; (4) any mismatch is a release blocker — fix the chapter or this
condensation, never let them drift apart. Record the check in the release's
CHANGELOG entry.

---

> [← Previous](13_GOVERNANCE_PROVENANCE_AND_SECURITY.md) · [Index](README.md)
