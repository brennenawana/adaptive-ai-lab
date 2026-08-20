# Suite v3 — Release Report

> STATUS: HISTORICAL EVIDENCE (marker added 2026-08-20; content otherwise unchanged)
> Authoritative record of this completed work — cite it for facts.
> It is not the current project plan. Sequencing: `current/AI_SYSTEMS_LAB_MASTER_PLAN.md`; index: `README.md`.
> Its §10 "next: R5" recommendation was executed long ago (R5, then R6).

Suite v3 is a **benchmark revision**. Every number below was measured against the
Suite v3 corpus, scorer and verifier; nothing here is comparable to a Suite v2 number
by subtraction (§ 8). Governing documents: `FIS_Suite_v3_Benchmark_Release_Goal_Prompt.txt`
(the milestone), `SUITE_V3_RELEASE_CONTRACT.md` (pre-registered scope, gates and
procedure), `OVERNIGHT_STATUS.md` § Milestone 5 (the live log).

## 1. Release identity

| field | value |
|---|---|
| suite version | **3** (`fis_platform/suite.py`), on every manifest and score row |
| release commit / tag | `7764601` / `suite-v3` |
| corpus digest | `1e7c5278ba1f4cc1cc96fa8a1f04946ab622270eaba4c5671274c21e9d39e528` (`scenarios/manifests/corpus_v3.json`; train `d9d1570e6b70…`, dev `5d5c94b049a9…`, test `8deea4a26c4b…`) |
| corpus | 288 scenarios — 96 test / 48 dev / 144 train, 12 classes; 720 provider events, 672 pipeline ledger entries; seed ranges unchanged |
| ontology version | 1 (root causes, actions, cause→action unchanged since v1) |
| scorer / verifier version | 3 / 3 |
| prompt version | 1 (`PROMPTS` unchanged; weak arms `cause_action_directed`, frontier `baseline`) |
| evidence mode | `FIXED_EVIDENCE`, two-phase plan, 8 tools, unchanged |
| model registry | `local-specialist` (Qwen3-8B Q4_K_M, 8082), `nemotron-lightning` (Nemotron 3.5 Lightning 30B-A3B IQ4_XS, 8083, `--fit on --fit-target 1024 --no-mmap`), `claude-frontier` (Claude Opus 5 via `claude` CLI 2.1.234, `--safe-mode --tools ""`), llama.cpp `b1-9b05354` |
| known limitations | contract § 9 (static balances; `add_failed_delivery`; whole-result forbidden scan; `entity_ids`-only fabrication check; CLI budget/seed/fingerprint; `_phase_two` limit 6) |

## 2. Changelog — the four benchmark defects (contract § 2)

