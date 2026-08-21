# Repository Restructuring — Pass A Migration Design

**STATUS: ACCEPTED WITH AMENDMENTS — Pass B authorized 2026-08-21. See the addendum below; where it conflicts with the body, the addendum governs.**

## Addendum (2026-08-21): owner decisions D1–D6 authorizing Pass B

- **D1 — Full implementation move: YES.** Stage 4 (the FIS implementation/runtime unit) executes now, not deferred. The final root is `README.md · Makefile · playbook/ · research/ · docs/ · projects/fis/`.
- **D2 — Track `corpus_v3.json`: YES.** Verify with `--check` against the frozen Suite-v3 identity first; `--write` is an explicit suite-identity operation and is not used. Suite v3 is not regenerated or altered.
- **D3 — Scope FIS clean-tree semantics: YES** (supersedes the body's D3 recommendation to keep whole-repo semantics). After the migration, re-enumerate the FIS provenance dependency closure and scope both dirty-path determination and the recorded `-dirty` commit-identity to that closure via one shared implementation, fail-closed. Edits to `playbook/`, `research/`, or lab-governance prose no longer dirty an unchanged FIS execution system.
- **D4 — `OWNER_DECISIONS.md` stays FIS-scoped** (supersedes §9c, which sent it to `docs/`). Its rows move FIS program state, so it lands at `projects/fis/OWNER_DECISIONS.md`, append-only history intact. A distinct lab-governance record (`docs/LAB_DECISIONS.md`) is created for repository-level decisions, and the restructuring authorization/acceptance is recorded there — not mixed into the FIS state log.
- **D5 — Archive this document after Pass B** into a dated history location (`docs/history/2026-08-21-restructuring/`, alongside the final migration report). The root stays small and product-oriented.
- **D6 — `docs/R6_EXPERIMENT_CONTRACT.md` MOVES** (supersedes the body's "pinned exception permanently in `docs/`", §1/§9b/§10). The owner rejects a stranded FIS artifact in `docs/`. The contract moves to `projects/fis/R6_EXPERIMENT_CONTRACT.md` via a narrow, explicit, fail-closed **provenance relocation mechanism**: historical recorded locators (sealed `contract_path` strings, the digested `GATES` path string, chained entries) remain byte-identical; the verifier maps the historical locator to the audited current canonical path; unknown relocations fail closed; the frozen blob's prefix-extension rule still validates against the moved bytes; R6 is **not** rerun and consumes no new look. Mechanism, call-site inventory, and required tamper/fail-closed tests are recorded with the implementation.

Execution discipline is unchanged: pure `git mv` for provenance-sensitive artifacts before any permitted living-document edits; snapshot/copy/verify for untracked evidence; no history rewrite; no `suite-v3` tag changes; staged green commits; the full validation battery plus the new relocation and scoped-dirty tests.

---

**Original proposal as reviewed (body unchanged below; D1–D6 above govern):**
Date: 2026-08-21 · Author: Claude (planning pass) · Scope: information architecture only — no methodology changes, no playbook version bump, no experimental-state changes.

Evidence base: 11-agent parallel inventory + adversarial verification over all 391 tracked files, the reference graph, every hash binding, and git/environment state. Every load-bearing claim below was verified by reading the implementing code or data; file:line citations are to HEAD (`bb44afa`).

One change was already made in this pass (a live defect, fixed per standing owner rule "enforce flagged deviations immediately"): `.claude/hooks/session-start-docs.sh` claimed the repo lives at `~/adaptive-ai-lab`, which does not exist. The two location lines now say `~/projects/adaptive-ai-lab`. The hook's identity/paths rewrite remains a Pass B item. Nothing else was touched.

---

## 1. Executive recommendation

**Identity.** This repository is the **Adaptive AI Lab**: it develops, validates, and improves the **Adaptive AI Systems Playbook** (`playbook/`, v0.1.1 — the primary, extraction-ready product) through generic research (`research/`) and real project implementations (`projects/`). The **Fintech Integration Sandbox (FIS)** is the first project implementation and the empirical source of the playbook's case studies — it is no longer the repository's identity.

**Central architectural decision.** Move the entire FIS surface — 25 documents, 10 implementation directories, its Makefile, pyproject, env files, and untracked evidence — under a **flat `projects/fis/`** that keeps every historical filename, while `docs/` becomes the repository/lab governance layer and `docs/research/`'s two reports become top-level `research/`. Flat, with filenames preserved, because the FIS document corpus is a dense web of **bare-filename citations inside frozen documents that may never be edited** — a single flat directory is the only layout in which those citations keep resolving.

**One permanent exception.** `docs/R6_EXPERIMENT_CONTRACT.md` **cannot move, ever.** Its repo-relative path is sealed inside the hash-chained R6 provenance registry (`contract_path` in all three candidates' `state.jsonl`), re-resolved at runtime via `git show HEAD:docs/R6_EXPERIMENT_CONTRACT.md` (`fis_platform/provenance.py:1244/1253/2478`), and embedded as a digested member of the frozen `GATES` dict (`fis_platform/r6_gates.py:24`). The registry is append-only by design; a redirect stub cannot satisfy the byte-prefix-extension rule. It stays in `docs/` as a documented pinned exception. (Verified live: HEAD blob `01811b52…` = frozen blob `0604d661…` + legal appends.)

**FIS stays in this repository.** Extraction criteria are defined (§14) but none is met; the playbook's 1.0 gate explicitly requires a second project instantiation, and FIS adjacency is what validates generalization.

**Biggest current structural problems.**
1. The root README, Makefile header, pyproject metadata, and both `.claude` hooks present the repository as FIS and re-imprint the old identity into every fresh session (the session hook also declared a wrong repo location — now fixed).
2. `docs/current/` means "current **for FIS**" without saying so, and the doc index's authority chain still names the executed `NEXT_STEP_M0.md` as "the single authorized next task" (M0 was accepted 2026-08-21 per `OWNER_DECISIONS.md`).
3. Two documents legitimately named "playbook" coexist (`playbook/` and `docs/current/EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK.md`) — the task premise that the latter is superseded is **wrong** (see §2), but the naming makes them look like competitors.
4. All FIS implementation code sits at the root, so the filesystem says "FIS repo with a playbook folder" instead of "lab with a playbook product and one project."
5. A lab-level layer (hardware/compute policy, owner decision record, GPU-hours ledger, lab charter) is currently buried inside FIS's `docs/current/`.

**Timing constraint (important).** The migration should land **before the Suite-v4 trigger review is planned and before the R7 contract freeze.** When TEST look #8 is planned, the trigger-review document's path is baked into the hash-chained TEST-look ledger and existence-rechecked at spend time (`fis_platform/test_looks.py:140-157,336`); when R7 freezes, its contract path is blob-bound into the registry. Migrating after either event bakes old-IA paths into unamendable records.

---

## 2. Current-state diagnosis

### Premise corrections (found by inspection; the design below incorporates them)

| Task premise | What the repository shows |
|---|---|
| "`docs/` becomes repository-level governance" | Not fully achievable. `docs/R6_EXPERIMENT_CONTRACT.md` is path-bound into the append-only registry and must stay forever (pinned exception). `docs/` becomes *governance + a one-file frozen-contract vault*. |
| "The old FIS playbook is superseded by `playbook/`" | **False.** `docs/README.md` records an explicit owner division of authority (2026-08-21): "`playbook/` = reusable methodology for any project; `docs/current/` = this project's specific application… **Neither overrides the other in its own domain.**" The FIS playbook v1.0 is the living normative methodology for FIS (its §11 maps every rule to `fis_platform` enforcement code; the R7 freeze depends on it). It becomes the project **adaptation**, not an archive. |
| "Reconcile the duplicate experiment-contract template" | Not duplicates: `playbook/templates/EXPERIMENT_CONTRACT.md` is a functional **superset** (same 18-section apparatus + rigor tiers, amendment-legitimacy rules, filled example), while the FIS v2 template keeps project bindings the generic one deliberately genericizes (SMOKE registry precondition, DEV/TEST names, blob binding, N_eff≈22, the `docs/<ID>` copy-target). `fis_platform/contract_spec.py` machine-checks the v2 shape and `CONTRACT_FROZEN` refuses without a validated spec. It becomes the project **extension**. Frozen contracts do *not* cite it as their template-of-record (they predate v2). |
| "`scenarios/manifests/*.json` are gitignored generated outputs" | True per `.gitignore`, but it contradicts the frozen record: `SUITE_V3_RELEASE_CONTRACT.md` §2E.5 (and docs/README, HANDOFF, the release report) say `corpus_v3.json` is "**(tracked)**". It is actually untracked — a pre-existing repo-integrity defect (owner decision D2, §15). It is also load-bearing: `run_eval.py:355-366` fails closed without it. |
| "infra data volumes are relative bind mounts" (implicit in path-risk worries) | **False.** `infra/compose.yaml` uses *named* Docker volumes (`fis_pgdata` etc.) keyed by compose project `name: fis`. Moving `infra/` orphans nothing, provided `name: fis` is preserved verbatim. The `.gitignore` `infra/pgdata|natsdata|miniodata` entries are vestigial. |
| "Scope in path, role in filename" applies everywhere | It cannot be applied to the frozen/registry layer: renaming any of the ~20 historical FIS docs orphans bare-filename citations inside unfixable frozen files, shipped playbook CASE studies, and code docstrings. The principle is applied via the **directory** (`projects/fis/`); only two *living* docs are renamed. |
| DB may store repo paths | **Cleared with evidence.** All 9 migrations and every INSERT site write ids, digests, and JSONB only — no repo file paths enter Postgres. Directory moves cannot break replay tooling. |
| Packaging must be preserved | The editable install is **already dead** (`.venv` `.pth` points at the deleted `~/projects/fintech-integration-sandbox`; pyproject's wheel `packages` list names a never-existent `platform_` and omits `fis_platform`). Everything runs on per-file `sys.path` anchors. The migration must *repair* packaging, not preserve it. |

### Per-area diagnosis

**Root (`README.md`, `Makefile`, `pyproject.toml`, `.gitignore`, `.env*`)** — Role: repo front door. Actual scope: 100% FIS-operational except `make help/test/lint`. Problem: carries the old identity on line 1; Makefile has no playbook target at all — the primary product has zero automation. Risk: low (living files), but they must be updated in the same commits as moves or every entry point dangles.

**`docs/` root (16 files)** — Role per its own index: 1 index, 4 living-normative FIS docs (HANDOFF, architecture, task-ontology, clean-room-boundary), 2 append-only records-of-record (experiment-log, routing-experiments — the durable numbers for the gitignored `evals/reports/`), 3 frozen contracts, 6 historical evidence docs. All FIS-scoped. Problem: none internally — the discipline is excellent — but it occupies the repo's conceptual root. Risk: the bare-filename citation web (contracts ↔ reports ↔ logs, in both directions across the frozen/living boundary) plus the R6 path binding.

**`docs/current/` (10 files)** — Mixed: FIS program docs (master plan §§2–7/9/10, FIS playbook, contract template, M0/M-STAT records, NEXT_STEP_M0) **plus a hidden lab-level layer** (master plan §1 identity / §8 hardware policy / §11 definition-of-done; `GPU_HOURS_LEDGER.md` — lab-scoped by the playbook's own "one ledger per fleet/lab" doctrine; `OWNER_DECISIONS.md` — the program acceptance mechanism). Problems: "current" states no scope; the index and hook still crown the executed NEXT_STEP_M0. Hard risk: `TEST_LOOK_LEDGER.md` is machine-validated at every TEST-gate run (`test_looks.py:417`, `run_eval.py:476`) and is an exists-on-disk test fixture.

**`docs/research/` (3 files)** — Two frozen, adversarially-verified research reports (the playbook's evidence base — clearly generic: they pass "still matters if FIS disappeared") plus one file that is *not research*: `PLAYBOOK_INTERNAL_EVIDENCE_MAP.md`, a living playbook-maintainer document ("NOT part of the shipped playbook") that is the designed firewall keeping FIS numerics out of shipped text. Hard risk found here: the 2026-08-20 report is **line-number-bound** by living code (`fis_platform/stats.py:303`, `scripts/mstat_stats.py:2/56/83` cite "lines 66/84/94") and by tracked evidence (`artifacts/mstat_standing_facts.json`) — pure rename only, never reflow.

**`docs/reference/` + `docs/superseded/`** — All five reference HTMLs are Company-Intelligence-Platform program documents (the program FIS serves), ~249 KB with zero shipped-playbook dependency; the four superseded files are executed FIS launch plans cited from inside frozen contracts at pre-2026-08-20 paths (already non-resolving *by design* — the path-map precedent). Both sets are clean FIS moves.

**`playbook/` (71 files)** — The shipped product is already extraction-shaped and machine-enforced: `check_playbook.py` (7 checks, all PASS at HEAD, verified by running it read-only) bans FIS strings, `docs/` links, and `adaptive-ai-lab|/home/wall` literals from shipped files. Problems: three root scaffolding docs + `planning/` (dev history) sit inside the product; the release validator itself is mis-filed *inside* the scaffolding it excludes; no Makefile/CI target runs it. Outbound provenance from shipped files is minimal and known exactly (§8).

**Implementation trees (`fis_platform/ evals/ scenarios/ schemas/ services/ scripts/ tests/ learning/ artifacts/ infra/`)** — One tightly coupled FIS unit; **nothing is shared tooling** (grep-verified: nothing outside these trees imports them; the only genuinely generic-leaning code — `stats.py`, `passk.py`, `tolerances.py`, `contract_spec.py`, `test_looks.py`, `predictions.py`, `ordering.py`, `schemas/common.py` — is the playbook-enforcement layer, flagged for *future* extraction, not now). Every module self-anchors via `Path(__file__).parents[N]`, so the unit moves atomically with almost no import changes. The exceptions are three git-subprocess guards in `provenance.py` that assume repo-root-relative paths (§10) and the runtime doc bindings above.

**`learning/` + `artifacts/`** — Append-only cryptographic evidence. All chain digests are content-only (a byte-identical `git mv` invalidates nothing); the path couplings live in *code* (fixable in the same commit) and in *sealed record strings* (never rewritten — path map covers them). `evals/reports/` (~110 untracked files) and `corpus_v3.json` are untracked but irreplaceable/load-bearing — a git-only migration silently loses both.

**`.claude/`** — `settings.json` is fully portable (`$CLAUDE_PROJECT_DIR`, no hardcoded paths). Both content hooks are active references that must be rewritten with the migration: the SessionStart hook injects the old identity + old reading order into every session; the PreCompact hook directs decision-flushing to four `docs/` paths that will move.

**git/env** — Clean tree, `main`, origin `brennenawana/adaptive-ai-lab` (already the new identity). No CI, no submodules/LFS/symlinks/case hazards, no pre-commit. Sole tag `suite-v3` → `7764601f…` (verified; never delete/re-point). Docs cite commits by SHA → **never rewrite history**. Do **not** rename the repo root directory: `~/.claude/projects/` already holds orphaned memory dirs from two previous moves; a third would orphan current auto-memory. The 2026-08-20 reorganization (`4948d5a`) is the in-repo precedent for exactly this migration pattern (pure `git mv` + same-commit reference updates + append-only status notes + a path map + "do not fix citations inside frozen/historical documents").

---

## 3. Proposed target information architecture

```
adaptive-ai-lab/
├── README.md                                   GOVERNANCE   [rewritten — lab identity front page]
├── Makefile                                    SHARED       [new thin delegator: fis-*, playbook-check, test]
├── .gitignore                                  SHARED       [generic rules only]
│
├── playbook/                                   PRODUCT      (Adaptive AI Systems Playbook v0.1.1)
│   ├── README/QUICKSTART/GLOSSARY/CHANGELOG/VERSION
│   ├── 00…14 chapters, templates/ (9), references/ (ledger + rendered + formulas + recipes)
│   ├── examples/                               PRODUCT+EVIDENCE (CASE quarantine zone — FIS numerics live here by design)
│   └── tools/check_playbook.py                 PRODUCT      [release validator, split out of planning/]
│
├── research/                                   EVIDENCE     (generic; frozen on landing; date-prefixed)
│   ├── README.md                               [new: status conventions, SPRT caveat, extraction status]
│   ├── 2026-08-19_NVIDIA_AI_Lab_Playbook_Research.md
│   └── 2026-08-20_AI_Lab_Methodology_Hardware_Strategy.md   [pure rename — line-number-bound]
│
├── docs/                                       GOVERNANCE   (repo & lab: how the methodology is developed)
│   ├── README.md                               [new governance index: authority model, path maps, pinned exception]
│   ├── LAB_CHARTER.md                          [from master plan §1 + §11, rewritten under new identity]
│   ├── COMPUTE_POLICY.md                       [from master plan §8]
│   ├── GPU_HOURS_LEDGER.md                     [lab-scoped ledger — playbook doctrine: one per lab]
│   ├── OWNER_DECISIONS.md                      [program acceptance record; gains the migration-acceptance row]
│   ├── playbook-development/EVIDENCE_MAP.md    [was docs/research/PLAYBOOK_INTERNAL_EVIDENCE_MAP.md]
│   ├── history/playbook-v0.1/                  HISTORY      [playbook build scaffolding: 3 root docs + planning/]
│   └── R6_EXPERIMENT_CONTRACT.md               PROVENANCE   ★ PINNED — path-bound in the R6 registry; never moves
│
└── projects/
    └── fis/                                    PROJECT      (flat; every historical filename preserved)
        ├── README.md                           [FIS index: authority chain, reading order, path map]
        ├── PROJECT_PLAN.md                     [was AI_SYSTEMS_LAB_MASTER_PLAN.md §§2–7,9,10 — living, renamed]
        ├── PLAYBOOK_ADAPTATION.md              [was EXPERIMENTAL_AIS_PLAYBOOK.md v1.0 — living, renamed]
        ├── EXPERIMENT_CONTRACT_TEMPLATE.md     [v2 — project extension of playbook/templates/EXPERIMENT_CONTRACT.md]
        ├── TEST_LOOK_LEDGER.md                 [machine-validated mirror — moves in the code stage, 4 coordinated edits]
        ├── SUITE_V4_TRIGGER_REVIEW_PROCEDURE.md [new: §16 of M_STAT_IMPLEMENTATION_MAP, extracted as living doctrine]
        ├── HANDOFF.md · architecture.md · task-ontology.md · clean-room-boundary.md
        ├── experiment-log.md · routing-experiments.md            (append-only records of record)
        ├── SUITE_V3_RELEASE_CONTRACT.md · R5_EXPERIMENT_CONTRACT.md        (frozen — byte-identical git mv)
        ├── SUITE_V3_RELEASE_REPORT.md · R5_LEARNED_ROUTING_REPORT.md
        ├── R6_MODERN_LOCAL_SPECIALIST_REFRESH_REPORT.md · R6_PERFORMANCE_AUTOPSY.md
        ├── OVERNIGHT_STATUS.md · SETUP-ACTIONS.md
        ├── M0_REPORT.md · M_STAT_REPORT.md · M_STAT_IMPLEMENTATION_MAP.md · NEXT_STEP_M0.md
        ├── reference/                          PROVENANCE   [5 program-design HTMLs + README]
        ├── history/superseded/                 PROVENANCE   [4 executed launch plans + README]
        ├── fis_platform/ · evals/ · scenarios/ · schemas/ · services/ · scripts/ · tests/
        ├── learning/                           PROVENANCE   [registries — byte-identical git mv]
        ├── artifacts/                          PROVENANCE   [tracked evidence — byte-identical git mv]
        ├── infra/
        ├── Makefile · pyproject.toml · .gitignore · .env · .env.example · .venv/ (rebuilt)
```

Why **flat** `projects/fis/` and not `experiments/<id>/` subdirectories or a `docs/` subtree: the frozen contracts, reports, and append-only logs cite each other **by bare filename in both directions** (e.g. frozen `SUITE_V3_RELEASE_CONTRACT` §1 → `routing-experiments.md`; frozen `R5_EXPERIMENT_CONTRACT` §12 → `SUITE_V3_RELEASE_REPORT.md`; ~18 bare-name cites of `OVERNIGHT_STATUS.md` across frozen reports), and those citations may never be edited. One flat directory is the only geometry in which the entire web keeps resolving. Completed milestone reports (M0/M-STAT) stay flat for the same reason. The `reference/` and `history/superseded/` subsets keep their subdirectories because they are annotated sets whose READMEs are living (links updatable) and nothing cites their members by bare name from outside the set.

---

## 4. Authority model

Precedence within any scope runs down the table; cross-scope conflicts are resolved by the scope column — a document is normative only for questions inside its scope.

| Scope | Normative source | Governs | Does NOT govern |
|---|---|---|---|
| Reusable AI-systems methodology | `playbook/` (chapters, templates, references; version = `playbook/VERSION`) | How any project builds/evaluates/operates AI systems; what a new project does first | FIS's current state or parameters; repo organization |
| FIS project | `projects/fis/README.md` index → `PROJECT_PLAN.md` (sequencing) → `PLAYBOOK_ADAPTATION.md` + `EXPERIMENT_CONTRACT_TEMPLATE.md` (method as instantiated) → `HANDOFF.md` (operational state) | Everything FIS: sequencing, parameters, execution, environment | Generic methodology; other projects |
| Program/lab decisions | `docs/OWNER_DECISIONS.md` (append-only; "milestone reports recommend; only entries here accept") | Milestone transitions, doctrine changes, this migration's acceptance | Technical content of any experiment |
| Lab charter & economics | `docs/LAB_CHARTER.md`, `docs/COMPUTE_POLICY.md` + `docs/GPU_HOURS_LEDGER.md` | Lab identity, definition-of-done, hardware buy/rent triggers | Project sequencing |
| Methodology development | `docs/` (playbook-development process, evidence policy, naming/versioning, this design) + `docs/playbook-development/EVIDENCE_MAP.md` | How playbook rules are derived, audited, versioned, released | AI-system engineering itself |
| Evidence | `research/` (informative, frozen) · `playbook/examples/CASE-*` (curated, informative) · `projects/fis/` records + `learning/` + `artifacts/` (primary) | Facts and provenance | Nothing — evidence never overrides a normative doc; it *changes* one via the documented promotion path (research → evidence map → chapter rule → CHANGELOG) |
| Frozen/historical records | The record itself (contracts, reports, logs, registries) | The facts and frozen definitions of their own events | Current instructions — "historical plans are never instructions" (retained verbatim from the current index) |

Conflict rules a new engineer needs, stated explicitly in the two indices:
- **Generic playbook rule vs project adaptation:** the adaptation wins *for that project*; the divergence must be recorded in the adaptation with a reason.
- **Current project plan vs frozen contract:** the frozen contract wins for its own experiment's definition; the plan wins for what happens next.
- **Research vs normative chapter:** the chapter wins; research is input. (The SPRT caveat is the standing example: the 08-20 report's §2.3 stale rows are overridden by its own corrections and the playbook.)
- **Case-study lesson vs generic method:** the chapter wins; cases are evidence with provenance.
- **`docs/` governance vs playbook methodology:** disjoint scopes; `docs/` never prescribes how to build an AI system, `playbook/` never prescribes how this repo is organized.
- **Code-as-record:** section references like "playbook §7" in `fis_platform`/scripts/tests docstrings bind to `projects/fis/PLAYBOOK_ADAPTATION.md` (which keeps its §-numbering), not to `playbook/` chapters. Declared in the adaptation's header.

---

## 5. Naming conventions

**Principle: scope in the path, role in the filename — applied to living files only.** Frozen, historical, ledger-recorded, or code-resolved names are immutable identifiers, not prose to normalize.

| Class | Rule | Examples |
|---|---|---|
| Current project authority | Role-oriented SCREAMING_SNAKE at project root | `projects/fis/PROJECT_PLAN.md`, `HANDOFF.md`, `PLAYBOOK_ADAPTATION.md` |
| Frozen contracts | `<ID>_EXPERIMENT_CONTRACT.md`, filename never changes after freeze; new contracts land flat at `projects/fis/` (template's copy-target updated **before** R7) | `R7_EXPERIMENT_CONTRACT.md` (future) |
| Experiment/milestone reports | `<ID>_…_REPORT.md`, frozen filename, flat beside their contracts | `M0_REPORT.md` |
| Append-only records | lowercase-hyphen historical names kept forever | `experiment-log.md`, `routing-experiments.md` |
| Research reports | `research/YYYY-MM-DD_Topic.md`; frozen on landing; corrections via new dated reports or index annotations, never edits (code may bind by line number) | `2026-08-20_AI_Lab_Methodology_Hardware_Strategy.md` |
| Case studies | `playbook/examples/CASE-NNN_slug.md`; FIS citations inside are bare-filename snapshots (see §10) | — |
| Methodology-development records | `docs/history/<release>/…`, structure preserved verbatim | `docs/history/playbook-v0.1/planning/…` |
| Generated/runtime | gitignored, path-anchored rules live in the owning project's `.gitignore` | `projects/fis/evals/reports/` |
| Ledgers of record | machine ledger path is code ("named in exactly one place"); human mirror beside it | `learning/registry/test_looks.jsonl` ↔ `TEST_LOOK_LEDGER.md` |
| Runtime identifiers (permanent, never rename) | `FIS_` env prefix, compose project `fis`, containers `fis-*`, volumes `fis_*`, DB `fis`/`fis_tools`, package `fis_platform`, import package `scripts` | — |

Only two renames in the whole migration, both living-normative docs whose old names misstate scope: `AI_SYSTEMS_LAB_MASTER_PLAN.md → PROJECT_PLAN.md` (after its lab-level sections split out) and `EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK.md → PLAYBOOK_ADAPTATION.md`. Everything else keeps its filename — including cryptic-but-cited names (`OVERNIGHT_STATUS.md` carries the only R3/R3b pre-registration records and is bare-name-cited from all three frozen contracts).

---

## 6. FIS migration model

- **`docs/current/` is dissolved.** Living authority flattens into `projects/fis/` (index, plan, adaptation, template, trigger-review procedure, TEST-look mirror); completed records flatten beside them; the lab-level layer (`GPU_HOURS_LEDGER`, `OWNER_DECISIONS`, master-plan §1/§8/§11) rises to `docs/`. Nothing named "current" survives.
- **Master plan → SPLIT.** `git mv` to `projects/fis/PROJECT_PLAN.md` (history preserved), then a separate owner-gated content commit removes §1/§11 (→ `docs/LAB_CHARTER.md`) and §8 (→ `docs/COMPUTE_POLICY.md`) and re-authors the precedence header (NEXT_STEP_M0 is executed; the successor "next task" is the Suite-v4 trigger review). Master-plan edits move program state, so this lands with an `OWNER_DECISIONS.md` acceptance row.
- **Old FIS playbook → `PLAYBOOK_ADAPTATION.md`** (living, normative for FIS). Header re-declared: "the FIS instantiation of Adaptive AI Systems Playbook v0.1.1; §-references in FIS code bind here." Keeps internal §-numbering so every "playbook §N" docstring stays resolvable. Its irreplaceable content: FIS parameters (144/48/96 splits, 36-case SMOKE, ICC 0.475 → N_eff≈22, ~37pp MDE, 7-look state, restart-flip facts, canary-at-v4 rule) and the §11 code-enforcement map. Not archived — see §2 premise correction.
- **Old contract template → project extension**, moved as-is; its copy-target instruction ("Copy this file to `docs/<ID>_…`") is updated to `projects/fis/<ID>_EXPERIMENT_CONTRACT.md` **before R7 freezes**.
- **HANDOFF** moves whole (living record; body below the 08-20 header is a deliberate snapshot — append/prefix only). As a living doc it is *exempt* from the do-not-fix rule: its stale `fintech-integration-sandbox` path mentions may be corrected. A future split of its lab-generic sections (WSL gotchas, model/effort guidance) into a lab ops doc is flagged but deferred.
- **architecture / task-ontology / clean-room-boundary** move whole (living-normative for FIS). `services/ai_orchestrator/prompts.py:30`'s normative-mirror comment and `fis_platform/suite.py` docstrings update in the same commit.
- **Contracts:** `SUITE_V3` and `R5` move byte-identically via `git mv` (content-bound freeze only — verified no runtime path resolution); `R6` **stays** (§1). Two living code strings update with the move: `evals/runner/compare.py:106` (prints the Suite-v3 contract path in a user-facing caveat) and `scripts/r5_amend_rule.py:84` (writes the R5 contract citation into future registry JSON). The already-committed `learning/registry/r5/selection_rule.json` citation of the old path is sealed history — never edited; path map covers it.
- **Reports, autopsy, OVERNIGHT_STATUS, SETUP-ACTIONS, both append-only logs:** pure `git mv`, filenames kept, zero content edits below status headers.
- **M-STAT map §16 (Suite-v4 trigger-review procedure)** is *copied* out into `projects/fis/SUITE_V4_TRIGGER_REVIEW_PROCEDURE.md` (living doctrine for the imminent next owner task must not live inside an executed historical plan); the map itself moves unchanged. Do this **before** look #8 is planned, so `trigger_review_ref` bakes the new path.
- **NEXT_STEP_M0** moves with an **appended** status note ("executed 2026-08-20/21; accepted per OWNER_DECISIONS row 1; see M0_REPORT.md") and is removed from every index/hook "next task" slot.
- **TEST_LOOK_LEDGER.md** moves **only in the atomic code stage**, with exactly four coordinated edits: `fis_platform/test_looks.py:417` (`default_markdown_path` → `_ROOT/"TEST_LOOK_LEDGER.md"`), `evals/runner/run_eval.py:476`, and the two `REAL_REVIEW_REF` fixtures (`tests/test_mstat_runner.py:48`, `tests/test_mstat_test_looks.py:45`). Table rows byte-preserved (field-exact validation against the machine ledger). The sealed `"docs/current/TEST_LOOK_LEDGER.md backfill"` strings in the machine ledger are never rewritten. (Fallback if the owner prefers zero code edits: keep a `projects/fis/docs/current/` shell for this one file — rejected here because it perpetuates the "current" pattern for one file at the cost of four verified edits.)
- **reference/ → `projects/fis/reference/`** (program-design docs, byte-identical; README links re-pointed; H0–H3/D0 re-home to their own `projects/<name>/` only if those programs ever activate). **superseded/ → `projects/fis/history/superseded/`** (byte-identical; README updated; path map gains the two-hop history `docs/<name>` → `docs/superseded/<name>` → `projects/fis/history/superseded/<name>`).
- **Implementation/runtime:** the entire unit (`fis_platform/ evals/ scenarios/ schemas/ services/ scripts/ tests/ learning/ artifacts/ infra/` + `Makefile` + `pyproject.toml` + `.env*` + FIS `.gitignore` rules) moves as **one atomic commit** — everything is `parents[N]`-anchored and survives a whole-unit move; splitting it breaks imports (`run_eval.py:47` imports `scripts.corpus_digest`; 7 test files import `scripts` as a package), evidence writers, and the corpus pin. Same-commit code fixes are enumerated in §10.
- **Project-specific research:** none exists as separate files today; the 08-20 report's FIS-specific content stays in the frozen report (line-number-bound, cannot split) with its FIS decisions already re-anchored in living FIS docs. Future FIS-only research lands under `projects/fis/` directly.

---

## 7. Research migration model

Corpus: exactly three files — so the structure is minimal by design (no taxonomy for taxonomy's sake).

| File | Classification | Home | Why |
|---|---|---|---|
| `2026-08-19_NVIDIA_AI_Lab_Playbook_Research.md` | Generic evidence (frozen) | `research/` | Vendor-methodology audit feeding chapters 05/06/07/09/10/12; passes "still matters if FIS disappeared" |
| `2026-08-20_AI_Lab_Methodology_Hardware_Strategy.md` | Mixed but unsplittable (frozen, **line-number-bound**) | `research/` | Statistics/methodology evidence for chapters 03/04/07/09/11/13; moves as a **pure rename** with its companion (they cross-cite by bare sibling filename); FIS-specific decisions inside are already re-anchored in living FIS docs |
| `PLAYBOOK_INTERNAL_EVIDENCE_MAP.md` | Playbook-development governance (living) | `docs/playbook-development/EVIDENCE_MAP.md` | Not research: the maintainer map of playbook rule → FIS evidence → external corroboration, extended per release (§4 holds the v0.1.1 audit dispositions); its own charter requires it to stay outside the shipped playbook |

`research/README.md` (generated) carries: (a) the freshness/status convention — *reports are frozen on landing; corrections arrive as new dated reports or index annotations, never edits, because code and evidence bind by line number*; (b) the migrated SPRT-staleness caveat from `docs/README.md:21` (load-bearing — a naive reader of §2.3 alone would adopt a rejected method); (c) each report's extraction status into playbook chapters; (d) the research-to-rule promotion path: research report → `docs/playbook-development/EVIDENCE_MAP.md` row → chapter rule with A–H class → `playbook/CHANGELOG.md` entry; (e) where project-specific research lives (`projects/<name>/`).

Code updates when `docs/research/` moves (same commit): `fis_platform/stats.py:303`, `scripts/mstat_stats.py:2/56/83` (the PRECISION_NOTE string is *emitted* into regenerated standing-facts output), `playbook/CHANGELOG.md:30` (a deliberate PATCH-class edit per its own semver rules, pointing at the evidence map's new home), plus living pointers in HANDOFF/plan/index. `artifacts/mstat_standing_facts.json`'s embedded old path is frozen evidence — untouched; the next regeneration emits the new path (a documented before/after discontinuity in evidence prose).

---

## 8. Playbook cleanup model

**Ships (stays in `playbook/`):** README, QUICKSTART, GLOSSARY (anchor-load-bearing — never rename), VERSION, CHANGELOG, chapters 00–14, templates/ (9), references/ (`sources.yaml` record-of-record + generated SOURCES.md + formulas + vendor notes + `tools/render_sources.py`, which is fully self-relative), examples/ (12 CASE + 10 SYNTH + WALKTHROUGH + README — the sanctioned quarantine zone for FIS numerics).

**Becomes development history (`docs/history/playbook-v0.1/`):** `PLAYBOOK_BUILD_PLAN.md`, `SOURCE_MAP_DRAFT.md`, `PASS2_AUTHORING_SPEC.md`, and all of `planning/` (briefs, seed JSONs, `build_sources.py`, `review_findings.json`, `w1_verification.json`) — subtree structure preserved verbatim so intra-tree citations keep resolving. These are already machine-declared scaffolding by the validator ("excluded from extraction at 1.0 alongside planning/"). Note recorded for the owner: the committed intent was to drop scaffolding *at 1.0*; doing it now at 0.1.1 is a deliberate early execution of that recorded intent, not a silent deviation. `w1_verification.json` is the provenance backbone for all 68 source-verification notes — archival keep is mandatory. `build_sources.py` is archived as non-runnable-from-archive (its `parents[2]` root would resolve into the archive; it fails loudly, never touches the live ledger).

**The one split:** `planning/pass2/check_playbook.py` is *living release tooling* mis-filed in scaffolding (it validated 0.1.1; all 7 checks PASS at HEAD). It moves to **`playbook/tools/check_playbook.py`** with three required edits: (a) `parents[2]` → `parents[1]`; (b) exclude `tools/` from its own inventory/portability scans (its source contains the banned strings as regex patterns and would fail its own check 2); (c) **extend the lint for the new geometry** — the link ban currently catches only `../docs`/`/docs/`; add `projects/` and `research/` (and keep the `adaptive-ai-lab|/home/wall` literal ban), otherwise the extraction firewall is blind to the new layout. A root `make playbook-check` target is added — today the primary product has zero automated guard.

**Deferred, deliberately:** `sources.yaml`'s generated header comments cite `planning/pass2/…` paths; fixing them forces a re-render + check-6 cycle for a comment, so they wait for the next natural ledger PATCH. `CHANGELOG.md:30` updates when the evidence map moves (§7).

**Extraction test:** after migration, `cp -r playbook/ /tmp/x && python3 /tmp/x/tools/check_playbook.py` must pass all 7 checks with zero repo context — the operational definition of "extraction-ready" (§13).

---

## 9. Migration manifest

Actions: MOVE (git mv, byte-identical) · RENAME (git mv, new name) · SPLIT · ARCHIVE (move to history area) · LEAVE · GENERATE (new/rewritten) · COPY-FS (untracked, filesystem copy + checksum verify) · DEFER. "Prov" = provenance risk of the *proposed action as specified* (raw risk of doing it wrong is noted in §10).

### 9a. Identity surface & governance

| Current | Class | Proposed | Action | References to update | Prov | Notes |
|---|---|---|---|---|---|---|
| `README.md` | GOVERNANCE | rewritten front page | GENERATE | — | none | §11 design; old identity line 1 |
| `Makefile` | FIS ops | `projects/fis/Makefile` + new root delegator | MOVE + GENERATE | line-1 pointer; root gets `fis-*` delegation + `playbook-check` | none | all targets are FIS-operational except help/test/lint |
| `docs/README.md` | mixed | `projects/fis/README.md` (FIS half) + new `docs/README.md` (governance half) | SPLIT | Makefile:1, root README, session hook | low | path map is APPENDED, never rewritten; both halves must state the same FIS authority chain |
| `.claude/hooks/session-start-docs.sh` | active ref | new-identity rewrite (location lines already fixed this pass) | GENERATE | all doc paths it names | none | highest-leverage file: re-imprints identity every session; keep the still-valid environment-facts block |
| `.claude/hooks/precompact-docs.sh` | active ref | new flush-target list (projects/fis docs + governance docs + playbook) | GENERATE | 4 hardcoded doc paths | none | otherwise decision-flushing lands on dead paths after the move |
| `.claude/settings.json` | config | statusMessage touch-up only | LEAVE | — | none | `$CLAUDE_PROJECT_DIR` wiring is portable |
| `pyproject.toml` | FIS | `projects/fis/pyproject.toml` | MOVE + fix | fix wheel `packages` (add `fis_platform`, drop nonexistent `platform_`), identity fields; keep `nemo-switchyard==0.2.0` pin verbatim (load-bearing for R1 equivalence) | low | packaging is already broken — this is a repair |
| `.gitignore` | mixed | root keeps generic; FIS path-anchored rules → `projects/fis/.gitignore` | SPLIT | `evals/reports/*`, `scenarios/manifests/*.json` (+ negations), `learning/training/runs/`, vestigial `infra/*data` | none | lapse = generated JSON gets committed beside the registry |
| `.env` / `.env.example` | FIS | `projects/fis/.env` (COPY-FS, 0600) / `.env.example` (MOVE) | COPY-FS / MOVE | run_eval + serve scripts resolve `.env` against the FIS root | none | never delete `.env`; `FIS_` prefix is permanent |

### 9b. `docs/` root (16 files)

| Current | Class | Proposed | Action | Prov | Notes |
|---|---|---|---|---|---|
| `HANDOFF.md` | living record | `projects/fis/HANDOFF.md` | MOVE | low | living: stale old-dir mentions may be fixed; future lab-ops split flagged |
| `architecture.md`, `task-ontology.md`, `clean-room-boundary.md` | living normative | `projects/fis/<same>` | MOVE | low | update docstring citations in `prompts.py:30`, `suite.py`, generator/report scripts |
| `experiment-log.md`, `routing-experiments.md` | append-only records | `projects/fis/<same>` | MOVE | med | git mv only; no edits below STATUS headers; they are the numbers-of-record for gitignored `evals/reports/` |
| `SUITE_V3_RELEASE_CONTRACT.md` | frozen | `projects/fis/<same>` | MOVE | med | byte-identical; update `compare.py:106` print string same commit |
| `R5_EXPERIMENT_CONTRACT.md` | frozen | `projects/fis/<same>` | MOVE | med | byte-identical; update `r5_amend_rule.py:84` writer same commit; sealed registry citation of old path stays |
| **`R6_EXPERIMENT_CONTRACT.md`** | **frozen, path-bound** | **`docs/` — permanent** | **LEAVE** | **high** | ★ pinned exception (§1); only §17-style appends ever legal |
| 3 reports + `R6_PERFORMANCE_AUTOPSY.md` | historical | `projects/fis/<same>` | MOVE | low | byte-identical; `sampler.py` docstring path updates (cited line numbers stay) |
| `OVERNIGHT_STATUS.md` | historical (R3/R3b pre-registration record) | `projects/fis/<same>` | MOVE | med | never rename — ~18 bare-name cites from frozen files; git history is the pre-registration evidence (`git log --follow`) |
| `SETUP-ACTIONS.md` | historical | `projects/fis/<same>` | MOVE | none | |
| `reference/` (5 HTML + README) | provenance | `projects/fis/reference/` | MOVE | low | byte-identical (evidence map's "extracted verbatim" claim stays checkable); README links re-pointed |
| `superseded/` (4 + README) | provenance | `projects/fis/history/superseded/` | MOVE | low | byte-identical; two-hop path map entry |

### 9c. `docs/current/` (10 files)

| Current | Class | Proposed | Action | Prov | Notes |
|---|---|---|---|---|---|
| `AI_SYSTEMS_LAB_MASTER_PLAN.md` | mixed living | `projects/fis/PROJECT_PLAN.md` + `docs/LAB_CHARTER.md` + `docs/COMPUTE_POLICY.md` | SPLIT (mv, then owner-gated content commit) | low | §6; CASE-001's bare-name citations become path-mapped snapshots |
| `EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK.md` | living normative | `projects/fis/PLAYBOOK_ADAPTATION.md` | RENAME | low | keeps §-numbering; header re-declares relation to playbook v0.1.1; update `predictions.py:6`, `canary.py:3`, `test_mstat_predictions.py:2` docstrings |
| `EXPERIMENT_CONTRACT_TEMPLATE.md` | template | `projects/fis/<same>` | MOVE | low | update copy-target instruction **before R7** |
| `TEST_LOOK_LEDGER.md` | living record, code-bound | `projects/fis/TEST_LOOK_LEDGER.md` | MOVE (code stage only) | high | the 4-edit coordinated move (§6); table rows byte-preserved |
| `GPU_HOURS_LEDGER.md` | lab record | `docs/GPU_HOURS_LEDGER.md` | MOVE | low | lab-scoped per playbook doctrine; rows byte-identical; header pointer → COMPUTE_POLICY |
| `OWNER_DECISIONS.md` | governance record | `docs/OWNER_DECISIONS.md` | MOVE | low | rows untouched; gains the migration-acceptance row |
| `M0_REPORT.md` | historical (owner-frozen) | `projects/fis/M0_REPORT.md` | MOVE | med | owner decision: "must not be altered" — byte-identical only |
| `M_STAT_REPORT.md`, `M_STAT_IMPLEMENTATION_MAP.md` | historical | `projects/fis/<same>` | MOVE | low | map's §16 **copied** (not removed) → `SUITE_V4_TRIGGER_REVIEW_PROCEDURE.md` (GENERATE) |
| `NEXT_STEP_M0.md` | executed plan | `projects/fis/NEXT_STEP_M0.md` | MOVE + append status note | low | removed from every "next task" slot |

### 9d. Research & playbook

| Current | Class | Proposed | Action | Prov | Notes |
|---|---|---|---|---|---|
| `docs/research/2026-08-19_…` | evidence | `research/<same>` | MOVE | low | with companion |
| `docs/research/2026-08-20_…` | evidence, line-bound | `research/<same>` | MOVE (pure rename) | high-if-edited | never reflow; update `stats.py:303`, `mstat_stats.py:2/56/83` |
| `docs/research/PLAYBOOK_INTERNAL_EVIDENCE_MAP.md` | governance | `docs/playbook-development/EVIDENCE_MAP.md` | RENAME | low | update its `w1_verification.json` pointer + `CHANGELOG.md:30` |
| — | — | `research/README.md` | GENERATE | none | §7 contents |
| `playbook/{BUILD_PLAN,SOURCE_MAP_DRAFT,PASS2_AUTHORING_SPEC}.md`, `playbook/planning/**` | scaffolding | `docs/history/playbook-v0.1/…` | ARCHIVE | low | structure preserved; internal old-path citations untouched |
| `playbook/planning/pass2/check_playbook.py` | live tooling | `playbook/tools/check_playbook.py` | SPLIT + 3 edits | none | §8; add `make playbook-check` |
| all shipped playbook content | PRODUCT | unchanged | LEAVE | none | `sources.yaml` header-comment refresh deferred to next ledger PATCH |

### 9e. Implementation unit (one atomic commit)

| Current | Class | Proposed | Action | Prov | Notes |
|---|---|---|---|---|---|
| `fis_platform/` | FIS code | `projects/fis/fis_platform/` | MOVE | high | same-commit `provenance.py` git-guard fixes (§10); `r6_gates.py` GATES dict never changes by a byte (digest-bound, incl. its `docs/` path string) |
| `evals/` `scenarios/` `schemas/` `services/` `scripts/` `tests/` | FIS code | `projects/fis/<same>` | MOVE | low–med | `parents[N]` anchors survive whole-unit move; `scripts` stays an importable sibling of `tests` |
| frozen/pre-registered code (`m0_classify.py`, `m0_metrics.py`, `m0_paired_probe.py`, `r3b_selection_rule.py`) | frozen code | with unit | MOVE (git mv, zero content edits) | med | freeze evidence = commit history; `--follow` works on pure renames |
| `learning/` (registries, datasets) | provenance | `projects/fis/learning/` | MOVE | high | byte-identical; chains are content-digest-based (verified) — nothing digests the tree's own path; sealed path strings inside records never rewritten |
| `artifacts/` (17 tracked evidence files) | provenance | `projects/fis/artifacts/` | MOVE | low | byte-identical; frozen absolute-path/sha256 references inside stay verbatim |
| `infra/` | FIS runtime | `projects/fis/infra/` | MOVE | low | `name: fis` + ports (5433/4222/8222/9000/9001/8082-8084/4000) + container/volume names never change; named volumes ⇒ no data orphaned; migrations content untouched |
| `scenarios/manifests/corpus_v3.json` | generated, load-bearing, untracked | `projects/fis/scenarios/manifests/` | COPY-FS + `corpus_digest --check` | high | digest `1e7c5278…` must verify post-move; regenerable only from the live DB |
| `evals/reports/` (~110 untracked files incl. `m0_paired_probe.server.log`) | generated, irreplaceable | `projects/fis/evals/reports/` | COPY-FS + count/checksum verify | high | NOT regenerable (historical arms' servers/models are gone); a committed artifact cites the server log by absolute path + sha256 — never delete |
| `.venv/` | local | rebuild at `projects/fis/.venv` | GENERATE (`pip install -e .`) | none | current editable install is dead; rebuilding at the FIS root also satisfies `switchyard/serve.sh`'s `$ROOT/.venv` lookup with zero edits |
| `scenarios/*_seeds.txt` (3 empty files) | vestigial | with tree; flag for later cleanup commit | MOVE / later delete | none | never read by any code |

---

## 10. Compatibility and provenance strategy

### The immutable set (never move, never edit — carved out as a class)

1. `docs/R6_EXPERIMENT_CONTRACT.md` — path + blob-bound (append-only §17 rows are the only legal change, ever).
2. `fis_platform/r6_gates.py` `GATES` dict — `digest(GATES)` == the sealed `gates_digest` `6b9699fe…` in all three CONTRACT_FROZEN entries (verified by recomputation). The `"docs/R6_EXPERIMENT_CONTRACT.md § 11"` string inside it is **data**; "fixing" it breaks verification of every frozen candidate.
3. All of `learning/registry/**` and `artifacts/**` content — append-only/hash-chained/sha256-anchored; moves are byte-identical `git mv` only. Sealed strings citing old paths (`contract_path`, `"docs/current/TEST_LOOK_LEDGER.md backfill"` ×7, `selection_rule.json`'s contract citation, absolute `/home/wall/…` host paths, `infra/serve-r6.sh` command lines) stay verbatim forever.
4. Frozen contracts above their append lines; historical reports/logs below their status headers; `OVERNIGHT_STATUS.md` in full (even its known-wrong M7.5 timestamps, per the autopsy's own discipline).
5. Registry record **filenames and directory names** (`models/*.json`, `candidates/<slug>@<digest12>/`) — `cmd_verify` loads by `path.stem`.
6. Git history and the `suite-v3` tag — plain forward commits only; no rebase/filter of pushed `main`; never delete/re-point the tag. Docs cite commits by SHA; pure renames preserve blob SHAs and `--follow`.
7. The repo root directory name/location — a rename would orphan `~/.claude` project memory a third time.

### Code path-sync points (update in the same commit as the corresponding move)

| Code site | Why |
|---|---|
| `provenance.py:1161-1183 dirty_paths_outside_registry` | parses repo-root-relative `git status --porcelain`; unfixed after the move it **falsely refuses every run** (loud). Fix: compare against `projects/fis/learning/registry/r6/`. |
| `provenance.py:1203-1241 registry_ahead_of_git_only_by_appends` | `git show HEAD:<rel>` is root-relative; unfixed, the exception is swallowed by `continue` and the anti-reset guard **silently disables** (the dangerous one). Fix: root-relative prefix. |
| `provenance.py:1244/1253/2478` contract defaults | stay `docs/R6_EXPERIMENT_CONTRACT.md` — valid because the contract LEAVEs. |
| `test_looks.py:417`, `run_eval.py:476`, 2 × `REAL_REVIEW_REF` fixtures | the TEST-look mirror move (§6). |
| `compare.py:106`, `r5_amend_rule.py:84` | user-facing/emitted contract-path strings for the two moving contracts. |
| `stats.py:303`, `mstat_stats.py:2/56/83` | research-report citation strings (one is emitted into regenerated evidence). |
| `prompts.py:30`, `suite.py`, `sampler.py`, `predictions.py:6`, `canary.py:3`, misc. docstrings | normative-mirror/citation comments; update opportunistically in the move commits. |
| `check_playbook.py` (3 edits) + new root Makefile targets | §8. |
| `.gitignore` split; pyproject `packages`/`testpaths`; venv reinstall | §9a/9e. |

Everything else was verified to need **zero** edits: `_ROOT`/`ROOT` anchors, suffix-based test assertions (`endswith("learning/registry/r6")` etc.), compose relative mounts, serve scripts, `render_sources.py`, DB (stores no paths).

### Historical references — intentionally preserved

The 2026-08-20 path-map mechanism is extended, never replaced. Two new dated sections (verbatim pattern of `docs/README.md:79-82`, including the "Do not 'fix' those citations inside frozen/historical documents" sentence) land in `projects/fis/README.md` and are summarized in the new `docs/README.md`:
- *2026-08 restructuring:* `docs/<name>` and `docs/current/<name>` → `projects/fis/<name>` (with the two renames listed); `docs/research/<name>` → `research/<name>`; `docs/superseded/<name>` → `projects/fis/history/superseded/<name>` (two-hop); `docs/reference/<name>` → `projects/fis/reference/<name>` (two-hop); playbook scaffolding → `docs/history/playbook-v0.1/<name>`; pinned exception: `docs/R6_EXPERIMENT_CONTRACT.md` did not move.
- Shipped CASE files' bare-filename citations (CASE-001 → contract/report/plan/log; CASE-006 → `OVERNIGHT_STATUS.md`; CASE-008 → `infra/switchyard/routes.yaml`) are **snapshot provenance**: preserved as written, resolvable via the path map; a one-line provenance note ("FIS paths refer to the lab layout as of v0.1.1; see the lab path map") may be added to `examples/README.md` at the next playbook PATCH — never silent per-CASE edits.

### Second-order effects (stated so they are chosen, not discovered)

- **Whole-repo dirty-tree semantics:** `suite.py` `git_head()` and the provenance clean-tree guards operate on the whole repository. Post-migration, an uncommitted edit *anywhere* (playbook, docs) stamps future FIS runs `-dirty` and can refuse run starts. Fail-closed and safe, but it changes "clean tree" from "FIS is clean" to "the whole lab is clean" — owner decision D3.
- **Evidence-prose discontinuity:** regenerated machine artifacts (standing facts, future registry entries, look #8's `trigger_review_ref`) will cite new paths while sealed history cites old ones. The path map is the resolution mechanism; the migration itself is recorded as a dated entry in `projects/fis/experiment-log.md` (append) and an `OWNER_DECISIONS.md` row so future audits resolve citations mechanically.
- **Two "playbook §N" namespaces:** resolved by declaration in `PLAYBOOK_ADAPTATION.md`'s header (§4).

---

## 11. Root README design

Opening (concept):

> **Adaptive AI Lab** develops and validates the **[Adaptive AI Systems Playbook](playbook/README.md)** — an evidence-driven, project-independent methodology for designing, evaluating, optimizing, deploying, and continuously improving AI systems. The lab runs real project implementations, harvests their frozen experimental evidence into case studies, and promotes what survives into the playbook.
>
> The loop: research evidence → playbook → project implementations → primary experimental records → curated case studies → playbook evolution — governed by the conventions in `docs/`.

Navigation block:

| I want to… | Go to |
|---|---|
| Start a new AI project | `playbook/QUICKSTART.md` |
| Read the methodology | `playbook/` |
| See the evidence behind it | `research/` · `playbook/references/SOURCES.md` |
| See a real implementation | `projects/fis/` — the Fintech Integration Sandbox, the lab's first project and the empirical source of the case studies |
| Read curated case studies | `playbook/examples/` |
| Understand how the playbook itself is developed, versioned, governed | `docs/` |
| Work on FIS | `projects/fis/README.md` (index, authority chain, verification commands) |

Then three short paragraphs: (1) what FIS is and its role (first instantiation; provides provenance; not the repo's scope); (2) the authority model in four lines (playbook = generic method; `projects/<p>/` = that project; `docs/` = lab governance; frozen records = facts of their own events — with the pinned R6-contract exception named explicitly); (3) health check (`make test`, `make playbook-check`). No FIS operational detail on the front page — that lives in `projects/fis/README.md`.

---

## 12. Execution sequence for Pass B

Commit discipline throughout (the `4948d5a` precedent): **moves are pure** (`git mv`, zero content edits to moved files in the move commit); cross-file reference updates ride in the same commit so every commit is green; content edits to moved files land in follow-up commits. No CI exists — each stage ends with the local gate battery (§13). All stages complete **before** the Suite-v4 trigger review is planned.

- **Stage 0 — Preflight (no commits).** Clean tree; record baseline: `make test` (expect 1064+ green), `scripts/r6_registry.py verify`, `scripts/test_look_ledger.py verify`, `make corpus-check` (digest `1e7c5278…`), `python3 playbook/planning/pass2/check_playbook.py` (7 PASS). Snapshot untracked evidence: file count + sha256 manifest of `evals/reports/` and `scenarios/manifests/corpus_v3.json` (written outside the repo).
- **Stage 1 — Research layer.** `git mv` the two reports → `research/`; evidence map → `docs/playbook-development/EVIDENCE_MAP.md`; generate `research/README.md`; update the code/citation sync points (§7). Gate: `make test`.
- **Stage 2 — Playbook boundary.** Split `check_playbook.py` → `playbook/tools/` (3 edits incl. lint extension); archive scaffolding → `docs/history/playbook-v0.1/`; update the evidence map's `w1_verification.json` pointer; add root `playbook-check` target (root Makefile is generated in Stage 5 — until then invoke directly). Gate: `python3 playbook/tools/check_playbook.py` (7 PASS) + `make test`.
- **Stage 3 — FIS documents.** `git mv` all `docs/` root + `docs/current/` files → flat `projects/fis/` per §9b/9c, **except** `R6_EXPERIMENT_CONTRACT.md` (LEAVE) and `TEST_LOOK_LEDGER.md` (Stage 4); includes the two renames (pure mv), `reference/`, `superseded/`→`history/superseded/`; `GPU_HOURS_LEDGER` + `OWNER_DECISIONS` → `docs/`; generate `projects/fis/README.md` (FIS index + path map) and `SUITE_V4_TRIGGER_REVIEW_PROCEDURE.md`; update both hooks' path lists, root README links (minimal interim edit), `compare.py:106`, `r5_amend_rule.py:84`, docstring sync points, subdir READMEs. Gate: `make test` (still green — code untouched except strings; TEST-look fixtures still resolve at the old path).
- **Stage 4 — Implementation unit (single atomic commit).** `git mv` the ten code/evidence trees + `Makefile` + `pyproject.toml` + `.env.example` → `projects/fis/`; move `TEST_LOOK_LEDGER.md` with its 4 edits; `provenance.py` git-guard fixes; `.gitignore` split; pyproject repair. Then non-git steps: COPY-FS `corpus_v3.json`, `evals/reports/*`, `.env`; rebuild `.venv` at `projects/fis/.venv` (`pip install -e '.[dev]'`). Gate (from `projects/fis/`): `make test` + `r6_registry.py verify` + `test_look_ledger.py verify` + `make corpus-check` + untracked-manifest comparison.
- **Stage 5 — Identity switch (owner-gated).** Split PROJECT_PLAN content (extract LAB_CHARTER/COMPUTE_POLICY; re-author precedence header); generate new `docs/README.md`, new root `README.md`, new root `Makefile`; full identity rewrite of both hooks; append the migration path-map sections; append the dated migration entry to `projects/fis/experiment-log.md`; **owner appends the acceptance row to `docs/OWNER_DECISIONS.md`** (master-plan edits move program state — this stage lands only with that row).
- **Stage 6 — Validation sweep + cleanup.** Full §13 battery incl. clean-room playbook extraction test and the CASE-citation existence check; separate small cleanup commit (empty seeds files; resolve owner decision D2 on `corpus_v3.json`); re-grep for `docs/current`, `docs/research`, `AI_SYSTEMS_LAB_MASTER_PLAN`, `EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK` in *living* files — hits must be zero outside frozen/historical/path-map contexts.

Rollback: every stage is a small set of pure-rename commits on `main` with a clean tree between stages — `git revert` of a stage's commits restores the prior state exactly (untracked COPY-FS steps are additive and idempotent). Nothing in any stage edits sealed records, so there is no unrecoverable action anywhere in the sequence.

## 13. Validation plan

| Check | Command | Pass criterion |
|---|---|---|
| Repository tests | `make test` (root delegator → `projects/fis`) | ≥ baseline count green, 0 new failures (baseline recorded Stage 0) |
| R6 registry integrity | `scripts/r6_registry.py verify` | every digest re-derives; contract-at-HEAD binding OK (also exercised by `test_mstat_smoke_lane.py::test_historical_registry_still_verifies` on every test run — the built-in acceptance check) |
| TEST-look ledger + mirror | `scripts/test_look_ledger.py verify` | chain OK; mirror validates at the new path; exactly 7 entries |
| Corpus identity | `make corpus-check` | digest `1e7c5278ba…` verifies at the new path |
| Playbook release validator | `python3 playbook/tools/check_playbook.py` | all 7 checks PASS (inventory, portability incl. extended lint, skeleton, links, citations, ledger freshness, glossary anchors) |
| Playbook portability (clean-room) | copy `playbook/` to an empty dir; run its `tools/check_playbook.py`; open README links | 7 PASS with zero repo context |
| CASE provenance | scripted check: the 7 CASE-cited FIS names (`R6_EXPERIMENT_CONTRACT.md` [in docs/], `R6_…_REPORT.md`, `R6_PERFORMANCE_AUTOPSY.md`, `experiment-log.md`, `OVERNIGHT_STATUS.md`, `infra/switchyard/routes.yaml`, master plan → path map) exist at their mapped homes | all resolve via tree or path map |
| Untracked evidence | compare Stage-0 sha256 manifest of `evals/reports/` + `corpus_v3.json` against `projects/fis/` copies | byte-identical, same count |
| Link/reference sweep | `git grep` for `docs/current`, `docs/research/`, old filenames across **living** files (excluding frozen/historical/path-map/history trees) | zero hits |
| Frozen-file integrity | `git diff <pre-migration>..HEAD -- <each frozen file>` shows rename-only (100% similarity); `git hash-object docs/R6_EXPERIMENT_CONTRACT.md` unchanged | pure renames everywhere; R6 blob untouched |
| Import/build | fresh `pip install -e projects/fis` in the rebuilt venv; `python -c "import fis_platform, schemas, evals, scenarios, services"` from `projects/fis` | imports resolve without cwd hacks |
| FIS operational | `make ps`, `make gateway-smoke` (servers up), one SMOKE-lane eval | healthy; ports unchanged |
| Hooks | start a fresh session | new identity, correct location, all listed paths exist |
| Git state | `git status --porcelain` | clean (plus intentionally untracked runtime files only) |

---

## 14. Future FIS extraction decision

**Keep FIS in this repository now.** Reasons: the playbook's own 1.0 gate requires two materially different project instantiations through frozen executed contracts — FIS is instantiation #1 and the calibration source for whether "generic" abstractions generalize; the curated CASE layer is fact-checked against FIS primary records that live here; the R6 provenance chain binds a `docs/` path in *this* repo; and operational burden is currently nil (no CI, no release cadence conflict, 193 MB total).

**Extraction triggers (any two ⇒ re-evaluate; owner decides):**
1. A second project implementation lands and the monorepo's whole-tree clean-checks/`make test` become operationally awkward across projects.
2. FIS acquires an independent release/deployment cadence or its runtime/CI (once CI exists) dominates repo operations.
3. Playbook reaches 1.0 and methodology development demonstrably no longer needs read access to FIS internals (CASE studies fully self-contained).
4. Publication/permission requirements diverge (e.g. playbook goes public, FIS stays private — note the clean-room boundary makes FIS *designed* to be publishable, so this may never fire).
5. Large runtime artifacts (model weights, training runs) make the shared repo inappropriate despite gitignore discipline.

**Intended future boundary if extracted:** `projects/fis/` moves wholesale to its own repo (the flat boundary designed here makes that one `git filter-repo`/subtree operation), *except* `docs/R6_EXPERIMENT_CONTRACT.md`, which is permanently anchored to this repository's history — the extracted repo would carry a copy plus a provenance pointer back to the lab repo's sealed original (this asymmetry is the one unavoidable cost of the R6 binding and is documented in the pinned-exception note). CASE studies stay with the playbook; cross-repo provenance is by stable filename + the path map + commit SHAs, exactly as the citation web already works.

---

## 15. Open owner decisions

**D1 — Does Pass B include Stage 4 (the implementation-unit move) now?**
Options: (a) full sequence as designed; (b) Stages 0–3 + 5–6 now, Stage 4 later.
**Recommendation: (a).** The identity goal fails while ten FIS directories sit at the root; the risk set is fully enumerated and mechanically verified; the window matters — Stage 4 must land before look #8/R7 bake paths into unamendable records, and deferring it also strands `TEST_LOOK_LEDGER.md` and the interim state indefinitely. Consequence of (b): a half-migrated root for an unknown period and a second migration window that must again dodge trigger-review/R7 timing.

**D2 — `corpus_v3.json` tracked-vs-untracked defect.**
The frozen Suite-v3 contract says "(tracked)"; reality is gitignored-untracked. Options: (a) track it (add `!scenarios/manifests/corpus_v3.json` negation in the FIS `.gitignore`) — matches the frozen record's intent, makes the identity pin survive clones, and any regeneration drift becomes a visible diff; (b) leave untracked and annotate the living docs.
**Recommendation: (a).** Consequence: one new tracked 2.2 KB file whose diff-noise is zero unless the corpus actually changes (which must be visible anyway).

**D3 — Clean-tree semantics after the move.**
Whole-repo dirty checks now mean "the whole lab is clean," and non-FIS edits can refuse FIS run starts / stamp `-dirty` into the append-only ledger. Options: (a) accept the stricter discipline (zero code change); (b) scope `dirty_paths_outside_registry`/`git_head` to `projects/fis/` (small code change, recorded as a method decision).
**Recommendation: (a) initially** — it is fail-closed and honest; revisit via a METHOD_DECISION_RECORD if it proves operationally painful once playbook/docs editing becomes frequent.

---

## Appendix — the 18 questions, answered by the design

| Q | Answer |
|---|---|
| 1. What is this repo for? | Root README ¶1: a lab that develops/validates the playbook via research + projects |
| 2. Main product? | `playbook/` (named in README ¶1) |
| 3. Start a new project? | `playbook/QUICKSTART.md` |
| 4. Reusable methodology files? | `playbook/` chapters + templates + references |
| 5. Research vs rules? | `research/` = evidence, never normative (its README says so) |
| 6. Repo-development process? | `docs/` (governance index) |
| 7. Where is FIS? | `projects/fis/` |
| 8. FIS's role? | First implementation + case-study source (root README ¶FIS) |
| 9. FIS's current plan? | `projects/fis/PROJECT_PLAN.md` |
| 10. FIS's frozen experiment records? | Flat in `projects/fis/` (+ pinned R6 contract in `docs/`, cross-referenced in both indices) |
| 11. Generic case studies? | `playbook/examples/` |
| 12. Primary record behind each case? | Named in each CASE's provenance block; resolvable via `projects/fis/` + path map |
| 13. Which contract template for a new project? | `playbook/templates/EXPERIMENT_CONTRACT.md`; FIS work uses `projects/fis/EXPERIMENT_CONTRACT_TEMPLATE.md` (its header says exactly this) |
| 14. How does a project specialize the playbook? | A `PLAYBOOK_ADAPTATION.md` in its project dir (FIS is the worked example) |
| 15. Which rules win on conflict? | §4 authority table, reproduced in `docs/README.md` |
| 16. Can `playbook/` be extracted cleanly? | Yes — clean-room check is a validation gate (§13) |
| 17. Can FIS become its own repo without another rewrite? | Yes — one flat boundary; §14 documents the single R6 asymmetry |
| 18. Cross-project vs FIS-only directories? | Nothing cross-project exists today except the playbook's own tooling; everything else is under `projects/fis/` — stated in `docs/README.md` |
