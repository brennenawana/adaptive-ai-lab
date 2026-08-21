# Suite-v4 Trigger Review — Procedure

**STATUS: LIVING — the standing procedure for the next owner-level task.**
Extracted verbatim during the 2026-08 repository restructuring from
`M_STAT_IMPLEMENTATION_MAP.md` §16 (the executed M-STAT plan, which remains the
historical record of this procedure's origin). The procedure lives here so the
imminent owner task is not governed from inside a completed historical plan.

When this review is written, its document should be created beside this file
(suggested: `SUITE_V4_TRIGGER_REVIEW.md`), linked from the TEST-look ledger entry
that plans look #8, and from R7's contract §5. The ledger machinery existence-checks
the `trigger_review_ref` path at plan **and** spend time — the review document's
path must be final before look #8 is planned.

---

The procedure, as preserved (M_STAT_IMPLEMENTATION_MAP.md §16):

1. **Who/when**: the scientific owner conducts it before any contract schedules
   TEST look #8 — i.e. before R7's contract freeze (template §5 requires the
   ledger entry with the review linked). Due at the next TEST-consuming milestone,
   whichever it is (R7 or R9).
2. **Question**: does accumulated TEST exposure (7 looks + standing
   spent-consequences) threaten the validity of an 8th look on Suite v3?
3. **Outcomes**: *not threatened* → record the review, link it from the TEST-look
   ledger and R7's contract §5; look #8 may proceed on v3. *Threatened* → Suite v4
   is released first as a versioned suite (cross-suite refusal, as v2→v3), under
   the fixed design rule **add scenario classes before adding replications**.
4. **Record**: a written review document, linked from the ledger.

Proposed rubric for the review document (proposal, not doctrine): enumerate the 7
looks and every decision already keyed off TEST readings — including R7's own
design motivation via R6's TEST truncation profile (indirect-adaptation exposure);
per-arm spent-ness vs the new look's purpose; leakage posture (corpus private, no
canaries in v3); statistical erosion of repeated looks against N_eff ≈ 22; explicit
verdict; if v4 fires, the class-addition plan.