| # | Suite v2 defect | model-neutral rationale | Suite v3 implementation | tests / invariants | evidence-visible effect |
|---|---|---|---|---|---|
| **A** background settlements | `_distractors()` settlements in S01/S02/S05/S06/S07/S08 were state rows with no delivery, event or posting — S10's `reconciliation_gap` signature as ambient noise in six classes (every S06 world: 4 settlements, 1 entry); S11 posted by direct `add_entry` with a counter id shape; background generated after the case; S07 deliveries "received" before their events | a world meant to contain one defect must not carry a second one as background; postings must be consequences, not fixtures; nothing an operator investigates happens after the case is opened | `_background()` publishes each background settlement (`settlement.created`, safe key) through the integration and ledger consumers; ordering per class (injected → background → case in S01/S02/S06/S07; background → decline → case in S05/S08); mapper version recorded per event, S06 rolls v3 back to v4 after the injected settlement; S07 clock advanced past the reversal before publishing; every settlement/reversal event keyed except S02's; `World.add_entry` deleted, `ledger.entries` out of the generator's tables | 69 corpus-wide invariants (`test_scenario_invariants.py`): posting multiplicity per class, nothing post-dates the case, `received_at ≥ occurred_at`, only S06's injected posting differs from its settlement, exactly one S07 inversion, injected refs precede background, key never discriminates; DB-gated projection == live rows for all 288 and no entry without a cause | ledger entries and webhook history exist for background purchases; `integration.events.mapping_version` shows 3 on S06's corrupted event, 4 elsewhere; rubric unchanged |
| **B** S08/S05 amounts vs balances | S08 drew amount and balance independently — 3 of 24 worlds had declined amount > available (dev S08-2003007 70 530 > 17 530), making the forbidden `insufficient_funds` hypothesis data-consistent; S05 left `ledger_balance` at its draw next to `available_balance = 150` | a risk-hold decline is not a funding problem, so the world must not make it one; balances are the snapshot at case time and available == ledger where nothing models a hold | S08 declined amount drawn strictly below `available_balance` (one draw); S05 `ledger_balance = available_balance = 150` | failing-first reproduction on seed 2003007, then corpus-wide: S08 amount < balance, S05 amount > balance, available == ledger everywhere | S08/S05 amounts and balances only; rubric unchanged |
| **C** forbidden-claim polarity | lookback-only 80 chars (a cue after the phrase — "insufficient funds … are all ruled out", E4-v2-dev S08-2001007 — scored as an assertion); `rfind(-1)+len` trimmed 2 chars off every window; leading-space cues lost at sentence/field start (E6b-G-both-dev S05-2000004 `system_outage`) | the metric is about *asserting* harm; a documented, deterministic same-sentence rule in both directions is the faithful reading; hedges stay assertions | `_LOOKAHEAD_CUES` (predicate negations only), boundary trim only when a boundary exists, padding at boundaries/edges only, string-value opener as a boundary; `SCORER_VERSION = "3"` | 38 fixtures incl. replay of the 4 recorded excerpts (2 refuted, 2 hedges still asserted); genuine assertions and cross-sentence laundering still fail | scoring only |
| **D** idempotency_key observability | `collect_observed_ids` harvested `*_id` + `provider_ref`; `get_webhook_history` already returned `idempotency_key`, so citing it (E4-v2-dev S01-2001000) read as fabrication | the verifier judges against what the model could observe; the key is the fact S01/S02 turn on | `_OBSERVED_ID_KEYS = {provider_ref, idempotency_key}`; `VERIFIER_VERSION = "3"`; no new tool surface | 17 verifier unit tests (every check good/bad, the S01 key, fabrication, gold fields never harvested); DB-gated: every S01 dev/test bundle contains and harvests the key | verification only |
| **E** suite identity (infrastructure) | `suite_version` a literal in the runner, persisted only in gitignored JSON; scenario ids identical across suites so v2 rows silently joined v3 manifests; comparability marked by a hard-coded run-id set | "v2 artefacts remain identifiable; cross-suite subtraction rejected" is not satisfiable otherwise | `fis_platform/suite.py`, migration 006 (columns + v1/v2 backfill), runner guards, suite-aware `compare.py`, `--allow-cross-suite` refusal in six scripts, corpus digest + `corpus_v3.json`, reachability on both splits | `test_corpus_live.py` | none (bookkeeping) |

## 3. Release gates (all at or before the freeze commit `7764601`)

| gate | result |
|---|---|
| automated tests | **368 passed, 1 skipped** (opt-in live); v2 → v3: 202 → 368 (+69 scenario invariants, +32 polarity fixtures, +17 verifier, +5 DB-gated corpus, +2 reference sanity, revised pipeline tests) |
| reachability | test 96 cases 12/12 classes ceiling 1.000, 0 capped; dev 48 cases 12/12 ceiling 1.000, 0 capped |
| determinism | full regeneration twice under `make corpus`: per-split and overall digests identical (`make corpus-determinism` → DETERMINISTIC) |
| projection/live agreement | generation asserts id-set equality per scenario; `test_projection_matches_the_live_pipeline` compares rows (status, mapping_version, amount, reference, posted_at, posting order) for all 288 — identical; no ledger entry without a normalized-event cause (672 = 224 + 112 + 336) |
| scenario invariants | 88 over every corpus seed (posting multiplicity, background addressable, nothing post-dates the case, `received_at ≥ occurred_at`, single injected defect, injected refs precede background, key never discriminates, S08/S05 amounts vs balances, balances consistent, gold answer all-pass, wrong answers fail) |
| scorer/verifier fixtures | 38 polarity (incl. 4 persisted-hit replays) + 17 verifier + gold-leak boundary |
| frontier DEV sanity | `E4-v3-dev` 48/48 all-pass; no disagreement, no impossible scenario, no surprising class; suite unchanged afterwards (§ 4) |

## 4. DEV baselines (48 cases, `ORDER BY scenario_id`, design A; contract § 6)

