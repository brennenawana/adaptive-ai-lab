# SCENARIO-02: Clustered Eval, Effective N

> [Index](../README.md) · [Examples](README.md)

**An invented scenario.** The project is fictional; the lesson and the reasoning are the
part to take seriously.
**Illustrates:** [03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md) ·
[04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md)

---

## Situation

Fifteen kinds of question the desk actually gets — holdings lookup, archive citation, loan
eligibility, hours and access, and so on. Eight questions written for each. One hundred
and twenty items in the finished suite. That felt like a real sample size, and for two
rounds nobody questioned it.

The desk in question is at a regional library system, and the suite exists to decide which
model should be working it. A patron asks something like *"does any branch have the 1954
county plat book, and can I borrow it?"* and the assistant answers from the catalog, the
local-history archive index, and the interlibrary-loan rules, citing what it used. The
suite itself was put together the way most eval suites get put together: list the kinds of
question, write a handful of each.

Reporting followed the same instinct. Item count was treated as sample size.
Percentage-point gaps were read straight off the pass-rate table.

## Decision faced

Two candidates had cleared an earlier screening gate and gone to the frozen 120-item test
suite. The challenger — a larger quantized open-weights model — scored 62 of 120. The
incumbent scored 48. That is a 14-item gap, **+11.7 percentage points**, and it was
written up as the round's headline finding and the basis for swapping the production
model.

The question is not whether the challenger is better. It might well be. The question is
whether a 120-item suite built as 15 families × 8 questions is strong enough evidence to
say so — and, more usefully, what a suite of that shape can support at all.

## Evidence

The headline table, exactly as it was reported:

| Arm | test all-pass (n = 120) | Rate |
|---|---|---|
| Challenger | 62 | 51.7% |
| Incumbent | 48 | 40.0% |
| **Headline gap** | **+14** | **+11.7 pp** |

Then someone re-read those same scores a different way.

Nothing new was run. No model was called again, no item was rescored. Every number above
is exactly what was measured. What changed is that the re-read asked one question first:
**within what grouping do these outcomes travel together?**

