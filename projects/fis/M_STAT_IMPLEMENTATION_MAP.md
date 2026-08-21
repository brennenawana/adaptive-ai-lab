# M-STAT Implementation Map

> STATUS: EXECUTED 2026-08-21 — this was the M-STAT work plan; the completion
> record is `M_STAT_REPORT.md`, which supersedes this map's status column.
> Governed by: `AI_SYSTEMS_LAB_MASTER_PLAN.md` (sequencing) and
> `EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK.md` (methodology). This map adds no normative
> authority of its own; where it restates doctrine, the playbook/master plan govern.
> Produced 2026-08-21 from a full code audit (7-area inspection, every claimed gap
> adversarially re-verified, zero refutations), then corrected per three owner
> decisions of 2026-08-21 (§0). Implementation begins only on `/goal`.
> Hard prohibitions until then and during M-STAT: no model inference, no
> TRAIN/DEV/TEST acquisition, no R7 work or contract freeze, no Suite-v4 review or
> release, no R9, no fine-tuning, no hardware spend, no modification of M0 results
> or historical reports. **M-STAT stops when its own guards are green.**

## 0. Owner decisions incorporated (2026-08-21)

1. **SMOKE is a literal registry state** (playbook §3). The audit's run-kind
   substitution is rejected. A dedicated `smoke` run kind may exist *in addition*
   if useful; it cannot replace the state. Doctrine: formal lifecycle state; fixed
   36 TRAIN cases = 12 classes × 3; deterministic round-robin order; single arm;
   append-only provenance; non-promotable by construction; can justify neither
   adoption nor elimination; cannot transition directly into a promotable later
   state bypassing the normal lifecycle. If implementation exposes a genuine
   historical-provenance contradiction, M-STAT **stops and returns the conflict**
   rather than silently changing the methodology.
2. **One authoritative TEST-look ledger.** The machine append-only ledger
   (`learning/registry/test_looks.jsonl`) is the enforcement / source-of-truth
   record; `docs/current/TEST_LOOK_LEDGER.md` becomes its generated or mechanically
   validated human-readable mirror (divergence fails validation). Seed the 7
   historical Suite-v3 looks faithfully, reinterpreting nothing; every future TEST
   path, local or frontier, consults the machine ledger; spend occurs at the first
   executed case. (Playbook §1, ledger header, and master plan §7 updated.)
3. **The Suite-v4 trigger review is not part of M-STAT execution.** M-STAT
   implements the machine gate that prevents Suite-v3 TEST look #8 without a valid
   trigger-review reference, preserves the review procedure (§16), and stops.
   M-STAT does not perform the review, does not decide whether look #8 may use
   Suite v3, does not create or release Suite v4, and does not draft or freeze R7.
   The review is a separate owner-level task after M-STAT completes.

## 1. Scope of record

No dedicated M-STAT spec doc predates this map; the requirement list of record is
the union of: playbook §11 (runner consequence guards, SMOKE state, round-robin
ordering, ledgers, canary GUIDs, `TrainedArtifact`), master plan §10 (R9 prereq:
pass^k protocol; FT-rig prereq: `TrainedArtifact` with the §9 field list), and
`NEXT_STEP_M0.md` §6-D / `M0_REPORT.md` §4 (deferred telemetry: TOOLS spans,
HARNESS events, periodic CLOCK-offset sampling, DB `inserted_at` fix).
Acceptance (master plan §10): **all guards fail-closed + tests green**, no inference.