Frontier = the sanity run `E4-v3-dev` (pre-registered: no suite change followed it).
Qwen session pid 586847; Nemotron restarted with unchanged flags and probed on a train
case (87.6–88.8 tok/s) right before its arm; each endpoint primed; nothing else on
8082/8083. Reproducibility gate Qwen A vs B: 47/47 output digests, 48/48 outcomes,
identical tokens and stop reasons — PASS.

| arm | run | model / quant / budget / prompt | all-pass | rc | act\|rc | evidence | verifier | unsup | forb | no-output | cap hits | wall p50 / p95 | TTFT p50 | out tokens (total / mean) | resource |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Qwen** (A) | `V3-qwen-dev` | Qwen3-8B Q4_K_M · 4096 · `cause_action_directed` | **17/48 = 35.4%** | 30 (62.5%) | 100% | 0.611 | 33 (68.8%) | 9 | 0 | 9 (schema) | 1 | 12.8 / 41.7 s | 0.5 s (probe) | 65 588 / 1 366 | 7.7 GB VRAM, RSS 8.7 GB, ~97 tok/s |
| Qwen (B) | `V3-qwen2-dev` | same session | 17/48 | 30 | 100% | 0.611 | 33 | 9 | 0 | 9 | 1 | 12.1 / 40.9 s | — | 65 588 | — |
| **Nemotron** | `V3-nemotron-dev` | Nemotron 3.5 Lightning 30B-A3B IQ4_XS · 8192 · `cause_action_directed` | **23/48 = 47.9%** | 31 (64.6%) | 100% | 0.675 | 36 (75.0%) | 0 | 0 | 12 (10 `length` + 2 schema) | 10 | 53.2 / 96.0 s | 2.2 s (probe) | 238 293 / 4 964 | ~8 GB VRAM beside Qwen (card 15.6/16.3 GB), RSS 13.0 GB, ~88 tok/s |
| **frontier** | `E4-v3-dev` | Claude Opus 5 via CLI 2.1.234 · CLI default · `baseline` | **48/48 = 100%** | 48 | 100% | 1.000 | 48 | 0 | 0 | 0 | 0 | 36.9 / 60.1 s | 9.4 s | 180 033 / 3 751 | $5.57 reference (input tokens under-reported: floor) |

Failure anatomy of the weak arms (all-pass is conjunctive): Qwen — 9 no-output
(pydantic schema: single-service corroboration or hedged fact), 9 unsupported claims
(fabricated ids: `ver_000000`, `proc_2000010_01`, field-name-prefixed ids), 9
evidence-only, 5 root-cause (S02→`duplicate_webhook_handled` ×2, S07→`reconciliation_gap`,
S08→`processor_decline`, S12→`kyc_hold` ×3 with evidence too, S11→`risk_hold`); Nemotron —
12 no-output (10 still in `<think>` at 8 192; all four S07 among them, as in R3b),
8 evidence-only, 5 root-cause (S02 ×1, S12 ×4 → `kyc_hold`), 0 unsupported. Neither
weak arm made a forbidden claim; neither has been tuned on any of this.

Per class (Qwen / Nemotron / frontier, of 4): S01 0/0/4 · S02 2/2/4 · S03 0/2/4 ·
S04 1/0/4 · S05 4/4/4 · S06 2/3/4 · S07 1/0/4 · S08 2/4/4 · S09 4/4/4 · S10 1/4/4 ·
S11 0/0/4 · S12 0/0/4.

## 5. Migration analysis (DEV, descriptive)

| pair | A both pass | B first pass / second fail | C first fail / second pass | D both fail |
|---|---|---|---|---|
| Qwen × Nemotron | 13 | 4 | 10 | 21 |
| Qwen × frontier | 17 | 0 | 31 | 0 |
| Nemotron × frontier | 23 | 0 | 25 | 0 |

- **Inversions (weak pass / strong fail): none** — the frontier passes every dev case,
  so no case rewards guessing over evidence and no harness review was triggered.
- **Qwen→Nemotron regressions (B = 4):** S02-2001001, S04-2003003, S06-2000005,
  S07-2000006 — every one a Nemotron `length` no-output (thinking budget vs contract),
  reviewed: not harness, not scenario.
