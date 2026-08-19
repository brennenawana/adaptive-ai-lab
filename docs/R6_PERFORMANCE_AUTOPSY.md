# R6 Performance Autopsy — where 24 hours went

**Scope:** forensic reconstruction of the R6 milestone's wall clock (2026-08-18 20:59:46 UTC `/goal` → 2026-08-19 21:02:56 UTC final commit `5f785a7`). No new inference was run; no canonical R6 data was mutated. **Sources:** the R6 run ledger and phase markers (`learning/registry/r6/{ledger,phases}.jsonl`), per-case rows in Postgres (`learning.case_scores` ⋈ `learning.trajectories`, including `created_at` insert timestamps), the three surviving llama.cpp session logs (`/tmp/fis-r6-*.log`), git commit times, subagent transcripts, and the session command log. **Analysis code:** `scripts/r6_performance_autopsy.py` → `artifacts/r6_performance_autopsy_{phase_timing,model_timing,slowest_cases}.csv` + `_summary.json`. Every figure below is labelled **MEASURED**, **ESTIMATED**, or **INFERENCE**.

**A clock caveat that affects every previously published latency (MEASURED).** On this WSL2 guest, `CLOCK_MONOTONIC`-based timers (Python `perf_counter`/`monotonic` → per-case `wall_ms`, the ledger's `wall_s`; llama.cpp `ggml_time_us` → `timings`/`api_ms` and every tok/s) ran **8–12 % slow versus realtime** while models were running (per-run ratios 1.082–1.118). Three independent realtime sources agree with each other end-to-end and disagree with the monotonic timers by the same factor: Postgres `created_at` deltas, ledger `started_at`/`finished_at`, and the llama.cpp *log-prefix* clock (e.g. the Qwen3.8 TEST session: log-prefix span 24,188 s ≈ ledger window 24,181 s ≈ `created_at` span 24,180.5 s, versus Σ monotonic `wall_ms` = 22,332 s; ratio 1.082). Per-run realtime/monotonic ratios: 1.082–1.118 (R6) and 1.091–1.102 for the four historical Suite-v3 runs — **the skew is chronic on this machine**, so every FIS latency ever published (R3→R6) understates realtime by ~8–11 %, uniformly (a small part of the per-case ratio — ≤0.5 pp on fast arms — is genuine 0.3–0.7 s/case harness time; the server-log cross-check isolates the pure clock skew at ~8 %); cross-arm comparisons are unaffected. Cause (**INFERENCE**): the well-known WSL2 monotonic-clock stall during host idle/power-management, with realtime kept correct by NTP stepping — consistent with the skew being largest overnight (1.11–1.12). Everything below uses **realtime** unless marked "monotonic".

---

## 1. Executive conclusion

```
R6 total wall time:                 24 h 03 m   (86,590 s, /goal → final commit)      MEASURED

Critical-path model inference:      22 h 20 m   (server-busy inside run windows)      MEASURED (3 sessions) / ESTIMATED (rest at the same 99.2–99.8 % busy share)
  └ of which cap-hit truncation:     9 h 55 m   (145 cases, 0 passes)                 MEASURED (±10 m)
Model/runtime management:           ~10–15 m    (≥10 model loads; 3 measured: 42+35+4 s; swaps inside gaps) ESTIMATED
Tool/scoring/DB/test execution:     ~10 m       (0.3–0.7 s/case idle, server-measured; 8 full-suite pytest runs ≈ 45 s) MEASURED/EST
Implementation/debugging:           ~50 m       (R6.1 36 m + UD-preflight fix 5 m + in-gap fixes)  MEASURED
Agent/subagent orchestration:       ~42 m critical-path (reviews B 16 m + C 10 m + implementer ~10 m + polling ~6 m); 80 m total subagent wall  MEASURED
Documentation/analysis:             ~15 m critical-path (drafted during runs; post-run window 14.9 m incl. review C)  MEASURED
Unattributed:                       < 5 m

Slowest model by cases/hour:        Qwen3.8-27B Q3_K_M — 12.6–15.2 cases/h across its four runs (vs Bonsai 37.8–44.9, Qwen3.5-9B 46–55)
Largest output-token generator:     Qwen3.8-27B Q3_K_M — 1.32 M of 3.00 M generated tokens (44 %)
Largest retry/restart source:       none — 0 HTTP/server errors, 0 retries, 0 unplanned restarts in 516 cases
Largest hardware bottleneck:        GPU memory *bandwidth* (decode measured at 353–496 GB/s effective ≈ 39–55 % of the 5080 Laptop's ~896 GB/s vendor spec); VRAM *capacity* only as a ceiling (no co-residency, no larger context)
Largest avoidable overhead:         nothing large was avoidable inside R6's frozen rules; the 9.9 h truncation burn is the biggest number, and it is the scientific finding (R7's target), not waste
```

**Why did R6 take ~24 h?** Because 93.4 % of it (22 h 28 m of run windows) was serial local-model decoding, 65 % of the milestone (15 h 39 m) was the Qwen3.8-27B family alone, and 41 % (9 h 55 m) was spent generating reasoning that hit the 8,192-token cap and scored zero — at a decode rate (27.8 tok/s realtime for the 27B) that is memory-bandwidth-bound on this GPU. The harness, tools, scoring, tests, and orchestration together account for well under 7 %.

## 2. R6 wall-clock reconstruction

| anchor | value | evidence |
|---|---|---|
| R6 start | 2026-08-18 20:59:46 UTC | `/goal` receipt (`goal_start.txt`, job log); phases.jsonl note |
| R6 finish | 2026-08-19 21:02:56 UTC | final commit `5f785a7` (git author date) |
| total elapsed | **86,590 s = 24 h 03 m 10 s** | MEASURED |
| Σ model-run windows (13 ledger segments, realtime) | **80,892 s = 22 h 28 m (93.4 %)** | ledger `started_at`→`finished_at`; interrupted Bonsai-probe segment bounded by its last DB insert |
| Σ all gaps between/around runs | **5,698 s = 95.0 m (6.6 %)** | ledger timestamps; itemized in § 3/§ 10 |

Pre-`/goal` (not counted): the R6.0 read-only reconciliation ran ≈ 18:42–19:07 UTC (≈ 25 m of work incl. an 18.5-m seven-agent workflow, MEASURED from transcript/scratch mtimes), followed by user review until `/goal`.

R6 executed as one continuous critical path: no idle stretch longer than the 20.6-m freeze gap existed anywhere in the 24 h (largest five gaps: 37.2 m R6.1 implementation, 20.6 m contract-freeze + review B, 14.9 m post-TEST reporting + review C, 5.3 m UD-preflight fix, 3.5 m quant-selection/serve swap).

## 3. Phase timing table

MEASURED (phases.jsonl + ledger + git). "Model run window" is realtime window sum of the runs inside the phase; the remainder of each phase is non-inference.

| phase | start (UTC) | finish | elapsed | primary activity | model-run window | non-run | evidence / confidence |
|---|---|---|---|---|---|---|---|
| R6.0 reconciliation | ~18:42 | 20:59:46 | ~2 h 18 m (pre-goal, excluded) | 6-inspector workflow + critic, SHA recomputation, report; then user review | 0 | all | scratch mtimes, workflow journal; HIGH for bounds |
| R6.1 provenance | 20:59:46 | 21:35:42 | 35.9 m | provenance module (Opus subagent 21:03–21:25), registry, gateway/serve/Makefile, Qwen3.5-9B download (21:03–21:05) + registrations, contract pre-registration, commits `b2f85d5`/`ac81825` | 0 | 35.9 m | phases.jsonl, git; HIGH |
| R6.2 TRAIN | 21:35:43 | 05:46:05 | 8 h 10 m | 8 TRAIN runs (4 pilots, 3 probes + 1 resume); quant selection; Bonsai compat probe; review A (22:56–23:10, concurrent); TRAIN_COMPATIBLE ×3 | 7 h 50 m | ~20 m | ledger; HIGH |
| R6.3 freeze | 05:46:05 | 06:05:11 | 19.1 m | § 10 freeze, CONTRACT_FROZEN ×3, review B (05:47–06:03) + follow-ups `f4ae5f5` | 0 | 19.1 m | phases, git, agent transcript; HIGH |
| R6.4 DEV | 06:05:11 | 11:32:38 | 5 h 27 m | 3 DEV runs + gate verdicts + Qwen3.8 TEST unlock (during Bonsai DEV) | 5 h 24 m | ~3.5 m | ledger; HIGH |
| R6.5 TEST | 11:32:38 | 20:48:42 | 9 h 16 m | 2 TEST runs + terminal records | 9 h 14 m | ~2 m | ledger; HIGH |
| R6.6 analysis | 20:48:42 | 21:02:17 | 13.6 m | TEST analysis JSON, accounting, report fill, review C (20:50–21:00) | 0 | 13.6 m | phases, git, agent transcript; HIGH |
| R6.7 report | 21:02:17 | 21:02:56 | 0.7 m | review-C fixes already applied; final commits | 0 | 0.7 m | git; HIGH |

Basing note: this table bases R6.1 at `/goal` (20:59:46), R6.3 at R6.2's end, and R6.7 at the final commit; `phase_timing.csv` uses the raw phase-marker timestamps (`phases.jsonl`), whose R6.1 marker was stamped at 21:26:20 after the registry code landed — both views are consistent with the same events. Doc reconciliation note: `OVERNIGHT_STATUS.md` M7.5 gives "11:24 → 20:35 UTC" for TEST — the ledger says 11:32:38 → 20:48:00; the ledger is authoritative (the prose values were projections; left unmodified per this autopsy's constraints).

