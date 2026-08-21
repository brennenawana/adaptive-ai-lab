# Repository Restructuring — Pass B Execution Report

**STATUS: HISTORICAL RECORD — the restructuring is complete.**
Date: 2026-08-21 · Design authority: `RESTRUCTURING_PASS_A.md` (this directory,
including its D1–D6 addendum) · Acceptance: `../../LAB_DECISIONS.md` row 1.

## Result

Starting SHA: `88f650a` (Pass A committed). Final SHA: the commit introducing this
report (see `git log` — every stage below names its own commit). The repository now
IS its stated identity:

```
adaptive-ai-lab/
├── README.md          the lab front page
├── Makefile           thin delegator (test, playbook-check, fis-%)
├── playbook/          THE PRODUCT — Adaptive AI Systems Playbook v0.1.1 + tools/
├── research/          generic evidence (2 frozen reports + index)
├── docs/              lab governance (charter, compute policy, lab decisions,
│                      playbook-development, history/)
└── projects/fis/      the first project implementation — ALL FIS primary records,
                       code, registries, evidence, infra, env, venv
```

## Stage commits

| Stage | Commit | What |
|---|---|---|
| Addendum | `f168756` | D1–D6 recorded in the Pass A design before execution |
| 1 | `ad44f14` | research/ to top level; evidence map → docs/playbook-development/ |
| 2 | `d03f843` | validator → playbook/tools/ (3 edits, lint extended); scaffolding → docs/history/playbook-v0.1/ |
| 3 | `08df60a` | 36 FIS documents → flat projects/fis/ (pure renames; 2 living renames); code citation strings |
| 4 | `765d492` | implementation unit (278 files) → projects/fis/; git-guard prefix fixes; TEST-look mirror rebind (4 sites); pyproject repair; .gitignore split; D2 corpus tracking; venv rebuild |
| 4b | `58ae8e1` | D6: R6 contract → projects/fis/ via `CONTRACT_PATH_RELOCATIONS` + 7 relocation tests |
| 4c | `446fc9e` | D3: clean-tree semantics scoped to projects/fis/ + 5 real-git scope tests |
| 5 | `be12b86` | identity switch: lab governance docs, indices, root surface, hooks |
| 6 | (this commit) | D5 archive, cleanup, final validation, this report |

## Owner decisions — disposition

- **D1 (full implementation move): DONE.** Nothing FIS remains at the repository
  root. All 10 implementation trees, Makefile, pyproject, env files, venv, and
  untracked evidence live under `projects/fis/`.
- **D2 (track corpus manifest): DONE.** `scenarios/manifests/corpus_v3.json`
  verified with `corpus_digest.py --check` (**DETERMINISTIC — identical to the
  recorded identity**, sha256 `561065f6…`, digest `1e7c5278…`) before tracking via
  a `.gitignore` negation. `--write` was never run; Suite v3 unchanged.
- **D3 (scoped clean-tree): DONE.** The re-enumerated FIS provenance closure is
  exactly `projects/fis/` (post-D6 nothing load-bearing remains outside; research/
  and playbook/ appear only as prose citations). `suite.git_head()` and
  `provenance.dirty_paths_outside_registry()` apply the identical `-- .` pathspec
  under `_ROOT`, so `-dirty` identity and dirty-path determination cannot disagree;
  fail-closed preserved. Tests: `test_fis_scope.py` (5, real git, lab-shaped temp
  repo — including the standalone-repo extraction shape).
- **D4 (OWNER_DECISIONS stays FIS-scoped): DONE.** `projects/fis/OWNER_DECISIONS.md`,
  rows byte-identical. New lab-level record `docs/LAB_DECISIONS.md` opens with the
  restructuring acceptance row (D1–D6).
- **D5 (archive the design): DONE.** Pass A + this report live in
  `docs/history/2026-08-21-restructuring/`. The root is the six-entry tree above.
- **D6 (R6 contract moves): DONE** — see below.

## The R6 relocation mechanism

Verified mechanics before implementing: the sealed `CONTRACT_FROZEN` payloads in
all three candidates' hash-chained `state.jsonl` record
`contract_path="docs/R6_EXPERIMENT_CONTRACT.md"` + `contract_revision=0604d661…`
(frozen blob); enforcement resolves the contract **by that recorded path at HEAD**
(`contract_blob_sha` / `committed_contract_extends`, applied at freeze and before
every DEV/TEST transition); the digested `GATES` dict embeds the same path string.

Mechanism: `provenance.CONTRACT_PATH_RELOCATIONS` — an explicit, exact-string,
one-hop mapping `historical recorded locator → current canonical path`, applied by
`resolve_contract_path()` inside the two lookup functions only. Why it preserves
scientific provenance:

- **The historical record is the identity's index; the content is the identity.**
  Sealed entries keep saying `docs/R6_EXPERIMENT_CONTRACT.md` — truthful at freeze
  time. The verifier maps that locator to where the *identical bytes* now live and
  then applies the unchanged frozen-blob byte-prefix-extension rule against the
  resolved path's committed content. Re-pointing the mapping at different bytes
  fails verification (content binds, not path).
- **Unknown locators fail closed** (identity passthrough → missing at HEAD →
  `None`/`False` → refusal). No search fallback exists.
- **New freezes never depend on it**: they record their actual canonical paths
  (`R6_CONTRACT_PATH = "projects/fis/R6_EXPERIMENT_CONTRACT.md"` is the default);
  the resolver is identity for canonical paths; entries are added only by audited
  migrations recorded in `LAB_DECISIONS.md`.
- The move itself was a pure `git mv`: blob `01811b52…` unchanged at the new path
  (= frozen `0604d661…` + the legal §17/status appends).

