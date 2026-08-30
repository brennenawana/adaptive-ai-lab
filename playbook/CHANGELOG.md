# Changelog

> Part of the **Adaptive AI Systems Playbook** · [Index](README.md)

Every entry here records three things, and all three are mandatory: **what
changed**, **why**, and **the evidence that forced it**. A decision to adopt or
reject a method also carries a
[METHOD_DECISION_RECORD](templates/METHOD_DECISION_RECORD.md). A sweep that
re-verifies the source ledger is filed as a PATCH.

## What the version numbers mean

The scheme is semver. Its interpretation was fixed at 0.1.0 and has not moved
since.

**A leading 0 is a statement about validation, not about polish.** While the version
is **0.x**, the methodology is still being generalized and validated, and one source
project is the only full instantiation of it. Read the chapters as procedures that
have been carried all the way through once — not as procedures that many teams have
run independently.

**1.0 is gated, not scheduled.** Reaching it requires successful instantiation on at
least two materially different project types. Each of those has to be carried
through at least one frozen, executed experiment contract, using only this playbook
and no source-project knowledge. Until that has happened, the number stays below 1
however complete the book looks.

Within that, each digit moves for its own reason:

- **MAJOR** — a PRINCIPLE changes meaning, or a template's required sections change
  incompatibly. These are the changes that can invalidate work already built against
  an earlier version.
