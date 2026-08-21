# CASE-002: Clustered Eval, Effective N

> [Index](../README.md) · [Examples](README.md)

Real empirical case from the FIS project (Fintech Integration Sandbox), a realistic
synthetic fintech-operations laboratory used to develop this playbook's methodology.

**Source:** INT-CASE-002 · **Date range:** 2026-08-18 – 2026-08-20
**Cited by:** [03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md) ·
[04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md)

---

## Situation

FIS's frozen TEST split ("Suite v3") holds 96 evaluation cases: 12 scenario classes
(S01–S12, each a distinct fintech-operations root-cause category — settlement
mapping errors, webhook duplication, KYC holds, provider outages, and so on), 8
cases per class. A milestone (internally "R6") compared four candidate local model
configurations against this split after each had already cleared a smaller DEV
gate: an incumbent (Qwen3-8B), a same-family upgrade (Qwen3.5-9B, rejected at DEV
on latency), a modern 27B quantized specialist (Qwen3.8-27B Q3_K_M), and a ternary
27B alternative ("Bonsai", Q2_0). Every arm ran the identical frozen prompt,
evidence bundle, scorer, and verifier; only the model artifact and its execution
system varied.

Reporting at the time treated the 96-item TEST split the way most eval suites are
treated by default: item count as sample size, percentage-point gaps read directly
off the pass-rate table.

## Decision faced

Qwen3.8-27B scored 47/96 strict all-pass on TEST; Bonsai scored 34/96 — a headline
gap of +13/96 = **+13.5 percentage points**, reported as "the strongest local"
finding and a candidate basis for selecting Qwen3.8-27B as the new specialist. The
question this case answers: was a 96-item, 12-class suite strong enough evidence to
support that model-ranking claim — and, more generally, what can a suite of this
shape support at all?

## Evidence

TEST-split strict all-pass, the two arms at the center of the headline claim:

| Arm | TEST all-pass (n=96) | Rate |
|---|---|---|
| Qwen3.8-27B Q3_K_M | 47 | 49.0% |
| Ternary Bonsai 27B Q2_0 | 34 | 35.4% |
| **Headline gap** | **+13** | **+13.5 pp** |

