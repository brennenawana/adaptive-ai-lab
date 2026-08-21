# FIS — Fintech Integration Sandbox

The Adaptive AI Lab's **first project implementation**: a realistic synthetic
fintech laboratory for AI-systems methodology — eval-driven model/routing/specialist
selection under frozen contracts, deterministic ground truth, and fail-closed
provenance. FIS is the empirical source of the playbook's real case studies
(`../../playbook/examples/CASE-*`). Its domain is disposable by design
(`clean-room-boundary.md`); the method it exercises is the asset.

Last reorganized: 2026-08-21 (the repository restructuring — see § Path map). If you
read nothing else, read this page.

> **Division of authority.** Reusable methodology lives in
> [`../../playbook/`](../../playbook/README.md) (the Adaptive AI Systems Playbook —
> generic, project-independent); THIS directory is normative for everything FIS:
> its plan, parameters, execution, and records. **Neither overrides the other in
> its own domain.** Lab-level governance (charter, compute policy, lab decisions,
> playbook-development process) lives in [`../../docs/`](../../docs/README.md).
> New/other projects start at `../../playbook/QUICKSTART.md`, never here.

## START HERE (strict reading order)

1. **[PROJECT_PLAN.md](PROJECT_PLAN.md)** — what FIS is building, where it is,
   methodology corrections, series roadmap, milestones. (Formerly
   AI_SYSTEMS_LAB_MASTER_PLAN.md; its lab-level §1/§8/§11 moved to `../../docs/`.)
2. **[SUITE_V4_TRIGGER_REVIEW_PROCEDURE.md](SUITE_V4_TRIGGER_REVIEW_PROCEDURE.md)**
   — the next owner-level task (M0 and M-STAT are executed and accepted;
   `OWNER_DECISIONS.md`).
3. **[PLAYBOOK_ADAPTATION.md](PLAYBOOK_ADAPTATION.md)** — the FIS instantiation of
   the methodology; every FIS experiment follows it. "playbook §N" citations in FIS
   code bind here.
4. **[EXPERIMENT_CONTRACT_TEMPLATE.md](EXPERIMENT_CONTRACT_TEMPLATE.md)** — how to
   write the next contract (v2; new contracts land flat in this directory).
5. **[HANDOFF.md](HANDOFF.md)** — operational state: what runs where, gotchas,
   verification commands.
