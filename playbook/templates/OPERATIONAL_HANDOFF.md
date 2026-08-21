# Operational Handoff

The operational-state document a new operator — or a future version of you — needs
to run, verify, and safely change a deployed system without re-deriving what is
already known. It stands beside, and always points back to, the
[execution system](../GLOSSARY.md#execution-system) identities pinned by an active
[experiment contract](../GLOSSARY.md#experiment-contract): the contract is the
per-experiment record, this is the standing operational picture across whatever is
currently running.

> Index: [../README.md](../README.md) · Governing chapter: [12. Observability, Learning, and Promotion](../12_OBSERVABILITY_LEARNING_AND_PROMOTION.md) (also [02. Execution System Model](../02_EXECUTION_SYSTEM_MODEL.md))

## When to use / when not to use

- **SHOULD** use whenever a system, service, or experiment moves from "the person
  who built it can hold it in their head" to "someone else — or a later version of
  the same person — must operate, verify, or extend it".
- **SHOULD** create or refresh it at every promotion boundary (shadow → canary →
  production; exploratory → consequential decision) so it exists before an incident
  forces it into existence.
- Use to accompany, not replace, the execution-system identities pinned by an active
  experiment contract (`EXPERIMENT_CONTRACT.md`) — that document is per-experiment;
  this one is the standing picture across whatever is currently running.
- **Do not** use this as a substitute for the
  [record of record](../GLOSSARY.md#record-of-record) — this document is a
  curated, human-readable summary that must always point back to the authoritative
  sources it summarizes, never replace them.
- **Do not** let it go stale silently. A review cadence belongs in §7 (Standing
  rules in force); an operational document nobody has touched since the system
  changed underneath it is a hazard, not documentation.
- Not required in full for a single-operator exploration that will never outlive
  the session it was written in — see rigor-tier applicability below.

## Rigor-tier applicability

| Tier | Requirement |
|---|---|
| Tier 1 — Exploratory | Optional. If used, a lightweight cut (§1 System inventory, §2 Execution-system identities, §4 Verification commands) is enough — the goal is that returning to the work after a gap does not require re-deriving how to run it. |
| Tier 2 — Consequential (default) | **SHOULD** be completed for any system a decision depends on or another person operates. All sections filled; refreshed at each promotion boundary. |
| Tier 3 — High-stakes/regulated | **MUST** be completed and kept current as living documentation, not a one-time artifact — it is part of the [rollback path](../GLOSSARY.md#rollback-path) evidence and is reviewed on the cadence stated in §7. |

Rigor attaches to the *system's* operational exposure, not the project's declared
tier: a Tier 1 exploration that quietly becomes the thing three other people depend
on has become a Tier 2 operational surface, and earns this document in full
whatever the originating project profile says.

---

## The Handoff

*Fill every section below for the system this handoff covers. Placeholders in
`[brackets]` carry inline guidance in italics — replace the placeholder, keep or
delete the guidance. No section may be silently omitted; see
["Delete no section"](#delete-no-section) at the end of this document.*

### 1. System Inventory

*What runs, where, and at what version. One row per service/component; add rows
freely, remove none of the columns.*

| Component | Runs where (host/environment) | Port / endpoint | Version / build identity | Owner |
|---|---|---|---|---|
| [component] | [host or environment class] | [port/endpoint placeholder] | [version, build hash, or container tag] | [role] |

### 2. Execution-System Identities in Force

*The full [execution system](../GLOSSARY.md#execution-system) currently pinned for
each system this document covers: model/artifact, runtime/provider, hardware/host,
harness, context policy, tools, workflow, generation/reasoning budget,
verifier/grader, environment. State the
[frozen identity](../GLOSSARY.md#frozen-identity) actually in force, not the
intended one — a [comparability claim](../GLOSSARY.md#comparability-claim) about
this system is only as good as this section.*

- [System/service name]: [artifact hash or upstream identity] · [runtime +
  version] · [hardware/host class] · [harness + version] · [context policy
  summary] · [tools attached] · [generation/reasoning budget] · [verifier/grader
  identity] · [environment notes]

### 3. Environment Gotchas and Their Workarounds

*Every recurring symptom this environment produces that is NOT a defect in the
system under study — each entry closes the loop from confusion back to a rule, so
the next operator does not re-diagnose it from scratch.*

| Symptom | Cause | Rule / workaround |
|---|---|---|
| [observable symptom] | [root cause] | [the standing rule that neutralizes it] |

*Generic pattern worth checking for — not this system's specific measured
instance: virtualized hosts (a WSL2-style host is a common example) can let
realtime and monotonic clocks drift apart under load. Symptom: latencies computed
from one clock disagree with the other. Cause: clock virtualization skew. Rule:
[dual-clock telemetry](../GLOSSARY.md#dual-clock-telemetry) on every span, with the
[authoritative clock](../GLOSSARY.md#authoritative-clock) declared per metric —
chapter 12.*

### 4. Verification Commands

*Executable, copy-pasteable commands that answer "is this actually working right
now?" — each with its expected output, so a mismatch is immediately legible as a
problem rather than something the operator has to interpret. Prefer generic
integrity-gate commands over ad hoc checks — see
[static integrity gates](../GLOSSARY.md#static-integrity-gates), chapter 03.*

| Check | Command | Expected output |
|---|---|---|
| [what this verifies] | `[executable command]` | [expected output or exit condition] |

### 5. Data Stores and Their Roles

*Every store this system reads or writes, labeled by its role, so nobody mistakes a
working cache for the [record of record](../GLOSSARY.md#record-of-record) or feeds
a working store back into evaluation.*

| Store | Role | Notes |
|---|---|---|
| [store identity] | authoritative / retrieval / working / [trajectory record](../GLOSSARY.md#trajectory-record) / learned-from-production | [isolation notes, retention, who may write] |

### 6. Active Experiments and Their States

*Every [experiment contract](../GLOSSARY.md#experiment-contract) currently open
against this system, and where it sits in its lifecycle — so an operator does not
treat a diagnostic run as decision-grade, or touch a frozen artifact mid-experiment.*

| Experiment | State (registered / frozen / qualifying / confirming / closed) | Notes |
|---|---|---|
| [experiment identity] | [state] | [what would break if touched] |

### 7. Standing Rules in Force

*[Consequence-bearing tolerances](../GLOSSARY.md#consequence-bearing-tolerance),
[purchase triggers](../GLOSSARY.md#purchase-trigger), stop conditions, and this
document's own review cadence — the rules an operator must not silently override.*

- [Rule]: [trigger condition] → [required response].
- **This document's review cadence:** [interval or triggering event].

### 8. Contacts / Ownership

*Who interprets results, who executes changes, and who to escalate to — roles, not
necessarily names, per the [experiment contract](../GLOSSARY.md#experiment-contract)
role split (scientific owner interprets; executor runs the rules; the contract
executes).*

| Role | Responsibility | Contact |
|---|---|---|
| [role] | [what this role owns] | [contact placeholder] |

---

## Delete No Section

Every numbered section above **MUST** appear in a filled handoff. If a section
genuinely does not apply to this system, write the section header with the body
`N/A — [reason]` rather than omitting it. Absence is a decision, and the next
operator needs to see that the decision was made rather than skipped.

---

## Miniature Filled Example

*Illustrative example — synthetic. Invented project ("Ledger-Assist", a small
internal document-QA service). All names, hosts, and numbers invented.*

**§1 System inventory:**

| Component | Runs where | Port / endpoint | Version | Owner |
|---|---|---|---|---|
| API gateway | rented single-GPU node, us-east | `/v1/answer` | build `a1b2c3d` | platform team |
| Retrieval index | same node | internal | index `2026-01-14` | platform team |

**§2 Execution-system identities:** Ledger-Assist v3 — model artifact
`hash:9f2a…` · runtime: open-source serving stack v0.9.x · rented single-GPU node ·
custom harness v1.4 · context policy: top-6 retrieved chunks, 2k-token budget ·
tools: document-search only · generation budget: 512 tokens · verifier:
citation-presence checker v1 · environment: containerized, no virtualization
concerns observed to date.

**§3 Environment gotchas:**

| Symptom | Cause | Rule |
|---|---|---|
| First request after 10+ min idle is slow (~8s) | Node scales workers to zero on idle | Treat cold-start latency as a separate metric; exclude from SLA sampling, or pre-warm before a benchmark |

**§4 Verification commands:**

| Check | Command | Expected output |
|---|---|---|
| Gateway healthy | `curl -s localhost:[PORT]/health` | `{"status":"ok"}` |
| Integrity gate passes | `[integrity-gate command]` | exit code 0, all items pass |

**§5 Data stores:**

| Store | Role | Notes |
|---|---|---|
| `answers_log` | trajectory record | append-only, 90-day retention |
| `eval_gold` | authoritative (held out) | write access restricted to eval maintainers |

**§6 Active experiments:**

| Experiment | State | Notes |
|---|---|---|
| "Retrieval chunk-count sweep" | qualifying | do not redeploy gateway until closed |

**§7 Standing rules:** Purchase trigger: 3 consecutive months of rented spend above
$400/mo → evaluate owned hardware. This document's review cadence: monthly, first
business day.

**§8 Contacts:**

| Role | Responsibility | Contact |
|---|---|---|
| Scientific owner | Interprets experiment results, approves promotion | [placeholder] |
| Executor | Runs deployments, verification commands | [placeholder] |

---

**Governing chapters:** [12. Observability, Learning, and Promotion](../12_OBSERVABILITY_LEARNING_AND_PROMOTION.md)
· [02. Execution System Model](../02_EXECUTION_SYSTEM_MODEL.md)

**Related templates:** [EXPERIMENT_CONTRACT.md](EXPERIMENT_CONTRACT.md) ·
[METHOD_DECISION_RECORD.md](METHOD_DECISION_RECORD.md)

[Index](../README.md) · [Glossary](../GLOSSARY.md)