A 2026-08-20 methodology-synthesis pass re-derived the suite's statistics against
FIS's own trajectory store (`learning.case_scores ⋈ learning.trajectories`) — no
new experiment, no new inference, only a re-read of numbers already in hand,
identifying the [clustering unit](../GLOSSARY.md#clustering-unit) (scenario class)
and estimating [ICC](../GLOSSARY.md#icc) by ANOVA on real per-class pass
indicators:

| Quantity | Value |
|---|---|
| N (TEST cases) | 96 |
| Clustering unit | scenario class (12 classes, m = 8 cases/class) |
| Measured ICC | 0.475 |
| [Design effect](../GLOSSARY.md#design-effect) DEFF = 1 + (m−1)·ICC | 1 + 7×0.475 = 4.33 |
| [Effective N](../GLOSSARY.md#effective-n) = N / DEFF | ≈ 22 |
| Cluster-robust paired t (per-class means, df = 11) | t = 0.98 |
| Unclustered [MDE](../GLOSSARY.md#mde), TEST(96), discordance pd .15–.30 | 10.9–15.5 pp |
| Cluster-corrected MDE at realized pd = 0.427 | ≈ 37 pp |
| DEV(48) unclustered MDE at pd = .30 | 21.6 pp (not detectable at pd = .15 — MDE ≤ pd always) |

The same re-read found the DEV-stage qualification gate — where Qwen3.8-27B (25/48)
beat Bonsai (21/48), a 4-case / 8.3-pp margin — used to separate candidates at DEV.

## What happened

The unclustered read was dangerously plausible: TEST(96)'s unclustered MDE range
(10.9–15.5 pp) sits right next to the observed 13.5-pp gap, so a naive
significance check could easily have come out either way and nobody would have
been alarmed by the closeness. Once the clustering unit was identified and ICC
measured at 0.475 — high, because within a scenario class the model's failure mode
is largely determined by what the class itself demands, not by per-case draw — the
design effect came out to 4.33 and the effective N to **≈ 22**, not 96. Cluster-robust
paired inference (t on the 12 per-class means, df = 11) on the Qwen3.8-vs-Bonsai
comparison gave t = 0.98: **not significant**. The cluster-corrected MDE at the
comparison's realized discordance (pd = 0.427) came out near 37 pp — the observed
13.5-pp gap was nowhere close to what the suite, honestly analyzed, could resolve.

The same correction reached backward into the DEV gate: the 4-case/8.3-pp margin
that had separated Qwen3.8-27B from Bonsai at DEV sat roughly an order of magnitude
inside DEV's own cluster-corrected MDE (21.6 pp at pd=.30). No historical number was
changed and no run was repeated — every score in both tables above is exactly what
was measured. What changed was what could honestly be claimed from those numbers:
Suite v3 at N=96/12-classes was reclassified as sufficient for gross configuration
gates, descriptive comparison, and certain-bound exclusion, and explicitly
**not** sufficient for fine-grained ranking between local model arms. The
methodology synthesis also flagged the deep design consequence: because DEFF is
governed by ICC and cluster size rather than raw N, the suite's planned refresh
("Suite v4") is committed to adding scenario classes before adding replications
within existing classes — that is where the power actually comes from at this ICC.

## The generic lesson

1. Identify the [clustering unit](../GLOSSARY.md#clustering-unit) — the grouping
   within which outcomes correlate (scenario class, document, template, session,
   user) — and estimate [ICC](../GLOSSARY.md#icc) from real per-cluster indicators
   before any percentage-point gap is read as a result. **MUST NOT** be assumed
   zero.
2. Compute [DEFF](../GLOSSARY.md#design-effect) = 1 + (m−1)·ICC and
   [effective N](../GLOSSARY.md#effective-n) = N/DEFF before interpreting item
   count as sample size. A suite that looks well-powered by raw N can carry a
   single- or low-double-digit effective N once clustering is honest.
3. Cluster-robust paired inference (t on per-cluster means, df = clusters−1) is the
   primary analysis whenever clustering is material; McNemar exact on discordant
   pairs is a legitimate secondary statistic but is anti-conservative under
   clustering — it can read as decisive exactly where a cluster-robust test does
   not.
4. In a clustered design, statistical power grows with the **number of clusters**,
   not with replications inside existing clusters. A suite refresh under high ICC
   should add classes/strata before it adds cases per class.
5. Every experiment contract states its cluster-corrected MDE and effective N
   **before** data, and reports [INCONCLUSIVE](../GLOSSARY.md#inconclusive) rather
   than a false read when the observed margin is smaller than the design can
   resolve. The `MDE ≤ discordance` sanity check (an MDE bigger than the
   discordance it is computed from is arithmetically impossible) catches a
   first-pass arithmetic error before it ships.

Encoded in: [04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md)
(statistics canon); `templates/EXPERIMENT_CONTRACT.md` §10 (statistical plan:
clustering unit, expected discordance, cluster-corrected MDE + effective N,
primary/secondary test declared before freeze); `references/STATISTICS_FORMULAS.md`
(DEFF / effective-N / MDE formulas, worked example).

## What would NOT have worked

- **Adding more TEST cases inside the same 12 classes.** With m already at 8 and
  ICC at 0.475, DEFF is set almost entirely by the clustering, not by N; growing N
  without growing the number of classes barely moves effective N. Suite v4's
  refresh design deliberately adds classes first for exactly this reason.
- **Trusting the McNemar exact secondary statistic alone.** McNemar assumes
  independent discordant pairs; measured ICC = 0.475 makes that assumption false
  for this suite, and the test would read as more decisive than the clustered data
  support — the anti-conservative failure mode the statistics canon names it for.
- **Treating the DEV-stage margin as confirmatory.** The 4-case gap that qualified
  Qwen3.8-27B over Bonsai at DEV was roughly an order of magnitude smaller than
  DEV's own cluster-corrected MDE; it was informative for a gross gate, not for
  ranking.

## References

- INT-CASE-002 (this case; source of record: `learning.case_scores ⋈
  learning.trajectories`, R6 registry)
- [EXT-STATS-001] Miller, "Adding Error Bars to Evals" (arXiv:2411.00640) —
  clustered/paired SE formulas and the power/MDE machinery applied above
- [NV-EVALSDK-001] NVIDIA NeMo Evaluator SDK — paired McNemar testing, power/MDE
  tables, GO/NO-GO gating with 95% CIs (the secondary-statistic precedent this case
  qualifies)
- [EXT-TESTBED-003] Efficient-eval / small-model-set reliability literature
  (tinyBenchmarks, Anchor Points, IRT-reliability) — corroborates that item count
  alone overstates a suite's ranking reliability

---

[Index](../README.md) · [Examples](README.md)
