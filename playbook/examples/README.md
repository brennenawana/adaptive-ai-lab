# Examples — Case-Study Library and Synthetic Worked Examples

> Part of the **Adaptive AI Systems Playbook** v0.1.1 · [Index](../README.md) ·
> [Quickstart](../QUICKSTART.md)

Two kinds of material live here, with different evidence status — read the label.

## Real empirical case studies (CASE-001…012)

These are **real**: they come from the FIS project (Fintech Integration Sandbox), a
realistic synthetic fintech-operations laboratory in which this playbook's
methodology was developed and stress-tested. Case files are the one place in the
playbook where that project's real numbers, names, and dates appear. Each follows a
fixed format — *Situation · Decision faced · Evidence · What happened · The generic
lesson · What would NOT have worked · References* — and separates **what happened in
that project** from **the rule you should take away**. Generic chapters cite these
by `[CASE: CASE-00N]` and remain readable without them.

| ID | Case | The lesson in one line | Backs chapters |
|---|---|---|---|
| [CASE-001](CASE-001_consequence-bearing-tolerances.md) | Consequence-bearing tolerances | Detection without a priced consequence is not a control | 00, 04, 07 |
| [CASE-002](CASE-002_clustered-eval-effective-n.md) | Clustered eval, effective N | Clustering silently destroys power; measure ICC before claiming significance | 03, 04 |
| [CASE-003](CASE-003_learned-router-leakage.md) | Learned-router leakage | A learned component must beat the group-identity ceiling under leave-one-group-out | 03, 04, 08 |
| [CASE-004](CASE-004_harness-defects.md) | Harness defects as instrument findings | Instrument defects impersonate model weakness; ceilings/inversions/disagreement find them | 02, 03 |
| [CASE-005](CASE-005_hardware-purchase-discipline.md) | Hardware purchase discipline | Measure the critical path and the demand ledger before spending capital | 06, 11 |
| [CASE-006](CASE-006_token-budget-confounding.md) | Token-budget confounding | An uncalibrated generation cap can manufacture a model-quality headline | 04, 05, 07 |
| [CASE-007](CASE-007_deterministic-cascade-gate.md) | Deterministic cascade gate | A verifier-gated deterministic cascade can beat the learned-gate design space | 08, 10 |
| [CASE-008](CASE-008_transport-serialization-defect.md) | Transport serialization defect | "Transparent" layers aren't; verify byte equivalence end to end | 02, 08, 12 |
| [CASE-009](CASE-009_suite-versioning-criteria-drift.md) | Suite versioning under criteria drift | Criteria drift is real; version the instrument, refuse cross-version comparison | 03, 13 |
| [CASE-010](CASE-010_pilot-optimism-collapse.md) | Pilot optimism collapse | Small-sample headlines run optimistic; adoption rules with fluke guards catch them | 03, 04 |
| [CASE-011](CASE-011_diagnostic-gate.md) | Diagnostic gate | A cheap pre-registered probe can decide an expensive experiment's fate | 04, 07 |
| [CASE-012](CASE-012_restart-instability-paired-controls.md) | Restart instability, paired controls | Measure your reproducibility boundary; then pair your controls | 02, 04 |

## The synthetic walkthrough

[WALKTHROUGH_rag-document-qa.md](WALKTHROUGH_rag-document-qa.md) — one complete
navigator pass ([QUICKSTART](../QUICKSTART.md) → profile → tier → archetype → first
sprint → frozen contract) on an invented document-QA project. **Entirely
fictional**, and deliberately shaped unlike the source project — it exists to prove
the navigator runs without any source-project knowledge.

## Synthetic worked examples (SYNTH-01…10)

Compact invented scenarios — one per project shape — showing the playbook's rules
firing on materially different problems. **All names and numbers are invented**;
each exercises at least one gate or tripwire for real.

| ID | Shape | The point it proves |
|---|---|---|
| [SYNTH-01](SYNTH-01_api-only-assistant.md) | API-only greenfield assistant | Eval-first bootstrap; the judge-calibration path for open-ended outputs |
| [SYNTH-02](SYNTH-02_private-local-deployment.md) | Privacy-mandated local deployment | Execution-system identity and reproducibility probes before any number is trusted |
| [SYNTH-03](SYNTH-03_high-throughput-extraction.md) | High-throughput extraction | Deterministic grading; operating points; cost-per-successful-task drives model size |
| [SYNTH-04](SYNTH-04_tool-calling-agent.md) | Tool-calling agent with write actions | Tool contracts, permission gating, injection threat model, observe-only graduation |
| [SYNTH-05](SYNTH-05_cost-reduction-routing.md) | Cost reduction via routing | Oracle analysis and break-even first; a leaky learned router is refused |
| [SYNTH-06](SYNTH-06_training-rejected.md) | Training rejected | Diagnosis lands on cheaper rungs; the ladder refuses the fine-tune |
| [SYNTH-07](SYNTH-07_training-justified.md) | Training justified | The evidence bar actually met: rig-first, ablation, forgetting gate, legality check |
| [SYNTH-08](SYNTH-08_high-stakes-audited-deployment.md) | High-stakes audited deployment | Tier 3: governance at intake, pass^k, human-gated canary, rehearsed rollback |
| [SYNTH-09](SYNTH-09_inconclusive-result.md) | An INCONCLUSIVE result | Below-MDE outcomes reported honestly; the decision made on cost, not a fake winner |
| [SYNTH-10](SYNTH-10_hardware-rent-vs-buy.md) | Hardware rent-vs-buy | Demand ledger + break-even + pre-committed trigger; the purchase correctly waits |

---

> [Index](../README.md) · [Quickstart](../QUICKSTART.md)
