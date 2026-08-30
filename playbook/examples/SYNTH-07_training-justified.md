# SYNTH-07: A Narrow Format-Adherence Gap That Survives the Ladder

> [Index](../README.md) · [Examples](README.md)

**Synthetic worked example — all names and numbers invented.**

## Profile summary

Six rungs of cheaper fixes have already been tried here, and each one closed
without closing the gap. What survives is small and specific: one family of
misclassified defect categories, and one nested-object shape the legacy
schema wants that the model keeps getting wrong. That narrow residue is what
makes this the uncommon project where fine-tuning is the correct next move.

"Corrigan Precision Manufacturing" converts freeform, voice-transcribed notes
from floor inspectors into a structured defect-report JSON that a legacy
maintenance system will accept. This is a continuation of a diagnosis already
in progress, not a fresh intake.

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

No archetype routing happens here, because this project is the continuation
of an intervention-ladder diagnosis rather than a fresh intake.

**Tier 2.** The system is internal, a delayed work order is the whole
downside, and a human reviews every report before dispatch for the duration
of the pilot. There is no safety case that would push it to Tier 3.

## The decisive moves

1. **Every rung above 7 was worked and closed, in order.** Rung 7 is not
   reached by argument. It is reached by exhausting everything cheaper, and
   recording what each rung returned.

   | Rung | What was tried | Result |
   |---|---|---|
   | 0 — instrument | Integrity checks on the eval itself | Clean |
   | 1 — runtime/harness | Serving stack and configuration ruled out | Clean |
   | 2 — evidence reachability | Confirmed adequate: the note itself contains everything the transformation needs | Closed |
   | 3 — output enforcement | Grammar-constrained decoding for output format | Helps, then plateaus |
   | 4 — specification | Prompt/spec iteration and few-shot examples | Plateaus below the bar |
   | 5 — generation budget | Budget calibration | No effect |
   | 6 — escalation | A stronger model tried in its place | *Also* plateaus below the bar |

   Rung 2 is worth pausing on, because it is where the sibling case diverges:
   here the evidence is present in the note, whereas
   [SYNTH-06](SYNTH-06_training-rejected.md)'s entire gap *was* the missing
   evidence. Rung 6 matters for the opposite reason — a stronger model also
   plateauing is what rules out "just use a bigger model" as the fix.

   What remains is narrow: a specific family of category-field
   misclassifications, plus a specific nested-object formatting quirk in the
   legacy schema. Together they hold the system at 93% schema-valid-plus-
   category-correct — 6 percentage points short of the bar.
2. **Data availability is checked, not assumed, before rung 7 is
   committed to.** Chapter 09's default procedure requires *stating* that the
   historical corpus demonstrably contains the missing skill. So a held-out
   slice of the 6-year archive is spot-checked, and the mapping is there: the
   route from freeform phrasing to the correct category field and nested-object
   shape is consistently present in the paired historical records, and
   learnable from them.
3. **Rig first.** The training, eval, and regression machinery is built and
   validated *before* any real fine-tune run. The rig is the same frozen eval
   used through rungs 0–6, plus a regression slice of unrelated plant-floor
   tasks the model also performs. It is frozen and dry-run against the
   untrained model, and it has to reproduce the known 93% baseline exactly
   before a single unit of training compute is spent.
4. **The sample size is an ablation, not a full-corpus run.** LoRA runs are
   ablated at increasing training-set sizes against the frozen eval, looking
   for the smallest sample that clears the bar. The distinction is
   deliberate. Sample sizes documented for broad style alignment do not
   transfer to a narrow behavioral fix like this one [EXT-FT-002]. Vendor
   guidance situates PEFT-scale fixes in the hundreds-to-low-thousands of
   example pairs [NV-RTXAIGARAGE-001] — treated here as a starting range to
   validate empirically, not a number to assume.
5. **[DECISION GATE]** the full-suite forgetting gate. The candidate
   checkpoint that clears the target bar is evaluated on the *entire* frozen
   suite, not only the target category and formatting slice. This is
   mandatory, because narrow fixes have measurably caused regressions
   elsewhere in comparable literature [EXT-FT-006]. The candidate passes: the
   target slice clears 99%, and no other stratum regresses outside its
   pre-registered tolerance.
6. **The terms-of-service check is recorded, not assumed.** Two separate
   questions get answered before anything is finalized.

   *Whose outputs are in the training data?* The corpus is entirely internal
   plant records plus the open-weights model's own outputs used for
   augmentation. No managed-API model's outputs are embedded anywhere in the
   records as training targets. That is checked per component rather than
   inferred from who owns the record (chapter 09 §5) — the check that would
   otherwise trigger a training-restriction review under that provider's
   terms [EXT-LEGAL-001].

   *Does the open-weights license allow this?* Its own license is checked for
   a derived-output clause permitting its generations as training targets —
   chapter 13's permitted-use review — and recorded alongside the
   terms-of-service check. Both are written down as a pass. Neither is left
   implicit.

## What was skipped and why

- **No routing or cascade design.** This is a single-model pipeline. Once the
  fine-tune closes the gap, there is no tiering question left to answer.
- **No pass^k reliability claims.** A deterministic single-pass
  transformation, with schema validation as the verifier — not a stochastic
  multi-turn agent.
- **No purchase-trigger or demand-ledger discussion beyond the existing
  workstation.** The fine-tune run was sized to a bounded number of rented
  GPU-hours, not to a standing commitment.
- **No learned-router leakage audit.** Nothing here is a router. Contrast
  [SYNTH-05](SYNTH-05_cost-reduction-routing.md), where that audit is the
  headline mechanism.

## Outcome

- Effort: ~7 weeks — 2 confirming that rungs 0–6 were exhausted and running
  the data check, 1 building the rig and dry-running it, 2 on the ablation
  sweep, 1 on the forgetting-gate run and its review, 1 rolling out to a
  reduced-review pilot.
- Training compute: the ablation sweep clears the bar at roughly a third of
  the available historical corpus. Total rented GPU time across the sweep and
  the final run is about 40 GPU-hours.
- Result: the schema-valid-plus-category-correct rate rises from the 93%
  ladder plateau to 99.4% on the target slice, and the full-suite forgetting
  check shows no stratum regressing beyond its pre-registered tolerance.
- Human review is relaxed from every note to a rolling spot-check sample on
  the pilot line. That relaxation is itself treated as a promotion decision:
  review reverts to 100% automatically if a rolling window drops below the
  bar. This is chapter 10's rollback discipline applied to a review policy
  rather than to a deployment.

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