- **Rescues (C = 10):** S02-2003001 (rc), S03 ×2 and S06-2001005, S10 ×3 (evidence
  completion), S06-2003005 and S08-2002007 (Qwen no-output), S08-2003007 (Qwen
  `processor_decline`), S10-2003009 (Qwen fabricated ids). Seven of the ten were Qwen
  *silent* failures.
- **Both fail (D = 21):** S01 ×4 (Qwen no-output ×4; Nemotron 2 no-output + 2 evidence),
  S11 ×4 (Qwen fabricates ids on every case; Nemotron 3 no-output + 1 evidence),
  S12 ×4 (both say `kyc_hold`), S07 ×3, S04 ×3, S03 ×2, S02 ×1.
- Silent (verifier-clean, wrong): Qwen 16, Nemotron 13 — 7 Qwen-silent cases pass
  under Nemotron, 7 stay silent, 2 become loud, 6 new silent (S01 ×2, S04 ×2, S11, S12).
- What the disagreements imply: the two weak arms fail on **different dimensions of
  the same classes** — Qwen on output shape and citation discipline (schema
  no-outputs, fabricated ids), Nemotron on finishing inside the budget (S07 never
  finishes) — while both share the same blind classes (S12 `compound_failure` read as
  `kyc_hold`, S01 duplicate handling, S11 false positive). Nemotron's +6 all-pass costs
  3.6× the output tokens and 4.2× the wall latency and a second model resident on the
  card. Nothing here selects a model; that is not this milestone.

## 6. R4 cascade baselines (replay of the unchanged `verifier` policy against `E4-v3-dev`)

| weak arm | cascade all-pass | weak acceptance | strong calls | rescue | unnecessary | routing FN | cost / attempt | cost / success | wall p50 | local out tokens |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen + R4 | **32/48 = 66.7%** | 33/48 (68.8%) | 15 (31.2%: 9 no-output, 6 unsupported) | 15/15 | 0 | 16 (33.3%) | $0.0405 | **$0.0608** | 16.7 s | 65 588 |
| Nemotron + R4 | **35/48 = 72.9%** | 36/48 (75.0%) | 12 (25.0%: all no-output) | 12/12 | 0 | 13 (27.1%) | $0.0330 | **$0.0453** | 54.7 s | 238 293 |
| strong-only | 48/48 | — | 48 | — | — | — | $0.1160 | $0.1160 | 37.2 s | — |
| oracle | 48/48 | 17 / 23 | 31 / 25 | — | — | — | $0.0788 / $0.0635 | — | — | — |

Every routing false negative is a verifier-clean answer wrong on evidence recall or
root cause (Qwen: 10 evidence, 6 rc/action; Nemotron: 8 evidence, 5 rc) — the gate's
blind spot is unchanged in kind from Suite v2. Escalations rescue 100% in both arms
and there are no unnecessary escalations.

## 7. TEST baselines (96 cases, exactly once per frozen arm, after tag `suite-v3`)

Run after tag `suite-v3` and after every DEV report; `make eval-v3-test` refuses to
start without the tag. Qwen in the same session as its DEV arm (pid 586847,
00:57–01:23 UTC); Nemotron restarted with unchanged flags and probed on a train case
(87.7–88.3 tok/s; pid 1045208, 01:24–03:05); frontier 03:06–04:15. `git_head` on the
Nemotron and frontier trajectories reads `2bbc0a1-dirty`: the working tree held
uncommitted *documentation* drafts at the time; `git diff suite-v3 -- . ':!docs'` is
empty, i.e. code and corpus identical to the tag. Cascade arms by replay of the
unchanged R4 `verifier` policy against `E4-v3-96`.

| arm | run | all-pass | rc | act\|rc | evidence | verifier | unsup | forb | no-output | cap hits | wall p50 / p95 | out tokens | cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Qwen 4096** | `V3-qwen-96` | **27/96 = 28.1%** | 68 (70.8%) | 100% | 0.628 | 74 (77.1%) | 12 | 0 | 13 (schema) | 1 | 12.9 / 33.8 s | 129 910 | $0 |
| **Nemotron 8192** | `V3-nemotron-96` | **48/96 = 50.0%** | 65 (67.7%) | 100% | 0.713 | 75 (78.1%) | 2 | 0 | 19 (15 `length` + 4 schema) | 15 | 55.8 / 94.1 s | 480 810 | $0 |
| **frontier** | `E4-v3-96` | **95/96 = 99.0%** | 96 (100%) | 99.0% | 1.000 | 96 | 0 | 0 | 0 | 0 | 37.6 / 61.0 s (TTFT p50 9.6 s) | 354 059 | $10.82 (floor) |
| **Qwen + R4** (replay) | — | **48/96 = 50.0%** | 85.4% | 100% | 0.806 | 100% | — | — | 0 | — | 15.4 s | 208 848 incl. strong | $0.0513 / success ($0.0256 / attempt) |
| **Nemotron + R4** (replay) | — | **69/96 = 71.9%** | 88.5% | 100% | 0.913 | 100% | — | — | 0 | — | 56.1 s | 565 884 incl. strong | $0.0380 / success ($0.0273 / attempt) |