## 4. Per-model timing and throughput

Full table: `artifacts/r6_performance_autopsy_model_timing.csv`. All four candidates ran the identical frozen server config: upstream llama.cpp `b1-9b05354` (Bonsai: Prism `b1-9fcaed7`), `-c 16384 -ngl 99 --flash-attn on --cache-type-k/v q8_0 --jinja --parallel 1`, cap 8,192, greedy seed 42, one server resident, fresh session + 8-token prime. One model turn per case; the fixed-evidence plan issues 9–12 tool calls (median 12, varying by scenario class) before the model call.

| | Qwen3.5-9B | **Qwen3.8-27B Q3_K_M** | Qwen3.8-27B UD-Q3_K_XL | Ternary Bonsai 27B | Qwen3-8B (hist.) | Nemotron (hist.) |
|---|---|---|---|---|---|---|
| artifact / runtime | `03b74727…` / upstream | `7f3b845b…` / upstream | `00cf92e6…` / upstream | `868c1171…` / Prism | replay only | replay only |
| splits run | TRAIN 48, DEV 48 | TRAIN 48, DEV 48, TEST 96 | TRAIN 36 | TRAIN 48, DEV 48, TEST 96 | 0 new | 0 new |
| cases attempted = completed | 96 | 192 | 36 | 192 | — | — |
| model invocations / turns / tool calls per case | 96 / 1 / 9–12 | 192 / 1 / 9–12 | 36 / 1 / 9–12 | 192 / 1 / 9–12 | — | — |
| retries / HTTP errors / restarts | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | — | — |
| cap hits (all → parse fail, 0 passes) | 23 | **88** | 18 | 16 | — | — |
| input tokens | 288,085 | **582,715** | 109,070 | 575,419 | — | — |
| output tokens | 546,744 | **1,318,066** | 251,699 | 878,764 | — | — |
| prompt-eval tok/s (surviving session) | 3,902 (DEV) | 1,089 (TEST) | not preserved | 1,211 (TEST) | — | — |
| decode tok/s — monotonic / **realtime** | 94.1 / **≈87** | 29.8 / **≈27.8** | 38.8 / **≈35.6** | 52.1–58.6 / **≈49.2** | 90.9 / ≈83 (hist.) | 87.3 / ≈79 (hist.) |
| total run-window time (realtime) | 1 h 55 m | **13 h 40 m** | 1 h 59 m | 4 h 55 m | 0 | 0 |
| case p50 — monotonic / **realtime** | 58–71 / **66–84 s** | 226–289 / **253–321 s** | 201 / **227 s** | 66–84 / **80–93 s** | — | — |
| case p95 (monotonic; +8 % for realtime) | 88–104 s | 270–312 s | 215 s | 141–151 s | — | — |
| cases/hour (realtime) | 46–55 | **12.6–15.2** | 18.2 | 37.8–44.9 | — | — |
| peak VRAM while serving (card total, MiB) | 8,044 | **15,682** (96 % of 16,303) | 14,773 | 10,183 (drifted +0.9 GiB in TEST) | — | — |
| peak host RAM | not recorded (spot `free -g`: no pressure) | ″ | ″ | ″ | — | — |
| offload | 0 layers (all-GPU) | 0 (66/66 on GPU, fit-probe verified) | 0 | 0 | — | — |
| model load time / serve cycles | 42.1 s cold (DEV) / 2 | 4.1 s warm (TEST); cold not preserved / 5 (incl. fit probe) | not preserved / 1 | 35.4 s (TEST) / 3 | — | — |

