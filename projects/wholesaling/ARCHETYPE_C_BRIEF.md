# Operative Brief — Archetype C for Wholesaling

> Digest of playbook chapters 03 (Evaluation Foundation) + 07 (Intervention
> Ladder), plus the EXPERIMENT_CONTRACT / EVAL_SUITE_RELEASE_CONTRACT templates
> and chapter 14's condensed gates, produced 2026-08-22 by a Sonnet subagent
> delegation and reviewed by the orchestrator. The chapters remain normative;
> this brief is a working reference for executing archetype C against the
> wholesaling system. Section citations (e.g. "03 §5.2") bind to the playbook.

**Route:** 01 → 03 (eval first) → 07. Chapter 05 (selection) is premature until
diagnosis; do not change the system before the eval exists (QUICKSTART row C).
**Confirm C applies** (QUICKSTART node 2): fires when the incumbent lacks an
established quality bar, or nobody can say whether it's failing because no trusted
measurement exists. A system meeting a *measured* bar but merely expensive is D, not
C; a predecessor you intend to **replace**, not repair, is not "the incumbent" here.

---

## 1. Error-analysis-first eval construction (03 §5.1, §5.3–§5.5)

1. **Harvest real failures first** (§5.1 step1, EXT-EVAL-003) — traces/tickets/
   transcripts from the actual population, open-ended notes, before writing any
   category. Never start from an imagined taxonomy.
2. **Synthesize a closed category set**, symptom/root-cause split where the shape has
   one. Deliberately let some symptoms map to ≥2 root causes at comparable base rates
   ("deliberately ambiguous symptoms") — caps a lookup near the majority-cause base
   rate instead of ceiling (§8.2 arithmetic); a real reasoning probe.
3. **Place the task on the shape map first** (§5.1): diagnose-and-act → all 4 layers
   (symptom/root cause/sanctioned action/forbidden claim); classification → root
   cause ≈ label, no action/forbidden layer; extraction → fields + forbidden
   *fabrication*; generation → required-facts + rubric dims + forbidden claims, no
   action set. Mark N/A layers explicitly — over-building the ontology for the shape
   is a named, expensive mistake.
4. **Stratify by root-cause class, not symptom** — sampling/ceiling/power key on root
   cause; symptom is a display grouping only.
5. **Define per-category evidence requirements** — what facts a correct answer needs
   and where they live (feeds reachability, step 8).
6. **Corpus design (§5.3):** stratified sampling; ≥1 distractor valid for no item;
   ≥1 absence case; forbidden-claim classes score as automatic failure; per-instance
   (not just modal) consistency vs. every forbidden hypothesis; filler content through
   the **same generation pipeline** as primary content (a bypass leaves a model-visible
   artifact — structural-leakage finding if found, CASE-004).
7. **Ground-truth source (§5.4):** generator-derived (verified, not argued);
   human-annotated (dual-label+adjudicate+report κ, §6); judge-mediated (open-ended
   only, behind full §5.7 calibration — nothing until calibrated).
8. **Instrument validation before any score is trusted (§5.5)** — static integrity
   gates, executable, full-corpus, never subsettable (CASE-004: 13 harness defects
   found this way, all initially read as model weakness): **reachability ceiling**
   per stratum (`ceiling(s)=reachable(s)/N(s)`, replayed through the real tool
   surface, never argued from the generator); **threshold-below-ceiling check** —
   any stratum with threshold ≥ ceiling **fails the release** (mechanical gate;
   margin illustrative ceiling ≥ threshold+0.05); **weak-beats-strong inversion
   check**; **cross-arm disagreement review** before crediting/blaming either arm;
   **gold-answer gate** (gold replayed through scorer must score at ceiling);
   **determinism check** (regenerate, compare digest); **frontier-saturation check**
   (strongest system must approach its own ceiling).
