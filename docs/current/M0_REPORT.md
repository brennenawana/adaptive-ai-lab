# M0 Report — Truncation Diagnostic + Telemetry Floor + GPU Benchmark

> STATUS: COMPLETED MILESTONE REPORT — a recommendation to the scientific owner
> (Brennen), not an autonomous gate. Executed 2026-08-20/21 against
> `NEXT_STEP_M0.md` rev 4 (decision rule frozen before inference; classification
> rubric frozen at commit `803b1a8`, before any treatment body existed).
> Per `NEXT_STEP_M0.md` § 11: after this report, M0 **stops**. Nothing below
> starts R7, M-STAT, R9, a fine-tuning rig, or a purchase.

## 1. Objective and what ran

M0 asked one question: **does additional reasoning budget produce useful task
rescue — deterministic-scorer passes on cases that reproducibly hit the 8192 cap —
or merely longer completed outputs?** It also had to land the telemetry floor, map
the context/cap fit envelope on the 16 GB card, and measure rented 3090/5090 decode.

What ran (all inference TRAIN-only, ledgered under the new `diagnostic` run kind;
DEV and TEST untouched; no TEST-look-ledger increment):

| piece | runs | inference |
|---|---|---|
| WP-C fit probe | `M0-qwen38-q3km-train-diag-fitprobe` | 3 full-cap stability generations (3 server sessions) |
| WP-B paired probe | `…-diag-ctrl8192`, `…-diag-treat12288`, `…-diag-sessionprobe` | 31 generations, ONE server session |
| §9 live smoke | (test, not a run) | 1 × 512-token TRAIN smoke |
| WP-E rented benchmark | — | **none — see § 5** |

Execution system: the frozen R6 candidate `qwen38-27b-q3km@8528f049af75`
(artifact `qwen3.8-27b-q3_k_m@7f3b845b5638`, re-hashed to
`7f3b845b…facfd7` before each work package; runtime
`llama.cpp-upstream-9b05354@0e90f9139596`, bound live via `/proc` exe+lib hashing;
server args digest `7c6f27cb…` — byte-identical to the frozen execution system).

## 2. Paired-probe results (WP-B — the causal core)

### The causal chain, explicitly

```
historical cap-hit population        15 pre-registered TRAIN cases (§5 of NEXT_STEP_M0.md),
                                     re-verified against learning.* and the registry freeze
                                     record (calibration.cap.per_cap."8192".capped = 15)
        ↓
contemporaneous reconfirmation       each case re-run at cap 8192, same frozen system,
                                     same fresh server session as its treatment
        ↓
paired cap intervention              identical request, max_tokens 8192 → 12288 (WP-C-
                                     certified), deterministic AB/BA order; ONLY the
                                     request-level cap differs (proven, § 2.4)
        ↓
deterministic outcome                scorer pass (rescue) / wrong completion / persistent
                                     truncation, classified by the pre-frozen rubric
        ↓
frozen decision rule                 precedence gate first, then the rescue bands
        ↓
recommendation                       to the owner (§ 6)
```

### 2.1 The frozen metric table (raw integers first)

| metric | value |
|---|---|
| `n_hist_cap` | **15** |
| `n_control_reconfirmed` | **15** (every control reproduced `stop_reason=length` at 8192, all at exactly 8192 output tokens) |
| `f_reconfirm` | 15/15 = **100%** |
| `n_rescue` | **9** |
| **`f_rescue`** | **9/15 = 60%** |
| `n_wrong_complete` | **1** → `f_wrong_complete` = 1/15 = 6.7% |
| `n_still_truncated` | **5** — convergent **5**, degenerate **0** |
| completed-unparseable edge (e) | 0 |
| `f_complete` | (9+1)/15 = 66.7% |
| pass-given-completion | 9/10 = **90%** |

Every number above regenerates mechanically from the committed artifact:
`python scripts/m0_metrics.py` (reads `artifacts/m0_paired_probe.csv`, writes
`artifacts/m0_metrics.json`).

### 2.2 Per-case outcomes