Per-model sums are in the CSV. MEASURED except: decode realtime (= monotonic ÷ per-run skew ratio, MEASURED skew), prompt tok/s only for the three surviving sessions (the serve script truncates the log on each start — 8 of 11 sessions lost), and load times for the same reason. Reasoning tokens are observable only as `reasoning_chars` (23k–36k chars on truncated Qwen3.8 cases).

**Historical replay-only arms ran zero new inference** — the 8082/8083 sessions were stopped at R6.2 start; every Qwen3-8B/Nemotron number in R6 came from frozen rows.

## 5. Twenty slowest cases

Full table: `artifacts/r6_performance_autopsy_slowest_cases.csv`. **All 20 are Qwen3.8-27B Q3_K_M cases from the TRAIN pilot** (285–368 s monotonic; ≈316–408 s realtime): rank 1 is `S01-1000000` (367.7 s), the cold-session warm-up anomaly (~4 min at ~1 tok/s before settling at ~27 tok/s — recorded in contract § 17); ranks 2–20 are 7,881–8,192-token generations, 15/20 cap hits with 23k–34k reasoning chars and (for 13 of them) zero content chars. Clustering (MEASURED):

- **By model:** exclusively Qwen3.8 Q3_K_M — its 8k-token generations at ~26–29 tok/s are 3.5–4× any other arm's case time. The slowest non-Qwen3.8 case in R6 was a Bonsai TEST case at 167.8 s monotonic (`S12-3001011`).
- **By generation length, not by tools or turns:** every R6 case had exactly 1 model turn and 9–12 pre-model tool calls; wall − api = 0.3–1.0 s. Latency is a pure function of output tokens (wall ≈ out_tokens ÷ decode-rate + ~3 s prompt).
- **By class:** S02, S06, S07, S10, S11, S12 — the classes whose reasoning does not converge within the cap (S07/S10/S11/S12 scored 0/8 on TEST for this model).
- **By session:** the pilot session decoded ~8 % slower than the TEST session (≈26.9 vs ≈29.3 tok/s monotonic on comparable 8k generations); cause not determinable from stored data (thermal/host power state suspected — the same overnight window shows the largest clock skew, 1.11). INFERENCE.
- **Not** by retries, restarts, server state, or tool loops: none occurred.

