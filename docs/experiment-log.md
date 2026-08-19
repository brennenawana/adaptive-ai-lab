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

> **Superseded by E6 (below), same day.** This held for `E2-v2-96`. E6 raised
> diagnosis to 65.6% and *dropped* evidence recall to 61.1%, making citation the
> binding constraint again. Left as written because the log is append-only and the
> reasoning was correct for the run it described.

E2 recalls 74.6% of required evidence and still identifies the root cause 16.7% of
the time. The "it fails because it cannot see the evidence" explanation is now
excluded by construction — the ceiling is 1.000 everywhere and the frontier arm
reaches it on the same bundles. What is left is reasoning.

### Finding 4 — zero forbidden claims from the local model, at any accuracy

E2 made 13 unsupported claims and **0 forbidden** ones across 96 cases, holding the
v1 result. Frequently wrong, never dangerous. Different failure modes, different
remedies.

### Harness bug #9 — the forbidden-claim detector counts refutations as assertions

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

---

## 2026-08-15 — E6b: citation recovery failed, four ways. Negative result.

E6 moved the bottleneck onto evidence recall (74.6% -> 61.1%, with 35 of the 63
correctly-diagnosed cases failing on evidence alone). Four prompt variants were run
on **dev** against variant C as control. **None beat it.**

| Variant | Change from C | Root cause | Evidence | >=0.8 | All-pass |
|---|---|---|---|---|---|
| **C** control | — | **62.5%** | **70.8%** | **22** | 35.4% |
| E recency | citation rules moved after the policy table | 56.3% | 60.1% | 15 | 27.1% |
| F eliminative | + cite records that ruled things out | 54.2% | 67.5% | 20 | 31.3% |
| G both | E + F | 62.5% | 67.4% | 22 | 35.4% |
| H subject | + cite the entity's state, not only the fault | 56.3% | 64.9% | 21 | 39.6% |

### What was learned, in order

**1. The attention-budget hypothesis is wrong, and backwards.** Moving the citation
rules later *cost* 10.7 points of recall (E vs C). They work better as part of the
task framing than as a closing reminder. That killed the original explanation.

**2. The real mechanism, read off the stored scores rather than guessed.** Among
cases E6 gets *right* but fails on evidence:

- **S10 misses exactly one id in 8 of 8 cases — the account.** It names the
  settlement that has no posting, concludes `reconciliation_gap` correctly, and never
  says which account it happened in. 1 of 2 required ids = 0.50.
- **S03 misses the account in 8 of 8.** Cites the pending verification and the card;
  2 of 3 = 0.667.

Nothing is being forgotten. The model cites what **proves** its conclusion and drops
what merely **corroborates** it. E2 cited those records more often precisely because
it was less decisive — E6 made the model quicker to commit, and terser with it.

**3. That diagnosis was then tested, and still failed.** Variant H asked, in general
operations terms, for the records establishing the entity's state. Recall went
*down*. The behaviour is not reachable by telling the model to do otherwise.

### The decision rule, fixed before H was run

With four dev cells already in hand, choosing a winner post hoc is fishing.
Registered in advance: **adopt H only if evidence recall >= C + 5 points AND root
cause >= C - 3 points.** H returned -5.9 and -6.3. Rejected.

H's all-pass (39.6%) is *higher* than C's (35.4%) and is precisely the number that
would have been cherry-picked without the rule — two cases on n=48, against declines
in both pre-registered metrics.

### Why this is a capability finding, not a rubric problem

The tempting move is to decide `account_id` was never really required evidence for
`kyc_hold` and trim the manifests. That is the `BAD_RUBRIC` trap — altering a rubric
after seeing model answers — and it is ruled out by a fact already in hand:

> **E4 scores 100% evidence recall on the same bundles.** Every required id is
> reachable, citable, and in practice cited by a stronger model.

The requirement is satisfiable; the gap is a real difference in thoroughness.
**Prompting has now failed four times to close it.** Recommendation: stop
prompt-tuning citation. Variant C stands as the E6 result.

`DEFAULT_PROMPT` stays `baseline` deliberately — the winner is invoked by explicit
run-id, so a future run without `--prompt` is still the control rather than silently
inheriting an intervention.

---

## Open questions

- ~~Does showing the model a category→plausible-actions table fix the action gap?~~
  **Answered (E6):** yes, completely — `act | rc` 18.8% -> 100%. But the larger
  effect was enumerating the hypothesis space, which is a different intervention.
- **Can the local model be made to cite corroborating evidence?** Four prompt
  variants say no (E6b). Open whether this is reachable at all below fine-tuning.
- Does runbook retrieval help, or is the evidence bundle already sufficient? (E3)
  Note E6 reframes this: diagnosis is no longer the main loss.
- At what escalation threshold does hybrid routing retain E4 accuracy at materially
  lower cloud dependence? (E5) — now more attractive, since the local arm's residual
  failure is concentrated in a dimension E4 saturates.
- Is the residual local failure evidence-selection or reasoning? The fixed-evidence
  mode isolates this: with evidence held constant, remaining errors are reasoning.

---

## 2026-08-16 — Routing foundation: R0 frozen, R1 measured (not equivalent), R2 oracle on dev

Full protocol and tables in `routing-experiments.md`; this entry records what was
found and what was deliberately not changed.

### R0 — `weak-baseline-v1`

