# Integration & Feedback — How Lab Work Reaches Wholesaling, and How Learnings Reach the Playbook

> The two bridges this instantiation runs on. Direction 1: lab decisions →
> wholesaling product changes. Direction 2: wholesaling evidence → playbook
> doctrine. Written 2026-08-22; owner-accepted changes only.

## Direction 1 — Applying lab output to the wholesaling repo

**Division of authority.** The lab decides *what and why* (diagnosis, eval
verdicts, contracts, gates). The wholesaling repo receives *scoped product
changes* through its own unchanged flow: feature branch → PR → `dev` → green
CI → operator-gated release. The lab never commits to wholesaling directly and
never merges lab documents into it; it exports **intervention packages**.

**The intervention package** is the only vehicle by which lab work becomes
product change. One package = one scoped change, carrying:

1. **License** — the diagnosis that justifies it: the RC class + ladder rung
   (or telemetry-floor / instrument-prerequisite designation), citing the
   contract or inventory finding.
2. **Spec** — exactly what changes in wholesaling (files, behavior, migration
   if any), written to be executable by a normal wholesaling feature-branch
   session under that repo's CLAUDE.md rules.
3. **Measurement** — which eval/suite version will verify the change, and the
   acceptance gate (pre-declared, consequence-bearing).
4. **Authorization line** — Tier-2 packages need the operator's go-ahead;
   anything touching live outreach/voice/compliance behavior or prod data is
   Tier-3 and needs explicit, per-package authorization (never inferred).

Execution: operator authorizes → a wholesaling feature branch implements the
spec → PR to `dev` cites the package ID → after merge, the lab records the
wholesaling PR number + merge SHA against the package. Provenance links run
both ways. The session mechanics — single self-contained briefs, the context
firewall, session-freshness rules, model selection — are defined in
[`HANDOFF_PROTOCOL.md`](HANDOFF_PROTOCOL.md); briefs live in
[`packages/`](packages/).

**Where artifacts physically live (boundary rule):**

| Artifact | Lives in | Why |
|---|---|---|
| Eval corpora, suite code, CI gates that score wholesaling behavior | **wholesaling** (`backend/tests/…`, like the existing pricing/valuation corpora) | An instrument that gates a repo's code belongs in that repo's CI; the pattern already exists there |
| Experiment contracts, verdicts, ledgers (look/prediction), autopsies, process log | **lab** (`projects/wholesaling/`) | The record of record for methodology; wholesaling PRs cite it by path + SHA |
| Prompt/version registries, telemetry tables | **wholesaling** (product schema) | Runtime provenance is product infrastructure |
| Suite release contracts | **lab**, naming the wholesaling commit SHA that pins the corpus | The freeze record references the frozen thing |

**Package queue (all pending operator authorization; none started):**

- **P1 — Condition instrument prerequisites**: export `vision_golden_label`
  to a committed, versioned corpus file; add a prompt-version constant to the
  vision prompt files and a `prompt_version` column on
  `condition_analysis_request`. License: rung 0 / RC-1 (inventory §2).
  Enables the M1 eval.
