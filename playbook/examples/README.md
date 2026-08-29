# Examples — Scenarios and Worked Examples

> Part of the **Adaptive AI Systems Playbook** v0.1.1 · [Index](../README.md) ·
> [Quickstart](../QUICKSTART.md)

Everything in this directory is invented. No real project, client, or measurement
appears anywhere in it. What is real is the reasoning: each example works through a
decision the playbook has an opinion about, and shows what went wrong when that
opinion was ignored.

Read them for the shape of the mistake, not for the numbers.

## Scenarios (SCENARIO-01…12)

Twelve fictional projects, each built around one lesson that is easy to agree with in
the abstract and easy to miss in practice. Each follows the same arc — *Situation ·
Decision faced · Evidence · What happened · The generic lesson · What would NOT have
worked · References* — and ends by telling you what to go check in your own work.

The chapters cite these as `[SCENARIO: SCENARIO-NN]`. A scenario illustrates a rule;
it is never the evidence for one. Where a chapter claims something is established,
the support is an external source in the [ledger](../references/SOURCES.md), not a
scenario. Chapters stay readable if you skip these entirely.

| ID | Scenario | The lesson in one line | Illustrates chapters |
|---|---|---|---|
| [SCENARIO-01](SCENARIO-01_consequence-bearing-tolerances.md) | Consequence-bearing tolerances | A threshold with no named consequence is an escape hatch nobody chose | 00, 04, 07 |
| [SCENARIO-02](SCENARIO-02_clustered-eval-effective-n.md) | Clustered eval, effective N | Count your groups, not your rows | 03, 04 |
| [SCENARIO-03](SCENARIO-03_learned-router-leakage.md) | Learned-router leakage | A learned component must beat the group-identity ceiling, or it learned the wrong thing | 03, 04, 08 |
| [SCENARIO-04](SCENARIO-04_harness-defects.md) | Harness defects | Check the ruler before you trust the measurement | 02, 03 |
| [SCENARIO-05](SCENARIO-05_hardware-purchase-discipline.md) | Hardware purchase discipline | Measure the critical path before you spend the money | 06, 11 |
| [SCENARIO-06](SCENARIO-06_token-budget-confounding.md) | Token-budget confounding | An uncalibrated output cap can invent a quality difference that isn't there | 04, 05, 07 |
| [SCENARIO-07](SCENARIO-07_deterministic-cascade-gate.md) | Deterministic cascade gate | Price routing's ceiling first; a few booleans may capture most of it | 08, 10 |
| [SCENARIO-08](SCENARIO-08_transport-serialization-defect.md) | Transport serialization defect | "Transparent" is a claim to test, not a property to assume | 02, 08, 12 |
| [SCENARIO-09](SCENARIO-09_suite-versioning-criteria-drift.md) | Suite versioning under criteria drift | Version the instrument; refuse comparisons across versions of it | 03, 13 |
| [SCENARIO-10](SCENARIO-10_pilot-optimism-collapse.md) | Pilot optimism collapse | Small-sample headlines run optimistic | 03, 04 |
| [SCENARIO-11](SCENARIO-11_diagnostic-gate.md) | Diagnostic gate | A cheap probe, agreed in advance, can settle an expensive question | 04, 07 |
| [SCENARIO-12](SCENARIO-12_restart-instability-paired-controls.md) | Restart instability, paired controls | Determinism is measured, not assumed | 02, 04 |

## The synthetic walkthrough

[WALKTHROUGH_rag-document-qa.md](WALKTHROUGH_rag-document-qa.md) — one complete
navigator pass ([QUICKSTART](../QUICKSTART.md) → profile → tier → archetype → first
sprint → frozen contract) on an invented document-QA project. **Entirely
fictional**, and deliberately shaped unlike everything else here — it exists to
show the navigator running end to end on an unfamiliar problem.

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