Variant C on `f48039a`, run `E6-cause_action_directed-96` (test): rc 65.6%, act|rc
100%, evidence 61.1%, verifier 78.1%, all-pass 29.2%, no-output 12/96 (4 raw
`length` + 8 schema-invalid), wall p50 13.8 s / p95 50.4 s, 2 443 in / 1 194 out
tokens per case. E6b closed on the recorded dev cells (none beat C under the
pre-registered rule); no second test run. `make test` 160 → 187 after this work;
reachability 96/96 test and 48/48 dev, 0 capped classes.

### R1 — Switchyard passthrough is *not* semantically invisible for the local arm

Switchyard 0.2.0 re-serialises JSON with sorted keys; llama.cpp compiles the response
schema to an order-sensitive GBNF grammar; the model is forced to emit properties in
alphabetical order and its greedy output changes. Proven with a byte tap and by
reproducing Switchyard's exact output on the direct path with only the schema keys
sorted. On dev (same server session, same order): 0/48 identical outputs, 34/48
identical scored outcomes, all-pass 14→11, rc 31→28, evidence 0.606→0.655, verifier
37→39, no-output 5→4; transport overhead +4 ms mean on 12.7 s calls; token accounting
reconciles to the token (117 426 / 62 627). A client-side GBNF string restores
transport equivalence but removes the model's `<think>` phase (llama.cpp applies
`response_format` lazily after reasoning) — **not adopted**; the frozen baseline is
untouched. Decision: keep the boundary and telemetry, do not put the weak stage
behind Switchyard until key order is preserved upstream or the schema order is
canonicalised in a versioned suite bump.

### R0 caveat found by R1 — "greedy + seed" is reproducible only within a server session

`R1-direct-dev` vs `R1-direct2-dev`, back-to-back: 47/48 identical digests, 48/48
identical outcomes (the first case in run order differs — different prompt-cache
predecessor). But `E6-C-directed-dev` (earlier server process) vs `R1-direct-dev`:
identical prompt tokens, output tokens different 48/48, outcomes different **23/48**,
all-pass 17 vs 14, evidence recall 70.8% vs 60.6%. The E6b decision rule (+5 pts
evidence) was, in hindsight, of the same order as this cross-session noise; the E6
test confirmation (65.6% rc, n=96) is unaffected in kind but every case-level
comparison between local runs must now be made within one server session and one
request order. Recorded `system_fingerprint b1-9b05354` and server start time on the
R0 record.

### R2 — paired weak/strong oracle on dev (`E6-C-directed-dev` × `E4-v2-dev`)

`E4-v2-dev` run once (48 frontier calls, all-pass 91.7%). Cells: weak-pass/strong-pass
16, weak-fail/strong-pass 28, weak-pass/strong-fail 1, both-fail 3 → safe-local 35.4%,
rescueable 58.3%, oracle hybrid 93.8%, oracle strong-call minimum 64.6%, hard-case
6.2%; cascade reference cost −35% vs strong-only. Every disagreement was reviewed
against the harness before being read as model behaviour:

- S06-2003005 (weak>strong): all S06 worlds carry three unposted background
  settlements — S10's signature — so `compound_failure` is a defensible reading;
  background settlements are unposted in 7 of 12 classes (only S11 posts).
- S08-2001007: scorer false positive (refutation cue after the phrase).
- S08-2003007: declined amount 70 530 > available balance 17 530, so the forbidden
  `insufficient_funds` hypothesis is data-consistent; the model hedged it.
- S01-2001000: verifier's observed-id collector does not harvest `idempotency_key`,
  so citing one reads as fabrication.

### Deliberately NOT changed

- Scorer, verifier and generator: all four harness candidates are recorded for a
  versioned suite bump, not patched mid-baseline.
- The frozen local baseline and `DEFAULT_PROMPT`.
- The schema property order (canonicalising it would silently re-baseline the local
  arm; `test_schema_property_order_is_not_alphabetical…` guards the record).
- The alphabetical-grammar variant was neither adopted nor rejected on the R1
  numbers — it is an unpre-registered prompt-format factor on n=48.

---

## 2026-08-16 — R0.1 Switchyard made transparent; R4 deterministic cascade on dev and test

Full tables in `routing-experiments.md` § R0.1 and § R4.

### R0.1 — fix at the adapter boundary, proven same-session

