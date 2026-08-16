# Experiment Log

Append-only. Each entry records what was run, what was found, and — importantly —
what was **not** changed as a result, so later readers can tell a principled
decision from a convenient one.

---

## 2026-08-15 — Platform stood up, first E2/E4 comparison (n=12)

### Configuration

| | |
|---|---|
| Local specialist | Qwen3-8B Q4_K_M, llama.cpp CUDA, greedy (temp 0, seed 42), `--parallel 1` |
| Frontier | Claude Opus 5 via subscription CLI, `--safe-mode --tools ""` |
| Evidence mode | `FIXED_EVIDENCE` both arms — identical bundle, so the difference measured is reasoning, not tool strategy |
| Split | test, 1 scenario per class |
| Verifier | schema, citation format, citation resolves to a call, cited ids observed, action code known, confidence calibration |

### Results (n=12 — directional only)

| Metric | E2 local 8B | E4 frontier |
|---|---|---|
| Strict all-pass | 8.3% | 50.0% |
| Root-cause accuracy | 41.7% | 83.3% |
| Next-action accuracy | 8.3% (1/12) | 75.0% (9/12) |
| Verifier pass | 83.3% | 100% |
| P95 latency | 101 s | 56 s |
| Reference cost / success | $0.00 | $0.1778 |

### Principal finding

The local model's failure is **not uniformly distributed**. It identifies the root
cause in 41.7% of cases but selects the correct operational action in 1 of 12 —
and not randomly: `replay_webhook` was chosen for a settlement mapping error, a
risk hold, and a compound KYC failure. That is anchoring on a salient action name,
not reasoning from cause to remedy.

A single accuracy figure would have hidden this entirely. It is the clearest
argument so far for the guide's per-dimension scoring.

**Implication for the ladder:** this reads as a prompt/schema gap (the model is
never shown which actions are plausible for a case category), which sits *above*
LoRA. E6 should be run before E7 is even considered.

### Harness defects found by running it

All three would have been misread as model weakness:

1. **llama.cpp GBNF converter rejects `minLength`/`maxLength`** — 400 on every
   local call. Fixed by stripping length constraints for grammar compilation only;
   the verifier still enforces them. Grammar guarantees shape, verifier guarantees
   semantics.
2. **Verifier rejected citations naming the tool** (`tool://get_ledger_entries/le_1`)
   rather than the service — failed 11 of 12 *correct* citations. Now accepts both.
3. **Fixed-evidence plan never called `get_webhook_history`** — required evidence
   was structurally unreachable for S01, S02, S06, S10. Plan is now two-phase:
   entity lookups, then provider-ref-driven event lookups.

Fixing (2) and (3) moved E2 root-cause accuracy 16.7% → 41.7%. **That gap was
infrastructure, not the model** — a direct instance of what the Discovery
Controller exists to prevent.

### Deliberately NOT changed

- **The action rubric was not widened.** Two E4 answers look defensible but scored
  wrong (S09 `contact_identity_vendor` when the vendor genuinely did change schema;
  S10 `inspect_mapping_version`). The rubric was written on the merits before any
  results existed. Adjusting it now would be tuning against the test set. Logged as
  a `BAD_RUBRIC` candidate for review **before** the next frozen suite version, not
  after seeing more scores.

### Caveats

- n=12 (one per class). A single case moves any rate by 8.3 points.
- E4 runs at 100% cloud dependence by construction — E5 is where the interesting
  cost/quality tradeoff appears.
- Frontier arm is not bit-reproducible: the subscription CLI exposes no
  temperature or seed. The local arm is. Recorded on the model manifest as
  `supports_seed`.

---

## 2026-08-15 — Corpus scaled to 288 scenarios

96 test / 48 dev / 144 train, all 12 classes in each split.

### Two bugs found by scaling

1. **Entity id collisions.** Ids were a per-scenario counter plus 3 random digits;
   across ~96 scenarios that collided (birthday problem). Ids now embed the seed.
