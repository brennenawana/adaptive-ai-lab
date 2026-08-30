# Method Decision Record

Six months from now somebody who was not in the room will ask why the work is done this
way. If nobody can answer, the question gets argued again from the start, by people with
less evidence than you have in front of you today.

A method decision record is that answer, written once. One decision about *method* —
adopted, rejected, revised, or superseded — with the reasoning that forced it, in the
style of an architecture decision record, so the reasoning outlives the person who made
it and future projects do not re-litigate a question this practice has already answered.
Feeds `CHANGELOG.md` on every entry.

> Index: [../README.md](../README.md) · Governing chapter: [00. Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md)

## When to use / when not to use

- **SHOULD** use when adopting, rejecting, or revising an element of method — a
  statistical rule, a stopping rule, a taxonomy entry, a template, a default — that
  will bind more than one project or experiment going forward.
- **SHOULD** use when two legitimate approaches conflict and a project-level
  decision rule is needed: this record IS that decision rule, written once instead
  of re-argued on every project where the conflict recurs.
- Use when a [vendor verdict](../GLOSSARY.md#vendor-verdicts) changes (FOLLOW →
  ADAPT → DEPRECATED) for a tool or method this practice depends on — the record is
  what lets a later reader see *why* the verdict moved, not only that it did.
- **Do not** use it for a single experiment's calibration choice — that belongs in
  the experiment's own amendment log
  ([EXPERIMENT_CONTRACT.md](EXPERIMENT_CONTRACT.md) §18 Amendment Log), not here.
- **Do not** use it for routine engineering changes with no methodology
  consequence (a refactor, a dependency bump) — this record is for decisions a
  future project would otherwise have to re-derive from scratch.
- Keep each entry short enough to write in one sitting. If the reasoning needs more
  than a page, the decision is probably still being made, not yet decided — come
  back when it is.

## Rigor-tier applicability

