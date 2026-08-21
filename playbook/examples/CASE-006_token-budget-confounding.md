# CASE-006: Token-Budget Confounding in a Model Comparison

> Real empirical case from the FIS project (Fintech Integration Sandbox), a
> realistic synthetic fintech-operations laboratory used to develop this
> playbook's methodology.

**Source ID:** INT-CASE-006 · **Date:** 2026-08-17 · **Cited by:**
[04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md) ·
[05. Model, Runtime, and Harness Selection](../05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md) ·
[07. Optimization and Intervention Ladder](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md)

## Situation

Experiment R3 tested whether a candidate model (Nemotron 3.5 Lightning
IQ4_XS) should replace the incumbent weak-tier model (Qwen3-8B Q4_K_M) in a
deterministic verifier cascade. The comparison ran on the dev split (n = 48)
under the project's then-frozen decoding configuration — `max_tokens 4096`
— with everything else held fixed: same prompt (`cause_action_directed`),
same evidence plan, same schema/grammar path, same scorer, greedy decoding,
seed 42. A same-session, zero-drift control (Qwen A → Nemotron → Qwen B, one
model-server process) confirmed A and B were byte-identical, so any
difference between arms was attributable to the model swap alone — or so the
design assumed.

## Decision faced

Whether to adopt Nemotron as the new weak-tier model, under a five-criterion
gate rule pre-registered *before* the R3 run (`OVERNIGHT_STATUS.md` §M3.5):
(1) all-pass improvement ≥ 5 cases, (2) silent-failure reduction ≥ 5 cases,
(3) regressions ≤ 3 cases, (4) p50 latency ≤ 30s, (5) favorable cascade
economics. The frozen `max_tokens 4096` cap was treated as a fixed property
of the harness, not as a variable the comparison itself needed to isolate.

## Evidence

R3 result (dev, n = 48, cap 4096; `experiment-log.md`, R3 entry):

| | Qwen (incumbent) | Nemotron (candidate) |
|---|---|---|
| strict all-pass | 14 (29.2%) | 12 (25.0%) |
| no-output | 5 (schema only) | 31 (29 length-cap + 2 schema) |
| silent (verifier-clean, wrong) | 23 | **4** |
| R4 cascade all-pass / escalation | 45.8% at 22.9%, $0.0545/success | 89.6% at 66.7%, $0.0868/success |

Migration matrix A/B/C/D = 4/10/8/26 — and the report is explicit about the
regressions: *"All 10 regressions are the 4,096-token cap hit inside
`<think>`."* Under the pre-registered gate, criteria 1, 3, 4, and 5 failed
and only criterion 2 (silent-failure reduction) passed; the verdict was
correctly "Nemotron does not qualify; Qwen stays incumbent" — but the report
flagged its own result as unsafe to read as a model-quality finding: *"The
one confound to resolve before the model comparison is meaningful is the
token budget."* Nemotron's apparent ~80% reduction in silent (confidently
wrong) answers — the raw silent-failure (verifier-clean, wrong) count fell
from 23 to 4, per the table above — was the number driving that instinct to
adopt it anyway; it was also the number about to be shown to be mostly an
artifact. (A related but distinct measure, the routing-false-negative
subset — silent failures that were also strong-reference passes — fell from
22 to 4 over the same comparison; the two counts move together but are not
the same metric.)

## What happened

R3b re-ran the identical comparison one factor changed: `max_tokens` 4096 →
8192, applied to **both** arms, in the same paired-session design (Qwen A →
Nemotron → Qwen B). The zero-drift control held again (Nemotron reproduced
R3's 19 completed cases byte-for-byte; a same-session Qwen diagnostic at
4096 after the 8192 run showed the budget was inert for Qwen except on one
case). Result (dev, n = 48, cap 8192; `experiment-log.md`, R3b entry):

| | Qwen 8192 | Nemotron 8192 | Nemotron 4096 (R3, for reference) |
|---|---|---|---|
| strict all-pass | 15 (31.2%) | **18 (37.5%)** | 12 |
| no-output | 0 | 9 | 31 |
| silent (verifier-clean, wrong) | 21 | **16** | 4 |
| output tokens (sum) | 62,673 | 239,961 | 172,436 |