Cascade routing on TEST: Qwen + R4 — 22 strong calls (22.9%: 13 no-output, 9
unsupported), rescue 21/22, unnecessary 0, routing false negatives **47/96 (49.0%)**;
Nemotron + R4 — 21 strong calls (21.9%: 19 no-output, 2 unsupported), rescue 21/21,
unnecessary 0, routing false negatives **26/96 (27.1%)**; strong-only $0.1139/success.

Pairwise (TEST): Qwen×Nemotron **A/B/C/D 21/6/27/42** — B: S03-3003002 (Nemotron
unsupported claim), S05-3001004 (Nemotron says `settlement_amount_mapping_error`),
S05-3005004 (evidence 0.50), S07-3003006/3005006 (`length`), S07-3006006 (unsupported
+ `reconciliation_gap`); C: 20 of 27 were Qwen silent evidence failures; D: S01 ×8,
S12 ×8, S11 ×6, S06 ×5, S07 ×5, S04 ×4, S10 ×3, S02/S03/S09 ×1. Qwen×frontier
27/0/68/1; Nemotron×frontier 48/0/47/1. **No inversion.** The single frontier failure,
S12-3002011, has the right root cause and 4/4 evidence but recommends
`replay_webhook` — the action the ontology keeps as a pure name-anchoring distractor
(sanctioned for no cause). Recorded; the rubric is not widened for it. Per class
(Qwen / Nemotron / frontier of 8): S01 0/0/8 · S02 4/7/8 · S03 2/6/8 · S04 1/4/8 ·
S05 7/6/8 · S06 0/3/8 · S07 3/0/8 · S08 4/8/8 · S09 6/7/8 · S10 0/5/8 · S11 0/2/8 ·
S12 0/0/7. Silent failures 47 (Qwen) vs 27 (Nemotron); every routing false negative
is verifier-clean and wrong on evidence recall or root cause. Nothing was tuned or
re-run after seeing TEST.

## 8. Suite v2 → v3 comparison (structural first)

**Which defects were removed.** Six classes no longer carry an unposted-settlement
signature that was S10's by definition; S08's declined amount now fits its balance and
S05's two balances agree; the scorer no longer counts a same-sentence refutation as an
assertion in either direction, nor drops sentence-initial cues, nor trims every window
by two characters; the verifier no longer calls a cited idempotency key a fabrication;
S11's ledger rows no longer wear a class-specific id shape; nothing in any world
post-dates its case; S07's deliveries arrive after their events; the injected event is
never the only unkeyed one.

**Which classes changed world/evidence semantics.** S01, S02, S05, S06, S07, S08 and
S11 (background posted, three more ledger entries and webhook trails per world; S06
shows `mapping_version 3` on the corrupted event and 4 elsewhere; S07's received times;
S05/S08 amounts and balances). S10's world is unchanged in kind but its gap is now the
*only* unposted settlement in the corpus, which is what the class was always meant to
mean. S03, S04, S09, S12: worlds unchanged in kind (all seeds regenerate byte-for-byte
except where background/keys touched them — S09 and S12 have no card activity and no
change at all beyond the suite label). Every class's rubric — root cause, required
evidence, actions, forbidden claims — is unchanged.

**Why raw score subtraction across suites is not a causal model measure.** The same
model on the same seed faces a different world in seven classes, is scored by a scorer
with a different (correct) polarity rule in every class, and is verified against a
larger observed-id set. A v3 − v2 difference for one arm mixes (a) the removal of
false failures the model never committed (verifier gap, scorer FP), (b) the removal
of defensible-but-wrong readings the v2 world invited (compound reading of S06,
insufficient-funds hedge on S08), and (c) genuinely different evidence to reason
over (more postings, more webhook trails). None of those is the model changing. The
Suite v3 baselines below are a **new reference point**; the migration story between
arms is told by the pairwise matrices *within* Suite v3 (§ 5), and any future arm is
compared to these v3 numbers, not to v2's.

