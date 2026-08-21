# Lab Decision Record

> STATUS: CURRENT / NORMATIVE (append-only). Decisions of the lab owner (Brennen)
> that move **repository/lab state**: identity, structure, governance, playbook
> releases, cross-project policy. Rows are appended, never edited. Project-level
> decisions (milestone acceptances, experiment authorizations) live in each
> project's own decision record — for FIS: `../projects/fis/OWNER_DECISIONS.md`
> (owner decision D4 below keeps that record project-scoped).

| Date | Decision |
|---|---|
| 2026-08-21 | **Repository restructuring authorized and accepted (Pass B, decisions D1–D6).** The repository is re-identified as the **Adaptive AI Lab**: `playbook/` is the primary reusable product, `research/` the generic evidence layer, `docs/` the lab-governance layer, `projects/fis/` the first project implementation holding all FIS primary records. D1: full implementation move executed. D2: `projects/fis/scenarios/manifests/corpus_v3.json` verified `--check`-identical to the frozen Suite-v3 identity and tracked. D3: FIS clean-tree/provenance semantics scoped to the FIS provenance dependency closure (`projects/fis/`), identically in dirty-path determination and `-dirty` commit identity (`fis_platform/suite.py`, `fis_platform/provenance.py`; tests `test_fis_scope.py`). D4: the FIS owner-decision record stays project-scoped at `projects/fis/OWNER_DECISIONS.md`; this lab record is created for repository-level decisions. D5: the Pass A design and the migration report archive to `history/2026-08-21-restructuring/`. D6: the frozen R6 contract moved to `projects/fis/R6_EXPERIMENT_CONTRACT.md` via the explicit fail-closed provenance-relocation record (`fis_platform/provenance.py::CONTRACT_PATH_RELOCATIONS`; tests `test_contract_relocation.py`); the sealed historical locator, the digested `GATES` path string, and every chained registry digest are byte-unchanged; R6 was not rerun and no DEV/TEST look was consumed. Design authority: `history/2026-08-21-restructuring/RESTRUCTURING_PASS_A.md` (with its D1–D6 addendum); execution record: `history/2026-08-21-restructuring/PASS_B_REPORT.md`. |