9. **Non-generator (human-annotated) path — `doctrine — not yet exercised`** (§6):
   dual-label+adjudicate+report κ w/ CI (the corpus's own reliability ceiling — no
   score beats it) → sampled-audit ceiling sized so its margin of error is smaller
   than the threshold-to-ceiling margin, reported as an interval → auditor
   independence (solvability auditor ≠ that stratum's own annotator) → gold-answer
   gate unchanged, run first each release → determinism analog (re-annotate a
   pre-registered subsample, drift → suite release) → disagreement review via
   adjudicator → judge-mediated ground truth only behind full §5.7.

**Governing principle (§4):** the instrument's ceiling is measured before its score
is believed — a low score on an unvalidated stratum measures the defect, not the
model (P2, instrument-outranks-the-score).

---

## 2. Canonical failure taxonomy (03 §5.2)

| # | Class | Meaning | Rung |
|---|---|---|---|
| RC-1 | **Evaluation-instrument defect** | Harness, corpus, gold, or eval grader is wrong | 0 |
| RC-2 | Infrastructure/runtime defect | Serving stack/transport/config/env corrupts execution | 1 |
| RC-3 | Missing/unreachable evidence | Needed facts absent, unreachable via retrieval/tools | 2 |
| RC-4 | Tool/API contract defect | Schema/addressing/ordering/permission mismatch | 3 |
| RC-5 | Output/format enforcement gap | Correct content lost to parsing/structure failures | 3 |
| RC-6 | Task-specification gap | System never told (instructions/decomposition/examples) | 4 |
| RC-7 | **In-system verification gap** | The system's OWN verifier passes failures silently | 4 |
| RC-8 | Capacity/budget exhaustion | Context/reasoning/generation budget bounds outcome | 5 |
| RC-9 | Routing/escalation mismatch | Wrong tier / mis-set escalation | 6 |
| RC-10 | Capability gap — learnable *(provisional)* | Skill exists in obtainable data | 7 |
| RC-11 | Capability gap — fundamental *(provisional)* | Model class can't do it at any budget | 8 |
| RC-12 | Architecture mismatch *(provisional)* | Topology wrong for the task shape | 9 |

**RC-1 ranks first:** an unvalidated instrument makes every other class
unverifiable; §5.5 clears it before any other diagnosis is trusted.

**RC-1 vs RC-7:** defective component in the **execution system under test** → RC-7
(rung 4); in the **measuring instrument** → RC-1 (rung 0). **When in doubt, RC-1** —
an unneeded instrument check is bounded cost; trusting a broken instrument is not.

**RC-10/11/12 provisional-residual:** assigned only after RC-1…RC-9 excluded,
distinguished by the *outcome of the rung selected*: try RC-10 first (cheaper); a
rung-7 INCONCLUSIVE/null reclassifies to RC-11; a staged ladder replay whose residual
tracks topology (not one component) evidences RC-12.

**Stochastic reliability is cross-cutting, not a 13th class** — measure pass^k at a
pre-registered k, classify the residual: RC-2/rung1 (unintended nondeterminism),
RC-8/rung5 (sampling/budget), RC-9/rung6 (retry/escalation), else provisional-residual.

**Non-ML/legacy incumbents map onto the same classes:** stale rules = RC-6; rules
firing on unavailable data = RC-3; broken integration = RC-2/RC-4; silently-accepted
unverified results = RC-7; misrouted work = RC-9.

---

## 3. Trusted eval + EVAL_SUITE_RELEASE_CONTRACT freeze (03 §5.9–§5.11, §7)

**Trusted = every §1-step-8 integrity gate green on the full corpus, plus a frozen,
versioned release.** Criteria drift only via a versioned release, never a silent edit
(P6).

| § | Contract section | Contents |
|---|---|---|
| 1 | Identity/Version | name, version id, prior version, what-changed-and-why, owner |
| 2 | Corpus Identity | generation method, determinism record, digest, item counts |
| 3 | Ontology Version | id + explicit breaking-change rule |
| 4 | Ground-Truth Gates | gold verification, **per-stratum ceiling (measured, never assumed 100%)**, frontier-saturation, inversion checks |
| 5 | Grader Identity | deterministic scorer version; judge+calibration record (else `doctrine — not yet exercised`) |
| 6 | Split Design | strata + clustering unit, split sizes/disjointness, canary strings |
| 7 | Static Integrity Gates | executable commands + pass/fail criteria; explicit full-corpus rule |
| 8 | Baseline Re-Measurement | which arms re-baseline, deadline/trigger |
| 9 | Cross-Suite Refusal | the enforcement mechanism (tooling), not a request |
| 10 | Release Checklist | all above + canaries + look-ledger entry |

**Release gate:** every gate passes, full corpus, before tagging — GO (tag/freeze,
cross-suite refusal switches over) or NO-GO (fix; no partial promotion).

**Ontology-change checklist:** bump version → sync model-facing + scorer copies with
an automated equality test → re-check reachability for changed classes → record
rationale → never compare across versions silently → never change a mapping in
response to one system's answers.

**Regression vs capability (§5.10):** regression = broad/cheap/run-often/"did
anything break"; capability = targeted/at-decisions/"can it do X." An intervention
gate always runs the **full** regression suite, never just the target slice.

**Smoke tier (§5.11):** fixed mini-suite, minutes not hours; catches harness/schema
breakage before real spend; run before every scored run, **never quote it** (huge
MDE by design, non-promotable). A smoke **failure** is fully actionable (RC-1/RC-2).

---

## 4. Judge vs deterministic grading (03 §5.6–§5.7, §7; 14 §3.2)

```
Output objectively verifiable?  ──yes──► deterministic grader (MUST)
Open-ended/preference-shaped?   ──yes──► calibrated LLM judge (§5.7 protocol first)
mixed → split: deterministic on the checkable part + judge on the rest, reported separately
```

Deterministic is default wherever a check exists. A frontier judge scored ~56.6% vs
a 50% pairwise-chance baseline on **forced-choice hard-item discrimination**
(JudgeBench, EXT-JUDGE-002) — a narrow finding, not a measure of schema/exact-match/
execution grading; it does not license judge-over-deterministic substitution.

**Judge admissibility — `doctrine — not yet exercised`.** No judge score may drive a
decision until all eight are complete and reported: (1) sampling design + dual-
labeled, adjudicated anchor-set reliability, human–human κ reported alongside judge
κ; (2) chance-corrected agreement (Cohen's/weighted/Fleiss' κ as applicable), never
raw percent; (3) bias audits, each a measured quantity + consequence-bearing
tolerance — position (pairwise only), length/verbosity, self-preference, style; arm
blinding mandatory and separate, any identifying artifact is a leakage finding; (4)
rubric stability across *k* paraphrases vs. a max flip rate; (5) domain-transfer
check before reuse; (6) drift monitoring, recalibrate on a pre-registered trigger
only; (7) κ reported with a CI, always; (8) pre-registered κ bar + CI-width ceiling,
written **before** step 1 runs.

| Condition | Outcome |
|---|---|
| κ's lower CI bound ≥ bar, CI width within ceiling | **Trusted-for-decision** |
| point estimate ≥ bar, lower bound below (or CI too wide) | **Directional-only** |
| point estimate below bar, any step incomplete, or bias breached | **Not usable yet** |

Trust keys on the lower bound so a small noisy anchor set can't buy unearned trust.
Carve-out at any tier: an uncalibrated judge may be **unrecorded triage** only —
never in a comparison, decision, or reported number. Tier scaling: Tier 1 — no judge
score licensed for any decision; Tier 2 — full protocol + project-defensible bar;
Tier 3 — Tier-2 + max CI width + anchor set's own human–human κ must exceed the bar.

---

## 5. Intervention ladder + diagnostic gates (07 §5.1–§5.2, §7; 14 §2, §3.5)

Two evidence bars per rung, never conflated: **entry** (licenses starting — a
diagnosis, not an achievement) vs. **exit** (licenses descending past it — what §7's
descent gate binds on). Entry absent = **inapplicable**, not exhausted; record as a
finding, never cleared by silence.

| Rung | Fixes | Exit evidence | Cheap diagnostic first |
|---|---|---|---|
| 0 instrument integrity | RC-1 | static integrity gates green | the gates *are* the diagnostic |
| 1 infra/runtime | RC-2 | reproducibility boundary measured, gap persists; byte fidelity verified every hop | restart/concurrency probes; byte-equivalence through every proxy |
| 2 evidence/retrieval | RC-3 | reachability audited per stratum, gap persists | reachability replay vs real tool broker |
| 3 tool/output contracts | RC-4, RC-5 | contract audit passed, payload schema verified, gap persists | schema validation against emitted payload |
| 4 spec & verification | RC-6, RC-7 | one-factor variants show no further gain; verifier coverage checked | one factor per arm vs pre-registered adoption rule |
| 5 gen/reasoning budget | RC-8 | cap re-derived from current length distribution; truncation in tolerance; paired cap-raise diagnostic ≤ RE-SCOPE/DROP | paired cap-raise diagnostic — never "raise and see" |
| 6 routing/escalation | RC-9 | oracle headroom captured (router built, gap persists) OR below materiality bar | paired-oracle opportunity map before building a router |
| 7 fine-tuning | RC-10 | frozen acceptance gate CONFIRMED/REFUTED; **INCONCLUSIVE ≠ exhausted** | rig-first de-risking on toy config |
| 8 larger/different model | RC-11 | frozen paired acceptance gate CONFIRMED/REFUTED | candidate-characterization pass |
| 9 architectural redesign | RC-12 | frozen acceptance gate CONFIRMED/REFUTED; no rung below | cheapest end-to-end baseline on proposed topology |

**Never train (rung 7+) around a defect at rungs 0–4.** Rung 0's priority and this
rule are not locally overridable without a written method decision record; rungs 1–6
may be locally re-sequenced on clear diagnosis. **RC-2 vs RC-4:** replay the same
payload through the transport with the tool held fixed — bytes change → rung1/RC-2;
payload mismatches its own contract → rung3/RC-4.

**Diagnostic gates — pick the highest applicable rung cheaply (§5.2).** Design
pattern: (1) name the hypothesis as a falsifiable claim; (2) find the cheapest
observable that discriminates it (deterministic pass rate, never completion-only);
(3) pre-register GO/RE-SCOPE/DROP bands with a **sufficiency floor `n_min`** derived
from the interval width needed to separate bands (ch.04 MDE), before running
anything — `reconfirmed_sample < n_min` → INCONCLUSIVE/RE-SCOPE always (never
DROP/GO); else apply bands to the metric's **interval**, not point estimate; a
*screening*-mode gate must print **RANKED** with no inferential claim. **Completion
alone never produces GO.** (4) Run paired/controlled/counterbalanced whenever
crossing a measured reproducibility boundary. (5) Verdict binds absent a documented
override; Tier 2+ ledgers it as a non-promotable diagnostic run kind. Worked example
(§8): n=20, f_rescue=45% point estimate but 95% CI [25.8%,65.8%] straddles a 30% GO
threshold → **INCONCLUSIVE**, not GO; correct n_min≈40. A rescue rate is always an
**upper bound** on the reconfirmed subset (selection effect), never a population rate.

**Stopping a rung (§7 opportunity-cost test):** stop when **either** (a) exit
evidence is satisfied (incl. a diagnostic gate showing headroom exhausted) **or** (b)
continuing cost exceeds the residual gap's value — whichever binds first. **(b)
licenses stopping work only, never descending** — descent still needs (a) or a
recorded inapplicability for every rung above the target; past rung 6 into
fine-tuning additionally needs the full rung-7 entry bar (taxonomy gap + every rung
above exit-cleared + data has the skill + economics close), never opportunity cost
alone.

---

## 6. First frozen EXPERIMENT_CONTRACT (templates/EXPERIMENT_CONTRACT.md; 04 §7; 14 §6.1)

Mandatory Tier 2+ before any qualify/confirm evidence is used. 18 sections, none
silently omittable (`N/A — reason` if genuinely inapplicable):

| § | Section | Required content |
|---|---|---|
| 1 | Question/Decision/Prediction | grade-without-asking question; decision per outcome; non-goals; prediction filled pre-call |
| 2 | Frozen Scientific Baseline | exact suite version (never "latest"), corpus/scorer identity, immovable incumbent |
| 3 | Artifacts | content hash + upstream identity per arm (managed-API: version string+endpoint/region+as-of date+redeploy probe) |
| 4 | Execution Systems/Node Placement | full identity per arm; reproducibility boundary declared |
| 5 | Manipulated vs Controlled Vars | exactly ONE factor per arm unless a factorial design is pre-registered |
| 6 | Split Protocol | iterate/qualify/confirm roles; stratum-interleaved round-robin (MUST); look-ledger entry |
| 7 | Calibration Rules | every parameter gets a consequence-bearing tolerance |
| 8 | Selection/Elimination Rules | pilot MDE; **no elimination below pilot MDE**; sub-MDE handling pre-registered |
| 9 | Feasibility Probes | stability/context-fit/capacity, before spending a split |
| 10 | Statistical Plan | clustering unit→ICC→DEFF→N_eff→MDE (α=.05/power=.80, reported regardless); verdict readings pre-data; pass^k plan if stochastic |
| 11 | Generation/Runtime Config | frozen for the run; a mid-run change = new execution system |
| 12 | Qualification Gates | thresholds from historical (iterate) data only, each names its consequence |
| 13 | Confirmation Protocol | one look ever; certainty-curtailment default-on (3 guards); human-approval gate at Tier 3 |
| 14 | Run States/Integrity | fail-closed; content-hash bound; ground-truth isolation; diagnostics non-promotable |
| 15 | Telemetry Requirements | dual-clock stamps, lifecycle events, per-invocation stats (telemetry floor — not retrofittable) |
| 16 | Analysis Plan | exact tables decided now, not post-hoc; replays counted as looks |
| 17 | Roles | scientific owner (only amender) vs executor (no mid-run improvisation) |
| 18 | Amendment Log | append-only; pre-registered, iterate-split-only, pre-execution, benefit disclosed, skeptical note if pro-pass |

**Consequence-bearing tolerance rule (throughout):** a tolerance with no named
consequence is an unpriced escape hatch and fails review. Every calibrated parameter
and qualification gate names ABORT/RECALIBRATE/PROCEED-WITH-DECLARED-CEILING, PROCEED
cost stated in writing *before* the run.

**MDE/N_eff/INCONCLUSIVE:** clustering unit → ICC (measured, or declared cold-start
prior + pre-registered re-estimation completing before the qualify look) → DEFF =
1+(m−1)×ICC → N_eff = N/DEFF → MDE at α=.05/power=.80, **reported regardless of
outcome**. A margin below the MDE is **INCONCLUSIVE**, never "no difference"; no
candidate eliminated on a margin smaller than the pilot MDE.

**Canonical 8-item freeze gate (04 §7 = template checklist = 14 §6.1):** contract
content-hash-bound before execution · every tolerance names its consequence + PROCEED
cost pre-registered · full statistical plan written · prediction-ledger filled · look
ledger updated · execution-system identity + clock declared per arm · elimination
threshold = pilot MDE · curtailment clause + 3 guards stated or disabled in writing.

---

## 7. Stop conditions and anti-patterns most likely to bite a small team (03 §7/§9, 07 §7/§9)

**Stop conditions:** stratum ceiling below its threshold (fix instrument first) ·
cross-arm disagreement unreviewed · held-out exposure past refresh threshold ·
rubric change with no independently identified defect · completion-only/proxy metric
about to license a GO · diagnostic sample below sufficiency floor read as DROP ·
INCONCLUSIVE at rungs 7–9 read as license to descend.

**Anti-patterns likely on a small team's existing pipeline:**
- **Ceiling-blind scoring** — per-stratum accuracy from existing logs without first
  computing reachability; the most tempting shortcut under deadline.
- **Score-driven harness/rubric changes** with no independently proven defect;
  **cross-version score subtraction** (the 16%→33.2% curated-subset figure,
  EXT-EVAL-005, is itself explicitly *not decomposed* into defect vs. population
  change — don't borrow it as if it were); **silent instrument-version mixing**.
- **LLM judge on verifiable output, uncalibrated** — the fastest shortcut when
  dual-labeling capacity is scarce; compounded by **judge trust read off a point
  estimate** instead of the CI lower bound, and **a bias "audit" with no measured
  number, tolerance, or consequence**.
- **Smoke-tier results quoted as evidence**; **pipeline-bypass content generation**
  for corpus filler; **completion-as-success proxy**.
- **Training around a defect at rungs 0–4** — the #1 shortcut ch.07 exists to block.
- **Underpowered diagnostic read as GO**, and its mirror, **insufficient
  reconfirmation read as DROP evidence**.
- **Generation-budget cap copied from another project/model generation** instead of
  re-derived from the current artifact's own length distribution; **variant spam at
  rung 4** with no enumerated hypothesis space or adoption rule.
- **Reading the ladder's entry column as a descent bar** — a false entry condition is
  exactly when descending past the rung is legitimate, not the opposite.

---

## 8. Multiple distinct AI surfaces — explicit gap

**Chapters 03, 07, and 14 do not directly address multi-surface systems.** A
targeted search across all three for "multi-surface / per-surface / each surface /
distinct surface" returned no hits — there is no stated rule for per-surface evals
vs. one system-level eval.

Conservative extrapolation only, **not chapter doctrine**: (a) 03 §5.1's task-shape
map is inherently per-task-shape — a surface performing a different shape (extraction
vs. generation vs. diagnose-and-act) would need its own ontology under §5.1's logic,
though the chapter never states "one eval per surface" as a rule; (b) 02's
execution-system identity (invoked as a prerequisite by both 03 §2 and 07 §2) implies
each surface, as a distinct execution system, needs its own pinned identity — but
this is chapter 02's territory, not read for this brief; (c) 07's rung diagnosis is
scoped to "the execution system under test" throughout (the RC-1/RC-7 discriminator
turns on exactly this) — a multi-surface pipeline would need RC classification and
rung selection applied per-surface.

If a real scoping answer is needed, that is open ground in chapter 02 (execution
system model) or chapter 08 (routing/workflows, multi-component systems) — neither
read for this brief — or should be escalated rather than assumed.