| Tier | Requirement |
|---|---|
| Tier 1 — Exploratory | Optional; useful personal practice, but nothing downstream depends on it existing. |
| Tier 2 — Consequential (default) | **SHOULD** be written whenever the decision will bind future comparable experiments — it is how a contradiction stays visible with a project-level decision rule instead of being re-decided ad hoc each time it recurs. |
| Tier 3 — High-stakes/regulated | **MUST** be maintained as the audit trail for the [rigor dial](../GLOSSARY.md#rigor-dial)'s Tier 3 requirement of periodic methodology audit — the review date in §7 is what that audit reads against. |

Rigor attaches to how far a decision's consequences travel, not to which project
happened to force it: a Tier 1 exploration that settles a question every later
project would otherwise re-ask earns a record here regardless of that project's own
tier.

---

## The Record

*Fill every section below for the decision being recorded. Placeholders in
`[brackets]` carry inline guidance in italics — replace the placeholder, keep or
delete the guidance. No section may be silently omitted; see
["Delete no section"](#delete-no-section) at the end of this document.*

### 1. ID and Date

*A stable identifier (sequential per practice, e.g. `MDR-YYYY-NNN`) and the date
the decision was made — the date it was decided, not the date somebody got around to
writing it up. Other records point at this ID (§8), so it does not change once
published.*

[MDR-ID], [date]

### 2. Status

*One of: proposed / adopted / rejected / superseded. A record can sit at
"proposed" while evidence is gathered; move it forward explicitly, never silently.
This is the first thing a later reader checks, and a record still at "proposed" is
not something to build on.*

[status]

### 3. Context

*The decision this record was forced to make, and why it could not be avoided —
what problem, contradiction, or new evidence made the prior default (or the
absence of one) untenable. If the context does not name something that broke, or two
defensible practices that could not both be followed, what you have is a preference
rather than a decision.*

[context, 2–5 sentences]

### 4. Decision

*The decision itself, stated as an instruction a future reader could follow
without re-reading the context — this is the sentence that gets quoted elsewhere.
Write it imperatively and name its scope: what must now be done, on which class of
work, and what stays out of scope.*

[decision statement]

### 5. Evidence

*What actually supports this decision. Three kinds are admissible, and they do not
carry the same weight:*

- *cited source IDs from the ledger (`[EXT-...]`, `[NV-...]`) — the strongest, because
  a reader can go and check them;*
- *first-principles reasoning — legitimate, and it has to be written out here, not
  gestured at;*
- *what happened on one project — real, and the weakest of the three, because nobody
  else can audit it.*

*Carry an [evidence-strength label](../GLOSSARY.md#evidence-strength-labels) on each
item. Where a single project's result is all you have, say so: on its own it supports a
generic default, not a generic normative principle — the B-versus-A distinction in the
[A-to-H classification](../GLOSSARY.md#a-to-h-classification) — and naming that ceiling
here is what stops a later reader assuming a stronger one.*

*A scenario is not evidence. The `SCENARIO-*` files are invented illustrations; link one
the way the chapters do (`[SCENARIO: SCENARIO-NN]`) if it shows the shape of the
reasoning, and keep it out of the list of things that support the claim.*

- [evidence item, with its source ID and evidence-strength label]

### 6. Consequences

*What this decision changes going forward, INCLUDING what becomes harder — a
decision with only upside was not examined honestly. State the trade explicitly; an
empty second line means the record is not finished.*

- Becomes easier / possible: [...]
- Becomes harder / ruled out: [...]

### 7. Review Date

*When this decision is re-examined — a fixed date, or a triggering event (a new
suite version, a vendor-verdict change, a stated volume of new evidence). Never
"indefinitely": everything here is a default until reviewed, and an unreviewed default
quietly hardens into a rule nobody chose.*

[review date or trigger condition]

### 8. Supersedes / Superseded-by

*Links to the record this replaces and, once it happens, the record that replaces
this one — so the decision history reads as a chain, not scattered fragments. Going
back to the older record to fill in its "superseded by" line is the step that gets
forgotten, and it is the one that makes the chain readable from either end.*

- Supersedes: [MDR-ID or "none"]
- Superseded by: [MDR-ID or "none — current"]

---

## Delete No Section

Every numbered section above **MUST** appear in a filled record. If a section
genuinely does not apply, write the section header with the body `N/A — [reason]`
rather than omitting it. Absence is a decision, and a reviewer needs to see that
the decision was made rather than skipped.

---

## Miniature Filled Example

*Illustrative example — synthetic worked instance: adopting cluster-robust paired
inference as this practice's primary comparison statistic, written in the abstract
with invented figures standing in for a real record.*

**§1 ID and date:** MDR-2026-014, 2026-03-04

**§2 Status:** adopted

**§3 Context:** Early experiment reports computed paired significance as if each
evaluation item were an independent observation. A pilot re-analysis found outcomes
correlated within evaluation strata (illustrative ICC ≈ 0.30 on a representative
suite) — enough that the uncorrected analysis was materially overstating
confidence. Continuing to report uncorrected paired tests risked shipping
decisions on noise mislabeled as signal.

**§4 Decision:** Cluster-robust paired inference (t-test on per-cluster paired
means, degrees of freedom = clusters − 1) is the primary statistic for any paired
comparison where a [clustering unit](../GLOSSARY.md#clustering-unit) is
identifiable. McNemar's exact test on discordant pairs is retained as a secondary
statistic, always labeled anti-conservative under clustering. Every experiment
contract must state its clustering unit and
[effective N](../GLOSSARY.md#effective-n) before reporting a verdict.

**§5 Evidence:**
- [EXT-STATS-001] (`strong-evidence`) — clustered/paired standard-error and
  power/MDE formulas this decision adopts directly.
- [NV-EVALSDK-001] (`strong-evidence`) — McNemar paired testing with reported
  power tables and MDE, confirming McNemar's applicability and its limits as a
  secondary check.

**§6 Consequences:**
- Becomes easier / possible: [INCONCLUSIVE](../GLOSSARY.md#inconclusive) verdicts
  are now distinguishable from genuine null results; reviewers can see the
  effective N behind every headline number.
- Becomes harder / ruled out: some comparisons that read as significant under the
  old (uncorrected) analysis now read as INCONCLUSIVE at the same sample size;
  every contract now carries an extra pre-registration step (estimate ICC, compute
  design effect) before it can freeze.

**§7 Review date:** Next major suite-version release, or 2026-09-01, whichever
comes first.

**§8 Supersedes / superseded-by:** Supersedes: none (first statistics-primary
decision on record). Superseded by: none — current.

---

**Governing chapter:** [00. Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md)

**Related templates:** [EXPERIMENT_CONTRACT.md](EXPERIMENT_CONTRACT.md) ·
[OPERATIONAL_HANDOFF.md](OPERATIONAL_HANDOFF.md)

[Index](../README.md) · [Glossary](../GLOSSARY.md)
