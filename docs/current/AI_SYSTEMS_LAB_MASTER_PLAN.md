# AI Systems Lab — Master Plan

> STATUS: CURRENT / NORMATIVE
> Current as of: 2026-08-21
> Supersedes: all prior program sequencing (the R6 report §11 "R7 next" recommendation is
> re-scoped by §3 below; the E0–E8 matrix, the FIS_MSI Pivot Guide sequence, and all
> pre-2026-08-20 next-step statements are historical).
> On conflict: this plan > `NEXT_STEP_M0.md` > `EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK.md` /
> `EXPERIMENT_CONTRACT_TEMPLATE.md` > `../HANDOFF.md` > historical plans.
> Historical **final reports** remain authoritative for the facts of their own
> experiments; they never override this plan's sequencing.

Evidence basis: `../research/2026-08-19_NVIDIA_AI_Lab_Playbook_Research.md` and
`../research/2026-08-20_AI_Lab_Methodology_Hardware_Strategy.md` (both adversarially
verified, the second re-derived against FIS's own trajectory store), reconciled against
the primary FIS record (HANDOFF, experiment-log, R5/R6/Suite-v3 reports and contracts,
R6 performance autopsy, provenance registry).

---

## 1. What we are building

Not "benchmark local models." The product of this lab is a **reusable company AI
systems methodology and platform**: the demonstrated ability to discover, for each
company task, which combination of *model, runtime, harness, context, tools, workflow,
verifier, routing policy, and (only when justified) training intervention* solves it
most reliably and economically — and to prove it with evidence a client can audit.

The target production topology (from the Canonical Architecture, unchanged):

```
small/local specialist  →  larger private/self-hosted model  →  frontier API / managed agent
```

with **evidence-driven routing** between tiers (the R4 deterministic verifier gate is
the incumbent pattern), **controlled promotion** (frozen evals, one-look discipline,
shadow/canary when a client system exists), and a learning plane that harvests
production failures back into evals, retrieval fixes, and — last on the ladder —
training data.

**FIS (the Fintech Integration Sandbox) is the realistic synthetic laboratory** in
which this methodology is being learned safely: 12 scenario classes, deterministic
ground truth, replayable corpus, fail-closed provenance. FIS is the means; the
transferable methodology is the end.

## 2. Where we are now

Completed foundation (facts that constrain future work; details in the linked records):

- **Suite v3** is the frozen benchmark: 288 scenarios (144 TRAIN / 48 DEV / 96 TEST),
  12 classes, deterministic generation (corpus digest pinned), deterministic scorer +
  verifier (v3), reachability ceilings measured per class, cross-suite comparison
  refused by tooling. `SUITE_V3_RELEASE_{CONTRACT,REPORT}.md`.
- **All-deterministic grading is vindicated** by the external literature (JudgeBench:
  LLM judges ≈ chance on objectively verifiable tasks). No LLM judge exists in FIS and
  none may be added without a κ-corrected, bias-audited, human-anchored protocol.
- **R3–R6 established the local-specialist landscape.** Current strongest local
  substrate: Qwen3.8-27B Q3_K_M (`qwen3.8-27b-q3_k_m@7f3b845b5638` on
  `llama.cpp-upstream-9b05354`), TEST 47/96 — competitive with Nemotron (48/96) but
  with **2 silent failures vs 27**, so the unchanged R4 cascade reaches **93/96 at 49%
  frontier utilization**. Its residual failure is a reasoning **budget** (8192-token
  cap; 47/49 TEST failures are truncations), not a behaviour gap — with a
  selection-effect caveat: the cases it finishes are the easier ones, so conversion at
  a larger cap is an upper bound, not a given. `R6_MODERN_LOCAL_SPECIALIST_REFRESH_REPORT.md`.
- **R5's learned-routing null is a standing lesson**: production-observable features
  mostly encode *which template the case is* (class-identity ceiling); nothing passed
  the leave-one-class-out gate. Learned routing stays shelved until a router beats the
  class-identity ceiling **under the leave-one-class-out protocol** on DEV — R5's
  secondary protocol already put routers above the ceiling on DEV and still returned a
  null, so that weaker condition does not unshelve; both local arms' TEST is spent for
  learned routing on Suite v3. The R4 deterministic gate — novel vs the published
  cascade literature (FrugalGPT/RouteLLM/AutoMix/Hybrid LLM are all learned gates) —
  remains the production pattern. `R5_LEARNED_ROUTING_REPORT.md`.
- **The R6 performance autopsy** measured: 24 h 03 m wall (≈24.1 h), 93.4% serial local decode, 41%
  (9h55m) cap-hit generation scoring zero; effective decode bandwidth 353–496 GB/s on
  the RTX 5080 Laptop; a chronic 8–12% WSL2 monotonic-clock skew affecting every
  published latency; one added inference node saves ~8.8 h on an R6-shaped milestone, a
  second adds 0.0 min. `R6_PERFORMANCE_AUTOPSY.md`.
- **Provenance discipline is ahead of available tooling**: hash-chained append-only
  registry, execution-system digests, fail-closed `--candidate` runner, contract
  frozen by git blob SHA (R6). Same-session-only reproducibility is *measured*
  (23/48 outcomes flip across a server restart) and enforced by rule.
- **13 harness/scenario defects** were found by three statistical detection mechanisms
  (reachability ceilings, weak-beats-strong inversions, cross-arm disagreement) — all
  requiring realism and breadth. This is the standing argument for FIS over any toy
  testbed, and the standing warning: check the ceiling before believing a low score.
- **Nothing is trained yet.** The evidence ladder has twice redirected effort away
  from training (E6: prompts fixed the diagnosis gap; R6: the budget, not the weights,
  is the constraint). The provenance schema cannot yet represent a self-produced model
  (`ModelArtifact` requires upstream repo/revision/URL), and no training code exists.

## 3. Methodology corrections after external research

Adjudicated against the two 2026-08 research reports. Every item below was accepted,
revised, or rejected **on the evidence cited in those reports**, not on recency.

**RETAINED (validated by external evidence)**
- Deterministic grading, frozen suites, pre-registration, one-look DEV/TEST, append-only
  logs, hash-chained provenance — several now shown *ahead of published practice*.
- The evaluate-first ladder (§5) — independently endorsed by NVIDIA's own 2026
  customization guidance ("build evaluation infrastructure first").
- The R4 deterministic cascade gate as the production routing pattern.
- Disjoint seed ranges + private corpus as leakage protection (GSM1k-consistent).
- FIS realism + class breadth over a smaller/faster generic testbed (Strategy B
  rejected; every realism-dependent discovery required FIS).

**REVISED**
- **R6's diagnosis**: not a missing stopping rule but a *decision-quality* failure —
  the TRAIN pilot detected the cap breach (15/36 vs ≤3/36 tolerance) and the contract's
  escape hatch said "proceed with truncation recorded" at no priced cost. Fix:
  **consequence-bearing tolerances** (every tolerance names ABORT / RECALIBRATE /
  PROCEED-WITH-DECLARED-CEILING + projected cost, enforced fail-closed in the runner).
- **Statistics**: cluster-robust inference over the 12 classes becomes primary.
  Measured on real R6 TEST data: paired-difference ICC 0.475 → design effect 4.33 →
  **effective N ≈ 22 pairs**. R6's +13.5pp headline (Qwen3.8 vs Bonsai) is *not
  significant* cluster-robustly. Suite v3 supports gross configuration gates,
  descriptive comparison, and certain-bound exclusion — **not significance claims
  between local arms**. Every contract now carries MDE + effective-N + INCONCLUSIVE.
- **Interim decisions**: deterministic **round-robin class ordering** replaces
  class-blocked execution order (5.4× more accurate prefixes; measurement-neutral).
- **Sequencing**: R7 is no longer automatic. **M0 (truncation diagnostic + telemetry
  floor + $4 rented-GPU benchmark) runs first** and decides R7's fate. See
  `NEXT_STEP_M0.md`.
- **The UD-Q3_K_XL withdrawal** was made below the pilot's own MDE (McNemar p≈0.22–0.48,
  on a cap-confounded metric) — the new **elimination rule** (no withdrawal below pilot
  MDE) corrects the class; UD re-enters selection in R7 if R7 runs.