| case | order | control @8192 | treatment @12288 | out-tokens | class | note |
|---|---|---|---|---|---|---|
| S02-1001001 | AB | length | **pass** | 10990 | a | |
| S02-1002001 | BA | length | **pass** | 11368 | a | |
| S05-1002004 | AB | length | **pass** | 8846 | a | |
| S06-1001005 | BA | length | **pass** | 8946 | a | |
| S07-1000006 | AB | length | length | 12201 | c | hit the SLOT ceiling (prompt ≈4.2k ⇒ 16384−prompt = 12201), not the requested cap |
| S07-1001006 | BA | length | length | 12288 | c | |
| S07-1002006 | AB | length | length | 12288 | c | |
| S08-1002007 | BA | length | **pass** | 9247 | a | |
| S10-1000009 | AB | length | **pass** | 10652 | a | |
| S10-1001009 | BA | length | **pass** | 11573 | a | |
| S11-1000010 | AB | length | complete, fail | 11386 | b | root cause CORRECT, action ok, verifier ok; failed on evidence recall 0.5 < 0.8 |
| S11-1001010 | BA | length | length | 12288 | c | |
| S11-1002010 | AB | length | **pass** | 11181 | a | |
| S12-1000011 | BA | length | **pass** | 9052 | a | |
| S12-1001011 | AB | length | length | 12288 | c | |

Facts that sharpen the reading:

- **Every rescue needed more than 8192 tokens** (min 8846, max 11573; median
  ≈10990). The budget was the binding constraint, not an incidental correlate.
- **Rescues are order-balanced**: 4 under AB (control first) and 5 under BA
  (treatment first) — no order/prompt-cache signature on the outcome. (TTFT does
  show the expected cache effect — the second arm of a pair processes its identical
  prompt from cache, ~140 ms vs ~2.8–3.4 s — which is precisely what the
  pre-registered counterbalancing distributes across arms.)
- **Prompt identity held in all 15 pairs**: control and treatment `input_tokens`
  are equal pair-wise (`input_tokens_all_equal: true`), so the fixed-evidence
  bundle was byte-stable across arms.
- **The class pattern is clean**: S02/S05/S06/S08/S10 convert fully (7/7),
  S11/S12 partially (2/5), **S07 not at all (0/3)** — the reversal-race class
  simply needs more than 12.2–12.3k tokens on this substrate.

### 2.3 Still-truncated shape: convergent 5, degenerate 0

The pre-frozen rubric (commit `803b1a8`, `scripts/m0_classify.py` — repetition
rate, tail trigram novelty, distinct-hypothesis count, tail evidence accumulation;
degenerate iff ≥2 indicators fire) fired **zero indicators on all five**: trigram
duplication 0.16–0.24, tail novelty 0.66–0.84, all 12 ontology hypotheses
considered, new evidence tokens still appearing in the tail.

The pre-declared manual read of every case **agrees with the rubric on all five**
(recorded separately; it never overrode a rubric verdict): the tails are
late-stage answer construction, not loops — four of five had already left
reasoning and begun emitting the JSON answer (content 344–3647 chars); the fifth
(S07-1001006) was drafting the facts array with tool citations inside its
reasoning. These are cases the *next* cap increment plausibly converts, not
degenerate spirals.

### 2.4 Only the cap differed (verified, not assumed)

Pre-flight assertions the probe refuses to run without (all held):
live server args digest == frozen execution system's (`7c6f27cb…`); control
generation config digest == the frozen `gc@5d1e73fdadd7`; treatment generation
config differs from control **in `max_tokens` alone** (field-wise comparison of
the derived config payloads); fresh server session (never seen by any ledger
line); session identity re-checked before every one of the 31 generations;
artifact re-hashed; binary set bound via `/proc`. The session held
(`pid=544692`) for all 31 generations, 21:19–00:27 UTC.

### 2.5 Reconfirmation-instability table

**Empty.** All 15 controls reconfirmed (each stopped `length` at exactly 8192
output tokens). The historical premise was fully stable in this session; the
precedence gate (`n_control_reconfirmed ≥ 10`) is passed at its maximum.

### 2.6 Selection-effect caveat (restated, as required)

The 15-case population is TRAIN and selection-biased relative to TEST: R6 measured
that Qwen3.8's *finished* subset is easier (Nemotron passes 61% of its finished
TEST cases vs 38% of its unfinished). TRAIN rescue at 60% is therefore an
**estimate with a stated optimistic direction of bias, not a TEST prediction**;
in whole-task terms the §7 sanity check maps ~60% rescue to roughly +28 TEST cases
*if it transported*, which the caveat says it will not do fully. R7's own
calibration and its one TEST look are where conversion gets measured for real.
M0 is a bounded diagnostic decision instrument, **not a significance test** — no
hypothesis test was run and none is implied.

### 2.7 Pass 1 (secondary, descriptive — zero weight in the decision)