| # | Requirement | Status in code | Blocks R7 freeze? | Touches frozen Suite v3? |
|---|---|---|---|---|
| 1 | Consequence-bearing tolerances | absent | yes | no |
| 2 | SMOKE registry state | absent | yes (contract §13) | no |
| 3 | Round-robin ordering | absent | yes | comparability boundary only (declared) |
| 4 | Cluster-robust MDE / N_eff / INCONCLUSIVE | absent | yes (contract §9) | no |
| 5 | Prediction ledger | absent | yes (freeze checklist) | no |
| 6 | TEST-look-ledger enforcement | partial | yes (look-#8 gate) | no |
| 7 | Suite-v4 trigger mechanics | partial | gate only (item 6) | no |
| 8 | Canary GUID mechanism | absent | mechanism only | activation would break the freeze — v4-only |
| 9 | `TrainedArtifact` | absent | no (FT-rig gate) | no |
| 10 | Certainty curtailment + 3 guards | absent | yes (contract §12) | no |
| 11 | Elimination-rule guard | absent | yes (UD re-entry) | no |
| 12 | pass^k protocol | absent | no (R9 gate) | no |
| 13 | Deferred telemetry (4 items) | 2 partial / 2 absent | M-STAT completion | additive schema change only |

## 2. Consequence-bearing tolerances

- **Current**: `scripts/r6_metrics.py:208-218` computes the cap tolerance post-hoc
  and silently degrades to `CAP_SET[-1]` when nothing meets it (the corrected R6
  defect, preserved in code); the runner loop (`evals/runner/run_eval.py:488-519`)
  catches per-case exceptions and continues — structurally unable to halt. The
  ABORT / RECALIBRATE / PROCEED-WITH-DECLARED-CEILING vocabulary exists nowhere in code.
- **Missing**: in-run violation counting against a pre-registered tolerance spec,
  halt at violation k+1 (curtailed exact counting), named-consequence dispatch.
- **Proposed**: new `fis_platform/tolerances.py` (spec + digest + pure evaluator +
  consequence enum, on the `r6_gates.py` constants→digest→trace pattern), wired
  into the `run_eval` case loop; halts in the `ProbeAbort(SystemExit)` style
  (`scripts/m0_paired_probe.py:117`). PROCEED requires a declared ceiling + cost
  payload before continuing.
- **Tests**: halt at exactly k+1; consequence recorded in events + ledger; PROCEED
  refused without ceiling/cost; resume interaction (counter recounts persisted rows).

## 3. SMOKE registry state (owner decision 1)

- **Current**: the state machine has exactly nine states and no SMOKE
  (`fis_platform/provenance.py:1014-1037`); `RUN_KINDS = ("eval", "diagnostic")`
  (`provenance.py:1817`); `Makefile:368-369 eval-smoke` (3-case DEV prefix) is dead
  against the registry; 36-case stratified selection machinery exists
  (`scripts/r6_pilot.py`) but emits class-major order.
- **Missing**: everything in the §0.1 doctrine.
- **Proposed**: add a **`SMOKE` state** to `STATES`/`TRANSITIONS` preceding the
  promotable path (SMOKE → REGISTERED; no edge from SMOKE to any later state), with
  `require_state`/payload validation enforcing: fixed 36 TRAIN cases (12×3,
  pre-registered and digested à la `r6_pilot.py:68-71`), deterministic round-robin
  order, single arm, results on the same hash-chained append-only ledger,
  non-promotable by construction (no transition may cite a SMOKE run; adoption and
  elimination payloads refuse SMOKE evidence). A `smoke` run kind may be added *in
  addition* for ledger-line typing, mirroring the `diagnostic` kind mechanics
  (`provenance.py:1852-1913, 1992-2003`) — it does not replace the state.
- **Historical-provenance risk (STOP clause)**: existing candidate chains begin at
  REGISTERED and `tests/test_r6_state_machine.py:231-236` asserts the exact current
  transition table. The extension must keep every existing hash-chained log valid
  (forward-only validation; SMOKE required for *new* candidates only). If a genuine
  contradiction with the historical record emerges, **stop and return the conflict
  to the owner** — do not reinterpret history or relax validation.
- **Tests**: state-machine table update; SMOKE non-promotability (no legal edge to
  promotable states; transition payloads citing SMOKE runs refused); ordering
  assertion; TRAIN-only; historical R5/R6 registry logs still verify byte-for-byte.

## 4. Round-robin ordering

- **Current**: `run_eval.py:249` `ORDER BY scenario_id` is the only ordering
  (class-blocked); `--scenario-ids-file` is re-sorted by it; `r6_pilot.py:43` is
  class-major; zero round-robin code repo-wide.
- **Proposed**: deterministic interleave keyed on the `Sxx-seed` id structure
  (seq-within-class, then class), applied **prospectively for TRAIN/DEV/TEST
  wherever prefix decisions matter** (playbook §4; DEV/TEST included because
  curtailment arithmetic reads prefixes), recorded per run in report + events.
- **Declared second-order effect**: case order changes the prompt-cache predecessor
  of every case (the documented within-session nondeterminism source,
  `run_eval.py:57-64`), creating a comparability boundary with historical runs for
  case-level local comparisons. R7's contract must declare it; frozen data unchanged.
- **Tests**: interleave correctness + determinism; `--limit N` yields a
  class-balanced prefix.

## 5. Cluster-robust statistics (MDE / N_eff / INCONCLUSIVE)

- **Current**: no statistical code at all (no scipy/numpy/statsmodels anywhere; the
  only stats import is `statistics.median`). Per-class scaffolding is ready
  (`r6_metrics.py:126-127` by-class counts; `:165-174` discordant pairs = McNemar
  cells). The playbook's standing facts (ICC 0.475, DEFF 4.33, N_eff ≈ 22) are
  currently reproducible by no committed script.
- **Proposed**: stdlib-only `fis_platform/stats.py` — exact McNemar via
  `math.comb`; paired-difference t over the 12 class means (df = 11, embedded
  critical-value table); ICC / design effect / effective-N; cluster-corrected MDE —
  plus reporting subcommands emitting CONFIRMED / REFUTED / INCONCLUSIVE / RANKED.
- **Acceptance test**: regenerate the standing facts from the committed R6 TEST
  record, making the playbook's quoted numbers mechanically regenerable (M0's
  standard). Known-answer tests include the curtailment firewall demo
  (McNemar 0.0596 → 0.0139).

