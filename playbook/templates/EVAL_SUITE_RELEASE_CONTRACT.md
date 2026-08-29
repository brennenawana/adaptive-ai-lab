# Eval Suite Release Contract

> A versioned, contract-governed release of an evaluation suite: the document that
> freezes what a [suite release](../GLOSSARY.md#suite-release) claims, gates, and
> refuses to compare against — before any score computed from it is trusted for a
> decision.
>
> Index: [../README.md](../README.md) · Governing chapter:
> [03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md)

## When to use / when not to

- **MUST** use this template for any suite version an
  [experiment contract](EXPERIMENT_CONTRACT.md) will cite as its frozen scientific
  baseline (§2 of that template) — a suite that qualifies or confirms a decision is
  itself part of the decision's evidence chain and needs the same discipline.
- **MUST** use it whenever an existing suite changes in any way that alters what a
  score means: items, gold answers, ontology, grader, or split boundaries. Write it
  *at the moment of freeze*, not while criteria are still being discovered — this is
  the [criteria drift](../GLOSSARY.md#criteria-drift) window closing.
- **SHOULD NOT** use it for routine, already-versioned regression runs against a
  suite whose release contract already exists — see
  [regression suite vs capability suite](../GLOSSARY.md#regression-suite-vs-capability-suite);
  that is ordinary CI against a frozen instrument, not a new release.
- **Do not** use it to license comparing two suite versions to each other — that
  comparison is *refused* by §9 of a completed contract, not authorized by
  completing one.
- One contract per suite version. A version with unlisted changes, or a "what
  changed" field left blank on anything but a first release, is a defect in this
  contract, not evidence that nothing changed.

## Rigor-tier applicability

| Tier | Requirement |
|---|---|
| Tier 1 — Exploratory | Not required. Ad hoc or [smoke-tier](../GLOSSARY.md#smoke-tier) evals may run without a release contract, but their results **MUST NOT** be cited as adoption or elimination evidence. |
| Tier 2 — Consequential (default) | **MUST** be completed before this suite version backs any [experiment contract](EXPERIMENT_CONTRACT.md). §4 and §7 below are this tier's concrete form of the [never-skippable floor](../GLOSSARY.md#never-skippable-floor)'s "define the evaluation boundary before any quality claim." |
| Tier 3 — High-stakes/regulated | **MUST** be completed as Tier 2, plus: a judge named in §5 **MUST** have a current calibration record before its scores may qualify a candidate; this contract is retained in the tamper-evident [record of record](../GLOSSARY.md#record-of-record) and revisited at the periodic methodology audit. |

Rigor attaches to the *decision's* consequence, not the suite's apparent maturity: a
suite first built for internal direction-finding that later backs a shipping
decision completes this contract at Tier 2+ before that decision is made.

---

## 1. Suite Identity and Version

- **Suite name:** [name]
- **Version:** [identifier — pick and state one convention (date-stamp, sequential
  integer, or semver) and use it consistently for this suite from here on]
- **Prior version:** [identifier, or `N/A — first release`]
- **What changed vs. the prior version, and why:** [list every change as *was X, now
  Y, because Z*. This is where [criteria drift](../GLOSSARY.md#criteria-drift) gets
  written down instead of silently absorbed — criteria and ground truth co-evolve as
  graders see real output, and that evolution is expected, not a discipline failure,
  as long as it is versioned rather than edited in place [EXT-EVAL-004]]
- **Effective date:** [date]
- **Owner:** [name/role]

## 2. Corpus Identity

- **Generation method:** [templated/generated, human-authored, mined-from-production,
  or mixed — state per stratum if it varies]
- **Determinism / identity record:** [generated corpus: seed + generator version +
  content digest, re-derivable from those three alone. Annotated corpus:
  annotation-batch identity + annotator roster + guideline version. Either way, the
  identity must be reconstructable, not just remembered by whoever built it]
- **Corpus digest/hash:** [digest]
- **Item count:** [N total]; [N per stratum]

## 3. Ontology/Taxonomy Version and Change Discipline

- **Task ontology version:** [identifier/link — see
  [task ontology](../GLOSSARY.md#task-ontology)]
- **Breaking-change rule:** [state plainly what counts as a breaking change here:
  adding/removing/redefining a category, a root-cause class, a forbidden-claim rule,
  or a scoring boundary. A breaking change to the ontology **MUST** produce a new
  suite version — never an in-place edit to an existing one]

## 4. Ground-Truth Gates

- **Gold-answer verification:** [method, who verified, date]
- **Per-stratum reachability/solvability ceiling:** [MEASURED value per stratum,
  printed — never assumed 100%. See
  [the full [reachability ceiling](../GLOSSARY.md#reachability-ceiling) definition]:
  a stratum whose ceiling sits below its own passing threshold is unwinnable, and its
  scores measure the defect, not the model. Fix or exclude it before release; do not
  ship it with a footnote]
- **Frontier-saturation check:** [run the strongest available system; does it
  approach its own measured ceiling? See
  [frontier-saturation check](../GLOSSARY.md#frontier-saturation-check) — a suite the
  strongest arm cannot approach is a suspect instrument]
- **Inversion check:** [any stratum where a weaker system beat a stronger one? See
  [inversion check](../GLOSSARY.md#inversion-check) — investigate the instrument
  before believing the score]

## 5. Grader Identity

- **Deterministic scorer/verifier version(s):** [version(s)]
- **Judge, if used:** [model/version + calibration-record reference. Judges score
  near chance on objectively verifiable tasks absent calibration [EXT-JUDGE-002];
  with no calibration record yet, mark this
  `status: doctrine — not yet exercised` and route decisions around it]
- **Grader-to-taxonomy binding:** [how scorer/judge output maps onto the
  [canonical failure taxonomy](../GLOSSARY.md#canonical-failure-taxonomy) root-cause
  classes, if it does]

## 6. Split Design

- **Strata:** [list each stratum and the
  [clustering unit](../GLOSSARY.md#clustering-unit) it represents — this feeds every
  MDE/effective-N calculation downstream in chapter 04]
- **Split sizes:** [iterate / qualify / confirm, or your equivalent split names, with
  item counts and disjointness stated]
- **Disjointness / leakage protections:** [how splits are kept non-overlapping; see
  [leakage](../GLOSSARY.md#leakage)]
- **Canary strings:** present: [yes/no]; location: [where embedded — see
  [canary string](../GLOSSARY.md#canary-string) [EXT-EVAL-007]]

## 7. Static Integrity Gates

- **Gate commands (executable):** [list each command, what it checks, and its
  pass/fail criterion — these must be runnable, not descriptive prose]
- **Full-corpus rule:** [state explicitly that these gates run on the FULL corpus on
  every release, never a subset. See
  [static integrity gates](../GLOSSARY.md#static-integrity-gates) — they are the
  instruments that catch instrument defects, so they do not inherit the sampling
  shortcuts applied elsewhere]

## 8. Baseline Re-Measurement Plan

- **Arms/incumbents that MUST re-baseline on this version:** [list]
- **Re-baseline deadline or trigger:** [date or condition]

## 9. Cross-Suite Refusal Statement

- [name the enforcement mechanism — a tooling/CI check, a comparison-function guard,
  whatever makes it structurally true — that refuses to compare a number computed on
  this suite version against a number from any other version. See
  [cross-suite refusal](../GLOSSARY.md#cross-suite-refusal): a paragraph asking
  people not to compare is not this]

## 10. Release Checklist

**All of the following MUST be true before this version is released for use in any
[experiment contract](EXPERIMENT_CONTRACT.md).**

- [ ] Ground-truth gates passed (§4)
- [ ] Static integrity gates green on the full corpus (§7)
- [ ] Frontier-saturation and inversion checks clean, or each anomaly explained
- [ ] Canary strings embedded and verified present
- [ ] Baseline re-measurement plan scheduled (§8)
- [ ] Cross-suite refusal mechanism verified live (§9)
- [ ] New version recorded in the [look ledger](TEST_LOOK_LEDGER.md) as a new
  instrument — prior exposure counts do not carry over to it

## Delete No Section

Every numbered section above **MUST** appear in a filled contract. If a section
genuinely does not apply to this suite, write the section header with the body
`N/A — [reason]` rather than omitting it. Absence is a decision; a reader needs to
see that the decision was made, not guess whether it was skipped.

---

## Miniature Filled Example

*Illustrative example — synthetic. Invented project: a warranty-claim triage system
whose eval suite gates whether a candidate model is trustworthy enough to recommend
approve/deny/escalate decisions. Tier 2. Condensed — a real contract fills every
field in every section above; this shows the shape.*

**§1 Identity:** Suite `warranty-claim-capability`. Version `2026-08-21`. Prior:
`2026-05-02`. Changed: added an absence-case stratum (claims with no defect found)
after the prior version's scoring showed the grader always located *some* defect to
cite; tightened the "escalate" gold criterion after reviewing 40 borderline outputs.
Owner: R. Alavi.

**§2 Corpus:** Human-authored from an anonymized claim sample, annotation batch
`2026-08-B`, two annotators plus adjudication. Digest `sha256:7c1e…`. 200 items
total, 25 per stratum across 8 strata.

**§3 Ontology:** `claim-taxonomy-2026-07`. Breaking change this release: added
`absence` as a category, forcing this version.

**§4 Ground-truth gates:** Gold re-verified by a third reviewer, 2026-08-18.
Reachability ceilings 96–100% across strata except the new absence stratum (90%;
three disputed items excluded from scoring pending resolution). Frontier check: the
strongest available system scores 93%, within 3pp of its own ceiling — clean.
Inversion check: none found.

**§5 Grader:** Deterministic field/citation scorer `2026-08`. No judge used.

**§6 Split design:** 8 strata (one per claim category, including absence); iterate
100 / qualify 50 / confirm 50, disjoint by claim ID. Canary string embedded in every
published excerpt.

**§7 Static integrity gates:** `evalctl verify gold`, `evalctl verify reachability`,
`evalctl verify digest` — all green on the full 200-item corpus, 2026-08-20.

**§8 Baseline re-measurement:** Incumbent rules engine and the current model
candidate both re-baseline on this version before 2026-09-01.

**§9 Cross-suite refusal:** The comparison tool reads a `suite_version` field from
both result sets and raises an error rather than emit a comparison if they differ.

**§10 Release checklist:** all boxes checked 2026-08-21.

---

**Governing chapter:** [03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md)

**Related templates:** [EXPERIMENT_CONTRACT.md](EXPERIMENT_CONTRACT.md) (§2 frozen
scientific baseline) · [TEST_LOOK_LEDGER.md](TEST_LOOK_LEDGER.md) ·
[PROJECT_PROFILE.md](PROJECT_PROFILE.md)

**See also:** [SCENARIO-09](../examples/SCENARIO-09_suite-versioning-criteria-drift.md)
(suite-versioning criteria drift) ·
[SCENARIO-04](../examples/SCENARIO-04_harness-defects.md) (harness defects an integrity
gate would have caught)

[Index](../README.md) · [Glossary](../GLOSSARY.md)
