# NEXT STEP — M0: Truncation Diagnostic + Telemetry Floor + $4 GPU Benchmark

> STATUS: CURRENT / NORMATIVE — the single authorized next step
> Current as of: 2026-08-20 (rev 4 — decision precedence made explicit:
> `n_control_reconfirmed < 10` → INCONCLUSIVE/RE-SCOPE regardless of `f_rescue`,
> and poor reconfirmation can never support DROP; `f_rescue` undefined at
> denominator 0. rev 3 — pre-launch correction: the R7 decision now keys
> on **useful task rescue** (`f_rescue`), not completion; the primary population is
> pinned to the 15 verified Qwen3.8 TRAIN cap-hit cases; the causal comparison is a
> contemporaneous same-session paired control at 8192 vs the raised cap, with
> pre-registered counterbalanced order. rev 2 applied the adversarial review:
> TRAIN-only cap-raise probe, the one authorized state-machine extension, single
> estimator.)
> Supersedes: `../HANDOFF.md`'s and the R6 report §11's "R7 next" recommendation.
> R7 is not cancelled — it is **conditional on M0's outcome** (decision table, §7).
> Governed by: `AI_SYSTEMS_LAB_MASTER_PLAN.md` §10.

## 1. Objective

Answer, for about a day of elapsed time (most of it unattended decode), 30 bounded
TRAIN generations, and ~$4 of rented GPU time, the question that decides whether R7
(reasoning-budget calibration) is worth 18–22 hours of wall clock: **does additional
reasoning budget produce useful task rescue** — deterministic-scorer passes on cases
that reproducibly hit the 8192 cap — **or merely longer completed outputs?** And land
the telemetry floor the R6 autopsy showed every long run needs.

## 2. Why this is the next step

Verified against the current repository state (2026-08-20):

- R6's headline unknown is whether the 8192-cap truncations **convert to passes**:
  47/49 Qwen3.8 TEST failures are cap-hits, but the finished subset is easier
  (Nemotron passes 61% of Qwen3.8's finished TEST cases vs 38% of unfinished) —
  "when it finishes it is right" is an upper bound, not a given. A case can complete
  at a larger cap and still be wrong. M0 therefore measures **rescue directly on
  TRAIN**: a paired cap-raise probe on the verified cap-hit population (§6 WP-B),
  which also yields completion, wrong-completion, and reasoning-shape evidence.
- **A historical-vs-new comparison cannot carry the causal claim.** FIS has measured
  restart-to-restart outcome instability (23/48 case outcomes moved across a server
  restart), so "historical R6 @ 8192 vs new M0 @ raised cap" confounds the cap with
  the session. WP-B runs a **contemporaneous paired control** — same frozen execution
  system, same server session, control @ 8192 vs treatment @ the WP-C-certified cap,
  counterbalanced order — so only the generation cap differs (playbook §8).
- The stored record cannot answer this today. Cap-hit cases produce no parseable
  result, so `learning.model_outputs` has no rows for them, and
  `fis_platform/model_gateway/local.py:148` reads `reasoning_content` but keeps only
  its length. One small persistence change (WP-A) makes the probe diagnosable.
- The autopsy's telemetry actions (dual clocks — every published latency is 7–12% low;
  signal-safe run-end lines; per-invocation TTFT/decode persistence — `ttft_ms` is
  None on every R6 row) must land **before** the next long run, or R7 produces another
  forensic reconstruction instead of a query.
- The hardware decision's one unknown — is a desktop 3090 1.0× or 1.4× the laptop on
  the pinned artifact? — costs ~$4 to measure and gates nothing else, so it rides along.
- M0 requires **no contract freeze and no DEV/TEST spend**. It does require one
  narrow, test-covered state-machine extension (§5: the `diagnostic` run kind),
  because the frozen Qwen3.8 candidate sits in the terminal `TEST_EVALUATED` state and
  the fail-closed runner correctly refuses TRAIN inference there today
  (`provenance.py` `require_state`; `run_eval.py --candidate` preflight). M0 extends
  the machine; it does not bypass it.

## 3. Questions M0 must resolve