`SwitchyardAdapter.build_body` rewrites every object schema into `allOf` components
(one property each, optional ones under `anyOf`, `additionalProperties` dropped) —
llama.cpp compiles that to the byte-identical grammar text as the plain schema, and
arrays survive Switchyard's key sorting. No suite change, no loss of the model's
`<think>` phase, direct path untouched. Same llama.cpp session (pid 4848,
`b1-9b05354`), same order, `prime-local` before each arm: `R01-direct2-dev` →
`R01-switchyard-dev` **48/48 identical output digests**, 48/48 outcomes, tokens
identical (117 426 / 62 938; Switchyard's routing log agrees to the token), model
p50 +11 ms. The one difference in the earlier direct arm was a stray `pytest` request
mid-run — live tests are now opt-in (`FIS_LIVE_TESTS=1`).

### R4 — deterministic cascade

Gate: escalate on no schema-valid output, unsupported claim, or any verifier failure
(nested policies none ⊂ parse ⊂ verifier; features are verifier-derived only).
Selection on dev by replay over the same-session weak run against `E4-v2-dev`, rule
pre-registered (adopt `verifier` unless > 2 unnecessary escalations beyond `parse`):
parse 5 escalations / 3 rescues; verifier 11 / 8, both 0 unnecessary → **`verifier`**.

| | weak-only | cascade | strong-only | oracle |
|---|---|---|---|---|
| dev (n=48, live `R4-cascade-verifier-dev`) | 29.2% | **50.0%** | 91.7% | 91.7% |
| test (n=96, one run `R4-cascade-verifier-96`) | 29.2% | **49.0%** | 99.0% | 100% |

Test: escalation 21.9% (12 unsupported claims, 9 no-output), rescue 19/21, unnecessary
0/96, false negatives 47/96, cost per success $0.046 vs $0.097 strong-only (floor),
wall p50 14.5 s vs 38.2 s. Dev→test 50.0% → 49.0%.

### What it demonstrates

Structural gates recover ~¼ of the weak→strong gap at ~22% strong calls, never
escalate a case the weak model would have passed, and turn 9 in 10 escalations into
passes. The remaining ¾ are verifier-clean answers that are wrong on root cause or
short on evidence — invisible to any production-available deterministic signal, and
the same family E6b showed prompting cannot move.

### Deliberately NOT changed

- Scorer, verifier, generator, suite v2, `weak-baseline-v1`, `DEFAULT_PROMPT`.
- No further trigger was added after seeing the oracle gap; no second look at test.
- The suite-v3 backlog (unposted background settlements; S08 declined amount >
  balance — it tripped the strong arm again in this run, S08-2003007; `idempotency_key`
  not an observed id; post-positioned refutation cue) stays a backlog.
- Nemotron / learned routing / QLoRA not started.

---

## 2026-08-17 — R3: Nemotron 3.5 Lightning compatibility spike and dev benchmark — negative under the pre-registered rule

Full tables in `routing-experiments.md` § R3.

### Compatibility: yes, on the same runtime

`bartowski/…-30B-A3B-GGUF` IQ4_XS (18.9 GB; experts IQ4_NL) on the same llama.cpp
build as Qwen (`b1-9b05354` already knows `nemotron_h_moe`), port 8083 beside Qwen
on 8082. Every GGUF of this model is ≥ 17.9 GB, so it cannot sit whole in 16 GB of
VRAM at any quant; hybrid placement (`--fit on`, experts partly in system RAM) works:
~8 GB VRAM beside Qwen, 15.3 GB alone. Deterministic, schema-valid, no crashes over
51 cases. **91–95 tok/s generation with `--no-mmap`**; with mmap the CPU-offloaded
experts fell to 20 tok/s once the page cache turned over — the dev run ran in that
state, so its latency column is an artefact (output digests identical across
placements). Prompt ≈ 1 400 tok/s (2.2 s TTFT on 3 150 tokens) vs Qwen 5 000 tok/s.

### Design A held: zero Qwen drift

Qwen control A → Nemotron → Qwen control B in one Qwen session (pid 4848, the same
process as every R0.1/R4 run): A vs B **48/48 identical output digests**, and
identical to `R01-direct2-dev`. Every difference below is model difference.

### Dev result (n=48, contract frozen: same prompt, evidence, schema, grammar path,
scorer, greedy/seed 42/`max_tokens 4096`)

| | Qwen | Nemotron |
|---|---|---|
| strict all-pass | 14 (29.2%) | 12 (25.0%) |
| root cause | 31 | 16 |
| evidence recall | 0.606 | 0.316 |
| no-output | 5 (schema) | **31 = 29 length-cap + 2 schema** |
| silent (verifier-clean, wrong) | **23** | **4** |
| among completed cases | — | 12/19 pass (63%), rc 84%, evidence 0.80 |

Migration matrix A/B/C/D = 4 / 10 / 8 / 26. All 10 regressions are the 4 096-token
cap hit inside `<think>` (reviewed: not harness, not scenario — thinking budget vs
contract). 6 of the 8 rescues were Qwen silent failures (S08 ×4, S03 ×2 evidence).
Silent false negatives 22 → 4; 15 of Qwen's silent failures become *loud* under
Nemotron (visible to the gate), 6 become passes, 2 stay silent, 2 new ones.

R4 replay, same `verifier` policy: Qwen+R4 45.8% at 22.9% strong calls, $0.0545 per
success; **Nemotron+R4 89.6% at 66.7% strong calls, $0.0868 per success**; frontier
91.7%, $0.1172 (floor). Nemotron+R4 keeps the three harness-flagged "w+s−" cases local
and misses 4 rescueable.

### Decision (pre-registered in `OVERNIGHT_STATUS.md` M3.5 before results)

Criteria 1 (all-pass +5), 3 (regressions ≤ 3), 4 (p50 ≤ 30 s), 5 (cascade economics)
**fail**; criterion 2 (silent −5) passes. **Nemotron does not qualify; Qwen stays the
incumbent; test untouched.**

### What it means

The candidate answers R3's actual question in the affirmative — it removes ~80% of
the valid-looking-but-wrong weak answers — but under the frozen 4 096-token budget it
does so mostly by not finishing, which the cascade turns into frontier calls. It is a
better investigator and a worse weak tier at this budget. The one confound to resolve
before the model comparison is meaningful is the token budget (a decoding-config
factor, to be varied for **both** arms on dev, one factor, same session pair).

