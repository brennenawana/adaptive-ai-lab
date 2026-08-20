# NEXT STEP — M0: Truncation Diagnostic + Telemetry Floor + $4 GPU Benchmark

> STATUS: CURRENT / NORMATIVE — the single authorized next step
> Current as of: 2026-08-20 (rev 2 — adversarial review applied: diagnostic redesigned
> as a TRAIN-only cap-raise probe; the one required state-machine extension made
> explicit; decision table given a single estimator)
> Supersedes: `../HANDOFF.md`'s and the R6 report §11's "R7 next" recommendation.
> R7 is not cancelled — it is **conditional on M0's outcome** (decision table, §7).
> Governed by: `AI_SYSTEMS_LAB_MASTER_PLAN.md` §10.

## 1. Objective

Answer, for about a day of elapsed time (most of it unattended decode), ≤36 bounded
TRAIN re-runs, and ~$4 of rented GPU time, the questions that decide whether R7
(reasoning-budget calibration) is worth 18–22 hours of wall clock — and land the
telemetry floor the R6 autopsy showed every long run needs.

## 2. Why this is the next step

Verified against the current repository state (2026-08-20):

- R6's headline unknown is whether the 8192-cap truncations **convert**: 47/49 Qwen3.8
  TEST failures are cap-hits, but the finished subset is easier (Nemotron passes 61% of
  Qwen3.8's finished TEST cases vs 38% of unfinished) — conversion is an upper bound,
  not a given. If most truncated trajectories do not complete at a modestly larger cap,
  R7's hypothesis is dead and running it would burn ~20 h to learn what M0 learns in
  hours. M0 therefore measures **conversion directly on TRAIN**: a bounded cap-raise
  probe on the known cap-hit cases (§6 WP-B), which also yields the reasoning-shape
  evidence (convergent vs degenerate) as a by-product.
- The stored record cannot answer this today. The R6 report's 16/47 TEST + 10/22 DEV
  "cut inside the JSON answer" split is derived from **stored per-invocation fields**
  (`content_chars`), not stored bodies — cap-hit cases produce no parseable result, so
  `learning.model_outputs` has no rows for them, and
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

1. **Conversion.** At the largest cap the card safely fits (target 12288 at
   `-c 16384`, per WP-C), what fraction of the known TRAIN cap-hit cases (a) complete
   and pass, (b) complete with a parseable but wrong answer, (c) remain truncated but
   convergent, (d) remain truncated and degenerate/circular?
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

## 5. Read/write boundaries

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
- **WP-B probe**: re-run the TRAIN cap-hit population — *selection rule: every TRAIN
  case with `stop_reason=length` on any R6 arm, re-run on the frozen Qwen3.8 Q3_K_M
  execution system* (expected n ≈ 19–36; Q3_K_M's own TRAIN cap-hits number 19) — at
  the WP-C-certified probe cap. TRAIN only. ~3–5 h unattended local decode.
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

**B. Cap-raise probe + classification** (~3–5 h decode + ~1 h analysis).
- *Pass 1 (offline, free, today):* field-based re-derivation over all 145 known R6
  cap-hit cases from stored `content_chars`/`reasoning_chars` (content started vs not;
  reasoning-only). This seeds the taxonomy and pins the population; it cannot inspect
  bodies (none are stored) and it does not by itself decide anything.
- *Pass 2 (the probe):* re-run the §5 TRAIN sample on the frozen execution system at
  the WP-C-certified probe cap (target 12288 @ `-c 16384`), `diagnostic` run kind,
  reasoning + content persisted (WP-A). Score against TRAIN ground truth (TRAIN
  scoring is unrestricted). Classify every case: **(a) completed & passed,
  (b) completed & failed, (c) still truncated, reasoning convergent,
  (d) still truncated, degenerate/circular** — (c)/(d) by pre-declared deterministic
  heuristics (repetition rate, distinct-hypothesis count, evidence accumulation) plus
  a manual read of every case (n is small). Caveats recorded in the report: outcomes
  are session-scoped (behavior class, not outcome reproduction, is the unit), and the
  TRAIN sample is selection-biased relative to TEST (the 61%/38% finished-subset
  effect) — probe results are an *estimate with stated direction of bias*, not a TEST
  prediction.

**C. Context/cap fit probe** (~1 h, before B). For candidate configurations
(`-c 12288/16384/20480` × caps 8192/10240/12288 as applicable): server fit (VRAM
headroom from logs + sampler), one TRAIN-prompt stability generation, recorded table.
Output: the certified probe cap for WP-B and the safe envelope for R7's design. No
quality measurement.

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

**F. Analysis + decision memo** (~1 h). Fill the §7 decision table; write
`docs/current/M0_REPORT.md` (format: §10). The master plan is updated only by the
scientific owner (§11).

## 7. Decision table (pre-registered)

**Primary estimator:** `f_complete` = fraction of the Pass-2 probe sample that
completes (classes (a)+(b)) at the probe cap. **Secondary:** among still-truncated
cases, the convergent:degenerate split ((c) vs (d)). One denominator — the Pass-2
sample; the TRAIN→TEST selection-bias caveat applies to every row and is restated in
the memo.

| M0 finding | Consequence (recommendation to the owner) |
|---|---|
| `f_complete` ≥ ~60% | **R7 GO** as designed (caps from WP-C's envelope; UD-Q3_K_XL re-enters under the elimination rule; (b)-share tempers the pass-conversion expectation) |
| `f_complete` ~30–60% | **R7 RE-SCOPED**: larger-cap/thinking-budget arms targeted at what the probe shows converts; honest wall cost restated before any freeze |
| `f_complete` < ~30%, or (d) dominates (c) among the still-truncated | **R7 DROPPED**; **R9 moves up**; Nemotron-tier specialization returns as the live alternative (R6 report §11 fallback) |
| WP-C: no cap > 8192 fits the 5080 safely | R7 infeasible locally as designed → rented-node R7 priced in the memo, or R7 dropped per the rows above |
| Benchmark: desktop 3090 ≥ ~1.2× laptop decode | Designated trigger-buy stays "used 3090"; ledger continues |
| Benchmark: 3090 < ~1.2× laptop (incl. parity or slower) | Designated buy reconsidered — 5090-class at Stage-3 conditions, or continued rental; trigger itself unchanged |
| Any result | **Hardware purchase remains deferred** (trigger unchanged); GPU-hours ledger now live |

Bands are judgment bands, not hypothesis tests — M0 is a diagnostic on a known
population, and its output is a *recommendation to the scientific owner*, not an
autonomous gate. Boundary values fall to the owner's reading.

## 8. Acceptance criteria

- Reasoning + truncated-content text persist for new runs (test proves round-trip);
  old rows untouched.
- The `diagnostic` run kind exists with its unit tests; `HEAD.json` and every
  candidate state byte-identical before/after M0's runs.
- Pass 1 covers 100% of the 145 known cap-hit cases (field-based); Pass 2 covers 100%
  of the §5-selected sample with per-case class + rationale recorded.
- Fit table covers every candidate configuration with fit/stability verdicts and
  names the certified probe cap.
- Telemetry: a smoke run shows dual clocks, lifecycle events, per-invocation stats;
  SIGINT leaves a run-end line.
- Benchmark JSON has 3 repetitions per GPU with pinned digests recorded; ledger exists.
- `make test` green (627+1 baseline plus new tests); no frozen file modified;
  `git status` clean at finish.

## 9. Required tests

Unit: reasoning/content round-trip; `diagnostic` run-kind legality matrix (TRAIN-only,
TEST_EVALUATED-permitted, DEV/TEST refused, no transition); truncation classifier on
synthetic fixtures (all four classes + edge cases); dual-clock fields; signal-safe end
line. Integration: one TRAIN-case smoke through the instrumented runner (live-gated,
skipped in CI as usual).

## 10. Required artifacts & report format

Artifacts: `artifacts/m0_caphit_classification.csv` (case, arm, split, pass-1 fields,
pass-2 class, rationale), `artifacts/m0_fit_probe.csv`, `artifacts/m0_gpu_benchmark.json`,
`docs/current/GPU_HOURS_LEDGER.md`, additive migration (if needed by WP-A).

`docs/current/M0_REPORT.md` sections: 1 Objective/what ran; 2 Probe results
(`f_complete`, class table, selection-effect caveat restated); 3 Fit envelope;
4 Telemetry floor delivered (before/after gaps table, incl. the §6-D deferred list);
5 Benchmark numbers vs laptop baseline; 6 Decision-table row selected +
recommendation; 7 Accounting (wall by authoritative clock, spend, GPU-hours);
8 Deliberately not done.

## 11. STOP condition

After the M0 report is written and committed: **STOP.** Do not start R7, M-STAT's
remaining code, R9, or any purchase. Return the report to the scientific owner
(Brennen) for interpretation; the decision-table row is a recommendation, and the
master plan's milestone table is updated only after the owner accepts it.