1. **Rescue.** Among the primary cases that *contemporaneously reconfirm* as cap-hits
   at 8192, what fraction **pass the deterministic scorer** at the WP-C-certified
   raised cap (`f_rescue`)? Secondarily: how much completes without passing
   (`f_wrong_complete`), how much stays truncated, and is the still-truncated
   reasoning convergent or degenerate?
2. **Fit envelope.** What context/output-cap combinations fit the frozen Qwen3.8
   execution system on the 16 GB card with measured headroom (R6 report §11: 15.1–15.2
   GiB of 16.3 at `-c 16384` q8_0 KV; 3.6k prompt + 12288 cap "barely fits")? Which R7
   cap options are actually safe?
3. **Telemetry floor.** Which of the autopsy §13 gaps are fixed and verified: dual-clock
   stamps, signal-safe run start/end, per-invocation prompt/decode/TTFT persistence,
   preserved server logs, GPU/RAM sampler?
4. **Rented decode reality.** Pinned-artifact decode (prompt + generation tok/s) on a
   rented 3090 and 5090 vs the laptop's measured baseline — the number the purchase
   trigger's designated buy keys off.

## 4. Non-goals (explicit)

- **No R7** (no cap *selection*, no contract freeze, no DEV/TEST case anywhere — the
  probe cap is a diagnostic instrument, not a calibrated choice; R7 performs its own
  TRAIN calibration under contract if it runs).
- **No fine-tuning**, no training code, no FT rig.
- **No new Suite version**, no scenario/scorer/verifier changes.
- **No model shopping** — no new artifacts enter the registry.
- **No routing redesign** — R4 policy and R5 conclusions untouched.
- **No hardware purchase** — the benchmark informs the trigger's designated buy only.
- **No registry state transitions** (UD-Q3_K_XL's un-withdrawal happens in R7's
  contract, not here). The `diagnostic` run kind (§5) adds ledgered run entries; it
  never transitions state.

## 5. Read/write boundaries and the primary population

**Primary population (verified 2026-08-20 against the primary record; pre-registered
here):** the **15 distinct TRAIN cases** where the frozen Qwen3.8 Q3_K_M execution
system itself produced `stop_reason=length` at the 8192 cap in R6 —
`learning.case_scores ⋈ learning.trajectories` over runs `R6-qwen38-q3km-train-pilot`
(15 of 36 cases) and `R6-qwen38-q3km-train-stab` (4 of 12; a subset of the same 15),
every row at `max_tokens: 8192`; independently confirmed by the registry freeze
record (`calibration.cap.per_cap."8192".capped = 15`, `n = 36`):

> S02-1001001, S02-1002001, S05-1002004, S06-1001005, S07-1000006, S07-1001006,
> S07-1002006, S08-1002007, S10-1000009, S10-1001009, S11-1000010, S11-1001010,
> S11-1002010, S12-1000011, S12-1001011

(8 scenario classes; all seeds in the TRAIN range.) Cases that cap-hit only on
*other* R6 arms (Qwen3.5-9B, Bonsai, UD) are **excluded from the primary denominator
and from the R7 decision**; they appear only in the Pass-1 secondary field scan.

**May change (code/docs):** `fis_platform/model_gateway/local.py` (+ `base.py`
response type), trajectory/invocation persistence for *new* runs, runner telemetry
(clocks, lifecycle events, TTFT capture), new scripts under `scripts/` (`m0_*`),
tests, migrations (new migration only, additive), `docs/current/*` **except
`AI_SYSTEMS_LAB_MASTER_PLAN.md`** (owner-gated, §11), benchmark/ledger artifacts —
**plus exactly one authorized state-machine extension:**

> `fis_platform/provenance.py`: add a `diagnostic` run kind — TRAIN-split-only,
> permitted at `TEST_EVALUATED` (in addition to the states TRAIN runs allow today),
> recorded through `begin_run`/`end_run` with a mandatory `purpose` tag
> (`M0-truncation-diag`), **no state transition, no effect on promotability**, unit
> tests proving: it refuses DEV/TEST splits, refuses non-terminal-state bypasses it
> doesn't need, and leaves `HEAD.json`/state unchanged. This is the only change to the
> fail-closed machinery M0 may make; it exists so the diagnostic is *ledgered inside*
> the machine rather than run beside it.