## 6. Prediction ledger

- **Current**: nothing — no file, no schema field, no freeze check; the R6 contract
  has no prediction section.
- **Proposed**: `docs/current/PREDICTION_LEDGER.md` (append-only) + a
  `CONTRACT_FROZEN` payload requirement (metric, point estimate, interval) in
  `_validate_payload`, + a small predicted-vs-actual scorer for reports.
- **Tests**: freeze refused without a prediction payload.

## 7. TEST-look-ledger enforcement (owner decision 2)

- **Current (partial)**: strong per-scope gates exist — R5 `begin_test_unlock`
  (`scripts/r5_replay.py:374-445`) and R6 `require_state` TEST gating
  (`provenance.py:1924-1937`) plus an independent DB spent-check
  (`run_eval.py:441-455`). But no code reads or writes `TEST_LOOK_LEDGER.md`; there
  is no global look counter; `--split` defaults to `"test"` (`run_eval.py:339`);
  and the registry gate binds only local llama.cpp arms (`run_eval.py:379-382`) —
  a frontier-arm TEST run is currently ungated.
- **Proposed**: hash-chained machine ledger `learning/registry/test_looks.jsonl`
  (append-only, seeded faithfully with the 7 historical looks — no
  reinterpretation) + `fis_platform/test_looks.py`; a runner gate for **every** arm
  on `split=test` requiring a planned-look entry; refusal of look #8+ without a
  non-empty `trigger_review_ref`; `--split` becomes required (no silent-TEST
  default); spend recorded at the first executed case; a validator that fails when
  the Markdown mirror diverges from the machine record (the mirror is generated or
  mechanically validated — never independently authoritative).
- **Tests**: unledgered TEST refused for frontier and local arms; look-#8 refusal
  without review ref; backfill = exactly 7; mirror-divergence validation failure.

## 8. Suite-v4 trigger mechanics

- **Current**: `SUITE_VERSION` + fail-closed comparability
  (`fis_platform/suite.py:52-114`) and the proven v2→v3 migration pattern already
  provide the release machinery. The live corpus digest is recorded per run but not
  compared against the pinned manifest (`run_eval.py:423`) — make that fail-closed
  while in this area.
- **M-STAT's only obligation here is the look-#8 gate (item 7).** Review and
  release are out of scope (§0.3, §16).

## 9. Canary GUID mechanism

- **Current**: absent; and there are no scenario files on disk — the corpus lives
  in Postgres, so "canary GUIDs in TEST files" means a token in model-observable
  TEST-split world content / `raw_payload`, plus any published excerpt.
- **Constraint**: `scripts/corpus_digest.py` digests every row of 13 tables — any
  canary injected into the v3 corpus changes the corpus digest and **breaks the
  Suite-v3 freeze**. Therefore M-STAT ships the *mechanism only* (schema field +
  generator injection point, strictly conditional), with **activation deferred to
  the Suite-v4 release**. No Suite-v3 mutation.
- **Tests**: v3 regeneration still reproduces digest `1e7c5278…` with the mechanism
  present and inactive.

## 10. `TrainedArtifact`

- **Current**: `ModelArtifact` is `format: Literal["gguf"]` with upstream-download
  fields (`provenance.py:536-567`); `learning/training/` is empty; zero code hits.
  Plug-in points ready: the self-digesting `_Record` base (`provenance.py:487-527`),
  `R6Registry._put`, and R5's dataset-digest/hyperparameter precedents.