6. **[`../../research/`](../../research/)** — the two 2026-08 deep-research reports
   (the evidence base for the current plan; see that index's SPRT caveat).

**When documents conflict:** PROJECT_PLAN → PLAYBOOK_ADAPTATION /
contract-template → HANDOFF → everything else. Historical **final reports** stay
authoritative for the facts of their own experiments but never override the current
plan. Historical **plans** are never instructions. Milestone transitions require
owner acceptance recorded in **[OWNER_DECISIONS.md](OWNER_DECISIONS.md)**
(append-only).

## CURRENT / NORMATIVE (the complete set — nothing else here is normative)

| Doc | Role |
|---|---|
| `PROJECT_PLAN.md` | Project strategy + sequencing authority |
| `PLAYBOOK_ADAPTATION.md` | FIS methodology (v1.0) — instantiation of playbook v0.1.1 |
| `EXPERIMENT_CONTRACT_TEMPLATE.md` | Contract template (v2, FIS extension) |
| `SUITE_V4_TRIGGER_REVIEW_PROCEDURE.md` | Standing procedure for the next owner task |
| `TEST_LOOK_LEDGER.md` | TEST-look ledger mirror (machine ledger `learning/registry/test_looks.jsonl` is the record of record; mirror validated fail-closed at every TEST gate) |
| `OWNER_DECISIONS.md` | Owner decision record (append-only; FIS program state) |
| `HANDOFF.md` | Operational state & environment record |
| `architecture.md` | Component map, ports, event topology (normative event-driven requirement) |
| `task-ontology.md` | Scenario classes, root causes, cause→action table |
| `clean-room-boundary.md` | What must never enter this sandbox |
| `experiment-log.md`, `routing-experiments.md` | Append-only experiment records (current through their last dated entry; per-entry "next milestone" lines are historical — sequencing lives in PROJECT_PLAN) |

## FROZEN EXPERIMENT CONTRACTS (binding records — do not edit)

`SUITE_V3_RELEASE_CONTRACT.md`, `R5_EXPERIMENT_CONTRACT.md`,
`R6_EXPERIMENT_CONTRACT.md` remain the binding definitions of their frozen
baselines and completed experiments; amendments are appended below the freeze line,
never inserted. The R6 contract is bound by git blob SHA in the provenance
registry; its freeze-time recorded path `docs/R6_EXPERIMENT_CONTRACT.md` is mapped
to its current location by the audited provenance-relocation record
(`fis_platform/provenance.py::CONTRACT_PATH_RELOCATIONS`, tested by
`tests/test_contract_relocation.py`) — the sealed registry entries and the digested
`GATES` path string keep the historical locator byte-for-byte. They are records,
not plans. New experiments use the v2 template, never these files.

## HISTORICAL EVIDENCE — cite for facts, not current instructions

`SUITE_V3_RELEASE_REPORT.md` · `R5_LEARNED_ROUTING_REPORT.md` ·
`R6_MODERN_LOCAL_SPECIALIST_REFRESH_REPORT.md` · `R6_PERFORMANCE_AUTOPSY.md` ·
`M0_REPORT.md` · `M_STAT_REPORT.md` · `M_STAT_IMPLEMENTATION_MAP.md` (its living
§16 is extracted to `SUITE_V4_TRIGGER_REVIEW_PROCEDURE.md`) · `NEXT_STEP_M0.md`
(executed plan) · `OVERNIGHT_STATUS.md` (live log of the 2026-08-16→19 milestones
M1–M7 — session markers, unrelated to program milestone M0; carries the R3/R3b
pre-registrations) · `SETUP-ACTIONS.md` (bootstrap record).

Each report's "recommended next milestone" was true when written and is superseded
by PROJECT_PLAN. The R6 report's §11 R7 recommendation was accepted via M0
(`OWNER_DECISIONS.md`) and remains gated on the Suite-v4 trigger review.

## REFERENCE DESIGNS (`reference/`) — consult, don't execute

See [`reference/README.md`](reference/README.md): the Canonical Architecture HTML
(two planes, five memory types, specialization ladder), the MSI FIS spec HTML (12
scenario classes, tool contracts; its E0–E8 matrix is closed), the MacBook guide (a
DIFFERENT machine — ignore), and the deferred H0–H3/D0 roadmaps.
`history/superseded/` holds executed launch plans — never instructions
([`history/superseded/README.md`](history/superseded/README.md)).

## Path map (historical citations resolve here; never "fix" them in frozen/historical documents)

- **2026-08-20 moves (pre-restructuring):** historical documents written before
  that date cite the superseded launch plans and reference designs at `docs/<name>`;
  those files then lived at `docs/superseded/<name>` / `docs/reference/<name>`.
- **2026-08-21 restructuring:** everything FIS moved into this directory, filenames
  preserved. `docs/<name>` and `docs/current/<name>` → `projects/fis/<name>`
  (two hops for the sets above: → `projects/fis/history/superseded/<name>` /
  `projects/fis/reference/<name>`). Two living docs were renamed:
  `AI_SYSTEMS_LAB_MASTER_PLAN.md` → `PROJECT_PLAN.md` and
  `EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK.md` → `PLAYBOOK_ADAPTATION.md` (bare-name
  citations of the old names are historical). Also: `docs/research/<name>` →
  `research/<name>` (repo root); `docs/current/GPU_HOURS_LEDGER.md` and
  `docs/current/OWNER_DECISIONS.md` → `docs/GPU_HOURS_LEDGER.md` stayed lab-level /
  `projects/fis/OWNER_DECISIONS.md` respectively; playbook build scaffolding →
  `docs/history/playbook-v0.1/`. The R6 contract's sealed registry locator is
  handled by the code-level relocation record (see § Frozen contracts). Design and
  execution record: `../../docs/history/2026-08-21-restructuring/`.

## EXPERIMENT ARCHIVE (where the data lives)

- `learning/registry/r5/`, `learning/registry/r6/` — cryptographic records (frozen
  policies, candidate state logs, run ledger). `learning/registry/test_looks.jsonl`
  — the hash-chained TEST-look ledger (7 looks spent).
- Postgres `learning.*` — trajectories, model outputs, routing decisions, case
  scores (append-only by convention; never truncated by `make corpus`).
- `scenarios/manifests/corpus_v3.json` — the pinned corpus identity (tracked since
  2026-08-21, owner decision D2; verify with `make corpus-check`, never `--write`
  casually). `artifacts/` — tracked autopsy + analysis CSVs/JSON.
- `evals/reports/` is gitignored raw run output — numbers of record are copied into
  `experiment-log.md` / `routing-experiments.md`.

## Working here

Operate from this directory: `make ps && make test` (see HANDOFF § "Verify
everything is alive"). `.venv` and `.env` live at this root. Clean-tree/provenance
semantics are scoped to this tree (owner decision D3): edits elsewhere in the lab
repo don't dirty FIS runs; anything modified or untracked inside this tree still
refuses fail-closed.