Two things happened at once, and they point in opposite directions on the
headline metric. First, the raw model-quality ranking **reversed**: Qwen
led by 2 all-pass at cap 4096; Nemotron led by 3 at cap 8192. Second,
Nemotron's silent-failure advantage — the number that had looked like an
~80% reduction — shrank to a 24% reduction (21 → 16) once both arms had
enough budget to finish: *"not the −80% of R3: the earlier advantage was
mostly unfinished reasoning counted as loud."* Replaying R3's own 29
length-capped Nemotron cases at the larger budget resolved them as 6
RECOVERED_PASS, 14 RECOVERED_FAIL (12 of them silent), and 9
STILL_LENGTH_CAPPED even at 8192 — so the cap had been manufacturing both
the apparent "candidate is worse" signal (unfinished cases scored as
failures) and roughly a fifth of the apparent "candidate is a much safer
answerer" signal (unfinished reasoning that would have been silently wrong
was instead visibly incomplete).

Even with the confound removed, Nemotron still did **not** qualify: the
pre-registered R3b gate failed on completion rate (39/48 complete against a
43-case threshold), on residual silent failures (16 against a tolerance of
6), and on migration-cell size (6 candidate-only regressions against a
tolerance of 5) — despite passing on raw pass count, cost, and latency. Qwen
remained the incumbent under R3b too, but for reasons that had nothing to
do with the cap: *"The 4,096-token limit was why R3 looked the way it did,
not why Nemotron does not qualify... it still cannot finish 9 cases in 8,192
tokens."* The budget question was closed by running one factor twice in a
paired design; the model-selection question was answered separately, by the
gate, on the corrected numbers.

## The generic lesson

**Portable rule: a shared generation/reasoning budget is not a neutral
harness setting when candidates differ in verbosity or reasoning style — it
is a variable that must itself be calibrated or isolated before a
model-comparison claim is trusted.** A cap that is comfortable for a terse
model and tight for a verbose one converts a capacity/budget effect
(canonical failure class [RC-8](../GLOSSARY.md#canonical-failure-taxonomy),
capacity/budget exhaustion) into what looks like a capability or
reliability difference between models — in either direction: it can make a
verbose-but-capable candidate look unreliable (unfinished answers scored as
failures) or make it look deceptively safe (unfinished reasoning scored as
"not yet wrong" instead of wrong). The decoding budget is part of the
[execution system](../GLOSSARY.md#execution-system) exactly as much as the
model weights are, and a [comparability claim](../GLOSSARY.md#comparability-claim)
between two arms is only valid once every factor but the one under test is
pinned identically — the [paired design](../GLOSSARY.md#paired-design)
R3→R3b used (one factor changed, both arms, same session, same case order)
is the pattern that isolates it correctly. This is also why chapter 07's
[intervention ladder](../GLOSSARY.md#intervention-ladder) places
generation/reasoning-budget calibration (rung 5) as its own rung, separate
from model/runtime selection: a budget confound has to be resolved before a
model-comparison result at any other rung can be believed, in either
direction.

## What would NOT have worked

Reading the R3 result at face value — "Nemotron cuts silent failures by
~80%, adopt it" — would have adopted a candidate largely for an artifact of
its cap hits, not its answer quality. Reading it the other way — "Nemotron
loses on all-pass and floods the cascade with escalations, reject it" —
would have rejected it for the same unexamined reason. Both readings were
available from the R3 table alone; neither was safe until the budget was
isolated.

Raising the cap for only the candidate (giving Nemotron room to finish
while leaving Qwen at 4096) would not have produced a valid comparison
either — that swaps a confound for a second, deliberately introduced one,
and stops being a model comparison at all. R3b's design changed
`max_tokens` for **both** arms in the same paired session specifically to
avoid this.

Concluding from R3b alone that "the budget question is closed and Nemotron
wins" would also have been wrong. Even with matched budgets and a genuine
+3 all-pass lead, Nemotron still failed the pre-registered qualification
gate on completion rate and residual silent failures, and still could not
finish 9 of 48 cases at 8192 tokens — at 3.8× the generated tokens and 4.5×
the latency of the incumbent. The raw pass-count reversal was informative;
it was the pre-registered gate, not the reversal, that decided adoption.

## References

- [NV-EVALSDK-001] NeMo Evaluator SDK `compare`/`gate` tooling — the
  published analog of this case's core requirement: paired comparison
  tooling that refuses cross-arm comparison once a configuration factor
  (there, the prompt template) differs between arms.
- Governing chapters: [04](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md),
  [05](../05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md),
  [07](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md).
- Glossary: [execution system](../GLOSSARY.md#execution-system),
  [comparability claim](../GLOSSARY.md#comparability-claim),
  [paired design](../GLOSSARY.md#paired-design),
  [canonical failure taxonomy](../GLOSSARY.md#canonical-failure-taxonomy),
  [intervention ladder](../GLOSSARY.md#intervention-ladder).
