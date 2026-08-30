# Test Look Ledger

Held-out evaluation data is a consumable. Every time somebody reads a held-out
split's outcomes, some of it is used up — because from that moment on, decisions
start being made in the light of what was seen there, and the split is a little
less held-out than it was. Nobody notices the fifth read unless it is written
down.

This is the fuel gauge. It is the append-only record of every
[look](../GLOSSARY.md#look) at a held-out split — this playbook's operational form
of the [look ledger](../GLOSSARY.md#look-ledger). "TEST" in the file name names
the generic role (held-out evaluation data), not a particular split: an entry here
can be a look at the qualify split or at the confirm split. An
[experiment contract](../GLOSSARY.md#experiment-contract) plans its look-ledger
entry at freeze (its §6 and Freeze Checklist); this document is where that plan is
actually kept, across every experiment that shares the split.

> Index: [../README.md](../README.md) · Governing chapter: [04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md) (also [03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md))

## When to use / when not to use

- **MUST** use from the first look at any held-out split — qualify or confirm —
  including offline replays of stored outputs. Open the ledger before the first
  look, not after. A look logged retroactively cannot fix an exposure decision
  that was already made blind.
- **MUST** log every look, not only the ones that "mattered". An unlogged look is
  unlogged exposure, and the [refresh trigger](#4-refresh-trigger) in §4 can only
  fire on what is recorded.
- **SHOULD** keep one ledger per project rather than one per experiment. The
  resource being tracked is the split, and several experiment contracts share it.
- **Do not** log iterate-split screening, racing, or successive-halving rungs
  here. That is
  [screening, not inference](../GLOSSARY.md#screening-vs-inference); it consumes
  iterate-split budget, tracked in the experiment contract, and never spends a
  held-out look.
- **Do not** log [smoke-tier](../GLOSSARY.md#smoke-tier) runs. The smoke tier is
  fixed and non-promotable by design, and never reads a qualify or confirm split.

## Rigor-tier applicability

| Tier | Requirement |
|---|---|
| Tier 1 — Exploratory | Not required as this structured artifact. The [never-skippable floor](../GLOSSARY.md#never-skippable-floor) still requires *some* record of held-out exposure — a dated note is enough. |
| Tier 2 — Consequential (default) | **MUST** be maintained. The experiment contract's Freeze Checklist requires a look-ledger entry to be planned before any qualification or confirmation data is used. |
| Tier 3 — High-stakes/regulated | **MUST** be maintained, and entries belong in the tamper-evident [record of record](../GLOSSARY.md#record-of-record), not a side document. |

Rigor attaches to the *split's* exposure, not the project's declared tier. Any
project reading a held-out split for a decision that will be acted on escalates to
the Tier 2 requirement for that reading, whatever tier the originating project
profile states. See chapter 00 §6 (rigor dial) and
[PROJECT_PROFILE.md](PROJECT_PROFILE.md).

---

## The Ledger

*Fill every section below for the split(s) this ledger tracks. Placeholders in
`[brackets]` carry inline guidance in italics — replace the placeholder, keep or
delete the guidance. No section may be silently omitted; see
["Delete no section"](#delete-no-section) at the end of this document.*

### 1. Counting Convention

*A fixed rule, not a per-project field — restated here so the ledger is
self-contained. Read it once before logging the first row, because the three
questions people get wrong are all answered below.*

A **look** is one arm's outcomes on a held-out split, read for a decision or a
report.

- Reading *K* arms in the same sitting for one decision is *K* looks — one row per
  arm. Each arm's outcomes were separately produced and are separately spendable.
- An **offline replay** — re-scoring or re-analyzing outputs you already stored —
  counts as a new look if it is a new read serving a new decision or report.
  Nothing was re-run, but the data was in front of you again, and it is the seeing
  that spends the split. An analysis computed *within* an already-counted look
  does not recount: a second summary statistic pulled from the same stored outputs
  for the same decision is still that one look.
- A look is spent at its **first** executed item, not its last (see
  [spend semantics](../GLOSSARY.md#spend-semantics)). So the row is logged when
  the read starts, not once the result is known. There is no
  peek-and-decide-not-to-log.
- Rows are append-only. A look logged in error gets a correcting row, never an
  edit or a deletion of the original.

### 2. Ledger Table

*One row per look, in the order they happened.*

| # | Date | Experiment | Arm / run | Items | Kind | Notes |
|---|---|---|---|---|---|---|
| [seq] | [YYYY-MM-DD] | [contract ID] | [arm name / run ID] | [items read] | execution \| replay | [decision served; anything unusual] |

*`#` is a permanent, append-only sequence — never renumbered, never reused.
`Items` is the count of held-out items actually read, not the split's full size. A
`replay` row's `Notes` must name what changed (a grader patch, a re-analysis) and
confirm it serves the same decision as its parent look — if it serves a different
decision, it is a new look, not a replay.*

### 3. Standing Consequences

*What has already been spent, and what was decided from it — so that a later
reader does not accidentally re-decide from a look somebody already spent.*

| Split | Experiment | Items spent / split size | Decision made | Date decided |
|---|---|---|---|---|
| qualify \| confirm | [contract ID] | [n] / [N] | [selected candidate / CONFIRMED / REFUTED / INCONCLUSIVE] | [date] |

### 4. Refresh Trigger

*The point at which the tank is low enough to stop and refuel, decided before the
first look rather than during the argument about whether this look is fine.*

**[PARAMETER]** Pre-register, before the first look: `after [N] looks OR [X]% of
any stratum's held-out items read on the confirm split — whichever fires first —
halt further confirm-split looks until the suite-refresh review below
completes.` Choose `N`/`X` against the split size and the number of comparisons
you expect, and record the reasoning here, not just the number.

**[DECISION GATE] Suite-refresh review.** *Inputs:* cumulative exposure from
§2/§3 against the trigger above. *Rule:* once the trigger fires, no further look
is taken on the affected split until this review closes. *Outcomes:* (a) a new
[suite release](../GLOSSARY.md#suite-release) is issued and the ledger continues
against the new version under
[cross-suite refusal](../GLOSSARY.md#cross-suite-refusal) — no comparison across
versions — or (b) continued use of the current version is explicitly
re-authorized, with a written rationale logged here.

**[DEFAULT]** (inference) When outcomes
[cluster](../GLOSSARY.md#clustering-unit), a refresh should prefer adding new
strata over adding more items inside existing ones. New strata buy independent
information toward [effective N](../GLOSSARY.md#effective-n). Replicating inside a
cluster that is already represented buys very little, because the cluster — not
the item — is the unit of information [EXT-STATS-001].

---

## Delete No Section

Every numbered section above **MUST** appear in a filled ledger. If a block
genuinely does not apply yet — no replays logged, no refresh review triggered —
write the section header with the body `N/A — [reason and date]` rather than
omitting it. Absence is a decision, and a reviewer needs to see that it was
considered, not skipped.

---

## Miniature Filled Example

*Illustrative example — synthetic. Invented project: the invoice-triage
assistant from [EXPERIMENT_CONTRACT.md](EXPERIMENT_CONTRACT.md)'s worked
example, Tier 2, tracking two prompt-variant experiments.*

**§2 Ledger table:**

| # | Date | Experiment | Arm / run | Items | Kind | Notes |
|---|---|---|---|---|---|---|
| 1 | 2026-03-02 | invoice-triage-C1 | baseline / confirm | 600 | execution | first confirm read for C1 |
| 2 | 2026-03-02 | invoice-triage-C1 | candidate / confirm | 600 | execution | [contemporaneous paired control](../GLOSSARY.md#contemporaneous-paired-control) for row 1 |
| 3 | 2026-03-09 | invoice-triage-C1 | baseline / confirm | 600 | replay | re-scored under a grader patch; same decision as row 1 |
| 4 | 2026-03-09 | invoice-triage-C1 | candidate / confirm | 600 | replay | paired with row 3 |
| 5 | 2026-04-14 | invoice-triage-C2 | candidate-B / qualify | 60 | execution | qualification look, second candidate |
| 6 | 2026-05-01 | invoice-triage-C2 | candidate-B / confirm | 600 | execution | confirm read, C2 |
| 7 | 2026-05-01 | invoice-triage-C2 | baseline / confirm | 600 | execution | paired control for row 6 |

Note rows 1 and 2: one decision, two arms, two rows. And rows 3 and 4: nothing was
re-run, but the stored outputs were read again under a patched grader, so the
exposure counts.

**§3 Standing consequences:**

| Split | Experiment | Items spent / split size | Decision made | Date decided |
|---|---|---|---|---|
| confirm | invoice-triage-C1 | 1,200 / 2,400 | CONFIRMED — candidate adopted | 2026-03-09 |
| confirm | invoice-triage-C2 | 1,200 / 2,400 | INCONCLUSIVE — below MDE | 2026-05-01 |

**§4 Refresh trigger (as pre-registered):** after 6 looks OR 60% of the confirm
split read, whichever first. Row 6 is the 6th confirm-split look → **trigger
fires** — suite-refresh review opened 2026-05-02; two additional vendor-category
strata added before any replication, per the §4 default; outcome: refreshed
suite issued 2026-05-20, ledger continues against the new version.

---

**Governing chapters:** [04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md)
· [03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md)

**Related templates:** [EXPERIMENT_CONTRACT.md](EXPERIMENT_CONTRACT.md) ·
[PREDICTION_LEDGER.md](PREDICTION_LEDGER.md) ·
[EVAL_SUITE_RELEASE_CONTRACT.md](EVAL_SUITE_RELEASE_CONTRACT.md)

[Index](../README.md) · [Glossary](../GLOSSARY.md)
