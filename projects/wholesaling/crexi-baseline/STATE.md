# Crexi Baseline — State of Work

> Durable handoff. Written 2026-08-27. Everything needed to resume without
> conversation history. Append-only in spirit: correct facts in place, add new
> sections at the end.

## Where things stand

**Epic:** build a reproducible, fully-observed baseline of the Crexi
ingest→analysis lane, then optimize. Plan approved; Phases 0–1 complete, Phase 2
(trace instrumentation) partially built, Phase 3+ not started.

**Current activity:** walking listings one at a time to harvest defect classes
(error analysis) — deliberately NOT building a corpus yet. Operator's call, and
correct: the playbook's ch. 03 §5.1 requires harvesting real failures before
deriving any ontology.

**Next task (operator-directed, not yet started):** full auditability of
*what produced each value* — deterministic script vs LLM vs external API — at
every step, before walking more listings.

## The rig

Repo: `~/code/adaptive-ai-lab`, branch `project/wholesaling-intake`.
All rig files under `projects/wholesaling/crexi-baseline/`.

| File | Role |
|---|---|
| `rig/env.sh` | Hermetic env. **source, never execute, never pipe.** `source rig/env.sh A\|B` |
| `rig/preflight.py` | Fail-closed gate. Asserts **effective outcomes**, not env inputs |
| `rig/preflight.sh` | Wrapper that runs the above from the guarded CWD |
| `rig/run.sh` | **The only sanctioned way to invoke anything.** cds to the work dir, runs preflight *there*, then execs |
| `rig/db.sh` | `up / schema / down / nuke / snapshot / restore / psql` |
| `rig/defects.py` | Stable defect-class registry (F-B1…F-B8), keyed to stages |
| `rig/trace.py` | Per-listing pipeline trace via runtime seam-wrapping (no product edits) |
| `runs/*.jsonl` | Trace + sweep outputs |
| `FINDINGS.md` | The defect write-ups with evidence chains |

Arms: **A** = deterministic (`AI_LOCAL_TRANSPORTS_DISABLED=true`, LLM income
extraction structurally off). **B** = AI-on (claude_sdk serves).

## Local database

- Docker `postgres:17`, digest-pinned, container `crexi-baseline-pg`, **port 55432**
- URL: `postgresql+psycopg://wholesaling:wholesaling@127.0.0.1:55432/wholesaling`
- Schema at alembic head **`0107_comm_fact_homes`**
- Sentinel row `rig_marker = 'crexi-baseline-rig'` proves identity (host+port alone
  do not: an ssh tunnel on `127.0.0.1:25432` reaches a **remote** Postgres)

**Row counts as of 2026-08-27:**

| table | rows |
|---|---|
| crexi_listings | 100 |
| crexi_comps | 846 |
| property / valuation / deal / listing | 25 each |
| audit_log | 62 |

Data provenance: a live FL ingest (`--states FL --db prod --apply --max-fetch 500`)
stopped early at 100 listings; comps accumulated from value-route passes.

## Safety — three fail-open defects found and fixed

The dominant risk is touching production. `crexi_ingest.py:55-72` /
`crexi_value_route.py:126-132` resolve their own DB URL and **fall back to
`backend/.env.local` (real Supabase) when a var is unset or empty**.

1. **R2 false pass.** Exporting `R2_*` as empty strings did NOT neutralize the
   photo mirror — `Settings` sets `env_ignore_empty=True`, so empty reads as
   unset and `backend/.env` supplied `R2_BUCKET=media`. **Measured
   `mirror.enabled=True` while the gate printed PASS.** Only a CWD with no
   `.env` works.
2. **Locality.** `127.0.0.1` proves nothing here (ssh tunnel to a remote PG,
   verified live — it answered and rejected our password). Gate now requires
   host+port+database+sentinel.
3. **Preflight/run CWD mismatch.** The gate passed from `runs/work` while the
   script ran from `backend/` and printed `photo mirror: ON (R2)`. `run.sh` now
   runs both in one CWD.

**Standing rule learned:** assert the *effective outcome*
(`build_crexi_mirror().enabled`), never the environment meant to produce it.

## Credentials

`CREXI_TOKEN` read by reference from `~/.config/crexi/token` (mode 0600, outside
both repos). Valid to **2026-10-11**, carries the `Comps` capability. It was
pasted in chat, so it lives in a transcript — **rotate after the baseline.**

## Defect classes found (details + evidence in FINDINGS.md)

| id | stage | rate (n=25) | summary |
|---|---|---|---|
| **F-B8** | arv | **100%** | `sale_event_name` never reaches `Comp.exclusion_reason` → universal ×0.55 haircut; moves 58% of ARVs below the 0.35 floor AND disables the package-deal exclusion |
| F-B6 | income | 76% | priced off tier-4 market median |
| F-B3 | arv | 60% | ARV confidence below the 0.35 floor (mostly an effect of F-B8) |
| F-B4 | income | 25% of extractions | `_numbers_in` can't parse `$400k` → correct extractions discarded |
| F-B2 | arv | all | `comp_set` computed (61/41 comps in memory) then **dropped at persist time** |
| F-B1 | income | 4% | per-unit band rejects a correct high-rent extraction |
| F-B5 | arv | 4% | no ARV despite comps fetched |
| F-B7 | income | — | no income signal at all |

Only **1 of 25** listings is defect-free.

## Corrections I made to my own claims

Recorded because they matter for trusting the rest:
- "Validator rejected 73%" — **wrong**; 11 of 13 rejections were `gross=None`,
  the LLM correctly reporting no stated income.
- "ARV may be anchored to the ask" — **wrong**; ARV is genuinely comp-derived.
- A crude regex screen suggested 22% band exposure — **discarded**, it was
  matching asking prices, not income.
- Two bugs in my own trace harness (chunk_limit semantics; ARV attributed to the
  predecessor listing because ARV computes before income).

## Known operational facts

- Value-route throughput: ~30s–2min/listing, dominated by comp fetches at
  `crexi_requests_per_second=2.0`. A full FL pass (1,511 type-matched) ≈ 12–40h.
- Income resolution alone: median **7.6s**/listing in Arm B (the LLM call).
- FL scope: 56 county partitions, 2,087 swept, 1,511 type-matched multifamily,
  `total_count=3,480`.
- Prod cron fires 01:41/07:41/13:41/19:41 UTC — stay clear during record passes.

## Not yet examined

- **Routing and gate stages.** Every listing so far terminates at
  `MF_REVIEW_HOLD_REASON`, so the gate has never done real work in a trace.
- The `F-B5` no-ARV case is undiagnosed.
- Ingest-stage defects (only the value-route half is instrumented).