The answer was the question family. Whether the assistant gets a holdings lookup right is
mostly determined by what holdings lookups demand — the catalog fields they need, the
disambiguation they require — not by which of the eight holdings questions you happened to
draw. That grouping is the [clustering unit](../GLOSSARY.md#clustering-unit). Once you
name it, you can measure how strongly outcomes correlate inside it. That correlation is
the [intraclass correlation](../GLOSSARY.md#icc), or ICC, and here it came out at 0.42 by
a straightforward analysis of variance on the per-family pass indicators.

An ICC that high has a mechanical consequence. Items inside a cluster partly repeat each
other, so each one carries less than a full item's worth of independent information. The
multiplier is the [design effect](../GLOSSARY.md#design-effect):

| Quantity | Value |
|---|---|
| N (test items) | 120 |
| Clustering unit | question family (15 families, m = 8 items each) |
| Measured ICC | 0.42 |
| DEFF = 1 + (m − 1)·ICC | 1 + 7 × 0.42 = **3.94** |
| [Effective N](../GLOSSARY.md#effective-n) = N / DEFF | 120 / 3.94 ≈ **30** |
| Cluster-robust paired t (15 family means, df = 14) | t = 1.12 |
| Unclustered [MDE](../GLOSSARY.md#mde) — smallest resolvable gap — at 15–30% disagreement | 9.9–14.0 pp |
| Cluster-corrected MDE at the realized 40% disagreement rate | ≈ 32 pp |
| Earlier screening gate (n = 45, m = 3): DEFF 1.84, effective N ≈ 24 | corrected MDE ≈ 31 pp |

The suite has 120 items. It has the statistical resolving power of about **30**.

## What happened

What makes this scenario worth reading is how nearly it passed unnoticed.

The naive read was not absurd. It was *plausible*. Every design has a smallest gap it can
reliably tell apart from noise — the minimum detectable effect, or MDE. Ignoring
clustering entirely, this suite's MDE sits between 9.9 and 14.0 pp, depending on how often
the two models disagree on an item. (That disagreement rate has a name too: **discordance**.
It drives the MDE arithmetic, because an item both models get right, or both get wrong,
tells you nothing about which is better.) The observed gap was 11.7 pp. That
lands right in the middle of the range. A quick significance check could have come out
either way, and nobody would have raised an eyebrow at how close it was.

Once the clustering was made honest, the picture changed completely:

- Cluster-robust paired inference — a t-test on the 15 per-family means, df = 14 — gave
  **t = 1.12. Not significant.**
- At the comparison's realized discordance of 0.40 (48 of 120 items where the two models
  disagreed: 31 favoring the challenger, 17 the incumbent), the cluster-corrected MDE came
  out near **32 pp**. The observed 11.7-pp gap was nowhere near what this suite, honestly
  analyzed, could resolve.
- The correction reached backward too. The 4-item, 8.9-pp margin that had separated the
  two candidates at the earlier 45-item screening gate sat well under a third of that
  gate's own corrected MDE of about 31 pp. It was informative for a gross pass/fail gate.
  It was never evidence of a ranking.

Be precise about what this does and does not say. **It does not say the incumbent is as
good as the challenger.** The challenger may genuinely be better; the ranking may be
exactly right. The finding is narrower and more uncomfortable than that: *this test was
never able to tell you.* An 11.7-pp gap and a 0-pp gap would have looked the same to it.

So the claim was reclassified rather than reversed. The 120-item suite was recorded as
sufficient for gross configuration gates, descriptive comparison, and ruling candidates
out by a wide margin — and explicitly **not** sufficient for fine-grained ranking between
model arms. The model swap went back to being an open question, decided later on operating
cost and latency, which the suite *could* measure.

The re-read also settled how the next suite refresh would be built, and this is the part
teams get backward. Because DEFF is driven by ICC and cluster size rather than raw item
count, adding items inside existing families barely helps. Two ways to spend the same 120
new questions, at this ICC:

- **Double the items per family** (15 families × 16 = 240): DEFF = 1 + 15 × 0.42 = 7.3,
  effective N = 240 / 7.3 ≈ **33**. Twice the suite, twice the runtime, and effective N
  moves from about 30 to about 33.
- **Add 15 new families** (30 families × 8 = 240): DEFF stays 3.94, effective N = 240 /
  3.94 ≈ **61**. The same 120 new questions, twice the resolving power.

The refresh was committed to adding families before adding items within families.

## The generic lesson

1. **Find the grouping before you read the gap.** Outcomes correlate inside some unit —
   scenario class, source document, prompt template, session, user, question family. Name
   that [clustering unit](../GLOSSARY.md#clustering-unit) and estimate
   [ICC](../GLOSSARY.md#icc) from real per-cluster indicators before any
   percentage-point difference is read as a result. ICC **MUST NOT** be assumed to be
   zero. It almost never is.
2. **Convert item count into effective sample size.** Compute
   [DEFF](../GLOSSARY.md#design-effect) = 1 + (m − 1)·ICC and
   [effective N](../GLOSSARY.md#effective-n) = N / DEFF before treating item count as
   sample size. A suite that looks comfortably powered by raw N can carry a single-digit
   or low-double-digit effective N once clustering is counted honestly.
3. **Make the cluster-robust test primary.** A t-test on per-cluster means, df = clusters
   − 1, is the primary analysis whenever clustering is material. McNemar's exact test on
   discordant pairs is a legitimate secondary statistic, but it is anti-conservative under
   clustering — it can read as decisive exactly where the cluster-robust test does not.
4. **New clusters buy power; new items inside old clusters saturate.** Effective N =
   km / (1 + (m − 1)·ICC) approaches a hard ceiling of k / ICC however many items each
   cluster holds. At ICC 0.42 with 15 families, that ceiling is about 36 — and the suite
   above was already at 30, roughly 85% of the way there. Under high ICC, a refresh adds
   strata before it adds replications.
5. **State the number before the data, and be willing to say the test failed.** Every
   experiment contract declares its cluster-corrected MDE and effective N *before* data,
   and reports [INCONCLUSIVE](../GLOSSARY.md#inconclusive) rather than a false read when
   the observed margin is smaller than the design can resolve. One cheap arithmetic guard
   catches most first-pass errors: an MDE larger than the discordance it was computed from
   is impossible, so `MDE ≤ discordance` should always hold.

## What would NOT have worked

**Adding more items inside the same 15 families.** With m already at 8 and ICC at 0.42,
DEFF is set almost entirely by the clustering, not by N. Doubling the suite moves effective
N by about three. That is a lot of runtime for almost no evidence.

**Trusting the McNemar secondary statistic on its own.** McNemar assumes the discordant
pairs are independent. Measured ICC 0.42 makes that assumption false here, so the test
would have read as more decisive than the clustered data support — exactly the
anti-conservative failure the statistics canon names it for.

**Treating the earlier screening gate as confirmation.** Two weak signals pointing the same
way are not one strong signal. They are the same underlying noise, sampled twice from the
same clusters.

**Running the whole thing again.** Worth stating explicitly, because it is the most common
reflex when a result gets questioned. Nothing in this scenario required a new experiment.
The correction came entirely from re-reading numbers that had been sitting in the results
table for two rounds. The instrument had been reporting its own limits the whole time; no
one had asked it the right question.

**How this lands on your project.** Take your current eval suite and answer one question:
what were the items generated *from*? If they came from a list of categories, templates,
source documents, or personas with several items each, you have clusters — and your
effective sample size is smaller than your item count, possibly by a factor of three or
four. Compute it from numbers you already have: ICC on the per-cluster pass rates, then
DEFF = 1 + (m − 1)·ICC, then N / DEFF. Run it against a comparison you have already shipped
a decision on. If that decision's margin is smaller than what the suite can resolve, you
have not necessarily made the wrong call — but you did not make it on the evidence you
thought you had, and the next one deserves to know that.

## References

- [EXT-STATS-001] Miller, "Adding Error Bars to Evals" (arXiv:2411.00640) — the
  clustered/paired standard-error formulas and the power/MDE machinery applied above.
- [NV-EVALSDK-001] NVIDIA NeMo Evaluator SDK — paired McNemar testing, power/MDE tables,
  GO/NO-GO gating with 95% confidence intervals; the secondary-statistic precedent this
  scenario qualifies rather than rejects.
- [EXT-TESTBED-003] Efficient-eval and small-model-set reliability literature
  (tinyBenchmarks, Anchor Points, IRT-reliability) — corroborates that item count alone
  overstates a suite's ranking reliability.
- Governing chapters: [03](../03_EVALUATION_FOUNDATION.md),
  [04](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md); formulas in
  [references/STATISTICS_FORMULAS.md](../references/STATISTICS_FORMULAS.md); statistical
  plan in [templates/EXPERIMENT_CONTRACT.md](../templates/EXPERIMENT_CONTRACT.md).
- Glossary: [clustering unit](../GLOSSARY.md#clustering-unit), [ICC](../GLOSSARY.md#icc),
  [design effect](../GLOSSARY.md#design-effect),
  [effective N](../GLOSSARY.md#effective-n), [MDE](../GLOSSARY.md#mde),
  [INCONCLUSIVE](../GLOSSARY.md#inconclusive).
- Related: [SCENARIO-03](SCENARIO-03_learned-router-leakage.md) — what clustering does to
  a learned component trained on the same suite.

---

> [Index](../README.md) · [Examples](README.md)
