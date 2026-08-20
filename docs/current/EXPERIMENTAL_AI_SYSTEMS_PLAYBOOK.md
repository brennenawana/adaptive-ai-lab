# FIS Experimental AI Systems Playbook — v1.0

> STATUS: CURRENT / NORMATIVE
> Current as of: 2026-08-20
> Supersedes: nothing by that name — no playbook file existed before this one. The
> de-facto methodology lived in `../HANDOFF.md` ("rules that carry"), the R5/R6
> experiment contracts, and `../routing-experiments.md`'s standing rules. §10 records
> the delta against that practice. New experiments follow this playbook via
> `EXPERIMENT_CONTRACT_TEMPLATE.md`.
> Governed by: `AI_SYSTEMS_LAB_MASTER_PLAN.md` (sequencing and strategy live there).

This document is the operating methodology: the rules every FIS experiment follows.
It encodes the corrections adopted after the 2026-08 external research
(`../research/`), each verified or re-derived against FIS's own data.

---

## 1. Splits and what they are for

| Split | Size | Role | Discipline |
|---|---|---|---|
| TRAIN | 144 | iterate freely: screening, calibration, pilots, diagnostics | consequence-bearing tolerances apply; re-runs allowed and ledgered |
| DEV | 48 | one look per candidate, qualification against pre-frozen gates | spent at first executed case |
| TEST | 96 | one look, confirmation only | spent at first executed case; every look recorded in the TEST-look ledger |

- **A split is spent at the first executed case**, not the last. Partial runs reveal
  the sufficient statistic; there is no "peek and re-run".
- **TEST-look ledger**: every TEST evaluation (any arm, any experiment, including
  offline replays) appends a row to `TEST_LOOK_LEDGER.md` — the authoritative count.
  Seven historical looks are backfilled there (V3 baselines ×3 with R4 replays counted
  within, R5 replays ×2, R6 ×2). **Look #8 requires the Suite-v4 trigger review first.**
- **Suite refresh trigger**: when the ledger review concludes accumulated TEST exposure
  threatens validity, Suite v4 is released as a versioned suite (cross-suite comparison
  refused by tooling, as v2→v3). **v4 design rule: add scenario classes before adding
  replications** — at measured ICC 0.4–0.6, power grows with the number of classes,
  not cases per class.

## 2. Static integrity gates (full-corpus, protected)

`make reachability` (per-class evidence-recall ceilings), gold-answer scoring, and
corpus determinism run **on the full corpus, always**. Subsetting any static gate is a
regression, not an optimization: the gates are the instruments that caught 13 harness
defects. A class scoring near zero is a ceiling problem until proven otherwise
(weak-beats-strong inversion = the scenario rewards guessing).

## 3. SMOKE (the cheap tier, fail-closed)

A **SMOKE registry state** precedes REGISTERED→…: fixed 36 stratified cases (12 classes
× 3, round-robin order), single arm, results written to the same append-only ledger,
**cryptographically marked non-promotable**. Purpose: minutes-scale detection of
schema/tool-contract/runner breakage with no hole in the fail-closed machinery.

- SMOKE results never justify adoption **or elimination** decisions (its MDE is
  ~25–31pp).
- There is no "relaxed lane": an execution path that skips the registry is the exact
  defect class the R6 guards were built to forbid.

## 4. TRAIN screening and calibration

- **Ordering**: deterministic **round-robin across classes** (S01-1, S02-1, …, S12-1,
  S01-2, …) for every run whose prefix might inform a decision. Class-blocked order
  makes every prefix unrepresentative (measured: 5.4× worse prefix estimates).
- **Screening >2 candidates**: ASHA-style rungs (e.g. 12→24→48, η=2) are permitted on
  TRAIN only, **class-balanced at every rung** (a 12-case rung in blocked order is 12
  cases of one class and inverts real rankings). Screening ranks; it never makes
  inference claims. It feeds the frozen comparison; it never replaces it.
- **Elimination rule**: no candidate is WITHDRAWN on a pilot margin below the pilot's
  own MDE (~9–11 cases of 36). Below that: both candidates proceed under a
  pre-registered budget, the decision defers to DEV, or the selection metric changes to
  one the pilot can resolve. (Precedent corrected: UD-Q3_K_XL was withdrawn at
  McNemar p≈0.22–0.48 on a cap-confounded metric; it re-enters selection in R7's
  contract, if M0 opens R7.)

## 5. Consequence-bearing tolerances (the R6 fix)

Every pre-registered tolerance **names its breach consequence** in the contract:

