# Changelog

> Part of the **Adaptive AI Systems Playbook** · [Index](README.md)
>
> Every entry records three things, mandatorily: **what changed**, **why**, and
> **the evidence that forced it**. Method adoptions/rejections carry a
> [METHOD_DECISION_RECORD](templates/METHOD_DECISION_RECORD.md); source-ledger
> re-verification sweeps are PATCH entries.

Versioning (semver, interpretation fixed at 0.1.0):
- **0.x** — the methodology is being generalized/validated; one source project is
  the only full instantiation.
- **1.0** — gated on successful instantiation on at least two materially different
  project types, each carried through at least one frozen, executed experiment
  contract using only this playbook (no source-project knowledge).
- **MAJOR** — a PRINCIPLE changes meaning, or a template's required sections change
  incompatibly. **MINOR** — new method/chapter/template/supported execution surface;
  a B→A promotion. **PATCH** — clarification, source refresh, link fix,
  non-normative example.

---

## 0.1.0 — 2026-08-21 — first authored release

| What | Why | Evidence |
|---|---|---|
| All 15 chapters (00–14), 9 templates, statistics formulary, vendor recipe notes, source ledger (101 sources), glossary (~90 terms), navigator (QUICKSTART + 6 archetypes + rigor dial), 12 empirical case studies, 10 synthetic worked examples, 1 synthetic end-to-end walkthrough | First authored version of the reusable, project-independent methodology; entry point for future projects | Extracted per the committed Pass-1 build plan and Pass-2 authoring spec from: a five-day experimental program's primary record (contracts, reports, autopsy, registries), two adversarially-verified 2026-08 research studies (vendor audit; methodology/hardware study re-derived against the source project's own trajectory data), and a live source re-verification sweep (2026-08-21) |
| Generic-vs-project boundary enforced: project numerics and identities quarantined to `examples/CASE-*`; generic text carries procedures only | The playbook must be usable with zero source-project context; single-project numbers are not defaults | Build-plan extraction rules §5 ("numbers never travel; procedures travel"); release portability check |
| Canonical failure taxonomy RC-1…RC-12 defined (ch. 03) with the intervention ladder keyed to it | The record carried two historical taxonomies plus an operating cause→action table; a single taxonomy with explicit mapping replaces a silent pick | Owner decision 9; historical taxonomies extracted verbatim and mapped (maintainer evidence map) |
| Rigor dial: three stakes tiers over a six-item never-skippable floor | As written, the source methodology read all-or-nothing; proportionality was a named gap (G2) | Owner decision 10; validated against synthetic profiles incl. a deliberately low-stakes project (W4/W9) |
| Judge-calibration protocol included as `doctrine — not yet exercised` (ch. 03) | Most client projects need judge-graded evals; the source project never exercised one — honesty marker instead of omission | Owner decision 1; JudgeBench/κ-deflation literature as the evidence base |
| Source ledger with live re-verification: 68 verifications, 53 CONFIRMED, corrections folded in (incl. two claim-attribution corrections and one platform-sunset flag) | FOLLOW/ADAPT verdicts are dated claims; several load-bearing sources are volatile | Authoring-pass verification sweep of 2026-08-21, recorded per source in `references/sources.yaml` (`last_verified` + notes): e.g., the NVIDIA open-eval-recipe blog does not carry the pinning/smoke claims previously attributed to it; NeMo Customizer early-stopping defaults are code-level, not doc guidance; the hosted OpenAI Evals platform sunsets 2026-11-30 |
| Rejections shipped as conditions, not verdicts (e.g., i.i.d.-calibrated sequential tests rejected *under clustered ordered execution*) | The source project's rejections were evidence-conditional; generic H-class is reserved for generically-wrong practices | Build-plan §5.4; statistics re-derivation on real trajectory data (α-inflation ~2.2× at measured clustering) |
| Pre-release validation: navigator dry-runs on 7 synthetic profiles (incl. a deliberately low-stakes one for the rigor dial); adversarial scientific/portability/consistency reviews; per-number fact-check of all 12 case studies against the primary record; all BLOCKER/MAJOR findings fixed before tagging | The playbook's own methodology applied to itself: instruments validated before their scores are believed | ~119 recorded findings (19 blocker, 59 major) — highlights fixed: an inverted threshold-vs-ceiling sentence; a mis-derived routing false-negative break-even; SE-vs-MDE conflation in a worked example; a bindable minimum-κ gate added to judge calibration; the quantization acceptance gate bound to the statistics canon; archetype-tree disambiguation for in-tenancy-managed-API profiles; eight case-study numeric/framing corrections to match the primary record |