**REJECTED**
- **Generic sequential stopping (SPRT / spending functions)** for FIS's structure:
  replayed on the four real pilot sequences, curtailed exact counting ("halt at the 4th
  tolerance violation") dominates; SPRT's α inflates ~2.2× under the measured class
  clustering. Certainty curtailment is adopted for *rigour and tail-risk only* — its
  measured value on real R6 data is 0.51 h of 24 h, never a speed story.
- **A separate generic minimal testbed** ("two-level lab" as a parallel system): the
  correct implementation is *inside FIS* — a SMOKE registry state (36 stratified cases,
  ledgered, cryptographically non-promotable) plus the decision rules above. A relaxed
  parallel lane would recreate the unrecorded execution path the fail-closed guards
  exist to forbid.
- **Buying hardware now** (any configuration): the second purchased GPU saves 0.0 min
  on the measured critical path; the market is in a documented memory-crunch bubble;
  lifetime demand is ~38 GPU-hours (≈$19 rented). Trigger-based policy in §8.
- **DGX Spark as a decode node**: 273 GB/s < the laptop's *achieved* 353–496 GB/s. It
  is a capacity tool; revisit conditions are pre-registered (§8).

**DEFERRED**
- Suite v4 — until the TEST-look-ledger trigger review, which is **due at the next
  TEST-consuming milestone**: 7 looks are already spent
  (`TEST_LOOK_LEDGER.md`) and R7's (or R9's) TEST look is #8, which requires the
  review first. Design rule fixed now: **add scenario classes before adding
  replications** (with ICC ≈ 0.4–0.6, power grows with the number of classes).
