# TEST-Look Ledger — Suite v3

> STATUS: CURRENT / NORMATIVE (append-only)
> Created 2026-08-20 with the seven historical looks backfilled from
> `../experiment-log.md` / `../routing-experiments.md`. Every future TEST evaluation
> appends a row **at contract-freeze time** (planned) and updates it at execution.
> Rule (playbook §1): **look #8 requires the Suite-v4 refresh-trigger review first.**

**Counting convention:** a look = one arm's outcomes on TEST being read for a decision
or report — including offline replays of stored outputs. Analyses computed *within* an
already-counted execution (e.g. the R4-cascade replay over the V3 baseline runs) do
not count again. SMOKE and TRAIN work never touches TEST and never appears here.

| # | Date | Experiment | Arm / run | Cases | Kind |
|---|---|---|---|---|---|
| 1 | 2026-08-17 | Suite v3 baselines | Qwen3-8B `V3-qwen-96` | 96 | execution |
| 2 | 2026-08-17 | Suite v3 baselines | Nemotron `V3-nemotron-96` | 96 | execution |
| 3 | 2026-08-17 | Suite v3 baselines | frontier `E4-v3-96` | 96 | execution (R4 replays computed within #1–3, not counted separately) |
| 4 | 2026-08-18 | R5 learned routing | Qwen tree policy (offline replay) | 96 | replay |
| 5 | 2026-08-18 | R5 learned routing | Nemotron `lr_core` policy (offline replay) | 96 | replay |
| 6 | 2026-08-19 | R6 refresh | Qwen3.8-27B Q3_K_M `qwen38-27b-q3km` | 96 | execution |
| 7 | 2026-08-19 | R6 refresh | Bonsai-27B `bonsai-27b` | 96 | execution |

**Standing consequences already incurred:** TEST is spent for learned routing on Suite
v3 for both local arms (`learning/registry/r5/test_unlock.json`), and spent for
`qwen38-27b-q3km` and `bonsai-27b` as R6 candidates.

**Next row is #8** → the Suite-v4 trigger review (design rule: v4 adds scenario
classes before replications) must be completed and linked here before any contract
schedules it. R7's planned TEST look, if M0 opens R7, is that look.