| Consequence | Meaning |
|---|---|
| **ABORT** | the run halts; the experiment returns to design |
| **RECALIBRATE** | the calibrated parameter is re-derived per a pre-registered procedure; the freeze happens only after the tolerance is met |
| **PROCEED-WITH-DECLARED-CEILING** | the run continues, with the projected cost and the measurement ceiling *stated in writing before proceeding* |

- Evaluation is by **curtailed exact counting**: with tolerance ≤k violations of n, the
  runner halts the phase at violation k+1 and escalates to the named consequence. No
  hypothesis test, no error-rate claim (SPRT rejected: α inflates ~2.2× under the
  measured class clustering, and count-to-k dominates it on the real pilot sequences).
- Enforcement is **in-run, fail-closed, in the runner** — in the same style as the
  existing `--candidate` refusal. A tolerance without a consequence clause fails
  contract review.
- Rationale (recorded): R6's pilot *measured* a 5× cap-tolerance breach and the
  contract's escape hatch said proceed, unpriced — 9h55m of zero-scoring generation
  followed. Detection was never the gap; the consequence was.

## 6. DEV/TEST discipline

- One look each, pre-frozen numeric gates (as R6 §11-style tables), select on DEV,
  confirm on TEST.
- **Certainty curtailment** (the standing rule; a contract may disable it only with a
  written justification): abort an arm when
  `passes + cases_remaining < ⌈bar·N⌉`. Exact arithmetic, assumption-free. Three
  mandatory guards:
  1. **Spend semantics** — the split is already spent; curtailment's only admissible
     consequence is irreversible rejection of that arm.
  2. **Interval-only reporting** — a curtailed arm reports the certain interval
     `[k, k+remaining]/N` plus unrun classes; never a partial point estimate.
  3. **Paired-comparison firewall** — curtailed arms never enter paired comparisons
     (measured on real data: curtailing flips a McNemar p from 0.0596 to 0.0139 purely
     compositionally).
- Stopping rules are adopted **for decision quality**; their measured speed value is
  ~2–4% of wall. Any contract claiming a speed rationale for a stopping rule is wrong.
- The 9.14h-class cap-burn is a *throughput/science* problem (it sits inside viable
  arms); it is addressed by budget calibration (R7) and bandwidth, not by stopping rules.

## 7. Statistics and reporting

- **Primary inference**: cluster-robust over the 12 scenario classes (paired-difference
  t on per-class means, df = classes−1). **Secondary**: McNemar exact on discordant
  pairs, always labeled anti-conservative under clustering.
- **Every contract states, before the freeze**: the expected discordance range, the
  cluster-corrected MDE, and the effective N. Standing facts for Suite v3: TEST
  paired-difference ICC 0.475 → DEFF 4.33 → **N_eff ≈ 22**; unclustered MDEs
  TEST(96) ≈ 11–16pp, DEV(48) ≈ 22pp at pd=0.30; cluster-corrected, **nothing is
  detectable at discordance pd ≤ 0.30, and the realized pd = 0.427 gives ~37pp MDE**
  (equivalently: since a detectable Δ requires Δ ≤ pd while MDE ∝ √pd at N_eff = 22,
  no difference ≤ 30pp between local arms is detectable).
- **INCONCLUSIVE is a legitimate verdict.** A null below MDE is never read as
  equivalence. The licensed alternative is a **pre-registered descriptive vocabulary**:
  R6's "47 vs 48 = competitive" reading is the norm *because* "competitive" (within ±4)
  was defined in the contract before data — the license comes from pre-registration of
  a descriptive category, never from the null itself.
- **Paired designs are free — claim them.** Same-seed cross-arm comparisons use
  paired-difference SEs, not two-sample.
- **pass^k for stochastic systems**: any reliability claim about a non-deterministic
  arm (the frontier arm first) reports pass^k (k=3–5) on a declared subset, not pass^1
  alone. (R9 runs the first measurement.)
- **Prediction ledger**: each contract records a pre-run effect-size point estimate +
  interval; predicted-vs-actual is scored in the report. A handful of entries (~5)
  make the "is this experiment worth DEV?" gate empirical.
- **Verdict vocabulary**: CONFIRMED / REFUTED / INCONCLUSIVE / (for screening) RANKED.
  Reports print both the primary and secondary statistics with the clustering caveat.

## 8. Determinism, reproducibility, telemetry

- **Deterministic graders wherever the task is objectively checkable** (vindicated by
  JudgeBench: LLM judges ≈ chance on verifiable tasks). Adding any LLM judge requires a
  κ-corrected, bias-audited, human-anchored calibration protocol — otherwise no judge.