- H-series / D-series execution (§6), vLLM throughput profile, NeMo Platform /
  Evaluator SDK adoption (watch quarterly), any LLM judge, client-shaped second testbed.

## 4. The lab operating model (lifecycle)

Every substantive experiment moves through this lifecycle. Details and enforcement
live in `EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK.md`; contracts instantiate it via
`EXPERIMENT_CONTRACT_TEMPLATE.md`.

```
REQUIREMENT / CLAIM            what decision will this evidence drive?
  ↓
TRUSTWORTHY EVAL SUBSTRATE     frozen corpus + deterministic ground truth + measured
  ↓                            reachability ceilings (suite-versioned)
STATIC INTEGRITY GATES         full-corpus only, protected from subsetting:
  ↓                            reachability, gold answers, corpus determinism
SMOKE                          36 stratified cases, single arm, ledgered,
  ↓                            non-promotable — minutes-scale breakage detection
TRAIN SCREENING / CALIBRATION  class-balanced, round-robin; consequence-bearing
  ↓                            tolerances; elimination rule (≥ pilot MDE)
CONTRACT FREEZE                pre-registered rules, MDE + effective-N, prediction,
  ↓                            consequence clauses, arm placement, authoritative clocks
DEV (one look)                 qualification gates fixed in the contract
  ↓
TEST (one look, ledgered)      curtailment with guards; interval-only partial reporting
  ↓
PERFORMANCE / LOAD             AIPerf/NIM method, concurrency=1 tier-1 profile,
  ↓                            dual-clock telemetry
ECONOMICS / ROUTING            break-even (min offload = judge_cost/(strong−weak)),
  ↓                            pass^k reliability for stochastic arms
SHADOW / CANARY / PROMOTION    when a client system exists: manual mirroring, small
  ↓                            causal metric set (SRE restraint), human-gated
PRODUCTION EVIDENCE            failure harvesting into TRAIN (ML-Test-Score Monitor-7)
  ↓
SYSTEM FIX / RETRIEVAL / TRAINING / NEW EVAL   selected by the decision hierarchy (§5)
```

Stopping rules exist for **decision quality**, explicitly not speed (measured speed
value ~2–4%). A tolerance breach is always a *priced, chosen* decision, never a drift.

## 5. The decision hierarchy

Intervention selection follows evidence, in strict order — never train around broken
infrastructure or missing evidence:

1. **Infrastructure / tool correctness** (reachability, schema, harness defects)
2. **Evidence / retrieval / context** (can the right facts be reached at all?)
3. **Prompt / workflow / verifier** (E6 moved root-cause accuracy 18.8% → 65.6%)
4. **Routing / escalation** (R4 gate; escalate before you specialize)
5. **Fine-tuning** (own-trace data only; full-TEST forgetting gate)
6. **Larger model / architectural change**

This ladder has been enforced by evidence twice (E6 → no QLoRA; R6 → budget before
weights). It is the same ladder as the Canonical Architecture §9, kept deliberately.