## 6. Inference vs non-inference decomposition

Because R6 ran one case at a time on one resident server, **summed inference ≈ critical-path inference** — there was no parallel work to double-count.

| component | time | basis |
|---|---|---|
| model-run windows (13 segments) | 22 h 28 m | MEASURED (ledger realtime) |
| └ server busy (requests in flight) | ≈ 22 h 20 m | MEASURED for 3 sessions (busy = 99.2–99.8 % of window); extrapolated to the rest — ESTIMATED |
| └ decode (token generation) | ≈ 21 h 50 m | MEASURED-derived: busy − prompt; prompt = 0.9–2.2 % of busy in all 3 surviving logs |
| └ prompt ingestion | ≈ 17–25 m (1.56 M billed input tokens, of which a share is prefix-cache-reused; measured evaluated-token rates 1.1–3.9 k tok/s) | MEASURED (3 sessions) + ESTIMATED (rest) |
| └ cap-hit truncation burn (inside decode) | **9 h 55 m ± 10 m** (145 cases, 9.14 h monotonic × skew; **0 passes**) | MEASURED |
| └ in-window harness (tools+scoring+persist+`nvidia-smi`, between requests) | ≈ 6 m total (0.3–0.7 s/case median server-idle) | MEASURED (3 sessions: 21.4/51.7/81.1 s) + ESTIMATED (rest) |
| model loading / switching / serve-stop cycles | ≈ 10–15 m across ≥10 loads (3 measured: 42.1 + 35.4 + 4.1 s) | ESTIMATED; sits inside the 95-m gap budget |
| scoring/verifier work | inside the 0.3–0.7 s/case idle (scorer is pure CPU over the parsed answer) | MEASURED bound |
| tests | 8 full-suite pytest runs ≈ 45 s + targeted runs ≲ 1 m | MEASURED (count from session transcript; 4.4–6.3 s each) |
| implementation/debugging (critical path) | ≈ 50 m: R6.1 (35.9 m) + UD-preflight fix (5.3 m gap) + swap-gap work | MEASURED gaps |
| subagents (critical path) | ≈ 36 m: review B 15.8 m + review C 9.8 m + implementer tail ≈ 10 m; review A (14.1 m) ran concurrently with the Q3_K_M pilot at zero critical-path cost | MEASURED transcript spans |
| report/documentation | mostly drafted during the Bonsai TEST run (zero critical path); post-run window 13.6 m | MEASURED |
| retries/failures | 0 model-call failures in 516 cases (the 145 trajectory `error` fields are all "model produced no parseable structured output" = the cap hits) | MEASURED |
| idle/wait (orchestrator poll latency after run ends) | ≈ 5–8 m total (gap starts 34–89 s after each run end, 13×) | MEASURED |

## 7. Serialization / GPU utilization

**How cases executed (MEASURED):** strictly one case at a time (`--parallel 1`, one slot), one model server resident at a time, arms strictly sequential. No continuous batching (available in the build, deliberately off), no parallel workers, no parallel arms.

**Was the RTX 5080 underutilized because the workload was serial? No — not within R6's rules.** Server-busy fraction of run windows: 99.5 % / 99.8 % / 99.2 % (three surviving sessions, server-clock MEASURED); GPU busy across the whole 24 h ≈ 22.3 h / 24.05 h ≈ **93 %**. Spot `nvidia-smi` during decode read 94–97 % GPU utilization (spot MEASURED, no timeseries). The card idled only during the 95 m of gaps.

**Sequential dependencies and their sources:**
- *model → tool → model loops:* **did not exist** — FIXED_EVIDENCE runs all of a case's 9–12 tool calls before its single model call; tool time lives in the 0.3–0.7 s inter-request idle.
- *case serialization:* reproducibility policy (`--parallel 1`; the serve script documents that concurrent slots change batching/numerics; R5 measured 23/48 case outcomes moving across a mere server restart — the basis for the fresh-session + single-slot rules).
- *arm serialization:* (a) VRAM — Q3_K_M used 15.7 GiB of 16.3; even the two smallest candidates together (7.9 + 9.2 GiB + contexts) exceed the card; (b) methodology — quant selection before DEV, pre-registered DEV order (Bonsai's efficiency gate consumes Qwen3.8's DEV reference), TEST after DEV_QUALIFIED. TESTs of the two qualified candidates were mutually order-independent, and TRAIN pilots of different candidates were independent.
- *TRAIN/DEV/TEST gates:* the state machine serialized phases per candidate, by design.

**Could cases have been parallelized safely?** Not without changing the execution system: continuous batching / multi-slot alters decoding numerics and would have had to be the frozen configuration from the start (with its own stability probe). Within R6, no. **Could arms have run in parallel?** Scientifically yes for *different candidates* (each is its own frozen execution system) — physically no on one 16 GiB card. A second GPU/machine would have allowed it (§ 9/§ 10). **Was continuous batching available but unused?** Yes — deliberately (determinism policy). **Would concurrency have changed determinism assumptions?** Within-arm concurrency: yes (measured basis above). Across-arm concurrency on separate hardware: no.

