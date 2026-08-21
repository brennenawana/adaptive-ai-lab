# CASE-012: Restart Instability and the Move to Paired Controls

> Real empirical case from the FIS project (Fintech Integration Sandbox), a
> realistic synthetic fintech-operations laboratory used to develop this
> playbook's methodology.

**Source ID:** INT-CASE-012 · **Date:** 2026-08-16 to 2026-08-17 · **Cited by:**
[02. Execution System Model](../02_EXECUTION_SYSTEM_MODEL.md) ·
[04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md)

## Situation

The project's local specialist model was served with what looked like a fully
deterministic configuration — greedy decoding (`temperature 0`), a fixed seed
(`seed 42`), a pinned model checkpoint, and a pinned inference-engine build. Local
runs recorded at different points in the project's history, sometimes hours or days
apart across separate launches of the model-server process, had been treated as
comparable on a case-by-case basis — an assumption baked into how prompt-variant and
routing decisions were being read.

## Decision faced

Whether "greedy decoding + fixed seed" was sufficient grounds to compare two local
runs' outcomes case by case regardless of when each was recorded, or whether the
[reproducibility boundary](../GLOSSARY.md#reproducibility-boundary) needed to be
measured explicitly before any causal claim crossing two runs could be trusted.

## Evidence

Two independent measurements, a day apart, isolated session identity (server-process
restart) as a factor while holding prompt bytes, model, decoding parameters, and (in
the second measurement) the generation-length budget fixed.

**Measurement 1 (2026-08-16, experiment R1).** Within one server session, run
back-to-back with the same case order: `R1-direct-dev` vs `R1-direct2-dev`.
Within-session reproducibility was near-total: 47/48 exact output-digest matches
(the one difference was the first case in run order, whose prompt-cache predecessor
differed between the two runs), 48/48 identical scored outcomes, 47/48 identical
token counts, and aggregates identical to the digit (all-pass 14, root cause 31,
verifier 37, evidence recall 0.606, no-output 5 — on both runs).

Then, across a restart: the historical run `E6-C-directed-dev` (an earlier server
process, same day) vs `R1-direct-dev` (a new server process). Input tokens were
identical 48/48 (the prompt bytes sent were unchanged — confirmed by a dedicated
byte-identity test on the request body), but output tokens differed on all 48 cases,
and **23 of 48 scored outcomes (47.9%) flipped** — all-pass 17 vs 14, evidence recall
70.8% vs 60.6%, verifier-pass 40 vs 37.

**Measurement 2 (2026-08-17, experiment R3b) — replication at a different decoding
budget.** Within one server session (`R3b` Qwen control A vs control B, back-to-back,
same case order): 47/48 digest matches (again the first-case predecessor effect),
48/48 identical outcomes, aggregates identical (all-pass 15, root cause 30, evidence
recall 0.648, verifier 36 — on both). Across sessions, holding the generation-length
budget fixed at the same value on both sides (`R3` Qwen run, session A, vs a same-day
same-budget re-run `R3b-qwen4096-dev` in a new session): **0/48 digest matches, and
only 24/48 (50.0%) scored outcomes agreed** — essentially a coin flip on outcome
identity, from a configuration whose contract (model, quantization, decoding
parameters, prompt, schema, scorer) was otherwise byte-identical.

## What happened

The two measurements agreed: within a single server session, the local arm was
reproducible to within one case's worth of prompt-cache-predecessor noise (47–48 out
of 48 digests, 48/48 scored outcomes). Across a server restart — a new process,
nothing else about the request or the model changed — roughly **half of all
case-level outcomes changed**, on two separate occasions a day apart (23/48 flipped
in the first measurement; 24/48 failed to match — an equivalent flip rate — in the
second), even though the aggregate all-pass rate moved by only a few points each time
(17 vs 14 in the first measurement). The instability was invisible at
the aggregate level and large at the case level: a comparison that trusted
case-by-case matching across a restart was, in the project's own words, "of the same
order as [the] cross-session noise" as the effect it was trying to measure. One
specific consequence was flagged directly: a prompt-variant selection made earlier in
the project, on a margin of about 5 evidence-recall points, was retrospectively of
the same magnitude as this now-measured session-to-session noise floor — the
selection's test-split confirmation was unaffected in its conclusion, but the margin
that had been used to read the dev-split comparison was no longer trustworthy on its
own terms.

