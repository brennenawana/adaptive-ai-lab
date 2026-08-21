# Experiment Contract Template — v2

> STATUS: CURRENT / NORMATIVE
> Current as of: 2026-08-20
> Supersedes: the implicit v1 structure (R5/R6 contracts' section pattern). v1
> contracts remain the binding records of their own experiments; v2 governs every
> contract frozen after this date.
> Governed by: `EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK.md` (the rules), and
> `AI_SYSTEMS_LAB_MASTER_PLAN.md` (whether the experiment should run at all).

Copy this file to `docs/<ID>_EXPERIMENT_CONTRACT.md`, fill every section, commit
**before** any TRAIN inference. Sections marked ⊕ are new in v2 relative to the R6
contract structure. `[...]` are placeholders. Delete no section — write "N/A —
<reason>" instead, so absence is a decision, not an omission.

---

## 1. Question and scope

- The single question this experiment answers, and **the decision its answer drives**.
- ⊕ **Prediction register**: pre-run effect-size point estimate + interval, per primary
  metric. (Scored predicted-vs-actual in the report; playbook §7.)
- Explicit non-goals.

## 2. Frozen scientific baseline

- Suite version, corpus digest, scorer/verifier versions, incumbent
  configurations/policies that must not move. Asserted at start and end.

## 3. Artifacts

- Every model artifact by SHA-256 + upstream revision (or `TrainedArtifact` record for
  self-produced weights), registry record normative.

## 4. Runtimes (execution-system identity)

- Pinned builds, binary-set digests, CUDA/driver/GPU identity, serve scripts.
- ⊕ **Node placement**: which arm runs on which node (owned/rented), pre-registered.
  Rented nodes: provider tier, single-session-per-arm rule, artifact digests verified
  on the remote host before any case.

## 5. Split protocol

- Cases per split; **round-robin class ordering** (playbook §4) for any run whose
  prefix may inform a decision; any screening rungs (class-balanced, sizes, η).
- ⊕ **TEST-look ledger entry**: this experiment's planned TEST look(s), appended to the
  ledger at freeze time. If this is look #8+ on the current suite, the refresh-trigger
  review must be linked here.

## 6. Calibration rules (TRAIN only) — ⊕ consequence-bearing

For each calibrated parameter (caps, budgets, server config):

| Parameter | Procedure | Tolerance | **Consequence on breach** | Projected cost if PROCEED |
|---|---|---|---|---|
| [e.g. output cap] | [smallest cap in {…} with capped ≤ k/n] | [≤ k of n] | ABORT / RECALIBRATE / PROCEED-WITH-DECLARED-CEILING | [stated wall/compute/validity cost] |

- Evaluation is curtailed exact counting: the phase halts at violation k+1.
- A tolerance without a named consequence fails contract review. No unpriced escape
  hatches (the R6 defect).

## 7. Candidate selection rules (TRAIN only)

- Selection metric and rule; **elimination rule compliance**: no WITHDRAWN below the
  pilot's own MDE (state the pilot MDE here: with n=36, ≈ [9–11] cases margin).
  Sub-MDE outcomes: both proceed / defer to DEV / change metric — pick and state.

## 8. Eligibility / feasibility probes

- Stability probes, context-fit probes, memory fits — procedure + thresholds.

## 9. ⊕ Statistical plan (pre-registered)

- Primary: cluster-robust paired inference over classes (df = classes−1).
  Secondary: McNemar exact (labeled anti-conservative).
- **MDE statement**: expected discordance range → cluster-corrected MDE at α=.05,
  power .80; **effective N** under the measured ICC (Suite v3 TEST: N_eff ≈ 22).
- **Verdict vocabulary**: CONFIRMED / REFUTED / INCONCLUSIVE (+ RANKED for screening).
  The reading for each possible outcome is written here, before data.
- pass^k plan if any arm is stochastic (k, subset, claim it qualifies).

## 10. Server / generation configuration per candidate

- Frozen at the named freeze point; exact flags, ports, session rules.

## 11. DEV qualification gates

- Numeric gates fixed from historical data only, with the gate table printed.
- ⊕ Each gate names its consequence (REJECTED is a consequence; so is
  QUALIFIED-WITH-DECLARED-CEILING).

## 12. TEST protocol

- One look; ⊕ certainty-curtailment clause (default-on) with the three guards (spend
  semantics, interval-only reporting, paired-comparison firewall) copied in;
  disabling curtailment requires a written justification here.

## 13. State machine

- Registry states and transitions in force (including SMOKE precondition: zero
  harness/schema/tool-contract violations on the SMOKE cases before REGISTERED work
  starts).

## 14. Integrity controls

- Fail-closed runner requirements, committed-tree rule, contract blob binding
  (append-only §18 after freeze), ground-truth isolation, live-test lockout.

## 15. ⊕ Telemetry requirements

- Dual-clock stamps on every span; **authoritative clock per metric stated here**;
  signal-safe run start/end events; per-invocation prompt/decode/TTFT persisted;
  server logs preserved; GPU/RAM sampler for runs > [threshold].

## 16. Analysis plan (offline, after TEST)

- Tables, replays (e.g. R4 replay), economics (break-even where routing is claimed),
  cost accounting (wall by authoritative clock, GPU-hours → ledger).

## 17. Roles

- Scientific owner (interprets), executor (runs the rules). The contract executes;
  the owner does not improvise mid-run (DSMB principle).

## 18. Amendment log (append-only after freeze)

- Rows only appended; nothing above this section changes after the freeze commit.

---

### Freeze checklist (all true before TRAIN inference)

- [ ] Committed before any TRAIN call; blob SHA recorded in the registry
- [ ] Every tolerance names a consequence; projected PROCEED costs stated
- [ ] MDE + effective-N + verdict readings written (§9)
- [ ] Prediction register filled (§1)
- [ ] TEST-look ledger updated (§5)
- [ ] Node placement + authoritative clocks declared (§4, §15)
- [ ] SMOKE pass recorded (§13)
- [ ] Elimination-rule threshold stated (§7)