## 6. Execution-surface roadmap (series reconciliation)

The program must eventually cover: local open inference (live), self-hosted/cloud open
inference (rented nodes, M0 onward), managed commercial APIs (live: frontier arm),
local subscription/OAuth coding-agent harnesses, cloud agent environments, and
dynamic/self-modifying harnesses (later, only where useful).

Four numbering series exist. Their relation, made explicit:

| Series | Scope | Status |
|---|---|---|
| **R-series** (R0–R6 done; R7/R8/R9 defined) | FIS specialist / routing / model science | Active — the main track |
| **M-series** (M0, M-STAT — new) | Methodology, diagnostics, telemetry; cheap, non-promotable, no TEST spend | Active — M0 is next |
| **E-series** (E0–E8, original MSI matrix) | Prompt/tool/context experiments | **Closed/absorbed**: E2/E4/E6/E6b done; E5→R4; E7→R8; E8→Discovery Controller (future); E3 demoted, revisit via §5 when evidence indicates |
| **H-series** (H0–H3) + **D-series** (D0–D5) | Harness/execution-surface science; developer-agent telemetry | **Deferred** — reference designs in `../reference/`; D0's telemetry-floor ideas are partially absorbed into M0 (dual clocks, lifecycle events, per-invocation stats) |

Disambiguation: `OVERNIGHT_STATUS.md`'s M1–M7 are *live-log session markers* for past
work, unrelated to program milestones M0/M-STAT.

The H/D tracks are not abandoned — they are the "execution-system science" half of the
lab and become active when the FIS track's evidence engine (post-M0/M-STAT) is stable
and a first client-shaped need for harness comparison exists. Their roadmap files are
reference designs, not commitments.

## 7. Statistical / experimental policy (summary — playbook is normative)

- **Splits**: TRAIN (iterate freely) / DEV (one look) / TEST (one look, ledgered).
  TEST looks are counted in the machine TEST-look ledger
  (`learning/registry/test_looks.jsonl`, landed by M-STAT; until then
  `TEST_LOOK_LEDGER.md` is the interim count of record, and thereafter its
  mechanically validated human-readable mirror — 7 historical looks backfilled);
  look #8 on Suite v3 requires the v4 trigger review.
- **pass^k on TEST** spends **one ledgered look** comprising k samples per case on a
  declared frozen subset; no selection decision may key off it (measurement only).
- **Screening**: class-balanced round-robin; ASHA-style rungs only class-balanced;
  screening ranks, never infers.
- **Tolerances**: every pre-registered tolerance is consequence-bearing
  (ABORT / RECALIBRATE / PROCEED-WITH-DECLARED-CEILING + projected cost), evaluated by
  curtailed exact counting, enforced fail-closed by the runner.
- **Elimination**: no candidate withdrawn on a margin below the pilot's own MDE.
- **Inference**: cluster-robust over 12 classes primary; McNemar exact secondary
  (labeled anti-conservative); per-experiment cluster-corrected MDE + effective N in
  every contract; **INCONCLUSIVE is a legitimate verdict** — a null below MDE is never
  read as equivalence.
- **Curtailment** (DEV/TEST): certainty curtailment only, with three guards — spend
  semantics (split spent at first executed case), interval-only partial reporting,
  paired-comparison firewall (curtailed arms never enter paired comparisons).
- **Stochastic arms**: pass^k (k=3–5) for reliability claims (frontier arm first, R9).
- **Reproducibility**: same-session single-slot rule for local case-level comparisons;
  deterministic graders always; suite refresh only by versioned release with cross-suite
  refusal; full-corpus static gates never subset.
- **Prediction ledger**: each contract records a pre-run effect estimate + interval;
  predicted-vs-actual is scored on completion.
- **Leakage**: disjoint seeds, private corpus, canary GUIDs in TEST content
  (mechanism: M-STAT; activation: next versioned suite release — never a mutation
  of a frozen suite).

## 8. Hardware / compute policy

Owned: RTX 5080 Laptop 16 GB (tier-1 node; measured 353–496 GB/s effective decode;
watch the live llama.cpp sm_120 bugs — CUDA-graph hang workaround
`GGML_CUDA_DISABLE_GRAPHS=1`). Ports/infra per `../architecture.md`.

