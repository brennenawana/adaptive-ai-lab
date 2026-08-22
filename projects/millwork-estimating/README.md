# Millwork Estimating — discovery project

The Adaptive AI Lab's **second project implementation**. This project applies the
[Adaptive AI Systems Playbook](../../playbook/README.md) to architectural millwork,
custom cabinetry, specialty wood manufacturing, installation, and contract/bid
estimating.

**Status:** prospective-client discovery. There is no formal client engagement or
production authorization yet. The only prospect-specific primary source currently in
this repository is the estimating-process description supplied during discovery.
Public documents under `research/` are surrogates, not evidence of how this prospect's
actual files are structured.

> **Division of authority.** Reusable methodology lives in `../../playbook/`.
> This directory owns only this project's hypotheses, research, future contracts,
> execution records, and project-private source material. Nothing learned here becomes
> generic playbook doctrine merely because it worked on this project.

## START HERE

1. **[PROJECT_PROFILE.md](PROJECT_PROFILE.md)** — current intake profile and unknowns.
2. **[WORKFLOW_HYPOTHESIS.md](WORKFLOW_HYPOTHESIS.md)** — what the present human flow
   appears to be and the first software/agent decomposition we should test.
3. **[PLAYBOOK_PATH.md](PLAYBOOK_PATH.md)** — high-level path from discovery to a
   measured, human-approved production pilot.
4. **[research/README.md](research/README.md)** — what the public research supports,
   what is inferred, and what remains unknown.
5. **[research/SURROGATE_PACK.md](research/SURROGATE_PACK.md)** — public surrogate
   document pack and source-by-source rationale.
6. **[`source/client/Estimating Process.txt`](source/client/Estimating%20Process.txt)**
   — prospect-supplied primary process description; preserve as received.

## Project thesis

The project is **not** "make a small local model imitate an estimator." The initial
problem is to turn a document-heavy, judgment-heavy workflow into a measurable
execution system whose failure modes are visible and whose commercial outputs remain
human-approved.

Initial production hypothesis:

```text
current project documents
        ↓
revision-aware ingestion + document index
        ↓
frontier multimodal reasoning + bounded agent skills
        ↓
structured takeoff / scope observations with source provenance
        ↓
deterministic estimating tools and business rules
        ↓
verification + exception/uncertainty queue
        ↓
human estimator review and approval
        ↓
proposal / handoff artifacts
        ↓
actual outcomes + corrections feed the eval corpus
```

The model is one component of the execution system, not the product by itself.

## Defaults until evidence changes them

- **Frontier-first.** Start with a strong managed multimodal model rather than forcing
  a weak local model to clear the capability floor.
- **Eval-first.** Historical completed projects should become the main evaluation
  substrate as soon as the prospect can safely provide examples.
- **Deterministic math.** Quantity arithmetic, unit conversions, waste factors,
  labor formulas, rollups, and sanity checks belong in tools/code wherever possible,
  not in free-form model reasoning.
- **Source-grounded outputs.** Every material scope/quantity/qualification should be
  traceable to sheet/page/room/detail/spec evidence when the source permits it.
- **Human approval.** No autonomous bid submission, final pricing commitment, or
  contract qualification during the initial production stages.
- **Skills/workflows are experimental objects.** We measure document indexing,
  traversal strategy, tool schemas, context policy, verification, decomposition,
  and reviewer UX even if the production model stays fixed.
- **Local models are optional R&D proxies.** They are useful only for intervention
  classes whose direction/ranking transfers to the frontier production target.
- **Fine-tuning is not a default.** It is considered only after a persistent,
  taxonomy-identified learnable gap remains after cheaper rungs are cleared.

## Current evidence state

Known from the prospect-provided process description:

- Go/No-Go review examines drawings, schedule, funding, location, competition,
  specification disqualifiers, wage/union requirements, AWI/QCP requirements,
  pre-approved vendors, and special casework constraints.
- Estimating is organized around Bluebeam takeoff followed by an Excel Bid Recap.
- Takeoff is room-by-room and spans floor plans, elevations, sections, finish
  schedules, and details.
- Pricing combines explicit formulas with estimator/team judgment, install duration,
  travel, drafting/CNC effort, and sanity-check ratios.
- The final proposal carries the bid amount plus exclusions/qualifications and is
  reviewed before submission.

Still unknown: the actual Bluebeam Tool Chest/markup schema, the Excel workbook and
formula topology, material/vendor-price sources, historical estimate accuracy,
review/override patterns, revision-change workflow, and the exact contract
assignment/resale workflow.

## First external ask

Keep the pre-contract request small. Highest-value examples are:

```text
- Architectural drawings
- Completed takeoff
- Bid recap spreadsheet
- Final proposal
- Job cost summary
```

Ideally these come from the same finished project; one coherent project chain is more
valuable than five unrelated examples.