- **P2 — Telemetry floor**: the `ai_call` table written inside
  `app.ai.router.complete` (kind, provider, model served, prompt hash +
  version, tokens, cost, latency, error, caller ref); stamp
  `MessageGenerated.model` through to the sent Email; stop dropping dive
  cost/duration/stop_reason. License: telemetry floor (ch. 12; inventory §3).
  **Local-subscription lanes are first-class in this package** (they are
  today's worst-instrumented paths and carry much of the volume):
  - Fix the flat-rate providers to surface real usage instead of the
    unconditional `usage={}` (`providers/codex_cli.py:215`,
    `providers/claude_sdk.py:168`) — record whatever the Agent SDK / CLI
    actually reports; where a number is genuinely unavailable, NULL plus
    wall-time plus a quota-event flag (usage-limit hit, semaphore wait), never
    a silent empty dict.
  - **Correlation across the genserver hop**: the serverless caller generates
    a call id, sends it on the wire (`app/ai/wire.py` contract), and the
    genserver writes its own server-side record (resolved model, SDK version,
    retries, usage) keyed to the same id — so the mac-mini's view and the
    serverless view join instead of the HTTP hop being a visibility wall.
  - **Router-bypass coverage**: the dive runner (raw Agent SDK subprocess) and
    any other bypass lane write `ai_call` rows directly from the runner —
    chokepoint logging alone never sees them.
  - **Cost semantics per supply class**: metered lanes record USD; flat-rate
    subscription lanes record tokens + wall-time + quota events (their real
    scarce resource is capacity, not dollars).
  - **Execution-identity fields** (ch. 02 prerequisite): per call, record the
    resolved model id (not just the requested one), transport (metered API /
    SDK / CLI / genserver), host, and CLI/SDK version where obtainable —
    ambient-login lanes re-resolve these per day and per machine, and no
    cross-run comparison is licensed without them.
- **P3 — Dive output-contract enforcement**: schema-enforced assessment
  emission (rung 3 / RC-5 candidate) — **only after** the dive diagnosis is
  done under a contract; listed to show sequencing, not to pre-commit.

Nothing else in wholesaling changes on the lab's account. Operational
incidents the lab surveys surface (voice posture, CIS 401) are reported to
the operator immediately but are the operator's to fix through normal product
work — the lab does not carry them as packages.

## Direction 2 — Feeding findings back into the playbook

The lab charter's loop is explicit: project evidence → curated
`playbook/examples/CASE-*` → playbook evolution via CHANGELOG. Wholesaling is
positioned to be the strongest source yet: a **live, multi-surface,
compliance-bound production system the lab cannot redesign** — materially
different from FIS (synthetic clean-room) and millwork (greenfield). The
playbook's own 1.0 gate requires two materially different instantiations
through frozen *executed* contracts; executing M1/M2 here directly advances
that gate.

**Mechanism:**

1. **Capture continuously, promote at gates.** Every candidate learning is
   appended to [`PLAYBOOK_FEEDBACK.md`](PLAYBOOK_FEEDBACK.md) (append-only
   ledger, one entry per finding) the moment it's observed, tagged as one of:
   - `GAP` — the playbook is silent where this project needed doctrine;
   - `CASE` — empirical evidence worth a `playbook/examples/CASE-*` study;
   - `CORRECTION` — project evidence contradicting or refining existing text;
   - `CONFIRMATION` — doctrine that worked as written (worth recording too:
     `doctrine — not yet exercised` labels get removed only on evidence).
2. **Promotion bar.** A finding becomes a playbook change only when it has
   real evidence behind it: a frozen executed contract, a completed
   instrument-validation pass, or a fully documented incident with preserved
   numbers. No vibes-cases — the playbook's own honesty rules (P12) apply to
   contributions, not just content.
3. **Cadence: harvest at milestone boundaries (M2, M3, M5), not
   continuously.** Prevents drive-by doctrine edits and keeps each playbook
   change reviewable. Each promotion is its own lab-repo PR touching
   `playbook/` (CASE file + any chapter cross-reference + CHANGELOG entry per
   its semver rules), owner-reviewed — playbook changes are governance-level,
   and `docs/LAB_DECISIONS.md` rows stay owner-written.
4. **Format discipline.** CASE studies follow the existing pattern: source
   project identified, numbers preserved, scope of the claim stated (one
   project's result is never rendered as consensus). GAP promotions propose
   doctrine explicitly labeled with its evidence strength — a wholesaling-only
   experience enters as `case-study + inference`, not as law.

**Already-seeded candidates** live in the ledger; the first promotion is
expected at M2 (the condition-instrument verdict makes the vision-bench trail
a complete CASE with an executed contract behind it).
