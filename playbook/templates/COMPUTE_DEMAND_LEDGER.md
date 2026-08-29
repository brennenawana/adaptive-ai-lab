# Compute Demand Ledger

The append-only record of compute demand — device-hours and spend, owned and
rented, month over month, including honest NOT-RUN rows — that this playbook's
[demand ledger](../GLOSSARY.md#demand-ledger) concept names. It exists to
distinguish within-run busyness from sustained fleet demand, and it must predate
the wanting of any hardware it might eventually be used to justify buying.

> Index: [../README.md](../README.md) · Governing chapter: [11. Economics, Hardware and Cloud](../11_ECONOMICS_HARDWARE_AND_CLOUD.md)

## When to use / when not to use

- **MUST** start this ledger before wanting the hardware — a
  [purchase trigger](../GLOSSARY.md#purchase-trigger) defined after the wanting
  starts is a rationalization, not a control.
- **MUST** log every month a project consumes owned or rented device-hours
  beyond ad hoc single-session exploration — training runs, evaluation runs,
  serving-capacity tests, anything that could eventually be cited to justify
  capital spend.
- **MUST** log NOT-RUN months honestly: a month with zero owned/rented usage
  still gets a row, so idle capacity stays visible rather than silently absent.
- **SHOULD** keep one ledger per fleet/lab, not per project — the decision this
  feeds (buy or don't) is about shared capacity.
- **Do not** treat this as a substitute for a
  [performance autopsy](../GLOSSARY.md#performance-autopsy) — this ledger is
  the cross-run monthly rollup; a single run's critical path and cost-bucket
  attribution belong in [PERFORMANCE_AUTOPSY.md](PERFORMANCE_AUTOPSY.md).
- Mark the whole template `N/A` only if literally no owned or rented
  device-hours are ever consumed (managed-API-only projects) — state that
  explicitly rather than omitting the file.

## Rigor-tier applicability

| Tier | Requirement |
|---|---|
| Tier 1 — Exploratory | Not required, but any purchase decision made from a Tier 1 project escalates to the Tier 2 requirement below the moment a purchase is even discussed — start the ledger then, not after. |
| Tier 2 — Consequential (default) | **MUST** be maintained before any hardware purchase decision. |
| Tier 3 — High-stakes/regulated | **MUST** be maintained, and entries belong in the tamper-evident [record of record](../GLOSSARY.md#record-of-record). |

Rigor attaches to the *purchase decision's* consequence, not the project's
declared tier: capital spend is a consequential decision wherever it
originates, and the ledger requirement follows the decision, not the
originating project's stated tier. See chapter 00 §6 (rigor dial) and
[PROJECT_PROFILE.md](PROJECT_PROFILE.md).

---

## The Ledger

*Fill every section below. Placeholders in `[brackets]` carry inline guidance in
italics — replace the placeholder, keep or delete the guidance. No section may
be silently omitted; see ["Delete no section"](#delete-no-section) at the end of
this document.*

### 1. Ledger Table

| Date | Milestone / project | Node | Purpose | Device-hours | Spend | Notes |
|---|---|---|---|---|---|---|
| [YYYY-MM-DD] | [milestone or project name] | owned \| rented · [device class] | training \| eval \| serving-capacity-test \| NOT-RUN | [hours; state the authoritative clock] | [$; "$0" if owned/idle] | [anything a later reader needs] |

*`Node`: name the device **class** generically enough to survive a hardware
refresh ("owned, single-GPU workstation" / "rented, multi-GPU node") — precise
SKUs belong in a private inventory, not this ledger's portable structure.
`Device-hours`: state which clock is
[authoritative](../GLOSSARY.md#authoritative-clock) — wall-clock reservation
time and device-busy time diverge, sometimes by a lot, and the purchase
decision needs to know which one it is reading; see
[dual-clock telemetry](../GLOSSARY.md#dual-clock-telemetry). A `NOT-RUN` row
still needs a date and a node — "which capacity sat idle, when" is exactly what
a busy-sprint illusion hides.*

### 2. Monthly Rollup

*The trigger in §3 reads this table, not the raw rows.*

| Month | Owned device-hours | Rented device-hours | Rented spend | Months at/above trigger threshold (running) | Notes |
|---|---|---|---|---|---|
| [YYYY-MM] | [h] | [h] | [$] | [count] | |

### 3. Purchase Trigger

**[PARAMETER]** Pre-commit, before wanting the hardware: `[K] consecutive
months of rented spend at or above $[X]/mo` **OR** `a committed always-on
serving requirement of ≥ [Y] sustained device-hours/month`. Derive `X`/`Y` from
the project's rent-vs-buy [break-even](../GLOSSARY.md#break-even) (chapter 11;
formulas in
[references/STATISTICS_FORMULAS.md](../references/STATISTICS_FORMULAS.md)) —
do not pick round numbers by feel.

**[DECISION GATE] Purchase trigger fired.** *Inputs:* the running count in §2.
*Rule:* capital may be considered only after the pre-committed condition above
is met by the ledger, never before. *Outcomes:*
1. **Trigger not met** → continue renting or using owned capacity as-is; no
   purchase discussion is licensed by this ledger alone.
2. **Trigger met** → open a benchmark-first sizing pass: run the actual (or
   representative) workload across candidate configurations and select the
   *minimal* configuration that clears the stated latency/throughput/cost
   target — not the largest affordable one [SCENARIO: SCENARIO-05].

**[STOP CONDITION] Stale-price purchase.** Before any order is placed,
re-verify current prices, specs, and availability for both the owned candidate
and the rental alternative used to justify it. The trigger fires the *review*,
not the order; a review built on prices checked longer ago than a routine
refresh cycle is void until re-priced. Hardware and cloud pricing move fast —
every number in §1–§2 is dated evidence, never a current quote.

---

## Delete No Section

Every numbered section above **MUST** appear in a filled ledger. If a project
genuinely has zero owned/rented device-hours (managed-API-only), write the
section header with the body `N/A — API-only, no device-hours to ledger` under
§1, and `N/A — no purchase decision in scope` under §2–§3, rather than omitting
them. Absence is a decision, and a reviewer needs to see that it was
considered, not skipped.

---

## Miniature Filled Example

*Illustrative example — synthetic. Invented project: the invoice-triage
assistant from [EXPERIMENT_CONTRACT.md](EXPERIMENT_CONTRACT.md)'s worked
example, Tier 2, periodic adapter fine-tuning plus eval runs.*

**§1 Ledger table:**

| Date | Milestone / project | Node | Purpose | Device-hours | Spend | Notes |
|---|---|---|---|---|---|---|
| 2026-01-14 | invoice-triage / pilot adapter | rented, single-GPU node | training | 6.0 (device-busy) | $18 | first candidate adapter |
| 2026-01-28 | invoice-triage / pilot adapter | rented, single-GPU node | eval | 2.5 (device-busy) | $7 | confirm-split read; see look ledger §2 rows 1–2 |
| 2026-02-01 | invoice-triage / ops | owned, workstation GPU | NOT-RUN | 0 | $0 | idle month, nothing scheduled |
| 2026-02-18 | invoice-triage / candidate-B | rented, single-GPU node | training | 9.0 (device-busy) | $27 | second candidate adapter |
| 2026-03-01 | invoice-triage / candidate-B | rented, single-GPU node | eval | 2.5 (device-busy) | $7 | confirm-split read; see look ledger §2 rows 5–7 |
| 2026-03-20 | invoice-triage / serving trial | rented, single-GPU node | serving-capacity-test | 14.0 (wall-clock) | $40 | operating-point sweep, ch. 06 |

**§2 Monthly rollup:**

| Month | Owned device-hours | Rented device-hours | Rented spend | Months at/above trigger threshold (running) | Notes |
|---|---|---|---|---|---|
| 2026-01 | 0 | 8.5 | $25 | 0 | below threshold |
| 2026-02 | 0 | 9.0 | $27 | 0 | below threshold |
| 2026-03 | 0 | 16.5 | $47 | 0 | below threshold |

**§3 Purchase trigger evaluation:** trigger = `3 consecutive months ≥ $300/mo
rented spend OR ≥ 200 sustained device-hours/month`. Neither condition is met
through 2026-03 (max monthly spend $47; max monthly hours 16.5) — **trigger not
fired; no purchase discussion licensed.**

---

**Governing chapters:** [11. Economics, Hardware and Cloud](../11_ECONOMICS_HARDWARE_AND_CLOUD.md)
· [06. Inference Performance and Capacity](../06_INFERENCE_PERFORMANCE_AND_CAPACITY.md)

**Related templates:** [EXPERIMENT_CONTRACT.md](EXPERIMENT_CONTRACT.md) ·
[PERFORMANCE_AUTOPSY.md](PERFORMANCE_AUTOPSY.md) ·
[PROJECT_PROFILE.md](PROJECT_PROFILE.md)

[Index](../README.md) · [Glossary](../GLOSSARY.md)
