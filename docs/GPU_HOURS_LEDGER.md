# GPU-Hours Ledger

> STATUS: CURRENT / NORMATIVE — the demand instrument for the hardware purchase
> trigger (master plan § 8: 3 consecutive months > ~$150/mo rented spend, or a
> committed always-on client serving tier, triggers the ONE benchmark-chosen buy).
> Append-only. Opened by M0 (2026-08-20) as required by NEXT_STEP_M0.md § 6-E.
>
> Columns: date, milestone, node (owned/rented + GPU), purpose, GPU-hours
> (authoritative clock: monotonic-derived wall of the serving/benchmark session),
> spend (USD actually billed; owned hardware = 0), notes.

| date | milestone | node | purpose | GPU-hours | spend USD | notes |
|---|---|---|---|---|---|---|
| 2026-08-20 | M0 | owned RTX 5080 Laptop 16 GB | WP-C context/cap fit probe (3 server sessions, 3 full-cap stability generations) | 0.40 | 0 | monotonic 1442.5 s (20:52–21:17 UTC); artifacts/m0_fit_probe_events.jsonl |
| 2026-08-20 | M0 | owned RTX 5080 Laptop 16 GB | WP-B paired cap-raise probe (31 generations, one session) + live smoke | 2.98 | 0 | monotonic 10688.3 s (21:19–00:27 UTC); artifacts/m0_paired_probe_events.jsonl |
| 2026-08-20 | M0 | rented 3090 (Secure/Community) | WP-E decode benchmark | 0 | 0 | **NOT RUN — no GPU-rental account/credentials exist in the lab environment.** Harness ready: `scripts/m0_gpu_benchmark_remote.sh` + `scripts/m0_gpu_benchmark.py`. |
| 2026-08-20 | M0 | rented 5090 | WP-E decode benchmark | 0 | 0 | as above |

## Monthly rollup (the trigger reads this)

| month | rented GPU-hours | rented spend USD | trigger status |
|---|---|---|---|
| 2026-08 | 0 | 0 | far below the ~$150/mo line; purchase stays deferred |
