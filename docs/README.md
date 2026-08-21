# Lab Governance

How the Adaptive AI Lab develops, validates, versions, and organizes its
methodology. This directory is normative for **repository/lab process only** — it
never prescribes how to build an AI system (that is `../playbook/`) and never
governs a project's execution (that is `../projects/<name>/`).

## Authority model (who governs what)

| Scope | Normative source |
|---|---|
| Reusable AI-systems methodology | [`../playbook/`](../playbook/README.md) (chapters, templates, references; version in `playbook/VERSION`) |
| A project's plan, parameters, execution, records | `../projects/<name>/` — for FIS: [`../projects/fis/README.md`](../projects/fis/README.md) (its index states the project's internal precedence) |
| Project methodology vs generic playbook | The project's `PLAYBOOK_ADAPTATION.md` wins *for that project*; divergences are recorded there with reasons. Neither overrides the other in its own domain. |
| Lab identity & definition of done | [`LAB_CHARTER.md`](LAB_CHARTER.md) |
| Lab economics & hardware | [`COMPUTE_POLICY.md`](COMPUTE_POLICY.md) + [`GPU_HOURS_LEDGER.md`](GPU_HOURS_LEDGER.md) (one ledger per lab; append-only) |
| Repository/lab decisions | [`LAB_DECISIONS.md`](LAB_DECISIONS.md) (append-only). Project decisions stay in the project's own record (`../projects/fis/OWNER_DECISIONS.md`). |
| Playbook development & evidence policy | [`playbook-development/EVIDENCE_MAP.md`](playbook-development/EVIDENCE_MAP.md) — the maintainer map from playbook rules to project evidence and external corroboration; the firewall keeping project numerics out of shipped generic text |
| Evidence (never normative by itself) | [`../research/`](../research/README.md) (generic, frozen reports) · `../playbook/examples/CASE-*` (curated) · project primary records. The promotion path research → evidence map → chapter rule → CHANGELOG is in `../research/README.md`. |
| Frozen/historical records | Authoritative for the facts and frozen definitions of their own events; never current instructions. |

## Repository model

```
README.md            the lab's front page
playbook/            THE PRODUCT — generic, extraction-ready (validator: playbook/tools/check_playbook.py)
research/            generic evidence (frozen, date-prefixed reports)
docs/                this governance layer + history/
projects/fis/        the first project implementation — ALL FIS primary records
```

Conventions that keep this true:
- **Scope in the path, role in the filename** — for living documents. Frozen,
  historical, ledger-recorded, or code-resolved names are immutable identifiers.
- **Historical citations are never rewritten.** Reorganizations extend the path
  maps (each moved set's index carries one; the FIS map is in
  `../projects/fis/README.md`) instead of editing frozen/historical documents.
- **Provenance relocations are code-level, explicit, and fail-closed.** The one
  existing instance: the R6 contract's sealed freeze-time locator is mapped to its
  current home by `CONTRACT_PATH_RELOCATIONS` in
  `../projects/fis/fis_platform/provenance.py` (added only by audited migrations
  recorded in `LAB_DECISIONS.md`; tested by `test_contract_relocation.py`).
- **Playbook releases** are validated by `make playbook-check` (7 checks including
  the portability/self-containment firewall) and recorded in
  `../playbook/CHANGELOG.md` with evidence; the 1.0 gate is defined there.
- Pure `git mv` for provenance-sensitive artifacts; no history rewrites; the
  `suite-v3` tag is never moved.

## History (`history/`)

Dated repository-development records — provenance, never instructions:
- [`history/playbook-v0.1/`](history/playbook-v0.1/) — the playbook's build
  scaffolding (plans, source maps, authoring specs, planning data, review and
  source-verification records behind v0.1.x).
- [`history/2026-08-21-restructuring/`](history/2026-08-21-restructuring/) — the
  repository re-identification: Pass A design (with owner decisions D1–D6) and the
  Pass B execution report.