### Deliberately NOT changed

Suite v2, scorer, verifier, prompt, `max_tokens`, `weak-baseline-v1`, R4 policy. No
Nemotron prompt adaptation, no `--reasoning-budget`, no test run. The S08
forbidden-claim scorer FP did not recur for Nemotron (its S08 answers pass); it
remains on the suite-v3 backlog. Qwen session pid 4848 (2026-08-16 08:14 UTC →
2026-08-17 05:15 UTC) was ended only after all same-session comparisons were
complete; both servers are up again in new sessions.

---

## 2026-08-17 — R3b: the token-budget factor (`max_tokens` 4 096 → 8 192, both weak arms, dev) — negative under the pre-registered rule; test untouched

Full tables in `routing-experiments.md` § R3b; rule and definitions in
`OVERNIGHT_STATUS.md` § M4.2 (committed at `99fe730` before any 8 192-token result).

### One factor

Same suite v2, dev split and order, prompt (`cause_action_directed`), evidence,
schema/grammar path, scorer, verifier, decoding (greedy, seed 42), checkpoints, quants,
llama.cpp build `b1-9b05354`, placement (`--no-mmap`) and R4 policy as R3; only
`max_tokens` changed, 4 096 → 8 192, for **both** Qwen and Nemotron. `run_eval
--max-tokens` (default 4 096) records the budget on every invocation; the config
digest gains `|max_tokens:8192` only when non-default. New observation-only telemetry:
`reasoning_chars` / `content_chars` from llama.cpp's `reasoning_content`.

### Design A held again

