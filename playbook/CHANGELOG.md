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

## 0.1.1 — 2026-08-21 — independent-audit correction release (PATCH)

An external independent audit of the committed v0.1.0 raised seven candidate
findings. Each was independently re-verified against the repository, re-derived
mathematically where applicable, and checked against the live source ledger before
any edit; the audit's having raised an issue was never treated as evidence.
Verdicts: 3 CONFIRMED, 4 PARTIALLY CONFIRMED, 0 rejected outright. Full
dispositions: `docs/research/PLAYBOOK_INTERNAL_EVIDENCE_MAP.md` §4.

| What | Why | Evidence |
|---|---|---|
| **Fixed** (09 §5, §9; 12; 14; GLOSSARY): training admissibility is component-level provenance, not trajectory ownership — "own trajectory" text that claimed to "sidestep the provider-output restriction entirely" removed; a trajectory from a cascade system embeds the escalation tier's managed-provider outputs | The prior wording let a cascade operator harvest frontier outputs as training targets while believing themselves compliant | The playbook's own default architecture (ch. 08) produces trajectories whose components have different permitted uses; provider terms restrict outputs regardless of who stores the record (EXT-LEGAL-001/002/003, verified 2026-08-21) |
| **Fixed** (11 Q0, 11 §8, 14 §3.4): chapter 11's compute-supply tree now applies the same admissible-execution-surface test as QUICKSTART node 5 and 05 §5.2 — a written requirement mandates self-hosting only when no compliant managed configuration satisfies it | 11's Q0 hard-ruled managed APIs OUT on *any* hard privacy constraint, contradicting the navigator's test and converting an admissibility filter into a self-hosting mandate | One rule across the playbook; QUICKSTART/WALKTHROUGH already modeled the in-tenant-managed-API case as admissible |
| **Changed** (04 §8, formulary §2/§3b/§14, CASE-002, source ledger): clusters-vs-replications phrasing corrected — within-cluster replication adds power monotonically for ICC < 1 but saturates at N_eff = k/ICC; independent clusters grow N_eff without bound; the absolute "not replications" wording removed | The absolute form was mathematically wrong (∂N_eff/∂m = k(1−ICC)/(1+(m−1)ICC)² > 0); the practical preference for clusters survives with its actual mechanism stated | Derived directly from the playbook's own DEFF model; Var(d̄_j) = σ_b² + σ_w²/m floors at σ_b |
| **Changed** (10 §4): "one change crosses a promotion stage at a time" → "one **declared treatment** at a time" — a frozen candidate execution system differing in several components is one legitimate treatment; system-level comparison licensed as a bundle, component-attribution claims still require ch. 04 isolation | The old wording accidentally forbade legitimate whole-system A/B promotion that ch. 02 already frames as first-class | 02's execution-system comparability model; the invariant that matters is no *undeclared* concurrent change |
| **Changed** (10 §5, §6, §12; templates/PROJECT_PROFILE field 4; SYNTH-08): human-baseline shadow gate — veto authority moved to the adjudicated regret ceiling; agreement rate is a compatibility diagnostic with a review trigger by default, and gates only when the project profile's field-4 behavioral-compatibility declaration (added as the carrier) makes it one | An unconditional agreement floor blocks a candidate that is systematically better than the incumbent human process — it rewards imitation over adjudicated correctness | The variant's own adjudication asymmetry (candidate-right/human-wrong is not regret) already implied it; the gate now matches, and the condition has a profile field to read from |
| **Changed** (02 §5, §9): "opt-in in every major open serving engine" narrowed — the two ledger-verified engines expose opt-in deterministic/batch-invariant modes (neither as its default); support, defaults, and guarantees vary by engine and version, and other engines were not verified for such modes; probe the frozen runtime, never infer determinism from feature availability | "Every" outran the ledger: exactly two engines' modes were live-verified (2026-08-21) | Source-ledger verification records (EXT-VLLM-001, EXT-SGLANG-001) |
| **Erratum recorded** (no file change needed): the v0.1.0 release summary and commit message stated G-dispositions as 16 COVERED / 3 DOCTRINE / 1 OUT-OF-SCOPE; the authoritative in-chapter dispositions are **15 COVERED / 4 COVERED-AS-DOCTRINE-NOT-YET-EXERCISED (G3, G5, G8, G10) / 1 EXPLICITLY-OUT-OF-SCOPE-FOR-0.1 (G9)**. No gap was reclassified; no shipped file carried the wrong count | Bookkeeping honesty: the summary miscounted; the chapters were always the record | Mechanical enumeration of the disposition lines in chapters 00–13 |
| **Release consistency check (14 §8) re-run** after the corrections, plus two bounded post-edit adversarial reviews (scientific consistency; practitioner portability across seven routing profiles) | 14's own rule: chapter-14 entries must match their source chapters at every release; the reviews check the corrections did not create new contradictions | The reviews caught the sweep gaps the first pass missed — all fixed before tagging: 14 §5's stale "one change at a time" deployment line; 05 §5.2 and 02 §5 Step 4 not yet carrying the admissibility test they were cited for; an 11 Q0-vs-§8 contradiction (resolved by the Q0a/Q0b split + a managed-surface row in §8's tier table); a missing component-provenance field in 12 §5.2's trajectory record; a missing profile carrier for the behavioral-compatibility declaration; worked-example alignment (SYNTH-07/08, 09 §11) |

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