## 8. Memory / offload analysis

MEASURED per-case `nvidia-smi memory.used` samples (card total; idle baseline 1,734 MiB) + server load logs:

| model | weights on GPU | VRAM while serving (MiB) | KV/compute fit | CPU offload | host RAM in decode | loads |
|---|---|---|---|---|---|---|
| Qwen3.5-9B | all | 6,971–8,044 | 16,384 ctx q8_0 KV, ample | none | none (all-GPU) | 2 (42.1 s measured cold) |
| Qwen3.8-27B Q3_K_M | all 66/66 (`--fit` probe: 13,279 MiB projected vs 14,895 free → no change needed) | 15,013–15,682 (**96 % of card**) | fits, ~0.6–1.3 GiB headroom | none | none | 4 (4.1 s warm measured; cold ≈ 60–90 s ESTIMATED from probe session) |
| Qwen3.8-27B UD-Q3_K_XL | all | 14,751–14,773 | fits | none | none | 1 |
| Ternary Bonsai (Prism) | all | 9,111–10,183 (+0.9 GiB drift during TEST, cause not determinable from stored fields) | fits | none | none | 3 (35.4 s measured) |

- **No R6 model was CPU-offloaded and none suffered memory-pressure runtime compromises** (MEASURED: load logs, flat VRAM traces, decode rates consistent across runs). GGUF size < 16 GB did *not* mean comfort: Q3_K_M at 96 % of the card is why nothing could co-reside and why a larger context for R7 may not fit (contract § 17 already records this).
- Models were unloaded/reloaded at every arm switch: ≥10 loads / 11 serve cycles (8 distinct `local_server_session` values stamped in the ledger + early unstamped sessions). Total load cost ≈ 10–15 m (ESTIMATED), all inside the measured 95-m gap budget.
- Host RAM: 47 GB, no pressure observed (spot MEASURED); the 4.1 s warm reload shows the 13.8 GB file stayed page-cached.

## 9. Model-specific bottlenecks

For each arm: slow per token, or many tokens, or something else?

- **Qwen3.8-27B Q3_K_M — both, and the combination is the milestone.** Slow per token: 27.8 tok/s realtime decode = 13.82 GB × 27.8 ≈ **384 GB/s effective weight streaming ≈ 43 % of the 5080 Laptop's ~896 GB/s — memory-bandwidth-bound** (896 GB/s is the vendor spec for this SKU: `nvidia-smi` confirms the GPU model and a 14,001 MHz max memory clock ⇒ 28 Gbps GDDR7, with the 256-bit bus taken from the published spec — EXTERNAL SPEC) (MEASURED rate; bandwidth attribution INFERENCE but consistent across all arms). Many tokens: median completed answer 5.8 k output tokens, and 88/192 cases ran to the full 8,192 (6.79 h monotonic ≈ 7.4 h realtime of cap burn — 31 % of the whole milestone for this one artifact). Not: tools (0.4 s/case), turns (1), offload (none), contention (sole resident), retries (0), loads (≤ 2 m total).
- **Qwen3.8-27B UD-Q3_K_XL** — same shape; 35.6 tok/s realtime (IQ-quant kernels faster per token) but *more* cap hits (18/36), so cases/hour only 18.2.
- **Qwen3.5-9B** — fast per token (≈87 tok/s realtime, 496 GB/s effective = 55 % MBU) but generated 5× Qwen3-8B's tokens per case (median 5.4–5.5 k); its DEV rejection was reasoning length, not runtime speed.
- **Ternary Bonsai** — 49.2 tok/s realtime on the Prism runtime (353 GB/s effective, 39 % MBU — the ternary kernels extract less bandwidth); moderate token counts (median ~4.1–4.6 k); fewest cap hits of the 27Bs. Its +0.9 GiB VRAM drift during TEST is the only unexplained runtime behavior in R6.
- **Prompt ingestion is a non-factor for all arms:** 0.9–2.2 % of busy time (MEASURED, 3 sessions); llama.cpp's within-session LCP prefix reuse was active (log-verified) — cases share the system+plan prefix.
- **Warm-up:** the first request of a cold Q3_K_M session ran ~4 min at ~1 tok/s (rank-1 slowest case). One-off per session; the 8-token prime did not absorb it. INFERENCE: first-touch page migration/graph capture on this build.

## 10. Developer-agent / harness overhead

Model benchmark time (22 h 28 m) versus Fable/Claude engineering time — the entire non-run budget is **95.0 m**, itemized (MEASURED, ledger gaps):