**Must not change:** anything else under `learning/registry/` (append-only writes via
`begin_run`/`end_run` — ledger rows + candidate-chain run entries — only; **no
transitions**); existing rows in `learning.*` tables (new runs insert, never mutate);
`scenarios/`, `evals/scorers/`, `fis_platform/verification/` (frozen suite identity);
the frozen contracts; `ground_truth` isolation.

**Inference budget (the only new inference authorized):**
- **WP-B paired probe**: the 15 primary cases × 2 arms (control @ 8192 + treatment @
  the WP-C-certified cap) = **30 generations**, one server session, TRAIN only,
  `diagnostic` run kind. ~3–4 h unattended local decode.
- Context-fit probes (WP-C): server loads + short TRAIN-prompt generations. Minutes each.
- Rented benchmark (WP-E): ~2 h on a 3090, ~2 h on a 5090, decode microbench on the
  pinned artifact + pinned llama.cpp build. ≈$4 (Community tier acceptable — synthetic
  or TRAIN-derived prompts only, never TEST content).

## 6. Work packages (order matters: A → C → B; D and E parallel)

**A. Persist reasoning + raw content** (~1 h). Surface `reasoning_content` (full text)
on `GenerationResponse`; persist **both** the reasoning text and the raw content text
for parse-failing responses on new runs, via the **trajectory-payload /
`ModelInvocation` route** (trajectories persist unconditionally;
`learning.model_outputs` only receives rows when the output parses — a column there
would miss exactly the cap-hit population, so that route is rejected). Unit test: a
fake llama.cpp `length`-stop response round-trips reasoning + truncated content to the
store.

**B. Paired cap-raise probe + classification** (~3–4 h decode + ~1 h analysis).
- *Pass 1 (offline, free, secondary):* field-based scan over all 145 known R6 cap-hit
  cases from stored `content_chars`/`reasoning_chars` (content started vs not). Context
  only; no influence on the R7 decision.
- *Pass 2 (the paired probe — primary):* for each of the 15 primary cases, run
  **CONTROL** (frozen Q3_K_M execution system, cap 8192) and **TREATMENT** (identical
  request, cap = WP-C-certified, target 12288) — both arms in **one server session**
  at the WP-C-certified server configuration (same `-c`, same flags, same slot;
  restart + TRAIN-case probe before the run per the same-session rule). **Only the
  request-level generation cap differs between arms.** If the certified `-c` differs
  from R6's frozen server context, that difference applies equally to both arms and is
  disclosed in the report (reconfirmation-vs-history is a descriptive bridge, not the
  causal comparison).
  *Pre-registered counterbalanced order:* cases sorted lexicographically by
  `scenario_id` (the §5 list order); even 0-based index → AB (control first), odd →
  BA — so order/prompt-cache-predecessor effects are not systematically confounded
  with cap.
  Score every generation with the deterministic scorer against TRAIN ground truth.
  Classify treatment outcomes: **(a) completed & passed (rescue), (b) completed &
  failed, (c) still truncated, reasoning convergent, (d) still truncated,
  degenerate/circular** — (c)/(d) by pre-declared deterministic heuristics
  (repetition rate, distinct-hypothesis count, evidence accumulation) plus a manual
  read of every case (n is small). Controls that do **not** reproduce
  `stop_reason=length` at 8192 are reported in a separate reconfirmation-instability
  table — never silently counted as rescues or failures — and their treatment results
  are descriptive only.

**Frozen metrics (all reported in `M0_REPORT.md`):**

| Metric | Definition |
|---|---|
| `n_hist_cap` | 15 (the §5 verified population) |
| `n_control_reconfirmed` | controls with `stop_reason=length` at 8192 in M0 |
| `f_reconfirm` | `n_control_reconfirmed / n_hist_cap` |
| `n_rescue` | treatment passes among reconfirmed cases |
| **`f_rescue`** | **`= n_rescue / n_control_reconfirmed` — the primary decision metric. Undefined when `n_control_reconfirmed = 0` (reported as UNDEFINED, never silently coerced to 0%)** |
| `n_wrong_complete`, `f_wrong_complete` | treatment completes (parseable, no length stop) but fails, among reconfirmed |
| `n_still_truncated` | treatment still `stop_reason=length`, among reconfirmed; with convergent (c) vs degenerate (d) counts |
| `f_complete` | completions ((a)+(b)) among reconfirmed — secondary |
| pass-given-completion | `n_rescue / (n_rescue + n_wrong_complete)` |

