# SYNTH-07: A Narrow Format-Adherence Gap That Survives the Ladder

> [Index](../README.md) · [Examples](README.md)

**Synthetic worked example — all names and numbers invented.**

## Profile summary

"Corrigan Precision Manufacturing" converts freeform, voice-transcribed
floor-inspector notes into a structured defect-report JSON matching a legacy
maintenance-system schema. This project continues an intervention-ladder
diagnosis already in progress — it is not a fresh intake.

| [Project profile](../GLOSSARY.md#project-profile) field | Value |
|---|---|
| Business outcome | Eliminate manual re-keying of inspector notes into the legacy system |
| Task population & volume | ~900 inspection notes/week |
| Criticality / failure cost | A malformed or misclassified report delays a maintenance work order; a human reviews before dispatch throughout the pilot |
| Quality/reliability target | ≥99% schema-valid JSON with correct defect-category field before review is relaxed |
| Latency / SLA | Near-real-time, a few seconds per note |
| Privacy / security | Internal plant data only |
| Data & knowledge availability | 6 years of historical notes paired with human-re-keyed structured records — large, directly relevant corpus |
| Tool / action permissions | None — pure text-to-structure transformation, no external tool calls |
| Model candidates | One open-weights model on owned hardware (data-residency preference, not mandated) |
| Owned / rentable compute | One owned GPU workstation already in use for other plant-floor ML; rented burst capacity for fine-tune runs |
| Managed APIs | One API model, used only as a periodic evaluation reference point |
| Budget | Workstation capital already sunk; fine-tune run rented separately |
| Staffing / time | 1 ML engineer, ~7 weeks |
| Deployment environment | On-prem plant network |
| Observability constraints | Existing plant telemetry pipeline, extended to log every transformation |
| Regulatory / compliance | Internal quality-system requirements only |
| Existing evidence | Baseline eval already run — this is a continuation |
| Stakes / consequence tolerance | Tier 2 |

## Archetype & rigor tier

This project is the continuation of an intervention-ladder diagnosis, not a
fresh archetype routing. Tier 2: internal, work-order delay is the downside,
and a human review step covers the pilot period, so there is no safety case
for Tier 3.

## The decisive moves

1. **Ladder rungs exhausted, in order, before rung 7 is even discussed.**
   Instrument checked (rung 0, clean); runtime/harness ruled out (rung 1,
   clean); evidence reachability confirmed adequate — the note itself
   contains everything needed, unlike [SYNTH-06](SYNTH-06_training-rejected.md)'s
   missing-evidence gap (rung 2, closed); grammar-constrained decoding tried
   for output-format enforcement and helps but plateaus (rung 3);
   prompt/spec iteration and few-shot examples tried and plateau below the
   bar (rung 4); generation-budget calibration tried, no effect (rung 5);
   escalation to a stronger model tried — it *also* plateaus below the bar,
   which rules out "just use a bigger model" as the fix (rung 6). What
   remains is narrow: a specific family of category-field misclassifications
   and a specific nested-object formatting quirk in the legacy schema,
   plateauing at 93% schema-valid-plus-category-correct — 6 percentage
   points short of the bar.
2. **Data-availability check before committing to rung 7.** Chapter 09's
   default procedure requires stating, not assuming, that the historical
   corpus demonstrably contains the missing skill. A held-out slice of the
   6-year archive is spot-checked: the mapping from freeform phrasing to the
   correct category field and nested-object shape is consistently present
   and learnable from the paired historical records.
3. **Rig-first.** The training/eval/regression machinery is built and
   validated *before* any real fine-tune run: the same frozen eval used
   through rungs 0–6, plus a regression slice of unrelated plant-floor tasks
   the model also performs, is frozen and dry-run against the untrained
   model to confirm it reproduces the known 93% baseline exactly, before any
   training compute is spent.
4. **Minimum-n ablation, not a single full-corpus run.** LoRA runs are
   ablated at increasing training-set sizes against the frozen eval to find
   the smallest sample that clears the bar. This is a deliberate distinction:
   sample sizes documented for broad style alignment do not transfer to a
   narrow behavioral fix like this one [EXT-FT-002], and vendor guidance
   situates PEFT-scale fixes in the hundreds-to-low-thousands of example
   pairs [NV-RTXAIGARAGE-001] — treated here as a starting range to validate
   empirically, not a number to assume.
5. **[DECISION GATE]** full-suite forgetting gate. The candidate checkpoint
   that clears the target bar is evaluated on the *entire* frozen suite, not
   only the target category/formatting slice — mandatory because narrow
   fixes have measurably caused regressions elsewhere in comparable
   literature [EXT-FT-006]. The candidate passes: the target slice clears
   99%, and no other stratum regresses outside its pre-registered tolerance.
6. **Terms-of-service check, recorded rather than assumed.** Before
   finalizing, training-data provenance is checked: the corpus is entirely
   internal plant records plus the open-weights model's own outputs used for
   augmentation — no managed-API model's outputs are used as training
   targets, which would otherwise trigger a training-restriction review
   under that provider's terms [EXT-LEGAL-001]. The check is written down as
   a pass, not left implicit.

## What was skipped and why

- **No routing/cascade design.** A single-model pipeline; once the fine-tune
  closes the gap there is no tiering question to answer.
- **No pass^k reliability claims.** A deterministic single-pass
  transformation with schema validation as the verifier, not a stochastic
  multi-turn agent.
- **No purchase-trigger / demand-ledger discussion beyond the existing
  workstation.** The fine-tune run was sized to a bounded number of rented
  GPU-hours, not a standing commitment.
- **No learned-router leakage audit.** Nothing here is a router; contrast
  [SYNTH-05](SYNTH-05_cost-reduction-routing.md), where that audit is the
  headline mechanism.

## Outcome

- Effort: ~7 weeks (2 confirming rungs 0–6 exhausted + the data check, 1
  rig-build and dry-run, 2 ablation sweep, 1 forgetting-gate run and review,
  1 rollout to a reduced-review pilot).
- Training compute: the ablation sweep clears the bar at roughly a third of
  the available historical corpus; total rented GPU time across the sweep
  and the final run is about 40 GPU-hours.
- Result: schema-valid-plus-category-correct rate rises from the 93% ladder
  plateau to 99.4% on the target slice; the full-suite forgetting check
  shows no stratum regressing beyond its pre-registered tolerance.
- Human review is relaxed from every note to a rolling spot-check sample for
  the pilot line. The relaxation is itself treated as a promotion decision:
  review reverts to 100% automatically if a rolling window drops below the
  bar (chapter 10's rollback discipline applied to a review policy, not just
  a deployment).

## Chapter trail

- [07. Optimization and Intervention Ladder](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md) —
  rung exhaustion, evidence at rungs 0–6
- [09. Training and Data](../09_TRAINING_AND_DATA.md) — data-availability
  check, rig-first, minimum-n ablation, LoRA sizing, forgetting gate
- [03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md) — the frozen
  eval reused as the training rig
- [13. Governance, Provenance, and Security](../13_GOVERNANCE_PROVENANCE_AND_SECURITY.md) —
  training-data provenance / terms-of-service check
- [10. Deployment and Operations](../10_DEPLOYMENT_AND_OPERATIONS.md) —
  promotion and rollback applied to the review-relaxation decision
- [00. Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md) — the
  rung-descent evidence rule that licenses reaching rung 7 here

---

[Index](../README.md) · [Examples](README.md)