| item | wall | classification |
|---|---|---|
| R6.1 provenance + registry + contract pre-registration (20:59→21:36) | 35.9 m | IMPLEMENTATION NECESSARY (the plan's § 7 fail-closed requirement had zero pre-existing code) |
| contract freeze + independent review B + follow-ups (05:45→06:06) | 20.6 m | SCIENTIFICALLY NECESSARY (pre-DEV gate review was a plan requirement; DEV was blocked on it by design) |
| post-TEST analysis + report fill + review C + final commits (20:48→21:03) | 14.9 m | SCIENTIFICALLY NECESSARY (final challenge) / DOCUMENTATION |
| 10 server-swap/record/transition gaps | 17.0 m total (34–212 s each) | IMPLEMENTATION NECESSARY (~11 m: loads, priming, state transitions) + AVOIDABLE (~5–8 m poll latency: run-end detection took 34–89 s each because orchestration polled) |
| UD-Q3_K_XL preflight refusal → `bind_running_server` fix `ef120b3` (01:35→01:41) | 5.3 m | IMPLEMENTATION NECESSARY (the guard caught a real record gap — driver-path `libcuda` — and failed closed as designed); the *fix* cost 5 m on the critical path |
| bonsai probe interruption (10-m foreground tool timeout) → resume | 0.6 m gap (34 s) + ~1 m re-preflight | AVOIDABLE (orchestrator ran a long eval in a foreground shell once; every other run was backgrounded) |

Subagents (MEASURED transcript spans): bootstrap workflow 7 agents, 18.5 m wall, ~975 k tokens — **pre-goal**, and it *shortened* the bootstrap (6-way parallel inspection; no duplicated work on the critical path). Provenance implementer 21.8 m (~10 m critical, rest overlapped my own edits). Review A 14.1 m — **zero critical path** (ran during the Q3_K_M pilot). Reviews B/C — critical path by design (gates). None was duplicative: A/B/C re-read the same state deliberately (independence requirement, plan § 16).

Other engineering during runs (review-A follow-ups `364428b`, `r6_metrics`/`r6_analysis`/`r6_dev_record`/report drafting, 8 full test-suite runs) was **hidden inside model-run windows** — measurable in git (41 commits in the window) but costing ≈ 0 wall.

Failed approaches: none abandoned; one guard bug (libcuda), one test flake (fixture timestamp, fixed in the freeze gap), one JSON-serialization fix (off-path). Total visible debug cost ≈ 8–10 m.

## 11. DGX Spark counterfactual

The measured decomposition says R6 was ~93 % single-stream decode, memory-bandwidth-bound at 353–496 GB/s effective on a 896 GB/s GPU. A DGX Spark (GB10, 128 GB unified, **273 GB/s** memory bandwidth — vendor spec, EXTERNAL) must be evaluated against exactly that:

| bucket | R6 measured time | Spark effect |
|---|---|---|
| LIKELY AFFECTED — token generation | ≈ 21 h 50 m | **Slower, not faster**: 273 GB/s peak vs 353–496 GB/s *achieved* here → decode ≈ 0.4–0.7× current speed even at generous MBU parity; the 27B chain alone would grow from 13.7 h toward 25–30 h |
| — prompt ingestion | ≈ 0.5 h | compute-bound; roughly a wash; immaterial either way |
| — CPU-offloaded inference / memory pressure | **0 h** (nothing was offloaded) | nothing to fix |
| — model loading/switching / residency | ≈ 10–15 m | eliminated by 128 GB co-residency — saves minutes |
| POSSIBLY — multiple models resident / parallel arms | up to 8.8 h of non-Q3_K_M arms could overlap the Q3_K_M chain | on Spark *alone*, parallel arms share the same 273 GB/s — aggregate decode still below the 5080's serial throughput; **as a second node beside the 5080** the overlap is real (§ below) |
| NOT AFFECTED | gates/reviews (~35 m), implementation (~50 m), scorer/tools (~10 m), docs, agent reasoning, methodology serialization | none |

Per-model: none was memory-*capacity* constrained in execution (all fit); all were bandwidth-constrained in decode; 128 GB removes only the co-residency ceiling and the (never-exercised-in-R6) Nemotron offload; that reduces model-load inconvenience and enables parallel arms, not the critical path of the dominant chain.

**Counterfactual totals (ranges, MEASURED components + stated assumptions):**
- **Spark replaces the 5080:** 24 h → **≈ 38–50 h**. Net strongly negative: −10–15 m of loads, +16–26 h of slower decode. *Would not have shortened this R6; it would have roughly doubled it.*
- **Spark added as a second node** (Qwen3.5-9B, UD pilot and Bonsai arms placed on it — each candidate is its own frozen execution system, so cross-node placement is scientifically legal if pre-registered; those arms decode ~2× slower there, 8.8 h → ≈ 17.5 h of Spark-side work, overlapping the 5080's 13.7 h Q3_K_M chain): total ≈ **18–19 h** (save ~5–6 h, 22 %). The Spark side becomes the new critical path.
- **Optimistic upper bound for *any* second node** (a 5080-class or faster second GPU instead of a Spark, perfect overlap, zero added gaps): critical path = Q3_K_M chain 13.7 h + gates/gaps ≈ **14.5–15.5 h** (save ~8.5–9.5 h, 35–40 %). The Q3_K_M chain itself is compressible only by more bandwidth (a ~1.8 TB/s workstation GPU ≈ 2× decode → chain ≈ 7 h) or by generating fewer tokens (R7's question).
- Memory bandwidth **is** the relevant decode variable here (MEASURED effective rates scale with artifact bytes across all four arms); FP4 FLOPS are not.

## 12. Software/harness improvements that beat hardware

| improvement | measured basis | expected saving on an R6-shaped milestone | classification |
|---|---|---|---|
| Resolve the reasoning-budget question (R7: cap > 8,192 / thinking budget) or pre-register a truncation-abort rule | 9 h 55 m produced 145 zero-scoring cases (41 % of wall) | up to ~8 h *of useful signal recovered* — the burn either converts to passes or stops early | REQUIRES VALIDATION (changes the execution system; must be frozen pre-DEV — this is exactly R7) |
| Second inference node for independent candidate arms | 8.8 h of non-dominant arms fully overlappable | 5–9 h | SAFE NOW (per-candidate execution systems are already machine-specific and pre-registered; no shared state) |
| Dual-clock telemetry (realtime + monotonic on every span); use realtime for wall metrics | every published latency understates realtime 7–12 % (chronic, MEASURED back to R3-era runs) | correctness, not time | SAFE NOW |
| Event-driven run lifecycle (run-end hook → record/serve next) instead of 30–60 s polling | 34–89 s latency × 13 run ends ≈ 5–8 m | ~5–8 m | SAFE NOW |
| Persist per-invocation `prompt_ms`/`predicted_ms`/TTFT and server lifecycle events; keep per-session logs (stop truncating on serve) | 8 of 11 session logs lost; prompt/decode split unrecoverable for them | evidence, not time | SAFE NOW |
| GPU/RAM sampler daemon (1–5 s cadence) during runs | utilization/VRAM known only from spot samples + per-case snapshots | evidence | SAFE NOW |
| Persistent servers across phases / prefix caching | loads ≈ 10–15 m; prefix reuse already active in-session; fresh-session-per-split is a frozen rule with measured justification (23/48 outcome moves across restart) | ≤ 10 m, and fresh-session must stay for DEV/TEST | SAFE NOW for TRAIN only |
| Case-level parallelism / continuous batching | numerics change; determinism policy | up to ~2–4× on paper | WOULD CHANGE EXPERIMENT SEMANTICS (adoptable only as a new frozen execution system + stability probe) |
| Targeted tests during dev + one final full suite | already the practice: 8 full runs ≈ 45 s total | none left | SAFE NOW (already done) |
| Automated provenance registration & phase stamps | already built in R6 (registry CLI, ledger, phases.jsonl — phases were manual CLI calls) | make phase/run events automatic in the runner | SAFE NOW |
| Reduced subagent rediscovery | reviews A/B/C re-read state *by design* (independence); the bootstrap fan-out saved time | none to cut safely | — |

## 13. D0/H0 telemetry implications

The schema below is derived from what this autopsy had to reconstruct by hand or could not recover. Every event carries `ts_realtime` **and** `ts_monotonic` (the 7–12 % skew was invisible until cross-checked), plus `experiment_id, phase, split, arm, candidate_id, config_digest`.

```
EXPERIMENT  phase_start/phase_end (auto-emitted by the runner, not manual CLI),
            run_start/run_end (end line written from an atexit/signal handler —
            the interrupted Bonsai probe left no end line), planned/completed cases
INFERENCE   invocation_id, case_id, model_turn, invocation_start/end,
            prompt_eval_start/end, decode_start/end, ttft   (all were lost: raw
            `timings` not persisted; ttft_ms None on every row),
            input_tokens, output_tokens, reasoning_tokens (chars was the only proxy),
            stop_reason, cap_hit, retry, error, artifact_sha, runtime_digest,
            gpu_layers/offload placement
TOOLS       tool_call_start/end, tool, success   (tool time was only inferable as
            "inter-request idle minus scoring")
HARNESS     subagent start/end + model + critical-path flag (reconstructed from
            transcripts), tests start/end (reconstructed by grepping the session log),
            report-generation spans, commit shas as events
SYSTEM      1–5 s sampler: GPU util, VRAM, host RAM, CPU (only spot samples existed);
            server lifecycle: start/model-load-start/loaded/stop with pid, port,
            artifact_sha, session_id (8 of 11 session logs were destroyed by the
            serve script's log truncation); host power/suspend events if obtainable
            (the suspected cause of the clock skew)
OUTCOME     scorer dims, verifier, strict pass, cap_hit, parse failure   (existed)
CLOCK       periodic realtime-vs-monotonic offset samples (would have made the skew
            a first-class measurement instead of a forensic discovery)
DB          stamp an explicit inserted_at instead of relying on now() (case 1's
            created_at predates its case — transaction-open artifact)
```

## 14. Missing evidence and uncertainty

- **Prompt/decode split, TTFT, load times for 8 of 11 server sessions** — logs truncated by `serve-r6.sh` on each start. Extrapolations marked ESTIMATED.
- **GPU utilization / host RAM timeseries** — spot samples only (94–97 % util during decode; no RAM pressure). The 93 % GPU-busy figure derives from server-log busy time, not from GPU counters.
- **Cause of the monotonic-clock skew** — measured precisely, attributed by INFERENCE (WSL2 timer behavior on a power-managed laptop host). Host-side logs were not examined.
- **Cause of the pilot-vs-TEST decode-rate difference (~8 %)** and of Bonsai's +0.9 GiB VRAM drift — not determinable from stored fields.
- **Reasoning content** — not persisted, so "long reasoning vs degenerate loop" on truncated cases remains unknowable (already recorded in the R6 report § 11).
- The Bonsai probe's first segment has no ledger end line (bounded by its last DB insert, ±1 case).
- Per-case `wall_ms` includes model call + transport only; tools/scoring live in the inter-request gap — bounded (0.3–0.7 s) but not itemized per component.

## 15. Five highest-value actions for future long-running FIS experiments

1. **Run R7 (reasoning-budget calibration) before any hardware decision** — 41 % of R6's wall clock went into 145 truncated, zero-scoring generations; converting or aborting that burn dwarfs every other lever. (Already R6's recommended next milestone; not started.)
2. **Fix time itself:** dual-clock stamps on every span and realtime-based wall metrics. Every latency this project has published is 7–12 % low; the fix is a few lines and retroactively explains historical numbers.
3. **Add a second inference node for independent candidate arms** (any ≥5080-class GPU; a DGX Spark works but decodes ~2× slower): measured saving 5–9 h on a 24 h milestone. Do *not* replace the 5080 with a Spark — decode here is bandwidth-bound and would slow ~2×.
4. **Make the runner emit lifecycle telemetry natively** (run/phase events with signal-safe end lines, per-invocation prompt/decode/TTFT, server start/load/stop, preserved per-session logs, GPU/RAM sampler): this entire autopsy should have been one query.
5. **Keep the things that measured cheap:** the fail-closed provenance/state machine, subagent reviews overlapped with runs, targeted tests + one final suite, and single-slot determinism — their combined critical-path cost was ~1.5 h (6 %), and two of the three reviews ran for free inside model windows.

## 16. Final questions, answered plainly

1. **Why ~24 h?** 22 h 28 m of serial, single-slot local decoding (93.4 %) — 65 % of the milestone was the Qwen3.8-27B family at ~28 tok/s realtime, and 41 % of the milestone was cap-hit reasoning that scored nothing — plus 95 minutes of everything else.
2. **Necessary or inefficient?** Overwhelmingly scientifically necessary *given the frozen contract*: the token volume was the experiment; serialization was VRAM + pre-registered methodology; overhead was ~6 %. The genuinely avoidable part was ~10–15 minutes (polling latency, one foreground-timeout interruption).
3. **Was the RTX 5080 the primary bottleneck?** Its memory *bandwidth* set the decode floor (39–55 % MBU achieved, so ~2× headroom exists even on this card in principle), and its 16 GiB forced arm serialization. But the workload's token count (3.0 M generated) is the multiplier — the card ran 93 %-busy.
4. **Memory/offload constrained?** None of the R6 models — zero CPU offload, all weights resident. Q3_K_M was capacity-*ceiling* constrained (96 % of card: no co-residency, limited context headroom). Historical Nemotron is the only offload-constrained model and it ran zero new inference.
5. **Fit comfortably but still slow?** Qwen3.5-9B and Bonsai — fast per token, slow per case because they generate 4–6 k reasoning tokens; Qwen3.8 both generates the most and decodes the slowest. Tool loops and harness behavior contributed ≈ 0 (single-turn cases, 0.3–0.7 s/case harness).
6. **Fraction that was actual local-model inference?** ≈ 93 % of wall (server-busy ≈ 22 h 20 m of 24 h 03 m).
7. **Implementation/harness overhead?** ≈ 6.6 % total non-run time (95 m), of which ~50 m implementation/debug, ~36 m gated reviews/orchestration, ~10 m loads/priming; in-run harness ≈ 0.4 %.
8. **Would a DGX Spark have shortened THIS R6 materially?** As a replacement: no — it would have lengthened it ~1.7–2.1× (273 GB/s vs 353–496 GB/s achieved decode bandwidth). As an added second node: moderately (~18–19 h, save ~5–6 h).
9. **Which phases would it help?** Only by overlapping the non-dominant arms of R6.2/R6.4/R6.5 (TRAIN pilots, Qwen3.5/Bonsai/UD runs) with the Qwen3.8 chain, plus minutes of load/residency. It cannot touch the 13.7 h Qwen3.8 chain, the gates, or the reviews.
10. **What software improvement beats hardware?** Settling the reasoning budget (R7): up to ~8–10 h of R6's wall is at stake, versus ~5–9 h for a whole extra GPU. Second: dual-clock/lifecycle telemetry (correctness of every number).
11. **Instrumentation before the next long milestone?** The § 13 schema — above all dual clocks, per-invocation prompt/decode/TTFT persistence, signal-safe run-end events, preserved server logs, and a GPU/RAM sampler.
12. **What changes in the experiment-launch template?** (a) pre-register arm placement across nodes and allow independent candidates to run in parallel; (b) pre-register a truncation-abort/budget policy alongside cap calibration; (c) require the telemetry schema before any TRAIN call; (d) keep foreground shells away from long runs (background + event hooks); (e) state in the contract which clock is authoritative for every latency metric.