Policy (adopted from the adversarially-corrected hardware study; §3.5 there):
- **Rent, don't buy, now.** Second node per multi-arm milestone (~$5–12, Secure-tier
  3090/A6000 class; captures the full measured 8.8 h overlap saving) with
  pre-registered cross-node arm placement. Training jobs rented ($5–30 each).
- **The $4 benchmark first** (in M0): pinned artifact + pinned build on rented 3090 and
  5090 — measures the only number the purchase decision turns on.
- **GPU-hours/month ledger** starts with M0. **Purchase trigger** (pre-committed):
  3 consecutive months > ~$150/mo rented spend, or a committed always-on client
  serving tier. On trigger: **one** benchmark-chosen GPU (default used 3090) on a
  minimal native-Linux host (~$2,050–2,700), with a thermal/decode acceptance test
  before it becomes an execution system.
- **Bandwidth lever** (only compresses the dominant chain): 5090-class, post-R7 and
  post-bubble — buy at ≤~$2.5K street or rent at $0.99/hr; never at ~$4,900 mid-crunch.
- **DGX Spark** becomes correct only under the pre-registered conditions (any two of:
  capacity-bound MoE/agent residency; single-box CUDA 70B QLoRA/long-context need;
  price ≤~$3.5K; power/acoustics dominate; client targets Spark). Track quarterly.
- **Capacity** (48 GB pooling / 128 GB) and cloud training: rent per session until the
  ledger proves sustained demand. **Re-verify all prices at order time** — the 2026
  memory crunch makes every recorded price a floor with weeks of shelf life.
- WSL2 clock skew (8–12%) stands until dual-clock telemetry lands (M0); a purchased
  node would run native Linux, retiring the skew for that node.

## 9. Fine-tuning roadmap

**Why training has not started**: the ladder (§5) has not reached it. Prompt/workflow
changes and the budget question have owned every gap so far; `ModelArtifact` cannot
represent a self-produced weight file; no training code exists. This is a success of
the methodology, not a delay.

**Evidence bar to start R8**: R7 and R9 complete, and a residual, class-identified gap
remains that SFT can plausibly close on the favoured substrate (per R6 §11: Qwen3.8-27B
Q3_K_M if specialization is revisited; Nemotron-tier specialization returns as the live
alternative if M0 shows extra reasoning budget does not rescue — low `f_rescue`,
wrong-complete-dominant, or degenerate truncations).

**Sequence** (the rig may be built any time after M-STAT — it de-risks the pipeline,
not the model; **R8 itself waits for the evidence bar**):
1. **FT pipeline rig** (the one legitimately separate, throwaway artifact): smallest
   viable base, ~200 synthetic examples, LoRA → merge → GGUF → quantize → serve →
   12-case eval, <30 min end-to-end. Purpose: de-risk the *pipeline*, not the model.
   Uses the `TrainedArtifact` provenance record **that M-STAT adds** (dataset digest,
   base artifact id, hyperparameters, seed, adapter SHA, pipeline digests). Deleted
   once boring.
2. **R8 QLoRA pilot** on the 9B/Nemotron tier: minimum-n as an ablation (50/150/450),
   staged SMOKE→DEV→TEST, **full-TEST forgetting gate** (never just the target slice).
   QLoRA floors: 9–14B fits the laptop; 27B needs 24 GB+; 70B rented.