- **Proposed**: `TrainedArtifact` record with the master-plan §9 field list
  (dataset digest, base artifact id, hyperparameters, seed, adapter SHA, pipeline
  digests) + registry put/get + CLI subcommand. Schema/provenance work only — no
  training. Gates FT-rig, not R7.

## 11. Certainty curtailment + three guards

- **Current**: nothing — no curtailment arithmetic, no interval-only reporting, no
  curtailed-arm flag; pairing tools have no exclusion concept.
- **Proposed**: `passes + remaining < ⌈bar·N⌉` in-run check (same module as item 2);
  persisted `curtailed` marker in ledger + events; interval-only reporting
  `[k, k+remaining]/N` + unrun classes for curtailed arms; pairing scripts
  fail-closed on a curtailed arm (the firewall).
- **Tests**: curtailment fires exactly at the bound; curtailed arm refused by every
  paired-comparison path; interval-only output shape.

## 12. Elimination-rule guard

- **Current**: `WITHDRAWN` requires only a non-empty reason string
  (`provenance.py:1740-1745`); the structural half (no WITHDRAWN after DEV) already
  exists. The UD withdrawal at a below-MDE margin is the recorded corrected precedent.
- **Proposed**: payload guard on the two legal WITHDRAWN edges — a
  pilot-selection-loss reason requires margin ≥ the pre-registered pilot MDE, or an
  explicit non-selection reason category. Required data already exists in ledger
  end-lines and state payloads.
- **Tests**: below-MDE selection withdrawal refused; non-selection withdrawals
  (e.g. runtime incompatibility) unaffected.

## 13. pass^k protocol (implementation without execution)

- **Current**: one attempt per case; `run_eval.py:131-132` hard-refuses subsets on
  DEV/TEST — pass^k needs a sanctioned path, not a bypass.
- **Proposed**: a pass^k run protocol on the `diagnostic`-kind template — declared
  frozen subset + k samples per case, recorded as ONE ledgered look
  (machine ledger, item 7), measurement-only (no selection may key off it).
  **Protocol code + tests only; the first measurement is R9's** — no execution in
  M-STAT. Not on R7's path; sequence last.

## 14. Deferred telemetry (M0 §6-D)

- **TOOLS spans (partial)**: broker records `latency_ms` + ordinal only
  (`broker.py:260-291`); `ToolCall` has no timestamps. Add dual-clock stamps /
  optional event emission from `invoke()`.
- **HARNESS events (partial)**: runner emits run/case level only; phase spans are a
  manual CLI call (`provenance.py:1414`); event context lacks
  `experiment_id/phase/candidate_id/config_digest` (digest currently computed after
  `run_start` — reorder). Floor: auto phase spans + enriched context +
  server-session events. The full autopsy-§13 HARNESS row (subagent/tests/report
  spans) stays deferred to the D-series.
- **CLOCK-offset sampling (absent)**: add an offset field / periodic CLOCK event to
  the 5 s sampler (both stamps already exist per event).
- **DB `inserted_at` (absent)**: `learning.*` `created_at` defaults to
  transaction-frozen `now()` (`002_domain.sql:207,220`, `007:19`, `008:26`).
  Migration 009 adds `inserted_at DEFAULT clock_timestamp()` — **nullable, no
  backfill** (a NOT NULL default would stamp migration time onto frozen historical
  rows); existing values untouched.

## 15. Decisions register (retained from the audit, confirmed by the owner)

- `--split` becomes required (no silent-TEST default).
- Stdlib-first statistics (no scipy dependency).
- Prospective round-robin ordering for TRAIN/DEV/TEST where prefix decisions matter.
- Nullable / no-backfill `inserted_at`.
- Canary mechanism only, for future suites; no Suite-v3 mutation.
- `TrainedArtifact` schema/provenance work in scope.
- pass^k protocol implementation without execution.
- **No unrelated cleanup during M-STAT** (including the empty `scenarios/*_seeds.txt`
  placeholders — noted, left alone).

Remaining deferred (unchanged): Suite-v4 release and class design; canary
activation; full §13 HARNESS row; GPU-hours-ledger automation (manual doc is
adequate); NeMo/vLLM/H-/D-series items.

Effort note: with tests to the M0 standard this is realistically 2–3 focused days
against the master plan's "~1 day code"; the R7-blocking subset (items 2–7, 11, 12)
is close to the one-day estimate.

## 16. Suite-v4 trigger review — preserved procedure (owner-level, after M-STAT)

Not part of M-STAT execution (§0.3). What the normative docs require:

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