**What the v2 numbers still tell you.** They remain the record of what each arm did
on the v2 corpus and are labelled `[v2]` in `make report`; every analysis script
refuses to pair a v2 run with a v3 run or with the v3 corpus unless told
`--allow-cross-suite`, and then prints the caveat above the numbers.

## 9. Known limitations (intentionally unfixed; contract § 9)

- Balances are static snapshots at case time; nothing derives them from entries.
- `add_failed_delivery` (S04, S12) remains the one hand-authored delivery path; the
  bus has no poison-message handling.
- The forbidden-claim scorer scans the whole serialised result, so a bare forbidden
  phrase in `hypotheses`/`uncertainties` without a cue counts, and hedged assertions
  count; scoring `facts[].claim` alone is deferred as a semantics change.
- The verifier checks `Fact.entity_ids` against observed ids, not the `<ref>` of a
  `tool://` source.
- The frontier CLI takes no token budget or seed and reports no runtime fingerprint;
  the runner's `max_tokens 4096` in its `runtime_context` is the runner default and is
  not passed; its input-token accounting under-reports (strong cost is a floor); the
  CLI auto-updated to 2.1.234 during this session (recorded).
- `_phase_two` follows the first six provider refs, so background webhook trails are
  only partly in the fixed-evidence bundle (unchanged from v2; the injected event
  always is).
- `evals/reports/<run>.json` holds only the cases of the invocation that wrote it
  (a `--resume` overwrites it with the remainder); `learning.*` is the record.
- Two Suite v2 forbidden hits (E4-v2-96 S08-3005007, E6-D-causes-dev S05-2003004)
  predate excerpt logging and cannot be replayed under the v3 rule.

## 10. What we are now optimising, and the one next milestone

**Dominant remaining bottleneck: silent-failure detection.** On TEST the unchanged R4
gate accepts 47 of 96 Qwen answers and 26 of 96 Nemotron answers that are
verifier-clean and wrong (evidence recall short, or the wrong label on S12/S01/S11);
it never escalates unnecessarily and rescues 21 of 22 / 21 of 21 of what it does
escalate. Weak-model capability is real too (root cause ~70% for both weak arms;
S12 `compound_failure`, S01 `duplicate_webhook_handled` and S11 `false_positive_alert`
are 0/8 for both), and Nemotron buys +21 TEST passes for 3.7× the tokens and 4.3× the
latency; but the largest gap between "what the system delivers" (50–72%) and "what
the pair could deliver" (99%) is the gate's blindness, not the frontier's reach.
Evidence/tool access and verifier coverage are not the constraint (frontier 99–100%
on the same bundles; verifier catches everything it is built to catch).

**Recommended next milestone — exactly one: R5, learned/classifier routing.** Train
and select on DEV a router over production-available features only (parse/verifier
signals, output length and structure, cited-id counts vs bundle size, class category
of the case, model confidence — never evidence recall or any gold field; the existing
`router_signals` gold guard and `test_routing_no_gold_leak` apply), pre-register the
selection rule in case counts (strong-call rate ceiling and unnecessary-escalation
budget), compare against the deterministic `verifier` policy and a transparent
baseline as the pivot guide requires, one TEST look. Not started here.

## 11. Errata (recorded after release; no number in a table changes)

- **§ 6 prose, Qwen DEV routing false negatives "10 evidence, 6 rc/action".** Under the
  exclusive bucketing R5 uses (root cause wrong → `root_cause`, whatever else also
  failed; root cause right and only evidence short → `evidence_only`), the same 16 cases
  split **7 root_cause / 9 evidence_only** (`scripts/r5_oracles.py --split dev`, section
  D; four of the seven root-cause misses also have short evidence). Nemotron's "8
  evidence, 5 rc" matches under both readings. The 16 / 13 totals, and every table cell,
  are unchanged. Related: § 4's Qwen anatomy "5 root-cause" then lists eight scenarios —
  seven silent root-cause misses plus S11-2003010, which is a verifier-visible
  unsupported-claim case, not a silent one. Recorded 2026-08-18 during R5.0.