**Hard constraint (verified against Anthropic's live terms)**: training data is
**own-trace only** — local-model trajectories scored against FIS's own ground truth.
Frontier (Claude) outputs are never SFT targets without prior authorization.
Using Claude to *evaluate* is unaffected.

## 10. Milestones (next 3–6)

Execution is conditional — later milestones run only if their gate opens.
**Milestone transitions after M0 require the scientific owner's acceptance of the
prior milestone's report; `NEXT_STEP_M0.md` §11's STOP governs post-M0 continuation
notwithstanding this plan's precedence order.** No agent self-assesses a GO.

| # | Milestone | Question | Why now | Prereqs | Cost class | Go/No-Go | Unlocks |
|---|---|---|---|---|---|---|---|
| **M0** | Truncation diagnostic + telemetry floor + $4 GPU benchmark | Does extra reasoning budget produce **useful task rescue** (`f_rescue`: deterministic passes among contemporaneously reconfirmed 8192 cap-hits, same-session paired control) — or only longer completed outputs? What caps fit the 5080? What is real rented 3090/5090 decode? | Decides R7's fate for ~a day + ~$4; autopsy's top telemetry fixes land before any long run | none | ~1 day, 30 paired TRAIN generations (15 verified cap-hit cases × 2 arms), no DEV/TEST | Precedence: `n_control_reconfirmed` < 10 → INCONCLUSIVE/re-scope regardless of `f_rescue` (never DROP); else `f_rescue` ≥ ~30% → R7 GO; ~10–30% or high-completion/low-rescue → re-scope; < ~10% → R7 dropped, R9 up (bands: `NEXT_STEP_M0.md` §7 — completion alone never produces GO) | R7 decision, hardware benchmark number, GPU-hours ledger |
| **M-STAT** | Methodology enforcement in code + registry | Do the corrected rules bind the runner, not just the docs? | The docs half ships with this plan (playbook + template); code half must exist before the next contract freeze | this plan | ~1 day code, no inference | All guards fail-closed + tests green | Every future experiment runs under template v2 |
| **R7** | Reasoning-budget calibration (re-scoped by M0) | How much truncation converts at caps >8192; does UD-Q3_K_XL become the better operating point? | Only if M0 preserves the conversion hypothesis | M0 GO, M-STAT, **Suite-v4 trigger review (R7's TEST is look #8)** | 1–2 days incl. rented second node ~$10; honest wall estimate 18–22 h at cap 12288 | Converts, prices, or closes the budget question | Specialist tier settled; UD re-decision; hardware Stage-3 input |
| **R9** | Routing economics + frontier reliability | Break-even (judge_cost/(strong−weak)) on FIS's own cascade; frontier pass^k (k=3–5) on a TEST subset | Cascade claims are single-look artifacts until qualified | M-STAT (pass^k protocol, §7); **its TEST exposure is a ledgered look — trigger review if it is look #8** | ~1 day, mostly frontier calls | — (measurement, not gate) | Client-sellable reliability + economics claims |
| **FT-rig** | Throwaway fine-tuning pipeline | Does the LoRA→GGUF→serve→eval loop work end-to-end with provenance? | Must exist before any R8; independent of R7/R9 outcomes | M-STAT (`TrainedArtifact`) | ~1 day, $0–5 rented | <30 min end-to-end, provenance record complete | R8 becomes possible |
| **R8** | QLoRA specialization pilot (conditional) | Does own-trace SFT close a residual class-identified gap without forgetting? | Only if R7/R9 leave a gap SFT can close | FT-rig + evidence bar (§9) | rig + $5–30/job rented | Full-TEST forgetting gate + cluster-robust gain | The training rung of the ladder, demonstrated |

Suite v4 is *triggered* work (TEST-look ledger), not a scheduled milestone. Hardware
purchase is *triggered* (§8), not scheduled.

## 11. Definition of done ("ready to transfer to a client")

The lab is done enough to sell when every row below has been exercised at least once
inside FIS **and** exists as a written, reusable procedure:

| Capability | Status 2026-08-20 |
|---|---|
| Task-specific trustworthy eval creation (ceilings, versioning, leakage guards) | **Done** (Suite v1→v3) |
| Local specialist selection under provenance + frozen contracts | **Done** (R6 method) |
| Reasoning-budget calibration as a procedure | M0/R7 |
| Frontier escalation with a deterministic gate | **Done** (R4; reliability qualification pending R9) |
| Measured routing economics (break-even, pass^k) | R9 |
| Self-hosted/rented tier operation (cross-node arms, pinned artifacts) | M0 onward |
| Training intervention when justified (rig, own-trace SFT, forgetting gate) | FT-rig/R8 |
| Serving characterization (AIPerf method, dual clocks, operating points) | Partial (autopsy); M0 telemetry + adoption |
| Shadow/canary promotion process | Doctrine written; exercised at first client system |
| Production failure harvesting into evals/training | Designed-in; exercised at first client system |
| Reproducible lineage end-to-end (incl. trained artifacts) | Done for downloads; `TrainedArtifact` pending |
| Publishable credibility artifacts | 3 identified (deterministic-gate cascade; class-identity ceiling; transport-serialization defect) — write-ups pending |

When the table is green (client-dependent rows may be green-by-doctrine), the next
engagement starts from procedure, not from research.