- **MINOR** — a new method, chapter, template, or supported execution surface. A
  B→A promotion counts here too: a statement that was a generic default hardening
  into a generic normative principle, in the
  [A–H classification](GLOSSARY.md#a-to-h-classification).
- **PATCH** — a clarification, a source refresh, a link fix, a non-normative
  example.

---

## A note on this build

This is the public build of the playbook. It differs from the releases recorded
below in one way that matters when you read them.

The 0.1.0 and 0.1.1 releases shipped twelve case studies drawn from a real project,
with that project's own measurements. This build does not contain them. They were
removed before publication and replaced by twelve invented scenarios, `SCENARIO-01`
through `SCENARIO-12`, which preserve each original's lesson and none of its data.

The entries below describe those releases as they actually were. Where they mention
case studies or empirical project evidence, that is an accurate record of what the
release contained — not a description of the files in this build. Nothing in this
build rests on that evidence: a scenario illustrates a rule and is never cited as
support for one, and every claim the chapters call established is carried by an
external source in the [ledger](references/SOURCES.md).

The removal also means the `/versions/` history feature is disabled here. It
reconstructed past releases from their git commits, which still contain the material
that was removed.

---

## 0.1.1 — 2026-08-21 — independent-audit correction release (PATCH)

An external independent audit of the committed v0.1.0 raised seven candidate
findings. Each one was independently re-verified against the repository, re-derived
mathematically where applicable, and checked against the live source ledger before
any edit was made. That the audit had raised an issue was never itself treated as
evidence. Verdicts: 3 CONFIRMED, 4 PARTIALLY CONFIRMED, 0 rejected outright. Full
dispositions were recorded in the source project's evidence map, which is not part
of this build.

| What | Why | Evidence |
|---|---|---|
| **Fixed** (09 §5, §9; 12; 14; GLOSSARY): training admissibility is component-level provenance, not trajectory ownership — "own trajectory" text that claimed to "sidestep the provider-output restriction entirely" removed; a trajectory from a cascade system embeds the escalation tier's managed-provider outputs | The prior wording let a cascade operator harvest frontier outputs as training targets while believing themselves compliant | The playbook's own default architecture (ch. 08) produces trajectories whose components have different permitted uses; provider terms restrict outputs regardless of who stores the record (EXT-LEGAL-001/002/003, verified 2026-08-21) |
| **Fixed** (11 Q0, 11 §8, 14 §3.4): chapter 11's compute-supply tree now applies the same admissible-execution-surface test as QUICKSTART node 5 and 05 §5.2 — a written requirement mandates self-hosting only when no compliant managed configuration satisfies it | 11's Q0 hard-ruled managed APIs OUT on *any* hard privacy constraint, contradicting the navigator's test and converting an admissibility filter into a self-hosting mandate | One rule across the playbook; QUICKSTART/WALKTHROUGH already modeled the in-tenant-managed-API case as admissible |
| **Changed** (04 §8, formulary §2/§3b/§14, SCENARIO-02, source ledger): clusters-vs-replications phrasing corrected — within-cluster replication adds power monotonically for ICC < 1 but saturates at N_eff = k/ICC; independent clusters grow N_eff without bound; the absolute "not replications" wording removed | The absolute form was mathematically wrong (∂N_eff/∂m = k(1−ICC)/(1+(m−1)ICC)² > 0); the practical preference for clusters survives with its actual mechanism stated | Derived directly from the playbook's own DEFF model; Var(d̄_j) = σ_b² + σ_w²/m floors at σ_b |
| **Changed** (10 §4): "one change crosses a promotion stage at a time" → "one **declared treatment** at a time" — a frozen candidate execution system differing in several components is one legitimate treatment; system-level comparison licensed as a bundle, component-attribution claims still require ch. 04 isolation | The old wording accidentally forbade legitimate whole-system A/B promotion that ch. 02 already frames as first-class | 02's execution-system comparability model; the invariant that matters is no *undeclared* concurrent change |
| **Changed** (10 §5, §6, §12; templates/PROJECT_PROFILE field 4; SYNTH-08): human-baseline shadow gate — veto authority moved to the adjudicated regret ceiling; agreement rate is a compatibility diagnostic with a review trigger by default, and gates only when the project profile's field-4 behavioral-compatibility declaration (added as the carrier) makes it one | An unconditional agreement floor blocks a candidate that is systematically better than the incumbent human process — it rewards imitation over adjudicated correctness | The variant's own adjudication asymmetry (candidate-right/human-wrong is not regret) already implied it; the gate now matches, and the condition has a profile field to read from |
| **Changed** (02 §5, §9): "opt-in in every major open serving engine" narrowed — the two ledger-verified engines expose opt-in deterministic/batch-invariant modes (neither as its default); support, defaults, and guarantees vary by engine and version, and other engines were not verified for such modes; probe the frozen runtime, never infer determinism from feature availability | "Every" outran the ledger: exactly two engines' modes were live-verified (2026-08-21) | Source-ledger verification records (EXT-VLLM-001, EXT-SGLANG-001) |
| **Erratum recorded** (no file change needed): the v0.1.0 release summary and commit message stated G-dispositions as 16 COVERED / 3 DOCTRINE / 1 OUT-OF-SCOPE; the authoritative in-chapter dispositions are **15 COVERED / 4 COVERED-AS-DOCTRINE-NOT-YET-EXERCISED (G3, G5, G8, G10) / 1 EXPLICITLY-OUT-OF-SCOPE-FOR-0.1 (G9)**. No gap was reclassified; no shipped file carried the wrong count | Bookkeeping honesty: the summary miscounted; the chapters were always the record | Mechanical enumeration of the disposition lines in chapters 00–13 |
| **Release consistency check (14 §8) re-run** after the corrections, plus two bounded post-edit adversarial reviews (scientific consistency; practitioner portability across seven routing profiles) | 14's own rule: chapter-14 entries must match their source chapters at every release; the reviews check the corrections did not create new contradictions | The reviews caught the sweep gaps the first pass missed — all fixed before tagging: 14 §5's stale "one change at a time" deployment line; 05 §5.2 and 02 §5 Step 4 not yet carrying the admissibility test they were cited for; an 11 Q0-vs-§8 contradiction (resolved by the Q0a/Q0b split + a managed-surface row in §8's tier table); a missing component-provenance field in 12 §5.2's trajectory record; a missing profile carrier for the behavioral-compatibility declaration; worked-example alignment (SYNTH-07/08, 09 §11) |

## 0.1.0 — 2026-08-21 — first authored release

| What | Why | Evidence |
|---|---|---|
| All 15 chapters (00–14), 9 templates, statistics formulary, vendor recipe notes, source ledger (101 sources), glossary (~90 terms), navigator (QUICKSTART + 6 archetypes + rigor dial), 12 empirical case studies, 10 synthetic worked examples, 1 synthetic end-to-end walkthrough | First authored version of the reusable, project-independent methodology; entry point for future projects | Extracted per the committed Pass-1 build plan and Pass-2 authoring spec from: a five-day experimental program's primary record (contracts, reports, autopsy, registries), two adversarially-verified 2026-08 research studies (vendor audit; methodology/hardware study re-derived against the source project's own trajectory data), and a live source re-verification sweep (2026-08-21) |
| Generic-vs-project boundary enforced: project numerics and identities kept out of the shipped examples; generic text carries procedures only | The playbook must be usable with zero source-project context; single-project numbers are not defaults | Build-plan extraction rules §5 ("numbers never travel; procedures travel"); release portability check |
| Canonical failure taxonomy RC-1…RC-12 defined (ch. 03) with the intervention ladder keyed to it | The record carried two historical taxonomies plus an operating cause→action table; a single taxonomy with explicit mapping replaces a silent pick | Owner decision 9; historical taxonomies extracted verbatim and mapped (maintainer evidence map) |
| Rigor dial: three stakes tiers over a six-item never-skippable floor | As written, the source methodology read all-or-nothing; proportionality was a named gap (G2) | Owner decision 10; validated against synthetic profiles incl. a deliberately low-stakes project (W4/W9) |
| Judge-calibration protocol included as `doctrine — not yet exercised` (ch. 03) | Most client projects need judge-graded evals; the source project never exercised one — honesty marker instead of omission | Owner decision 1; JudgeBench/κ-deflation literature as the evidence base |
| Source ledger with live re-verification: 68 verifications, 53 CONFIRMED, corrections folded in (incl. two claim-attribution corrections and one platform-sunset flag) | FOLLOW/ADAPT verdicts are dated claims; several load-bearing sources are volatile | Authoring-pass verification sweep of 2026-08-21, recorded per source in `references/sources.yaml` (`last_verified` + notes): e.g., the NVIDIA open-eval-recipe blog does not carry the pinning/smoke claims previously attributed to it; NeMo Customizer early-stopping defaults are code-level, not doc guidance; the hosted OpenAI Evals platform sunsets 2026-11-30 |
| Rejections shipped as conditions, not verdicts (e.g., i.i.d.-calibrated sequential tests rejected *under clustered ordered execution*) | The source project's rejections were evidence-conditional; generic H-class is reserved for generically-wrong practices | Build-plan §5.4; statistics re-derivation on real trajectory data (α-inflation ~2.2× at measured clustering) |
| Pre-release validation: navigator dry-runs on 7 synthetic profiles (incl. a deliberately low-stakes one for the rigor dial); adversarial scientific/portability/consistency reviews; per-number fact-check of all 12 case studies; all BLOCKER/MAJOR findings fixed before tagging | The playbook's own methodology applied to itself: instruments validated before their scores are believed | ~119 recorded findings (19 blocker, 59 major) — highlights fixed: an inverted threshold-vs-ceiling sentence; a mis-derived routing false-negative break-even; SE-vs-MDE conflation in a worked example; a bindable minimum-κ gate added to judge calibration; the quantization acceptance gate bound to the statistics canon; archetype-tree disambiguation for in-tenancy-managed-API profiles; eight case-study numeric/framing corrections |