- **Contemporaneous paired control for causal claims across sessions.** When a
  historical-vs-new-run comparison is confounded by measured runtime/session
  nondeterminism (the restart instability below), causal attribution to one
  intervention requires a contemporaneous paired control — both arms in the same
  server session, everything except the intervention held fixed, order
  pre-registered and counterbalanced (e.g. AB/BA) — or the causal claim must be
  explicitly declared unavailable and the comparison labeled descriptive.
- **Same-session single-slot rule** for case-level local comparisons (measured: 23/48
  outcomes flip across a restart). Restart the `--no-mmap` endpoint before its arm;
  probe only with TRAIN cases; never probe mid-run; `FIS_LIVE_TESTS` off during paired
  runs.
- **Dual clocks**: every span carries realtime + monotonic stamps; the contract states
  which clock is authoritative per metric (WSL2 skew is measured at 8–12%). Wall-clock
  claims use realtime.
- **Run lifecycle**: signal-safe run start/end events, per-invocation prompt/decode/
  TTFT persisted, server logs preserved, GPU/RAM sampler on long runs. (M0 lands the
  floor; the autopsy §13 schema is the reference.)
- **Provenance**: hash-chained registry, execution-system digests, contract frozen by
  git blob SHA where the state machine enforces it. The registry is the record of
  record; dashboards (MLflow/W&B) may mirror it, never replace it.
- **Leakage**: disjoint seed ranges per split; corpus stays private; **canary GUIDs**
  go into TEST scenario files and any published excerpts (M-STAT adds them).
- **Cross-node arms are licensed** when pre-registered: session-scoped reproducibility
  means a rented Secure instance holding one session per arm satisfies the same-session
  rule exactly as well as an owned card. Quantize for the deployment target, not the
  dev box.

## 9. Economics

- Routing claims carry the break-even check: minimum offload = judge_cost/(strong−weak).
- The **GPU-hours/month ledger** is the demand instrument; the hardware purchase
  trigger and rent-vs-buy break-even (H* ≈ 17–20 h/week sustained for 3 years at
  current prices) live in the master plan §8.
- Local-vs-cloud-vs-API decisions re-run the break-even when the ledger says demand
  changed; all recorded prices are floors with weeks of shelf life — re-verify at
  order time.

## 10. Relation to prior practice (KEEP / CHANGE / ADD / REMOVE)

Delta against the de-facto methodology (HANDOFF "rules that carry" + R5/R6 contracts +
routing-experiments standing rules):

**KEEP** — select on DEV, one TEST look, one factor per arm; gold labels score but
never choose; frozen suites + versioned releases + cross-suite refusal; deterministic
graders; pre-registered adoption rules (they caught two cherry-picks); fail-closed
registry/state machine; same-session rule; full-corpus static gates; append-only logs;
the evaluate-first ladder; clean-room boundary.

**CHANGE** — tolerances become consequence-bearing (R6 §6's "record and proceed"
escape hatch is the corrected defect); case order becomes round-robin (was class-blocked
by `ORDER BY scenario_id`); primary statistics become cluster-robust (McNemar demoted
to secondary); pilot margins below MDE no longer eliminate candidates (UD-quant
precedent corrected); "exactly one next milestone" statements in reports remain
recommendations, not commitments — sequencing authority is the master plan.

**ADD** — SMOKE registry state; MDE + effective-N + INCONCLUSIVE in every contract;
TEST-look ledger + Suite-v4 trigger; certainty curtailment with guards; prediction
ledger; pass^k for stochastic arms; canary GUIDs; dual-clock + lifecycle telemetry;
GPU-hours ledger; break-even economics on routing claims; per-contract authoritative-
clock declaration; pre-registered cross-node arm placement.

**REMOVE** — nothing from the frozen record. Two *draft* proposals from the research
were rejected before adoption and are recorded so they are not re-proposed: SPRT-style
sequential testing (dominated, α-inflated under clustering) and a named parallel
"method-development tier" (recreates the unrecorded execution path; SMOKE-as-state
replaces it).

## 11. Enforcement status

This playbook is normative now; code enforcement lands as **M-STAT** (runner
consequence guards, SMOKE state, round-robin ordering, ledgers, canary GUIDs,
`TrainedArtifact`). Until M-STAT ships, any experiment that would rely on an
unenforced guard must implement it in its own contract tooling first. The next
contract freeze (R7's, if M0 opens it) requires template v2 + M-STAT guards in place.