Qwen A → Nemotron → Qwen B in one Qwen session (pid 586847): A vs B **47/48 identical
digests, 48/48 identical outcomes** (the first case in run order differs by 8 tokens —
the endpoint had been probed with that case's prompt before priming). A same-session
Qwen 4 096 diagnostic run after B: 46/48 identical to A — `max_tokens` is inert for
Qwen except on the one case that needs 4 105 tokens (S07-2003006: silent wrong at
8 192, `length` no-output at 4 096). The R3 → R3b Qwen shift (14 → 15 all-pass, 0/48
identical digests) is cross-session drift, as R1 recorded, not the factor. Nemotron,
by contrast, reproduced R3's 19 completed cases byte-for-byte in a new session.

### Result (dev, n=48)

| | Qwen 8 192 | **Nemotron 8 192** | Nemotron 4 096 (R3) |
|---|---|---|---|
| complete (`stop`) / `length` | 48 / 0 | **39 / 9** | 19 / 29 |
| strict all-pass | 15 (31.2%) | **18 (37.5%)** | 12 |
| root cause · evidence · verifier | 30 · 0.648 · 36 | 31 · 0.649 · 34 | 16 · 0.316 · 16 |
| silent (verifier-clean, wrong) | 21 | **16** | 4 |
| output tokens · wall p50 / p95 | 62 673 · 11.5 / 35.1 s | 239 961 · **52.0 / 94.1 s** | 172 436 · 206 s (mmap-slow) |

R3's 29 length-capped cases at 8 192: **RECOVERED_PASS 6, RECOVERED_FAIL 14 (12 of them
silent), STILL_LENGTH_CAPPED 9 (all four S07 `reversal_race`), OTHER 0.** So the cap
explained all of the loudness and about a fifth of the failures: 6/29 capped cases
(6/36 of R3's failures) were correct answers waiting to finish. Migration matrix vs Qwen
A: A/B/C/D = 9 / 6 / 9 / 24 (B: 3 length cap, 2 verifier-unsupported, 1 wrong root
cause; C: 6 Qwen-silent, 2 Qwen no-output, 1 Qwen verifier). Silent failures Nemotron
16 vs Qwen 21 (−24%, not the −80% of R3): the earlier advantage was mostly unfinished
reasoning counted as loud. R4 replay, unchanged `verifier` policy: Qwen + R4 52.1% at
25.0% strong calls, $0.0553/success, p50 15.1 s; **Nemotron + R4 64.6% at 29.2%,
$0.0534/success, p50 55.4 s** (R3: 89.6% at 66.7%, $0.0868); frontier 91.7%, $0.1172.
The extra budget buys local passes at flat cost per success — it does not reduce
frontier utilisation (29% vs 25%), and costs 3.8× the tokens and 4.5× the latency.

### Decision (rule pre-registered before the run, applied by `scripts/r3b_selection_rule.py`)

Gate PASS · **A FAIL** (39/48 complete, threshold 43) · B PASS (18 ≥ 14; rc +1 vs Qwen A,
tolerance 2) · **C FAIL** (silent 16 > 6) · **D FAIL** (cell B 6 > 5) · E PASS (29.2% < 50%,
$0.0534 ≤ $0.070) · F PASS (p50 52.0 s ≤ 75 s). **Nemotron does not qualify; Qwen stays
the incumbent; TEST NOT RUN.**

### What it means

The 4 096-token limit was why R3 looked the way it did, not why Nemotron does not
qualify. With the budget removed the two weak arms are measured on the same footing:
Nemotron is marginally better on this contract (+3 local passes, +6 cascade passes,
equal root cause and evidence, 5 fewer silent failures) at 3.8× the generated tokens,
4.5× the latency, a second model resident on the card, and slightly *more* frontier
traffic — and it still cannot finish 9 cases in 8 192 tokens. The token-budget
question is closed; what remains is a model comparison, and on suite v2 it does not
change the incumbent.

### Deliberately NOT changed

Suite v2, scorer, verifier, prompt, `DEFAULT_MAX_TOKENS` (4 096), R4 policy,
`weak-baseline-v1`. No Nemotron prompt adaptation, no `--reasoning-budget`, no test
run, no suite v3, no learned routing, no QLoRA. Runtime finding recorded, not acted
on beyond the make target: an idle `--no-mmap` Nemotron process degrades to ~50 tok/s
over hours and recovers to ~93 tok/s on restart with identical flags; outputs are
placement-independent, latency is not.

**Next (one): suite v3**, then re-baseline Qwen, Nemotron and the frontier together with
the budget fixed and recorded per arm.

---

## 2026-08-17/18 — Suite v3: a deliberate benchmark release, then fresh DEV and TEST baselines for Qwen, Nemotron and the frontier

Governing documents: `FIS_Suite_v3_Benchmark_Release_Goal_Prompt.txt`,
`SUITE_V3_RELEASE_CONTRACT.md` (pre-registered, committed at `7d606cf` before any
implementation or model run), `SUITE_V3_RELEASE_REPORT.md` (numbers),
`OVERNIGHT_STATUS.md` § Milestone 5 (live log). Freeze tag `suite-v3` at `7764601`.

### What Suite v3 changed, and why each change is model-neutral

Four defect classes, each found by arm disagreement during R2/R4 and deferred rather
than patched mid-baseline; each answers "which invariant was wrong under v2" without
reference to any model's score:

1. **Background settlements** (generator, pipeline). Six classes carried
   S10's `reconciliation_gap` signature as ambient noise: `_distractors()` created
   settlements no consumer ever posted. Now `_background()` publishes them and the
   consumers post them; S11's hand-written postings (a class-identifying id shape)
   go through the same path and `World.add_entry` is gone; background precedes the
   case; the mapper version is recorded per event so S06's bad release touches only
   the injected settlement; S07's deliveries arrive after their events; every
   settlement/reversal event carries a safe key except S02's. Ledger rows in the
   corpus: 672, all pipeline-caused.
2. **S08/S05 amounts vs balances** (generator). S08 drew amount and balance
   independently (3 of 24 worlds had declined amount > available; dev S08-2003007);
   S05's ledger balance sat unexplained next to available = 1.50. Balances are the
   snapshot at case time; S08's decline now fits inside it, S05's exceeds it and the
   two balances agree.
3. **Forbidden-claim polarity** (scorer). Lookback-only, a dead boundary guard, and
   lost sentence-initial cues; now one documented same-sentence rule in both
   directions (`SCORER_VERSION 3`), with the recorded false positives replayed and
   the recorded hedges still counted.
4. **`idempotency_key` observability** (verifier). The key the model was shown by
   `get_webhook_history` was not harvested as an observed id (`VERIFIER_VERSION 3`).

Plus the bookkeeping the goal required: suite identity on every manifest and score
row (migration 006, v1/v2 rows backfilled and untouched otherwise), a runner that
refuses a corpus/code mismatch or a run-id reused across suites, suite-labelled
`compare.py`, cross-suite refusal in every analysis script, a canonical corpus digest
(`scenarios/manifests/corpus_v3.json`), and reachability on both model-facing splits.

### Deliberately NOT changed

Root causes, actions, cause→action table, prompts (`DEFAULT_PROMPT` still
`baseline`; weak arms still `cause_action_directed`, frontier still `baseline`),
schema and grammar path, tools and the evidence plan, the 0.8 threshold, decoding,
`DEFAULT_MAX_TOKENS`, the R4 `verifier` policy, `add_failed_delivery`, `learning.*`,
every Suite v2 run row, the R3b verdict. No prompt tuning, no learned routing, no
QLoRA, no ontology expansion. One correction was made after the sanity run had
started (M5.4): the injected S06/S07/S10 events also carry a key so the key never
discriminates the injected event — a world-consistency fix from reading the bundle,
not from a model result; the sanity run was restarted from scratch on the
regenerated corpus.

### Release gates (all pass; report § 3)

368 tests; corpus regenerated (`make corpus`, 3.8 s, 720 events / 672 entries),
digest `1e7c5278…`, second regeneration byte-identical; reachability test 96/96 and
dev 48/48 with 0 capped classes; projection == live rows for all 288 scenarios;
88 scenario invariants; gold answers score all-pass everywhere; scorer/verifier
fixtures pass; frontier DEV sanity 48/48 with no disagreement — Suite v3 frozen at
tag `suite-v3` (`7764601`).

### DEV baselines (n=48; report § 4–6)

| arm | budget | all-pass | rc | evidence | verifier | no-output | cap hits | wall p50/p95 | out tokens |
|---|---|---|---|---|---|---|---|---|---|
| Qwen3-8B Q4_K_M (`V3-qwen-dev`; B `V3-qwen2-dev` identical 48/48 outcomes) | 4096 | **35.4%** | 62.5% | 0.611 | 68.8% | 9 | 1 | 12.8 / 41.7 s | 65 588 |
| Nemotron 3.5 Lightning IQ4_XS (`V3-nemotron-dev`) | 8192 | **47.9%** | 64.6% | 0.675 | 75.0% | 12 | 10 | 53.2 / 96.0 s | 238 293 |
| Claude Opus 5 CLI (`E4-v3-dev`) | CLI default | **100%** | 100% | 1.000 | 100% | 0 | 0 | 36.9 / 60.1 s | 180 033 |

Pairwise A/B/C/D: Qwen×Nemotron 13/4/10/21 (the four regressions are Nemotron `length`
no-outputs; seven of the ten rescues were Qwen silent failures); Qwen×frontier
17/0/31/0; Nemotron×frontier 23/0/25/0 — **no inversion**, so no harness review was
triggered. Unchanged R4 `verifier` policy by replay: Qwen + R4 66.7% at 31.2% strong
calls ($0.0608/success, p50 16.7 s); Nemotron + R4 72.9% at 25.0% ($0.0453, p50
54.7 s); rescue 100%, unnecessary 0, routing false negatives 16 / 13 — all
verifier-clean answers wrong on evidence or root cause.

### TEST baselines (n=96, once each, after the freeze)

| arm | budget | all-pass | rc | evidence | verifier | no-output | cap hits | wall p50/p95 | out tokens |
|---|---|---|---|---|---|---|---|---|---|
| Qwen3-8B Q4_K_M (`V3-qwen-96`) | 4096 | **28.1%** (27) | 70.8% | 0.628 | 77.1% | 13 | 1 | 12.9 / 33.8 s | 129 910 |
| Nemotron 3.5 Lightning IQ4_XS (`V3-nemotron-96`) | 8192 | **50.0%** (48) | 67.7% | 0.713 | 78.1% | 19 | 15 | 55.8 / 94.1 s | 480 810 |
| Claude Opus 5 CLI (`E4-v3-96`) | CLI default | **99.0%** (95) | 100% | 1.000 | 100% | 0 | 0 | 37.6 / 61.0 s | 354 059 |

The one frontier miss (S12-3002011) is a correct diagnosis with 4/4 evidence and the
`replay_webhook` distractor as the action — recorded, rubric unchanged. Pairwise
A/B/C/D: Qwen×Nemotron 21/6/27/42 (B: 2 `length`, 2 unsupported, 1 wrong label, 1
evidence; 20 of the 27 rescues were Qwen silent evidence failures); Qwen×frontier
27/0/68/1; Nemotron×frontier 48/0/47/1; no inversion. Unchanged R4 `verifier` policy
by replay: Qwen + R4 **50.0%** at 22.9% strong calls, rescue 21/22, unnecessary 0,
routing false negatives 47/96, $0.0513/success, p50 15.4 s; Nemotron + R4 **71.9%** at
21.9%, rescue 21/21, unnecessary 0, false negatives 26/96, $0.0380/success, p50 56.1 s;
strong-only $0.1139/success.

### What it means

Suite v3 numbers are a new reference point, not a delta on v2 (report § 8): seven
classes' worlds changed, the scorer's polarity rule changed for every class, and the
verifier's observed set grew. Within v3 the picture is consistent across DEV and
TEST: the frontier saturates the suite (100% / 99.0%), so nothing in it rewards
guessing; Nemotron 3.5 Lightning at 8 192 outscores Qwen at 4 096 by +6 (DEV) / +21
(TEST) passes for ~3.7× the tokens and ~4.3× the latency and still cannot finish S07
inside its budget; both weak arms are blind to the same classes (S01, S11, S12) and
fail on different dimensions (Qwen: schema no-outputs and fabricated ids; Nemotron:
the cap). The cascade's rescue rate is ~100% and its unnecessary-escalation rate is 0,
so **the binding constraint is now silent-failure detection** — 47/96 (Qwen) and
26/96 (Nemotron) accepted answers on TEST are verifier-clean and wrong. That is the
R5 question (`HANDOFF.md`, report § 10). This milestone selects no model and tunes
nothing; the Suite v2 verdicts (Qwen incumbent; R3b closed) are neither confirmed nor
overturned by v3 numbers, because they are not comparable to them.

### Deliberately NOT changed after the numbers

Nothing. No prompt, budget, routing, scorer, verifier or generator change was made
after any Suite v3 score was seen; TEST was run once per arm and not revisited.

## 2026-08-18 — R5: learned silent-failure routing over production-observable features (offline-first; TRAIN acquired, DEV selected, TEST once per model)

Governing documents: `FIS_R5_Learned_Silent_Failure_Routing_Plan.html`,
`R5_EXPERIMENT_CONTRACT.md` (skeleton `e3b8066`; TRAIN-driven amendments `76a7ec1`,
`4b10da0`, `3e04dc7` — each before the corresponding DEV replay), `R5_LEARNED_ROUTING_REPORT.md`
(numbers, interpretation), `OVERNIGHT_STATUS.md` § Milestone 6 (live log). Suite v3, models,
prompts, budgets, evidence plan, scorer, verifier and the R4 gate unchanged; new inference:
288 local TRAIN calls (Qwen 41/144 = 28.5 %, Nemotron 66/144 = 45.8 %), 0 frontier, 0 TEST.

### What was built
`fis_platform/routing/features.py` — `RoutingFeatureSnapshot` v1 (58-name allowlist over
model/runtime, verifier, tool trajectory, answer echo; forbidden names are schema errors;
deterministic digest; extractor reads only the local invocation, verifier verdict, tool calls,
error and the answer's own label/action) with 43 leak-guard tests; `learn.py` (stdlib L2
logistic + CART ≤ 3, AUC/AP/Brier, LOGO/stratified folds, JSON artifacts with digests);
migrations 007 (`learning.model_outputs`: the answer body, kept from now on — the frozen
Suite v3 arms had only its sha256) and 008 (`learning.routing_decisions` telemetry);
`r5_dataset/train/replay/oracles/amend_rule/diagnostics.py`; a fail-closed selection state
machine (one selection record per model, winner-only freeze, TEST unlock bound to the recorded
winner + lineage, append-only, one look per model; 17 temp-registry tests). R4 reproduced from
the frozen trajectories on DEV and TEST on every field.

### Result (report § 6–9)
- **Labels are class-clustered** (P(unsafe | class) 0.09–1.0 on Qwen TRAIN; six/eleven
  classes one label on Nemotron) and four allowlisted case constants identify the scenario
  class for 45/48 DEV cases, so under the plan's primary leave-one-class-out protocol **no
  candidate passed the TRAIN gate for either model** (per-fold LOGO AUC mean 0.39 Qwen /
  0.61 Nemotron). Under the skeleton alone R5 is a null result.
- Under the secondary, deployment-matched protocol (registered before DEV, with the a-priori
  utilization caps removed for it — both amendments necessary for any selection): Qwen DEV
  `lr_full` 47/48 @ 70.8 % (FN 16 → 1, unnec 4), `lr_core` 44/48, `tree` 39/48 @ 56.2 %;
  Nemotron DEV `lr_full` 45/48 @ 50.0 % (FN 13 → 3, unnec 2, AUC 0.953 — above the
  class-identity ceiling 0.876), `lr_core` 40/48 @ 39.6 %, `tree` 44/48; the contract's
  tie-break "fewer frontier calls" froze the least-escalating survivor for both models
  (`r5-qwen-tree-stratified-v1` τ 0.70; `r5-nemotron-lr_core-stratified-v1` τ 0.50).
- **TEST, once each:** Qwen tree **75/96 (78.1 %)** vs R4 48/96, FN 47 → 20 (27 caught: 22
  evidence, 5 root cause), unnecessary 6, utilization 57.3 % (oracle 70.8 %), $0.0799/success
  — meets the pre-registered reading (a reading a random escalator of that size also meets
  with p ≈ 0.59; the catch count itself is beyond chance, p = 0.003; a class prior would have
  caught 39). Nemotron `lr_core` **74/96 (77.1 %)** vs R4 69/96, FN 26 → 21, unnecessary 6,
  utilization 33.3 %, $0.0509/success — **not confirmed** (K_test 7); AUC 0.557 on the
  accepted subset.
- Silent family: what is caught is caught by template (S03/S04/S06/S10/S11/S12) and, for
  `lr_full`, by the answer's said label (S02 `duplicate_webhook_handled`, S12 `kyc_hold`);
  Nemotron alone shows a within-template behaviour signal (`content_chars` within-class AUC
  0.26). Oracles: Qwen 95/96 at 70.8 % min-useful utilization, Nemotron 95/96 at 49.0 %;
  three-tier cheapest-sufficient on TEST 27 Qwen / 27 Nemotron / 41 frontier / 1 unresolved,
  not template-clean.

### What it means
Production-observable features raise the cascade far above R4 on this benchmark, but what
they carry is template difficulty (plus a thin said-label layer); within-template silent
failure was not detected, and TRAIN's label structure gives little power to find a small
signal. Nemotron is the better base for learned routing (lower silent base rate, routers above
the class ceiling on DEV, within-class signal) but its cascade p50 exceeds the frontier's.
Pre-registration lessons recorded, not repaired: the tie-break selects the least-escalating
survivor; U = catches − unnecessary degenerates at unsafe rates ≥ 0.5 (and to escalate-nothing
below it with a weak ranker); pooled LOGO AUC is null-biased under class-clustered labels;
n = 48 gives the rule little power against a random escalator. Recommended next milestone
(exactly one): QLoRA specialization of the local tier (Nemotron first) on TRAIN, targeted at
evidence-citation discipline on the systematically failing templates, measured with the R5
replay/oracle instrument; not started.

### Deliberately NOT changed
Suite v3 (corpus, scorer, verifier), prompts, budgets, evidence plan, the R4 gate, model
configurations; no R6 multi-tier learned routing, no QLoRA, no dynamic harness work; nothing
re-selected or re-run after a DEV or TEST look. Both models' TEST is now spent for learned
routing on Suite v3.

## 2026-08-18/19 — R6: modern local specialist refresh (Qwen3.5-9B, Qwen3.8-27B, Ternary Bonsai; cryptographic provenance; TRAIN-only selection, DEV gates, TEST once)

Plan `FIS_R6_Modern_Local_Specialist_Refresh_Plan.html`; contract `R6_EXPERIMENT_CONTRACT.md`
(pre-registered before the first TRAIN pilot, frozen at `b4e9095`, amendments appended only);
report `R6_MODERN_LOCAL_SPECIALIST_REFRESH_REPORT.md`; record `learning/registry/r6/`.

### Configuration
| | |
|---|---|
| Suite | v3 unchanged (corpus `1e7c5278…`, scorer 3, verifier 3, prompt `cause_action_directed`, FIXED_EVIDENCE), asserted at start and end |
| Controls (replay only) | Qwen3-8B Q4_K_M (`d98cdcbd…`, cap 4096), Nemotron 3.5 Lightning IQ4_XS (`c7be5d2c…`, cap 8192), frontier `E4-v3-*` |
| Candidates | Qwen3.5-9B Q4_K_M (`03b74727…`, acquired from the pinned revision), Qwen3.8-27B Q3_K_M (`7f3b845b…`, TRAIN-selected over UD-Q3_K_XL `00cf92e6…`), Ternary Bonsai 27B Q2_0 (`868c1171…`) on the Prism llama.cpp fork |
| Execution system (all candidates) | upstream llama.cpp `b1-9b05354` (Bonsai: Prism `b1-9fcaed7`), `-c 16384 -ngl 99 --flash-attn on` q8_0 KV `--jinja --parallel 1`, cap 8192 (calibration: no allowed cap met the ≤ 3/36 truncation tolerance), greedy seed 42, one resident server, fresh session + 8-token prime |
| Provenance | every trajectory carries artifact SHA-256, GGUF metadata digest, runtime digest (binary set + CUDA/driver/GPU), server-args digest, generation-config digest, execution-system digest, session; runner binds the running server to the record before any call |
| Splits | TRAIN: 36-case stratified pilot (digest `fde034b0…`) + 12-case stability probes; DEV: one run per frozen candidate after the contract freeze and two independent Fable reviews; TEST: once per DEV-qualified candidate |

### Results (report § 4–7)
| | Qwen3-8B | Nemotron | Qwen3.5-9B | Qwen3.8-27B Q3_K_M | Bonsai | frontier |
|---|---|---|---|---|---|---|
| TRAIN pilot (36) | 8 | 15 | 13 | 20 (UD 16) | 15 | — |
| DEV (48) | 17 | 23 | 23 | 25 | 21 | 48 |
| DEV gate | — | — | REJECTED (p50 58 s > 38.6 s; no-output 10 > 8; quality met) | QUALIFIED | QUALIFIED | — |
| TEST (96) | 27 | 48 | — | 47 | 34 | 95 |
| silent DEV / TEST | 16 / 47 | 13 / 27 | 12 / — | 1 / 2 | 21 / 41 | 0 / 1 |
| no-output (cap) DEV / TEST | 9 (1) / 13 (1) | 12 (10) / 19 (15) | 10 (10) / — | 22 (22) / 47 (47) | 5 (4) / 8 (8) | 0 |
| unchanged R4 cascade DEV / TEST | 32 / 48 | 35 / 69 | 36 / — | 47 / 93 (FN 1 / 2) | 27 / 55, FN 40 | — |
| p50 wall DEV / TEST | 12.9 / 13.2 s | 53.8 / 55.8 s | 58.1 s | 263 / 265 s | 79.5 / 76.8 s | 37 s |
| resident GPU (alone) | — | — | 7.1 GiB | 15.1 GiB | 9.1 GiB | — |

Pairwise: no local arm dominates another on DEV or TEST (every pair complementary); frontier
dominates all. Nemotron vs Qwen3.8 on TEST: 29 both / 19 Nemotron-only / 18 Qwen3.8-only /
30 neither; Qwen3.8 unique among locals 15 (S01, S04), Nemotron 12 (S10, S06, S11).
Stability probes 12/12 identical (Qwen3.8 across sessions). New inference 516 local cases,
0 frontier calls; ~24 h wall.

### What it means
A modern 27B at Q3 (Qwen3.8) is the strongest local and, under the *unchanged* R4 verifier
gate, yields 93/96 on TEST at 49 % frontier utilization with two false negatives — because
its failures are visible truncations at the 8192 cap, not silent wrong answers. It is
competitive with Nemotron on raw all-pass (47 vs 48), not better, and slower (265 s vs 56 s);
the two are complementary. Qwen3.5-9B gains +6 DEV cases over Qwen3-8B (= Nemotron) but at
4.5× the latency and with 10 cap hits — rejected by the pre-registered small-tier gate. Bonsai
qualifies as an efficiency point on DEV (0.61× memory, 0.30× latency of Qwen3.8, ≥ floor; on
TEST 0.67× memory) and carries the largest silent burden on DEV, second-largest on TEST. The strongest local's residual failure is a reasoning
budget, not a behaviour gap: QLoRA on Qwen3.8 is not the next step, nor is a router; Nemotron specialization (27 TEST
silent failures at a fifth of the latency) is the fallback if the budget study fails to convert. Recommended next
milestone (exactly one): R7 reasoning-budget calibration of the frozen Qwen3.8 execution
system (caps > 8192 / thinking budget, TRAIN-selected, one DEV, one TEST). Not started.

### Deliberately NOT changed
Suite v3, prompts, tools, evidence plan, scorer, verifier, frontier rows, the R4 gate; no
training, no learned router, no model-specific prompt tuning, no cap/quant/prompt change after
DEV, no rerun after TEST. Qwen3.5-9B's TEST was never opened. TEST is now spent on Suite v3
for `qwen38-27b-q3km` and `bonsai-27b` as well.
