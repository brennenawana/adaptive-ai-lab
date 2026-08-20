# FIS / AI Systems Lab — Documentation Index

Last reorganized: 2026-08-20. If you read nothing else, read this page.

## START HERE (strict reading order)

1. **[current/AI_SYSTEMS_LAB_MASTER_PLAN.md](current/AI_SYSTEMS_LAB_MASTER_PLAN.md)** — what we are building, where we are, what changed after the 2026-08 research, milestones.
2. **[current/NEXT_STEP_M0.md](current/NEXT_STEP_M0.md)** — the single authorized next task (implementation-ready).
3. **[current/EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK.md](current/EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK.md)** — the experimental methodology every experiment follows.
4. **[current/EXPERIMENT_CONTRACT_TEMPLATE.md](current/EXPERIMENT_CONTRACT_TEMPLATE.md)** — how to write the next contract (v2).
5. **[HANDOFF.md](HANDOFF.md)** — operational state: what runs where, gotchas, verification commands.
6. **[research/](research/)** — the two 2026-08 deep-research reports (the evidence base for the current plan).

**When documents conflict:** master plan → next-step plan → playbook/contract-template →
HANDOFF → everything else. Historical **final reports** stay authoritative for the
facts of their own experiments but never override the current plan. Historical
**plans** are never instructions.

## CURRENT / NORMATIVE (the complete set — nothing else is normative)

| Doc | Role |
|---|---|
| `current/AI_SYSTEMS_LAB_MASTER_PLAN.md` | Program strategy + sequencing authority |
| `current/NEXT_STEP_M0.md` | The next task |
| `current/EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK.md` | Methodology (v1.0) |
| `current/EXPERIMENT_CONTRACT_TEMPLATE.md` | Contract template (v2) |
| `HANDOFF.md` | Operational state & environment record |
| `architecture.md` | Component map, ports, event topology (normative event-driven requirement) |
| `task-ontology.md` | Scenario classes, root causes, cause→action table |
| `clean-room-boundary.md` | What must never enter this sandbox |
| `experiment-log.md`, `routing-experiments.md` | Append-only experiment records (current through their last dated entry; **their per-entry "next milestone" lines are historical recommendations — sequencing lives in the master plan**) |

## FROZEN EXPERIMENT CONTRACTS (binding records — do not edit)

`SUITE_V3_RELEASE_CONTRACT.md`, `R5_EXPERIMENT_CONTRACT.md`, `R6_EXPERIMENT_CONTRACT.md`
remain the binding definitions of their frozen baselines and completed experiments.
They carry **no status headers by design**: `R6_EXPERIMENT_CONTRACT.md` is bound by git
blob SHA in the provenance registry (`committed_contract_extends` — append-only after
freeze), and the freeze discipline applies to all three in spirit. They are records,
not plans. New experiments use the v2 template, never these files.

## HISTORICAL EVIDENCE — safe to cite for facts, not current instructions

`SUITE_V3_RELEASE_REPORT.md` · `R5_LEARNED_ROUTING_REPORT.md` ·
`R6_MODERN_LOCAL_SPECIALIST_REFRESH_REPORT.md` · `R6_PERFORMANCE_AUTOPSY.md` ·
`OVERNIGHT_STATUS.md` (live log of the 2026-08-16→19 milestones M1–M7 — session
markers, unrelated to program milestone M0) · `SETUP-ACTIONS.md` (bootstrap record).

Each report's "recommended next milestone" was true when written and is superseded by
the master plan. The R6 report's §11 R7 recommendation is now **conditional on M0**.

## REFERENCE DESIGNS (`reference/`) — consult, don't execute

| Doc | What it is |
|---|---|
| `Company_Intelligence_Platform_Canonical_Architecture_v1.html` | The production north-star design (two planes, five memory types, specialist definition, ladder, phases 0–9). Still the design reference; program sequencing is the master plan's. |
| `Company_Intelligence_Platform_MSI_Experimentation_and_Fintech_Sandbox_Guide.html` | The original FIS spec (12 classes, tool contracts, E0–E8 matrix). Scenario/tool definitions remain definitional; the E-matrix is closed/absorbed (master plan §6). |
| `Company_Intelligence_Platform_MacBook_Pro_Hybrid_Deployment_Guide.html` | A **different machine** (24 GB M4 Pro Mac). Ignore unless working on that deployment. |
| `Harness_Intelligence_Roadmap_H0_H3.html` | Deferred harness-science roadmap (H-series). Not started; its FIS-state snapshot is stale. |
| `Developer_Agent_Telemetry_D0_Initial_Plan.html` | Dormant D-series telemetry plan. Not started; M0 absorbs its dual-clock/lifecycle ideas for FIS runs. |

## SUPERSEDED (`superseded/`) — DO NOT USE FOR CURRENT TASKS

Executed launch plans/prompts, kept for provenance: `FIS_MSI_Pivot_Guide_Switchyard_Nemotron.html`,
`FIS_R5_Learned_Silent_Failure_Routing_Plan.html`, `FIS_R6_Modern_Local_Specialist_Refresh_Plan.html`,
`FIS_Suite_v3_Benchmark_Release_Goal_Prompt.txt`. See `superseded/README.md`.

**Path map (2026-08-20 moves):** historical documents written before this date cite
these files at `docs/<name>`; they now live at `docs/superseded/<name>` (the four
above) or `docs/reference/<name>` (the five reference designs). Do not "fix" those
citations inside frozen/historical documents.

## EXPERIMENT ARCHIVE (where the data lives)

- `learning/registry/r5/`, `learning/registry/r6/` — cryptographic records (frozen policies, candidate state logs, run ledger).
- Postgres `learning.*` — trajectories, model outputs, routing decisions, case scores (append-only by convention; never truncated by `make corpus`).
- `scenarios/manifests/corpus_v3.json` — corpus identity. `artifacts/` — autopsy + analysis CSVs/JSON.
- `evals/reports/` is gitignored — numbers of record are copied into `experiment-log.md` / `routing-experiments.md`.