Caveat recorded in the report: the TRAIN sample is selection-biased relative to TEST
(the 61%/38% finished-subset effect) — probe results are an *estimate with stated
direction of bias*, not a TEST prediction.

**C. Context/cap fit probe** (~1 h, before B). For candidate configurations
(`-c 12288/16384/20480` × caps 8192/10240/12288 as applicable): server fit (VRAM
headroom from logs + sampler), one TRAIN-prompt stability generation, recorded table.
Output: the certified probe cap + server configuration for WP-B and the safe envelope
for R7's design. No quality measurement.

**D. Telemetry floor** (~2–3 h). Dual-clock (realtime + monotonic) stamps on
run/phase/case spans; signal-safe run start/end lines (atexit/signal handlers);
per-invocation prompt tokens, decode tokens, TTFT, decode rate persisted per case;
server logs preserved per run; lightweight GPU/RAM sampler for long runs.
*Scope note (pre-registered):* this is the floor, not the full autopsy §13 schema —
TOOLS spans, HARNESS events, periodic CLOCK-offset sampling, and the DB `inserted_at`
fix are deliberately deferred to M-STAT. Tests: clock fields present and sane in a
smoke run; run-end line written on SIGINT.

**E. Rented benchmark + ledger** (~2 h hands-on). RunPod (or equivalent) 3090 and
5090: pinned artifact `qwen3.8-27b-q3_k_m@7f3b845b5638`, same llama.cpp commit as the
frozen runtime (rebuild for the target arch; record binary digests), matching server
flags where hardware permits; measure prompt-processing and decode tok/s at the
R6-representative operating point (single slot, ~3.6k prompt, long generation), 3
repetitions. Record: `artifacts/m0_gpu_benchmark.json` + the opening row of
`docs/current/GPU_HOURS_LEDGER.md`.

**F. Analysis + decision memo** (~1 h). Compute the §6 metrics, fill the §7 decision
table; write `docs/current/M0_REPORT.md` (format: §10). The master plan is updated
only by the scientific owner (§11).

## 7. Decision table (pre-registered; frozen before inference)

**Primary decision metric: `f_rescue = n_rescue / n_control_reconfirmed`** —
treatment passes among contemporaneously reconfirmed 8192 cap-hits (undefined at
`n_control_reconfirmed = 0`). Completion (`f_complete`) is diagnostic context and
**can never by itself produce a GO**.

**Precedence gate (applied before the bands):**

```
if n_control_reconfirmed < 10:
    verdict = RE-SCOPE / INCONCLUSIVE, regardless of f_rescue.
    Poor reconfirmation means the historical premise / causal denominator is
    unstable — it is NOT evidence that extra budget fails to rescue, and it
    can never support DROP.
else:
    apply the frozen rescue bands below (GO / RE-SCOPE / DROP).
``` Band sanity check at the verified n: with
`n_hist_cap = 15`, one case ≈ 6.7pp, so ≥ ~30% ≈ ≥ 5 rescues and < ~10% ≈ ≤ 1; in
whole-task terms, 47 of Qwen3.8's 49 TEST failures are cap truncations, so ~30%
rescue — *if it transported, which the selection-bias caveat says is optimistic* —
implies roughly +14 TEST cases (~+15pp), material against R7's 18–22 h cost, while
~10% implies ~+5 cases, marginal. The default bands survive this check and are frozen
as-is.

