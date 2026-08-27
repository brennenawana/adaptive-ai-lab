# Walk-Test Findings — 2026-08-27

> Two isolated walk tests run through `tools/walktest/` (fresh headless
> sessions, no memory, full tool-call telemetry). Sandboxes:
> `/private/tmp/walktest/20260827-004206` (lab workspace) and
> `.../20260827-004600` (product repo, `CLAUDE.md` kept as the artifact under
> test).

## Test A — lab workspace (`projects/wholesaling/`), CLAUDE.md stripped

**Rating 3/5.** Run *after* the four defects found by the contaminated
pre-test were fixed, so this measures the corrected workspace.

Reading order followed the intended chain exactly: `find` → `README.md` →
`GOAL.md` → `SESSION_PROMPTS.md` → `PROCESS_LOG.md` → `PROJECT_PROFILE.md` →
`PLAYBOOK_PATH.md` → `leads-gtm/README.md` → `packages/P1/*` → … (14 reads).

Verdict: *"every fact needed is present and internally consistent once
assembled — but it takes real cross-file reconciliation rather than a single
clean path."* Two concrete fixes it names:

1. **`PROCESS_LOG.md` should carry a running current-state summary at its
   head** instead of requiring full-log reconstruction. The append-only log has
   outgrown "read the tail" as an orientation mechanism.
2. **Supersession banners should replace stale sections, not merely flag
   them.**

## Test B — product repo (`~/code/wholesaling`), CLAUDE.md KEPT

37 tool calls. The agent independently verified claims rather than trusting
docs — it parsed every `revision`/`down_revision` pair across 121 migration
files to compute the true head.

### Doc-vs-code defects found

| # | Claim | Reality | Proof |
|---|---|---|---|
| 1 | **Alembic head is `0054_agent_captured_contact`** — stated in `CLAUDE.md`, `README.md`, **and** `STATUS.md`, all "verified at code head 2026-06-23" | True head is **`0107_comm_fact_homes`** — **53 migrations later**, most recent dated Aug 13 | full scan of 121 files in `backend/alembic/versions/` |
| 2 | `ARCHITECTURE.md` §3 marks **five core engines as "Stub"** (`underwriting/engine.py`, `valuation/engine.py`, `routing/router.py`, `guardrails/gate.py`, `generation/email_type1.py`) — "raise `NotImplementedError`… a builder fills the bodies" | All five **fully implemented**, 479–1838 lines each, **zero** `NotImplementedError` | line counts + `grep -c NotImplementedError` → 0 on all five |
| 3 | **`underwriting/engine.py`'s OWN module docstring** says *"TYPED STUBS… a builder fills the bodies"* | 814 lines of implemented math, no stub markers — the docstring was never updated when the implementation landed | `backend/app/underwriting/engine.py:1-5` vs its body |
| 4 | `CLAUDE.md` is written **entirely for Windows 11** — `py` launcher, `C:\Business\Wholesaling`, `.venvs\py313` PowerShell activation, `Invoke-WebRequest`, cp1252 encoding, Windows Credential Manager | Machine is **Darwin/macOS**; no `.venvs\` of any kind exists | environment + `find` |
| 5 | "751 backend tests green, hermetic suite" | **Unverifiable in-session** — pytest blocked by the approval gate. 403 test files exist, consistent with a large suite, but status unconfirmed | `backend/tests/` |

### Why #3 is the serious one

The staleness is **inside the code**, in the module docstring of the file that
produces the numbers this business is about to sell. Any fresh session — or a
new harness with no memory — orienting toward underwriting reads *"typed
stubs, a builder fills the bodies"* at the top of an 814-line implemented
solver. That is actively misleading about the single most consequential file in
the product, and it is the same defect class as `Docs/IMAGE_ANALYSIS.md`
documenting a default the code no longer uses.

Note #1 and #2 compound: a reader who believes the docs thinks the system is
53 migrations behind *and* that its pricing engines are unimplemented.

### Rig artifact, not a repo defect

The agent flagged "not a git repo — the documented branch/PR workflow is not
exercisable." That is a consequence of `build.sh` stripping `.git` by default,
not a property of the repo. Re-run with `--keep-git` if the workflow itself is
under test.

## What this validates

The rig paid for itself on its first real run. These defects were invisible to
every prior survey in this workstream **because every prior survey had memory** —
the agents already knew the true migration head and that the engines were
implemented, so they never read the docs as a newcomer would and never noticed
the docs were wrong.

**Direct consequence for the harness decision** (`HARNESS_SELECTION.md`): a
migration to DeepSeek Harness or opencode drops Claude Code's memory entirely.
Every one of these stale claims would then be load-bearing for a fresh session.
Fixing orientation docs is a **prerequisite** to a harness migration, not a
nicety.

## Recommended package (P4 — not yet authorized)

Cheap, mechanical, high leverage: correct the Alembic head references in
`CLAUDE.md`/`README.md`/`STATUS.md`, remove the "Stub" designations from
`ARCHITECTURE.md` §3, rewrite `underwriting/engine.py`'s module docstring to
describe what it actually is, and either port `CLAUDE.md`'s environment section
to macOS or split it into per-platform sections. Add a CI check that the
documented Alembic head matches the computed head — the same drift-guard
pattern `test_underwriting_version.py` already uses for layer digests.