The offline field scan covers all **145** known R6 cap-hit (run, case) pairs
(`artifacts/m0_caphit_fieldscan.csv`): 30 were cut inside the answer, 115 still
inside reasoning; 19 rows belong to the primary-population runs (15 pilot + 4
stab), matching the pre-registered counts exactly.

## 3. Fit envelope (WP-C)

All probes on the frozen artifact/runtime, q8_0 KV, flash-attn, `-ngl 99`,
single slot; one full-cap `ignore_eos` stability generation per context (worst
case per ctx — KV is allocated for the whole context at startup); VRAM ceiling
criterion 16000 MiB of 16303, decode floor 15 tok/s. Table:
`artifacts/m0_fit_probe.csv`; certification: `artifacts/m0_fit_certification.json`.

| ctx | cap exercised | fit | VRAM peak (MiB) | decode tok/s | wall |
|---|---|---|---|---|---|
| 12288 | 8192 | OK | 15686 | 25.7 | 323 s |
| **16384** | **12288** | **OK — certified for WP-B** | 15715 | 20.8 | 596 s |
| 20480 | 12288 | OK | 15727 | 25.1 | 494 s |

Safe envelope for R7's design (owner's call, not a commitment): caps up to 12288
fit at the frozen ctx 16384 — **but** the longest primary-case prompt (~4.2k
tokens) leaves only 12201 generation slots there (S07-1000006 measurably hit that
ceiling), so **caps > ~12.2k on long-prompt cases need ctx 20480**, which loads
and decodes cleanly with ~575 MiB headroom. ctx 20480 showed no decode collapse
(25.1 tok/s). The 16384@12288 rate (20.8) vs 20480@12288 (25.1) difference is
noted as within-session variance, not characterized further here.

## 4. Telemetry floor delivered (WP-D)

| autopsy §13 gap | before | after M0 | evidence |
|---|---|---|---|
| dual clocks on spans | wall-only, 8–12% skew invisible | every lifecycle event carries `ts_realtime`+`ts_monotonic` | `fis_platform/telemetry/clocks.py`; events files |
| signal-safe run end | interrupted runs left no end line | `run_end` guaranteed via atexit+SIGINT/SIGTERM, once | `lifecycle.py`; SIGINT test green |
| per-invocation TTFT / decode | `ttft_ms` None on every R6 row | llama.cpp `timings` persisted verbatim per invocation; `ttft_ms` = prompt_ms | 31/31 probe rows carry TTFT |
| reasoning text | lengths only | `reasoning_text` persisted; `content_text` for parse-failing responses | WP-A; round-trip test |
| server logs | truncated per relaunch (8 of 11 lost in R6) | per-session log files + stable symlink; copied beside the run | `serve-r6.sh`; `evals/reports/m0_paired_probe.server.log` |
| GPU/RAM sampler | spot samples only | 1–5 s sampler on long runs | `sampler.py`; `m0_paired_probe_samples.jsonl` |

**Deliberately deferred to M-STAT** (pre-registered in NEXT_STEP_M0.md § 6-D):
TOOLS spans, HARNESS events, periodic CLOCK-offset sampling, the DB `inserted_at`
fix.

## 5. Rented benchmark (WP-E) — INCOMPLETE: infrastructure unavailable

**No GPU-rental account or credentials exist in the lab environment** (no
provider API key in `.env`, no runpodctl/module). Renting requires an account and
payment method only the owner can create. Per the fail-closed rule, this is
recorded as an **incomplete work package**; no uncontrolled substitute comparison
was made.

Delivered instead, ready to run for ≈$4 once credentials exist:
`scripts/m0_gpu_benchmark_remote.sh` (self-contained: pinned llama.cpp commit
rebuilt per arch with digests recorded, artifact sha256-verified before any
measurement, llama-bench at the R6-representative operating point, 3 reps, JSON
out; **no FIS corpus content ever reaches the rented host**) and
`scripts/m0_gpu_benchmark.py assemble` (merges the per-GPU outputs into
`artifacts/m0_gpu_benchmark.json` beside the laptop baseline).

Hardware consequences: the decision-table hardware rows are **unanswered**; the
purchase **remains deferred** (trigger unchanged — this M0 outcome could not have
triggered a purchase in any case); the GPU-hours ledger is **live**
(`docs/current/GPU_HOURS_LEDGER.md`, opened with M0's rows: 3.38 owned-GPU hours,
$0; rented 0 h, $0). Local decode context for the eventual comparison: 20.8–27.2
tok/s at the R6-representative operating point this session. Benchmark numbers
remain **trigger inputs only**, never purchase decisions.