**Confirmations:** R6 was **not** rerun; **no** DEV or TEST look was consumed (the
TEST-look ledger holds exactly 7 entries, chain OK); **no** registry entry was
rewritten (all 106 `learning/` + `artifacts/` files moved as `R100` pure renames);
`GATES` is byte-identical and `GATES_DIGEST` recomputes to the sealed
`gates_digest` (`6b9699fe…`); the historical `contract_path` strings are untouched.
Tests: `test_contract_relocation.py` (7, read-only against the real registry and
git history): sealed payload verifies through relocation; old path gone; new path
carries the identical blob and the frozen revision still prefixes it; unknown
relocation fails closed; target substitution fails; wrong frozen blob fails;
canonical paths are identity (one hop, no chains).

## Other moves and repairs

- **Research:** the two 2026-08 reports → `research/` (pure renames — the 08-20
  report is line-number-bound by code and committed evidence); new `research/README.md`
  carries the freeze convention, the SPRT caveat, and the research-to-rule
  promotion path. `PLAYBOOK_INTERNAL_EVIDENCE_MAP.md` → `docs/playbook-development/EVIDENCE_MAP.md`.
- **Playbook cleanup:** build scaffolding (3 root docs + `planning/`) →
  `docs/history/playbook-v0.1/` (structure preserved, citations untouched);
  `check_playbook.py` → `playbook/tools/` with its root anchor fixed, itself
  excluded from its own scans, and the link rule strengthened to full
  self-containment (no shipped link may escape `playbook/`) plus a `projects/fis`
  portability ban. `sources.yaml` header-comment refresh deferred to the next
  ledger PATCH (recorded in Pass A).
- **Packaging repair (not preservation):** the editable install had been dead
  since a pre-rename checkout and the wheel `packages` list named a never-existent
  `platform_`. Fixed the list (adds `fis_platform`, `scripts`), rebuilt a fresh
  `uv` venv at `projects/fis/.venv` with `.[dev,routing]` + pytest-asyncio; the
  `nemo-switchyard==0.2.0` pin is preserved.
- **Untracked evidence:** traveled with the directory renames;
  `evals/reports/` verified **98 files, byte-identical** to the Stage-0 sha256
  snapshot; `corpus_v3.json` byte-identical; `.env` relocated 0600-preserved,
  hash-verified before the source was removed.
- **Hooks:** both rewritten (new identity, correct location, new reading order,
  D3 scope fact; environment-facts block carried over) and verified by execution.
- **Cleanup:** three empty, never-read `scenarios/*_seeds.txt` removed; stale root
  `.venv`/caches removed; Pass A archived (D5).

## Validation (final battery, all green)

| Check | Result |
|---|---|
| Full suite (`make test`) | **1077 passed, 2 skipped** (baseline 1065 + 12 new tests) |
| R6 registry (`r6_registry.py verify`) | 4 candidates, 0 problems — every digest re-derives |
| TEST-look ledger + mirror | 7 entries, chain OK; mirror OK at `projects/fis/TEST_LOOK_LEDGER.md` |
| TEST-look count | exactly 7, unchanged |
| Corpus identity (`--check`) | DETERMINISTIC — identical to the recorded identity |
| Playbook validator | 7/7 PASS |
| Clean-room extraction (`cp -r playbook/` elsewhere, run its validator) | 7/7 PASS with zero repo context |
| Frozen-file purity (`git diff 88f650a HEAD -M100%`) | all contracts/reports/ledgers/OVERNIGHT_STATUS/M0/M-STAT records `R100`; registry+artifacts 106/106 `R100`; experiment-log rename + 39 insertions, 0 deletions (append-only) |
| R6 blob | `01811b52…` at old and new HEAD paths (identical) |
| Relocation + tamper tests | 7/7 pass |
| Scoped-dirty positive/negative tests | 5/5 pass |
| FIS imports/packaging | `fis_platform, schemas, services, scenarios, evals, switchyard` import from the fresh venv |
| FIS operational | `fis-postgres`/`fis-nats` healthy on 5433/4222; no inference run (none needed — no look consumed; the 8082 model server was simply not running) |
| Reference sweep (living files) | clean — remaining old-path strings are deliberate path-map/provenance mentions |
| Hooks | executed; emit the new identity and valid paths |
| `git status` | clean at each stage boundary |

## Known exceptions and architectural debt

- Sealed historical strings intentionally keep pre-restructuring paths (registry
  `contract_path`/`source` fields, `GATES`, committed `artifacts/` evidence, frozen
  docs' citations) — resolved by the path map and the relocation record, never by
  edits.
- `playbook/references/sources.yaml` header comments still cite the archived
  scaffolding paths — deferred to the next natural ledger PATCH (comments, not
  data; a fix forces a re-render cycle).
- Shipped CASE studies cite FIS records by bare filename as snapshot provenance;
  CASE-001's two `AI_SYSTEMS_LAB_MASTER_PLAN.md` citations now resolve via the
  path map (rename of a living doc). A one-line provenance note in
  `playbook/examples/README.md` can ride the next playbook PATCH.
- If FIS is ever extracted to its own repository, `CONTRACT_PATH_RELOCATIONS` and
  the `_git_prefix()`-derived guards are the two places that already anticipate it
  (the scope tests cover the standalone shape); the relocation table would gain its
  second audited entry then.
- Historical registry `code_commit` values were recorded under whole-repo dirty
  semantics; future ones use the D3 scope. At every historical entry the two rules
  coincide (recorded trees were clean repo-wide) — disclosed in the experiment-log
  migration entry.