No configuration bug was found or fixed — restart-to-restart output variance under
greedy decoding on this inference stack is a property of the runtime (consistent
with the mechanism described in the external nondeterminism literature below), not
an application defect to patch. The response was procedural: every trajectory record
was made to carry a `runtime_fingerprint` (build identity) and a session identifier
(process id, start time) so that same-session membership could be verified after the
fact, not assumed; and case-level comparisons between local runs were restricted to
being made **within one server session and one request order** going forward. Where
a causal claim needed to cross an intervention (a prompt change, a routing hop, a
budget change), the two arms were run back-to-back in the same session with order
pre-registered — a contemporaneous paired control — rather than compared against a
historical run from a different process.

## The generic lesson

**Portable rule: a [reproducibility boundary](../GLOSSARY.md#reproducibility-boundary)
— the envelope within which repeated runs actually agree (same session? across
restarts? across hosts? under concurrency?) — MUST be measured, never assumed from a
configuration's stated determinism (a fixed seed, `temperature 0`) alone.** Two
runs with byte-identical inputs and a nominally deterministic decoding
configuration can disagree on roughly half their case-level outcomes purely because
they were served by two different process launches. Once that boundary is measured,
every comparability claim must be scoped to it: same-session, same-order comparisons
are trustworthy at the case level; cross-session comparisons are not, and any
[causal claim](../GLOSSARY.md#comparability-claim) that would otherwise cross the
boundary requires a [contemporaneous paired control](../GLOSSARY.md#contemporaneous-paired-control)
— both arms in the same session/window, order pre-registered and counterbalanced —
or the claim must be explicitly declared unavailable and the comparison relabeled
descriptive. This is why chapter 02 defines the execution system to include
session/runtime identity as a first-class, hashable component, and why chapter 04
requires a measured reproducibility probe before any experiment contract treats
historical and freshly run arms as interchangeable.

External corroboration: independent nondeterminism research on GPU inference finds
the dominant mechanism for exactly this kind of restart-to-restart divergence to be
reduction-order sensitivity that varies with GPU/runtime state — present even with no
concurrency and a fixed seed — rather than batching effects alone [EXT-DETERM-001].
That literature's own recommended mitigation (deterministic/batch-invariant kernels)
is shipped by major inference engines only as an opt-in, throughput-costly beta; the
project's same-session, single-slot discipline is the standard-shaped operational
answer available without adopting that beta path, and it targets the dominant
variance source directly at the level that matters for decisions — the outcome, not
the bit pattern.

## What would NOT have worked

Trusting "greedy decoding + fixed seed" as sufficient for cross-session, case-level
reproducibility would not have worked — it is the assumption this case directly
falsifies, twice, a day apart — both times at the same 4,096-token decoding budget,
deliberately held fixed the second time specifically to isolate the session effect
from the (separately confirmed) budget factor. Comparing historical
runs across restarts and reading the resulting deltas as caused by whatever changed
between them (a prompt variant, a routing hop) would also not have worked without a
same-session control: the measured session-to-session noise (23–24 outcomes per 48,
essentially the same order of magnitude as several of the project's early decision
margins) is large enough to manufacture or mask an apparent effect on its own.
Averaging over more historical runs would not fix this either, since the noise is a
property of *which session* produced a case's answer, not simple sampling variance
that shrinks with more runs drawn the same confounded way.

## References

- [EXT-DETERM-001] Thinking Machines ("Defeating Nondeterminism"); arXiv:2506.09501;
  vLLM and SGLang batch-invariance documentation; llama.cpp maintainer discussion —
  reduction-order/GPU-state variance as the dominant nondeterminism mechanism at
  `temperature 0`, independent of concurrency.
- Governing chapters: [02](../02_EXECUTION_SYSTEM_MODEL.md),
  [04](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md).
- Glossary: [reproducibility boundary](../GLOSSARY.md#reproducibility-boundary),
  [contemporaneous paired control](../GLOSSARY.md#contemporaneous-paired-control),
  [comparability claim](../GLOSSARY.md#comparability-claim),
  [frozen identity](../GLOSSARY.md#frozen-identity),
  [dual-clock telemetry](../GLOSSARY.md#dual-clock-telemetry).