## 6. Decision-table row selected + recommendation

Applying the frozen rev-4 rule in order (mechanically:
`artifacts/m0_metrics.json`):

1. **Precedence gate**: `n_control_reconfirmed = 15 ≥ 10` → passed; the bands apply.
2. **Bands**: `f_rescue = 9/15 = 60% ≥ ~30%` → **STRONG R7 GO**.

Row selected: **“STRONG R7 GO — material deterministic rescue, not just
completion.”** Completion played no role in the verdict: the one
completed-but-failed case sits in `f_wrong_complete`, and `pass_given_completion`
= 90% says raised-cap completions were overwhelmingly *correct* completions.

**Recommendation to the owner** (the decision is yours; M0 only recommends):

- **R7 as designed**, with WP-C's envelope as the feasibility input: caps beyond
  ~12.2k on long-prompt cases require ctx 20480 (which fits with headroom);
  the 5 convergent still-truncated cases — 3 of them S07, 4 of 5 already inside
  the answer — say the conversion curve has not flattened at 12288, so R7's cap
  ladder should include at least one rung above it.
- `f_wrong_complete = 6.7%` (and its failure being evidence-recall, not
  diagnosis) tempers but does not threaten the conversion expectation.
- UD-Q3_K_XL re-enters selection in R7's contract under the elimination rule, per
  the standing correction.
- Honest cost note: at ~25 tok/s and the observed lengths, R7's 18–22 h estimate
  remains plausible for a 12288-cap arm; a 16k-cap/ctx-20480 arm decodes ~33%
  longer per truncated case.

Per the master plan § 10 and NEXT_STEP_M0.md § 11: **this report's row is a
recommendation; the master plan's milestone table moves only on the owner's
acceptance. R7 also requires M-STAT and the Suite-v4 trigger review (its TEST
look is #8) before any contract freeze.**

## 7. Accounting

| item | value | clock |
|---|---|---|
| WP-C wall | 1442.5 s (0.40 h), 3 sessions | monotonic |
| WP-B wall | 10688.3 s (2.97 h), one session (21:19–00:27 UTC) | monotonic (realtime span agrees to <1%) |
| generations | 31 paired-probe (291,474 output tokens: 122,880 control + 164,594 treatment + 4,000 session-probe) + 3 fit-probe + 1 smoke (512 cap) | |
| GPU-hours (owned) | **3.38** → ledger | |
| rented spend | **$0** (WP-E not executed) | |
| frontier calls | 0 | |
| DEV/TEST cases executed | **0** (splits untouched; no TEST-look increment) | |
| registry | state logs + HEAD.json byte-identical before/after (verified twice: by the probe and independently against the pre-M0 sha256 snapshot); 8 diagnostic ledger lines appended | |
| tests | 672 passed + 2 skipped (baseline 627+1, +45 new M0 tests, +1 live smoke — run live: passed) | |

## 8. Deliberately not done

1. **No R7 work**: the probe cap is a diagnostic instrument; no cap was *selected*,
   no contract drafted, no thinking-budget arm explored.
2. **No M-STAT beyond M0's own scope** — the §6-D deferred list stands.
3. **No registry state transitions** — UD-Q3_K_XL remains WITHDRAWN until R7's
   contract; the diagnostic run kind cannot transition anything by construction.
4. **No suite/scenario/scorer/verifier change**; no model shopping; no routing
   change; no fine-tuning artifacts.
5. **No hardware purchase or rental**; WP-E recorded incomplete rather than
   approximated.
6. **The rubric was not tuned after outcomes** — thresholds are the freeze-commit
   values; the manual read was recorded beside, never instead of, the rubric.
7. **The 12288→12201 slot-ceiling nuance on S07-1000006 was disclosed, not
   patched** — re-running it at a larger ctx would have been a post-outcome design
   change.

---

*Artifacts:* `m0_paired_probe.csv` (+ per-generation events/samples JSONL),
`m0_metrics.json`, `m0_caphit_fieldscan.csv`, `m0_fit_probe.csv`,
`m0_fit_certification.json`, `docs/current/GPU_HOURS_LEDGER.md`; rubric:
`scripts/m0_classify.py` (frozen at `803b1a8`); reasoning/content texts:
`learning.trajectories` by the trace ids in the CSV.
