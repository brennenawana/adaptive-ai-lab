# SCENARIO-12: Restart Instability and the Move to Paired Controls

> [Index](../README.md) · [Examples](README.md)

**An invented scenario.** The project is fictional; the lesson and the reasoning are the
part to take seriously.
**Illustrates:** [02. Execution System Model](../02_EXECUTION_SYSTEM_MODEL.md) ·
[04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md)

---

## Situation

Greedy decoding, `temperature 0`. A fixed seed. A pinned set of weights, a pinned build
of the inference engine. One request at a time, no concurrent traffic. Every line of that
list was true here — and that list is the entire case for believing two runs of the same
items will produce the same answers.

The items are support tickets, and the model sorting them belongs to a university's IT
help desk. It reads the requester's message plus their account and device records,
assigns one of five queues — accounts and access, network, managed devices, teaching-room
AV, security — and flags the lines of the record that support its choice. The evaluation
suite is 48 tickets, each with a known correct queue.

Given a configuration that deterministic, the team had been treating any two runs as
comparable ticket by ticket, no matter when each was recorded — last Tuesday's run against
this morning's, across however many times the model server had been stopped and started in
between. Prompt-variant choices and routing decisions were being read off exactly that kind
of comparison.

## Decision faced

Is "greedy decoding plus a fixed seed" enough to compare two runs ticket by ticket,
whenever each was produced? Or does the envelope within which runs actually agree — the
[reproducibility boundary](../GLOSSARY.md#reproducibility-boundary) — have to be
measured before any claim is allowed to cross it?

The boundary is cheap to measure, so they measured it.

## Evidence

Three measurements, isolating one thing at a time. Prompt bytes, model, decoding
parameters and (from the second measurement on) the generation budget were all held
fixed. The only thing that moved was which process, or which machine, produced the
answer.

**Measurement 1 — within one session, then across a restart.** First, the same 48
tickets were run twice back to back inside a single server session, same order. The
result is what everyone expects from a fixed seed:

- 47 of 48 outputs matched exactly, byte for byte. The one that did not was the first
  ticket in run order, whose cache predecessor differed between the two passes.
- 48 of 48 scored outcomes were identical.
- 47 of 48 output token counts were identical.
- Every aggregate matched to the digit: correct queue 31, supporting lines cited 37,
  both right 14 — on both runs.

Then the same 48 tickets were compared against a run from earlier that morning, made by
a different launch of the same server, on the same machine, with nothing else changed.
A dedicated byte-identity test confirmed the request bodies sent were identical on all
48. And:

- Output token counts differed on **all 48** tickets.
- **23 of 48 scored outcomes (47.9%) flipped.**
- Aggregates moved a little: both right 17 versus 14, correct queue 33 versus 31,
  supporting lines cited 40 versus 37.

**Measurement 2 — the same test again, a day later, at a different generation budget.**
Within one session, back to back, same order: 47 of 48 exact matches (the same
first-ticket effect), 48 of 48 identical outcomes, identical aggregates on both runs
(both right 15, correct queue 30, lines cited 36). Across two sessions, with the
generation budget deliberately pinned to the same value on both sides so that the
budget could not be blamed: **0 of 48 outputs matched byte for byte, and only 24 of 48
outcomes (50.0%) agreed.** A coin flip, from a configuration that was otherwise
identical down to the request bytes.

**Measurement 3 — a second machine.** The same pinned weights and pinned engine build,
the same 48 tickets, on a second host of the same class: **21 of 48 outcomes (43.8%)
agreed** — no better than a restart on the original machine.

## What happened

The measurements agreed with each other, which is what makes them usable. Inside a
single server session, the system was reproducible to within one ticket's worth of
cache-predecessor noise, on two separate days. Across a restart — a new process, nothing
else about the request or the model changed — **about half of all ticket-level outcomes
changed**: 47.9% on the first measurement, 50.0% on the repeat a day later. Moving to a
second machine changed 43.8%, which is the same picture rather than a worse one. The
boundary is the session, and crossing it by any route costs roughly the same.

Notice what this looked like from the aggregate view: the headline pass rate moved by
about three tickets out of 48, which anyone would have shrugged at. Underneath that calm
surface, half the individual answers were different. The instability was nearly
invisible in the summary and enormous at the ticket level.

One consequence landed immediately. A prompt-variant choice made earlier in the project
had rested on a margin of about five points on the citation metric, read off a
comparison between two runs from different sessions. That margin was the same size as
the session-to-session noise this exercise had just measured. The later confirmation on
the held-out split still stood on its own terms — but the development-split margin that
had originally motivated the choice no longer supported the reading that had been put
on it.

**No bug was found, and none was fixed.** Restart-to-restart variation under greedy
decoding on this kind of inference stack is a property of the runtime, not a defect in
the application. Independent work on GPU nondeterminism points at the mechanism:
floating-point reduction order shifts with GPU and runtime state, so the same input takes
a marginally different numerical path and, at a token where two candidates are nearly
tied, comes out the other side [EXT-DETERM-001]. It happens with no concurrency and a
fixed seed. That literature's own mitigation — deterministic, batch-invariant kernels —
ships in major engines only as an opt-in beta with a throughput cost. The response here
was procedural instead, aimed at the level that decides things: the outcome, not the bit
pattern.

Three changes went in:

1. **Every stored record carries its runtime identity.** A build fingerprint, plus a
   session identifier (process id and start time), so that "these two results came from
   the same session" is something you can verify afterwards rather than something you
   assume.
2. **Ticket-level comparisons are scoped to one session and one request order.** Not as
   a guideline — as the stated license. Anything wider gets relabeled descriptive.
3. **Any causal claim runs as a pair.** When a comparison has to cross an intervention
   — a prompt change, a routing hop, a budget change — both arms run back to back in the
   same session, with the order pre-registered and counterbalanced. That is a
   [contemporaneous paired control](../GLOSSARY.md#contemporaneous-paired-control), and
   it is the only design that survives a boundary this narrow.

Something else fell out of that instrumentation work, unlooked for. While session
identity was being added, every timing span was made to carry both a wall-clock and a
monotonic stamp. Cross-checking the two revealed a systematic skew on the virtualized
host — the clocks drifted against each other, quietly biasing every latency number the
project had published. Nobody suspected it. It was found only because both clocks were
captured and could be compared:
[dual-clock telemetry](../GLOSSARY.md#dual-clock-telemetry) is cheap at write time and
impossible to reconstruct later.

## The generic lesson

**A reproducibility boundary — the envelope within which repeated runs actually agree
(same session? across restarts? across machines? under concurrent load?) — must be
measured. It is never inferred from a configuration's stated determinism.** A fixed
seed and `temperature 0` describe an intention. They are not a measurement. Two runs
with byte-identical inputs and a nominally deterministic decode disagreed here on
roughly half their ticket-level outcomes, purely because two different process launches
produced them.

Once the boundary is measured, every comparability claim gets scoped to it. Same
session and same order: trustworthy at the item level. Across a restart or across a
machine: not. A [causal claim](../GLOSSARY.md#comparability-claim) that would cross the
boundary needs a contemporaneous paired control — both arms inside the window, order
pre-registered and counterbalanced — or the claim is declared unavailable and the
comparison is relabeled descriptive. This is why chapter 02 treats session and runtime
identity as a first-class, hashable part of the execution system, and why chapter 04
will not let an experiment contract treat a historical arm and a fresh arm as
interchangeable without a probe result behind it.

There is an operations corollary worth carrying into chapter 10. If your system does not
reproduce item by item against a frozen copy of *itself*, then a shadow or canary
comparison against the incumbent is a comparison of outcome *distributions*, judged with
the same statistics as any other experiment. Treating one differing output as a
regression, on a system that was never shown to match itself, manufactures alarms that
train your operators to ignore alarms.

### How this lands on your project

Run the cheapest version of this today. Take twenty items you already have. Run them,
restart the model server, run the identical twenty again, and count how many outcomes
changed. That number is your license: it tells you whether last week's run may be
compared to this morning's ticket by ticket, or only in aggregate, or not at all. If
the answer surprises you, go and look at the last decision you made from two runs
recorded at different times, and ask whether the margin you acted on was bigger than
the number you just measured. Then check whether your stored results even record which
process produced them. If they do not, that is the first fix — you cannot scope a claim
to a session you did not write down.

## What would NOT have worked

- **Trusting "greedy decoding plus a fixed seed" for item-level reproducibility across
  sessions.** That is the assumption this exercise falsified, twice, a day apart — the
  second time with the generation budget held fixed on both sides, so the session was
  the only thing left to explain the difference.
- **Reading deltas between two historical runs as caused by whatever changed between
  them.** Session noise of 23 to 24 outcomes per 48 can manufacture an effect that was
  never there, or hide one that was.
- **Averaging over more historical runs to smooth it out.** This is not sampling
  variance that shrinks as you add runs. It is a property of *which session* produced a
  given answer, and more runs drawn the same way inherit the same confound.
- **Reading the aggregates and concluding all was well.** The pass rate moved by about
  three tickets. Half the individual answers had changed underneath it.
- **Treating it as a bug to fix.** There was nothing to patch. The fix was to measure
  the boundary and design comparisons that stay inside it.

## References

- [EXT-DETERM-001] Nondeterminism and batch-invariance work (including
  arXiv:2506.09501, and the batch-invariance documentation of major inference engines) —
  reduction-order and GPU-state variance as the dominant mechanism at `temperature 0`,
  independent of concurrency.
- Governing chapters: [02](../02_EXECUTION_SYSTEM_MODEL.md),
  [04](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md); operational corollary in
  [10](../10_DEPLOYMENT_AND_OPERATIONS.md); instrumentation floor in
  [12](../12_OBSERVABILITY_LEARNING_AND_PROMOTION.md).
- Glossary: [reproducibility boundary](../GLOSSARY.md#reproducibility-boundary),
  [contemporaneous paired control](../GLOSSARY.md#contemporaneous-paired-control),
  [comparability claim](../GLOSSARY.md#comparability-claim),
  [frozen identity](../GLOSSARY.md#frozen-identity),
  [dual-clock telemetry](../GLOSSARY.md#dual-clock-telemetry).

---

> [Index](../README.md) · [Examples](README.md)