2. **`scenario_id` collided across splits.** It was `seed % 100_000`, so train seed
   1,000,000 and test seed 3,000,000 both rendered `S01-00000` — the same primary
   key for a training and a test scenario. This would have silently defeated the
   disjoint seed ranges that exist specifically to prevent leakage. Now uses the
   full 7-digit seed.

Neither was reachable by a single-scenario test. Added `test_generator_uniqueness.py`,
which builds a multi-split corpus and asserts global uniqueness of every id space
including `provider_ref` (a collision there would splice one scenario's webhook
evidence into another's investigation).

**Prior n=12 results are not comparable to anything generated after this change** —
the corpus was regenerated with new ids.

---

## 2026-08-15 — E2 at n=96 (test split)

`run_id=E2-local-96`, local Qwen3-8B, FIXED_EVIDENCE, 96 scenarios (8 per class).

| Metric | n=12 | **n=96** |
|---|---|---|
| Strict all-pass | 8.3% | **5.2%** |
| Root-cause accuracy | 41.7% | **29.2%** |
| Next-action accuracy | 8.3% | **13.5%** |
| Verifier pass | 83.3% | **64.6%** |
| Required-evidence recall (mean) | — | 58.0% |
| Unsupported claims (total) | — | 37 |
| Forbidden claims (total) | — | **0** |
| P50 / P95 latency | — | 18.9 s / 58.1 s |
| Tool calls per case (mean) | — | 10.7 |

### Findings

1. **The n=12 result was optimistic.** Root-cause accuracy fell 41.7% → 29.2% with
   8× the data. Worth remembering the next time a 12-case result looks encouraging:
   one case was worth 8.3 points.

2. **The action gap is structural, not sampling noise.** 29.2% on diagnosis vs
   13.5% on remedy — the model is ~2× better at identifying the fault than at
   choosing the response. This was the E6 hypothesis at n=12 and it survived.

3. **Zero forbidden claims in 96 cases.** The model is frequently *wrong* but not
   *dangerous* — it never asserted confirmed fraud or any other harmful conclusion.
   These are different failure modes with different remedies, and the strict
   all-pass metric alone would have hidden the distinction.

4. **New at scale: citation discipline degrades.** Verifier pass 64.6% with 37
   unsupported claims, against 83.3% at n=12. Harder cases produce weaker citation
   behaviour — not visible in the small sample.

### Deliberately NOT done

**E4 was not re-run at n=96.** The event-driven migration regenerates the corpus,
which invalidates every score including this E2 run. Spending ~90 minutes of
frontier calls (and subscription rate limit) on a baseline about to be discarded is
waste. Both arms get baselined once, on the final event-sourced corpus.

Consequence: **the E2 n=96 numbers above are a pre-migration reference point only.**
Do not compare them to anything produced after the event layer lands.

---

## 2026-08-15 — Event migration landed; suite bumped to v2

Steps 5–7 of the migration in `architecture.md`. S01, S02, S06, S07, S09 and S10 now
publish `ProviderEvent`s; the integration and ledger consumers materialise every
consequence. `World.add_event` is deleted, `add_delivery` is narrowed to
`add_failed_delivery`.

**The corpus was regenerated. `EvalRun.suite_version` is now `2`.** Neither the
root-cause set nor the cause→action mapping changed, so this is not an ontology
change — but the corpus and the tool set both did, and v1 scores are not comparable
to v2 scores. `E2-local-96` (pre-migration) is kept and the new run ids are
`E2-v2-96` / `E4-v2-96` so the two cannot be confused.

### What became emergent

| Class | Before | After |
|---|---|---|
| S01 | two hand-written delivery rows, one flagged `deduplicated` | published twice with one idempotency key; the consumer's dedupe ledger suppresses the second |
| S02 | two hand-written ledger entries | published twice with no key; the consumer genuinely cannot tell retry from reality, so it posts twice |
| S06 | entry written with a transposed amount | mapping v3 transposes it; the ledger posts what it was told |
| S07 | entries written with inverted timestamps | reversal published *before* a settlement that occurred earlier; reverse the two `publish` calls and the anomaly disappears |
| S09 | raw/normalized mismatch written by hand | mapping v2 does not know `APPROVED_WITH_CONDITIONS` and turns a real approval into `failed` |
| S10 | entry simply omitted | the settlement event is never published — the ledger never heard about it |

Determinism survives because envelope ids are `uuid5` over the scenario id rather
than `uuid4`. Every materialised row is named after the envelope that caused it, so
random ids would have given the same seed a different world on every regeneration —
and, worse, left each manifest citing the *previous* run's row ids while the
`ON CONFLICT DO NOTHING` on manifests hid it.

### The harness defect this exposed — larger than the migration itself

**No webhook delivery in the entire pre-migration corpus was reachable by any tool
call. 0 of 312.**

The fixed-evidence plan reaches the event trail by walking `provider_ref` out of
phase-one results and calling `get_webhook_history` with it. No delivery's
`provider_event_id` had ever been set to a `provider_ref` that any state row carried,
so the second hop always came up empty. Measured ceilings on evidence recall against
a 0.8 threshold:

| Class | Ceiling before | Observed E2 recall (n=96) | Ceiling after |
|---|---|---|---|
| S01 | 0.250 | 0.000 | 1.000 |
| S02 | 0.500 | 0.500 | 1.000 |
| S04 | 0.333 | 0.333 | 1.000 |
| S09 | 0.500 | 0.500 | 1.000 |
| S12 | 0.500 | 0.406 | 1.000 |

The observed recalls sit exactly on the structural ceilings for S02, S04 and S09 —
the model was not failing to find this evidence, it was never shown it. **Five of
twelve classes could not pass evidence recall whatever the model did**, and the
resulting numbers read as model weakness.

This is the same defect as harness bug #2 from the n=12 entry above, which was
recorded as fixed. Adding the second hop made the evidence *addressable in principle*
but nothing ever checked that a real address existed. Hence a third invariant in
`task-ontology.md` §5: reachability must now be **demonstrated against the built
corpus** (`make reachability`), not argued from the generator.

S04 needed more than an address. `provider_outage` is defined by clustering across
customers and every tool was keyed by `customer_id`, so the signal was invisible in
principle — root-cause accuracy was 0.000 across all 8 cases. Three changes:

1. `get_verifications` v2 takes an optional `vendor` + `window_hours`, anchored on
   the customer's own verification times.
2. The outage vendor is **pinned** across the cluster. It had been drawn per
   verification, so the four "vendor timeouts" often came from three different
   vendors — three coincidences, not an outage.
3. `Clock.before()` — backdated fields (`created_at`, `opened_at`, `issued_at`) no
   longer rewind the shared cursor. `tick(days=-30)` per customer had scattered
   S04's four "simultaneous" timeouts **a month apart**. The scenario had never
   contained the cluster it claimed to model.

Scenarios now occupy disjoint 48-hour slots on the timeline, because a vendor+time
query is the first tool whose results are not confined to one scenario by
construction.

**Second-order consequence, stated plainly:** the v2 baseline moves for two reasons
at once — the corpus is event-sourced *and* five classes stopped being unwinnable.
Any improvement over `E2-local-96` is therefore **not** evidence that event sourcing
helped the model. The clean reading of v2 is as a new reference point, not as a
delta. A migration-only comparison was available (port first, fix reachability
after) and was deliberately not taken: it would have meant knowingly baselining a
corpus with five impossible classes, and E6 needs a trustworthy floor more than the
migration needs an attributable delta.

### Results — E2 and E4, n=96, suite v2

_Both arms baselined together on the final corpus, per the plan._

`E2-v2-96` (Qwen3-8B local, greedy) and `E4-v2-96` (Claude frontier via CLI), both
`FIXED_EVIDENCE`, 96 test scenarios.

| Metric | E2 local 8B | E4 frontier |
|---|---|---|
| **Strict all-pass** | **3.1%** | **91.7%** |
| Root-cause accuracy | 16.7% | 99.0% |
| Next-action accuracy | 17.7% | 100% |
| Required-evidence recall (mean) | 74.6% | 100% |
| Verifier pass | 77.1% | 100% |
| Unsupported claims (total) | 13 | 0 |
| Forbidden claims (total) | 0 | 7 — **all false positives, see below** |
| P95 latency | 40.1 s | 59.2 s |
| Reference cost / success | $0.00 | $0.1083 |

### Finding 1 — the corpus is now fully solvable, and that is the point

E4 scores 100% on evidence recall, action, and verifier, and 99.0% on root cause
(95/96, one S06 miss). It is 1.000 on eleven of twelve classes.

This is the strongest available evidence that the reachability work was correct.
A suite where the strongest available model saturates every dimension has no
structural caps left in it: the remaining failures are the model's. Before the fix,
five classes could not be passed by any model, and no amount of model quality would
have shown it.

### Finding 2 — the local model's action choice is independent of its own diagnosis

This is the sharpest result in the project so far, and it replaces the earlier
framing.

| E2, action accuracy conditioned on… | value | n |
|---|---|---|
| …the root cause it gave was **correct** | 18.8% | 16 |
| …the root cause it gave was **wrong** | 17.5% | 80 |

**Identical.** Knowing the cause does not improve the local model's chance of
choosing the right remedy. It is not reasoning cause → action badly; it is not
reasoning cause → action *at all*. The action is drawn from somewhere else — most
likely surface features of the case text.

The n=96 v1 entry framed this as "~2× better at diagnosis than remedy" (29.2% vs
13.5%). On v2 the aggregate gap is gone (16.7% vs 17.7%) — but the conditional above
shows the underlying defect is worse than the aggregate suggested, not better. **E6
should be evaluated on the conditional, not on aggregate action accuracy**, which a
model can raise by guessing common actions.

### Finding 3 — evidence is no longer the bottleneck

E2 recalls 74.6% of required evidence and still identifies the root cause 16.7% of
the time. The "it fails because it cannot see the evidence" explanation is now
excluded by construction — the ceiling is 1.000 everywhere and the frontier arm
reaches it on the same bundles. What is left is reasoning.

### Finding 4 — zero forbidden claims from the local model, at any accuracy

E2 made 13 unsupported claims and **0 forbidden** ones across 96 cases, holding the
v1 result. Frequently wrong, never dangerous. Different failure modes, different
remedies.

### Harness bug #8 — the forbidden-claim detector counts refutations as assertions

**E4's 7 forbidden claims are all false positives, verified by reproduction.** The
detector is a bare substring match:

```python
hits = [c for c in manifest["forbidden_claims"]
        if c.replace("_", " ") in text or c in text]
```

S08 forbids `insufficient_funds`. E4 wrote, with a citation:

> "Account acc_3000007_01 has status 'restricted' with an available balance of
> 413520 GBP equal to its ledger balance, so the decline was **not caused by
> insufficient funds**."

That is the correct reasoning for S08 — the decline is a risk hold, and ruling out
insufficient funds is exactly what a competent investigator does. The evidence
bundle does not contain the phrase, so this is the model's own prose. All 7 affected
cases are correct on every other dimension.

**Corrected E4 all-pass is 95/96 = 99.0%** (the single genuine failure is
S06-3007005). As-measured is 91.7%.

Deliberately **not fixed**, by the same reasoning that keeps the action rubric
frozen: this is a metric about *harm*, and loosening it is a semantics decision to
be made on the merits rather than while producing the baseline it happens to affect.
A negation guard is a heuristic that can produce false *negatives* — the dangerous
direction. Scoring `facts[].claim` instead of the whole serialised output is the
better fix and needs its own thought. **Decide before E6**, which re-runs E2 and
inherits the detector.

### The S07 regression, found by disagreement between the arms

Worth recording as a method note. The first v2 run had E4 at **12.5%** on S07 while
scoring ~100% on ten other classes — and the *weaker* local model scoring higher on
that class. An inversion where the stronger arm does worse is the signature of a
scenario that rewards guessing.

It was a regression this migration introduced. The ledger consumer stamps
`posted_at` from `occurred_at` (deliberately — arrival time would hide the very
reordering S07 is about), so a settlement that occurred at T+65 but arrived after the
T+75 reversal posts with the *earlier* timestamp. The hazard therefore moved entirely
into `posting_seq`. `get_ledger_entries` sorted by `posted_at` and never returned
`posting_seq`, so the model saw a perfectly chronological, net-zero ledger — and the
only conclusion the evidence supported was that nothing was wrong. E4 answered
`false_positive_alert` with careful, correct reasoning.

Entries are now returned in posting order with `posting_seq` included. E4 went
**0.125 → 1.000** on S07. Both arms were re-run from scratch afterwards; the numbers
above are post-fix.

Same defect as unreachable webhook evidence, one layer down: the fact was in the
database and no tool call surfaced it. That is now four distinct instances, which is
why `make reachability` exists.

### Caveats

- E2 produced no parseable structured output in 9 of 96 cases (v1: 7 of 96 — same
  rate). Concentrated in S01 this run. Not diagnosed; a candidate for E8.
- E4 is not bit-reproducible: the subscription CLI exposes no temperature or seed.
- E4's cost is reference list-price equivalent, not billed.

---

## 2026-08-15 — E6: two interventions, and they are not the same one

Four prompt variants, local Qwen3-8B, `FIXED_EVIDENCE`. **Selection on the dev split**
(48 scenarios) — choosing a variant on test would be tuning against the test set,
which is the one rule the frozen-suite design exists to enforce. The winner then runs
on test exactly once.

| Variant | What it adds | Root cause | **act \| rc** | Verifier | All-pass |
|---|---|---|---|---|---|
| **A** baseline | nothing (control) | 18.8% | 44.4% *(n=9)* | 77.1% | 4.2% |
| **B** policy table | cause→action mapping | 56.3% | **100%** *(n=27)* | 77.1% | 37.5% |
| **C** table + directed | mapping + "look up the cause you concluded" | **62.5%** | **100%** *(n=30)* | **83.3%** | 35.4% |
| **D** causes only | the twelve labels, no actions | 60.4% | 34.5% *(n=29)* | 77.1% | 8.3% |

`act | rc` is action accuracy among cases whose root cause was correct — the metric
E6 is about. Aggregate action accuracy rises if a model merely guesses common
actions; this does not.

### The result: the diagnostic gain and the action gain have different causes

B and C tripled **root-cause** accuracy, which the cause→action intervention has no
business doing. They changed two things at once: they taught the mapping, and they
enumerated the twelve valid root causes in the prompt for the first time. Variant D
was added to separate them — same causes, same order, action column deleted.

D recovers **essentially all of the diagnostic gain and none of the action gain**:

- **Diagnosis 18.8% → ~60% comes from enumerating the hypothesis space.** Nothing to
  do with remedies. The label set was already enforced by the response grammar, so
  the model could never emit an invalid cause — but a grammar constrains what may be
  *emitted*, and does nothing for what is *considered*. Naming the candidates in the
  prompt is what let it reason over them.
- **Action 44.4% → 100% comes from the mapping.** D, without it, stays at 34.5% —
  indistinguishable from the control.

The original E6 hypothesis was that the model "has no model of which remedies attach
to which defects". That is confirmed, and the fix is complete: `act | rc` is 100%,
i.e. every case it diagnoses correctly now gets a sanctioned action. But the *larger*
effect was hiding underneath it and is a different, cheaper, more general finding —
one that would have been mis-attributed to the remedy table if D had not been run.

**Had E6 stopped at B or C, the log would have recorded "teaching the cause→action
policy triples diagnostic accuracy", which is false.**

### Reading the numbers honestly

- **`next_action_accuracy` is no longer a measure of judgement** in B and C. With the
  policy table in the prompt it measures lookup compliance — by design, not by leak.
  It is not comparable to E2's. Judge these variants on `act | rc` and on root cause.
- **B vs C is within noise.** 56.3% vs 62.5% on n=48 is three cases. C was chosen for
  the confirm run on the strength of root cause *and* verifier pass (83.3% vs 77.1%),
  and because its directive is the theoretically motivated one, not because the
  difference is significant.
- **The control reproduces.** Variant A on dev scored 18.8% root cause against
  `E2-v2-96`'s 16.7% on test — so dev and test are comparable in difficulty and A is
  a valid same-run control rather than a comparison against another day's number.
- `test_prompt_table_matches_the_rubric` pins the taught policy to the scorer's
  `acceptable_next_actions`. If they drift, a variant is penalised for correctly
  applying what it was told, and the natural reading is "the intervention failed".

### Confirmed on test (`E6-cause_action_directed-96`), and it moved the bottleneck

Variant C, test split, run once:

| Metric | E2-v2-96 | **E6 (variant C)** |
|---|---|---|
| Root-cause accuracy | 16.7% | **65.6%** |
| act \| rc | 18.8% | **100%** |
| Strict all-pass | 3.1% | **29.2%** |
| Verifier pass | 77.1% | 78.1% |
| Forbidden claims | 0 | 0 |
| **Required-evidence recall** | **74.6%** | **61.1%** ⚠ |

Root cause 3.9× and all-pass 9.4×, with test (65.6%) slightly *above* the dev
estimate (62.5%) — so the variant was not overfitted to dev by the selection.

**But evidence recall fell 13.5 points, and that is now the binding constraint.**

| | E2-v2-96 | E6 |
|---|---|---|
| Cases clearing the 0.8 evidence threshold | 51 | **34** |
| Cases with root cause correct | 16 | 63 |
| **Correct diagnosis, failed on evidence** | 5 | **35** |
| Passed everything | 3 | 28 |

E6 diagnoses 63 of 96 cases correctly and loses **35 of them** on evidence recall
alone. Before the intervention, evidence was abundant and diagnosis was the
bottleneck; now diagnosis is largely solved and citation is the bottleneck. The
all-pass metric is conjunctive, so this single dimension is holding back roughly a
third of the suite.

The likely mechanism is attention budget: the variant C prompt is substantially
longer, and the citation rules — unchanged and verbatim — now compete with a policy
table for the model's attention. A model that reaches its conclusion faster also
appears to feel less need to enumerate what it read. This is a cost of the
intervention, not a separate regression, and it was invisible on the aggregate
figures that improved.

**This is the next thing to work on, and it reframes E3.** Retrieval was queued to
answer "does explicit company knowledge help diagnosis". Diagnosis is no longer where
the loss is. The open question is now whether evidence citation can be recovered
without giving back the diagnostic gain — a prompt-level question that should be
tried before E3 or E5.

### What this implies for the ladder

The specialization ladder puts prompt/context work above retrieval above training.
This is a strong argument for staying on the low rungs: two prompt changes moved the
local 8B's root-cause accuracy from 18.8% to ~60% and closed the action gap
completely, with no retrieval, no routing and no training. **E7 (QLoRA) should not be
considered until E3 and E5 have been run against this new baseline** — the headroom
that remains is much smaller than it was this morning.

### E4 re-run under the corrected scorer

E4 was re-run after the forbidden-claim detector was made polarity-aware:

| | before fix | after fix |
|---|---|---|
| Strict all-pass | 91.7% | **99.0%** |
| Root cause | 99.0% | 100% |
| Forbidden claims | 7 | 1 |

99.0% is exactly the corrected figure predicted when the false positives were first
identified, which validates both the diagnosis and the fix. Seven of eight phrasings
are now handled; **one residual false positive remains** (S08-3005007, again
`insufficient_funds`), whose wording was not captured — the frontier arm is not
reproducible and raw output is not persisted. The scorer now records an excerpt of
the matched text alongside the label, so the next occurrence is auditable without
re-running a case and hoping for the same phrasing.

E2 is unaffected by the fix: it scored 0 forbidden claims before and after, and the
change can only remove hits.

- Does showing the model a category→plausible-actions table fix the action gap? (E6)
- Does runbook retrieval help, or is the evidence bundle already sufficient? (E3)
- At what escalation threshold does hybrid routing retain E4 accuracy at materially
  lower cloud dependence? (E5)
- Is the residual local failure evidence-selection or reasoning? The fixed-evidence
  mode isolates this: with evidence held constant, remaining errors are reasoning.