| M0 finding | Consequence (recommendation to the owner) |
|---|---|
| **STRONG R7 GO** — `f_rescue ≥ ~30%` (≥ ~5 of 15 if all reconfirm), absent contradictory evidence | R7 as designed: material deterministic rescue, not just completion (caps from WP-C's envelope; UD-Q3_K_XL re-enters under the elimination rule; `f_wrong_complete` tempers the conversion expectation) |
| **R7 RE-SCOPE / INCONCLUSIVE** — `n_control_reconfirmed < 10` (the precedence gate: INCONCLUSIVE regardless of `f_rescue`); **or**, with the gate passed: `f_rescue` ~10–30%; **or** high `f_complete` with low `f_rescue` (budget buys completions, not correctness); **or** many still-truncated cases remain convergent (probe cap likely too small) | R7 re-scoped at what the probe shows converts (larger caps / thinking-budget arm / different target), honest wall cost restated before any freeze — or returned to the owner as INCONCLUSIVE |
| **R7 DROP / R9 MOVES UP** — requires `n_control_reconfirmed ≥ 10` **and** `f_rescue < ~10%`, with the diagnostic pattern (wrong-complete-dominant, degenerate reasoning among (c)/(d)) showing extra budget is not the main bottleneck. Poor reconfirmation is never evidence for DROP | **R7 dropped**; **R9 moves up**; Nemotron-tier specialization returns as the live alternative (R6 report §11 fallback) |
| WP-C: no cap > 8192 fits the 5080 safely | R7 infeasible locally as designed → rented-node R7 priced in the memo, or R7 dropped per the rows above |
| Benchmark: desktop 3090 ≥ ~1.2× laptop decode | Designated trigger-buy stays "used 3090"; ledger continues |
| Benchmark: 3090 < ~1.2× laptop (incl. parity or slower) | Designated buy reconsidered — 5090-class at Stage-3 conditions, or continued rental; trigger itself unchanged |
| Any result | **Hardware purchase remains deferred** (trigger unchanged); GPU-hours ledger now live |

Bands are diagnostic judgment bands, not hypothesis tests — M0's output is a
*recommendation to the scientific owner*, not an autonomous gate. Boundary values
fall to the owner's reading.

## 8. Acceptance criteria

- Reasoning + truncated-content text persist for new runs (test proves round-trip);
  old rows untouched.
- The `diagnostic` run kind exists with its unit tests; `HEAD.json` and every
  candidate state byte-identical before/after M0's runs.
- All 15 primary cases have both a control and a treatment generation in one server
  session, in the pre-registered AB/BA order; every §6 metric computed; every
  treatment outcome classified with per-case rationale; non-reconfirming controls in
  the separate instability table.
- Pass 1 covers 100% of the 145 known cap-hit cases (field-based, secondary).
- Fit table covers every candidate configuration with fit/stability verdicts and
  names the certified probe cap + server configuration.
- Telemetry: a smoke run shows dual clocks, lifecycle events, per-invocation stats;
  SIGINT leaves a run-end line.
- Benchmark JSON has 3 repetitions per GPU with pinned digests recorded; ledger exists.
- `make test` green (627+1 baseline plus new tests); no frozen file modified;
  `git status` clean at finish.

## 9. Required tests

Unit: reasoning/content round-trip; `diagnostic` run-kind legality matrix (TRAIN-only,
TEST_EVALUATED-permitted, DEV/TEST refused, no transition); paired-order generator
(deterministic AB/BA assignment over the §5 list); truncation classifier on synthetic
fixtures (all four classes + edge cases); dual-clock fields; signal-safe end line.
Integration: one TRAIN-case smoke through the instrumented runner (live-gated,
skipped in CI as usual).

## 10. Required artifacts & report format

Artifacts: `artifacts/m0_paired_probe.csv` (case, class prefix, order AB/BA, control
stop_reason, control pass, reconfirmed?, treatment stop_reason, treatment pass,
treatment class (a)–(d), rationale), `artifacts/m0_caphit_fieldscan.csv` (Pass-1
secondary), `artifacts/m0_fit_probe.csv`, `artifacts/m0_gpu_benchmark.json`,
`docs/current/GPU_HOURS_LEDGER.md`, additive migration (if needed by WP-A).

`docs/current/M0_REPORT.md` sections: 1 Objective/what ran; 2 Paired-probe results —
the full §6 metric table, the (a)–(d) class table, the reconfirmation-instability
table, selection-effect caveat restated; 3 Fit envelope; 4 Telemetry floor delivered
(before/after gaps table, incl. the §6-D deferred list); 5 Benchmark numbers vs
laptop baseline; 6 Decision-table row selected + recommendation; 7 Accounting (wall
by authoritative clock, spend, GPU-hours); 8 Deliberately not done.

## 11. STOP condition

After the M0 report is written and committed: **STOP.** Do not start R7, M-STAT's
remaining code, R9, or any purchase. Return the report to the scientific owner
(Brennen) for interpretation; the decision-table row is a recommendation, and the
master plan's milestone table is updated only after the owner accepts it.
