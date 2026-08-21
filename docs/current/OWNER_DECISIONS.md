# Owner Decision Record

> STATUS: CURRENT / NORMATIVE (append-only). Decisions of the scientific owner
> (Brennen) that move program state. Milestone reports recommend; only entries
> here (or owner-authored master-plan edits) accept. Rows are appended, never
> edited.

| Date | Decision |
|---|---|
| 2026-08-21 | **M0 recommendation accepted.** The owner reviewed `M0_REPORT.md` and accepted its STRONG R7 GO row (`f_rescue` = 9/15 = 60%). R7 is scientifically justified. R7 remains blocked on: (1) M-STAT complete, (2) the Suite-v4 trigger review (R7's TEST look is #8). M0 results and artifacts are historical evidence and must not be altered. |
| 2026-08-21 | **Pre-M-STAT doctrine corrections** (recorded in commit `4b45e57`): SMOKE is a literal registry state, not a run kind; the machine TEST-look ledger (`learning/registry/test_looks.jsonl`) is the source of truth with `TEST_LOOK_LEDGER.md` as its mechanically validated mirror; the Suite-v4 trigger review is owner-level work after M-STAT, never part of M-STAT execution. |
| 2026-08-21 | **M-STAT execution authorized** (`/goal`). Scope: methodology enforcement in code + registry per `M_STAT_IMPLEMENTATION_MAP.md`. Explicitly NOT authorized: R7 execution or contract freeze, Suite-v4 trigger verdict or release, DEV/TEST consumption, R9, fine-tuning, hardware spend. |
